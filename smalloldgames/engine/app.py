from __future__ import annotations

import argparse
import logging
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

import glfw

from smalloldgames.data.storage import ScoreRepository
from smalloldgames.games import DEFAULT_GAME_MODULES
from smalloldgames.games.benchmark_game import BenchmarkScene
from smalloldgames.menus import LauncherScene, LeaderboardScene, SettingsScene

from .audio import AudioEngine
from .debug_overlay import DebugOverlay, FrameProfile
from .game_registry import GameDefinition, GameRegistry
from .input import GameAction, InputState
from .resources import ResourceRegistry
from .scene import Pop, Push, SceneContext, Transition

_log = logging.getLogger(__name__)

WINDOW_WIDTH = 540
WINDOW_HEIGHT = 960
FIXED_DT = 1.0 / 120.0
MAX_FRAME_DT = 1.0 / 20.0


def _content_rect(container_width: int, container_height: int) -> tuple[float, float, float, float]:
    scale = min(container_width / WINDOW_WIDTH, container_height / WINDOW_HEIGHT)
    width = WINDOW_WIDTH * scale
    height = WINDOW_HEIGHT * scale
    x = (container_width - width) * 0.5
    y = (container_height - height) * 0.5
    return (x, y, width, height)


class _AppComponent:
    def __init__(self, app: App) -> None:
        object.__setattr__(self, "_app", app)

    def __getattr__(self, name: str):
        return getattr(self._app, name)

    def __setattr__(self, name: str, value) -> None:
        if name == "_app":
            object.__setattr__(self, name, value)
            return
        setattr(self._app, name, value)


class PlatformBootstrap(_AppComponent):
    def initialize(self) -> None:
        self.audio.set_enabled(self.score_repository.get_sound_enabled())

        if not glfw.init():
            raise RuntimeError("GLFW could not initialize. Run the app inside a graphical desktop session.")
        self._glfw_initialized = True

        glfw.window_hint(glfw.CLIENT_API, glfw.NO_API)
        glfw.window_hint(glfw.RESIZABLE, glfw.TRUE)
        self.window = glfw.create_window(WINDOW_WIDTH, WINDOW_HEIGHT, "Small Old Games", None, None)
        if not self.window:
            raise RuntimeError("GLFW could not create a window.")
        glfw.set_window_size_limits(self.window, 360, 640, glfw.DONT_CARE, glfw.DONT_CARE)

        glfw.set_key_callback(self.window, self.on_key)
        glfw.set_cursor_pos_callback(self.window, self.on_cursor_pos)
        glfw.set_mouse_button_callback(self.window, self.on_mouse_button)

        self.renderer = self.resources.create_renderer(
            self.window,
            canvas_width=WINDOW_WIDTH,
            canvas_height=WINDOW_HEIGHT,
        )
        self.draw_list = self.resources.create_draw_list(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.games = GameRegistry.from_modules(
            DEFAULT_GAME_MODULES,
            ctx=self.ctx,
            on_exit=self._make_launcher,
        )
        initial_scene = (
            self._startup_scene_factory(self) if self._startup_scene_factory is not None else self._make_launcher()
        )
        self._transition_to(initial_scene)

    def close(self) -> None:
        try:
            if self.renderer is not None:
                self.renderer.close()
                self.renderer = None
        finally:
            self.score_repository.close()
            self.audio.close()
            if self.window is not None:
                glfw.destroy_window(self.window)
                self.window = None
            if self._glfw_initialized:
                glfw.terminate()
                self._glfw_initialized = False

    def on_key(self, _window: glfw._GLFWwindow, key: int, _scancode: int, action: int, _mods: int) -> None:
        self.inputs.on_key(key, action)
        if action == glfw.PRESS:
            if self.inputs.action_pressed(GameAction.QUIT):
                glfw.set_window_should_close(self.window, True)
            if self.inputs.action_pressed(GameAction.DEBUG_TOGGLE):
                self._show_debug = not self._show_debug

    def on_cursor_pos(self, _window: glfw._GLFWwindow, xpos: float, ypos: float) -> None:
        window_width, window_height = glfw.get_window_size(self.window)
        if window_width <= 0 or window_height <= 0:
            self.inputs.on_cursor_pos(-1000.0, -1000.0)
            return
        content_x, content_y, content_width, content_height = _content_rect(window_width, window_height)
        if (
            xpos < content_x
            or xpos > content_x + content_width
            or ypos < content_y
            or ypos > content_y + content_height
        ):
            self.inputs.on_cursor_pos(-1000.0, -1000.0)
            return
        scale = content_width / WINDOW_WIDTH
        local_x = (xpos - content_x) / scale
        local_y = WINDOW_HEIGHT - (ypos - content_y) / scale
        self.inputs.on_cursor_pos(local_x, local_y)

    def on_mouse_button(self, _window: glfw._GLFWwindow, button: int, action: int, _mods: int) -> None:
        if button == glfw.MOUSE_BUTTON_LEFT:
            self.inputs.on_pointer(action)


class RuntimeLoop(_AppComponent):
    def run(self) -> None:
        last_time = time.perf_counter()
        accumulator = 0.0
        fps_timer = 0.0
        fps_counter = 0
        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            frame_start = time.perf_counter()
            frame_time = min(frame_start - last_time, MAX_FRAME_DT)
            last_time = frame_start
            accumulator += frame_time

            fps_timer += frame_time
            fps_counter += 1
            if fps_timer >= 0.5:
                self._fps = fps_counter / fps_timer
                fps_timer = 0.0
                fps_counter = 0

            set_touch_regions = getattr(self.inputs, "set_touch_regions", None)
            if callable(set_touch_regions):
                touch_regions = getattr(self.scene, "touch_regions", None)
                if callable(touch_regions):
                    set_touch_regions(tuple(touch_regions()))
                else:
                    set_touch_regions(())

            consumed_inputs = False
            fixed_updates = 0
            update_started = time.perf_counter()
            while accumulator >= FIXED_DT:
                try:
                    result = self.scene.update(FIXED_DT, self.inputs)
                except Exception:
                    _log.exception("Scene update failed, returning to launcher")
                    result = Transition(self._make_launcher())
                fixed_updates += 1
                accumulator -= FIXED_DT
                if not consumed_inputs:
                    self.inputs.end_frame()
                    consumed_inputs = True
                if result is not None:
                    self._apply_scene_result(result)
                    accumulator = 0.0
                    break
            update_ms = (time.perf_counter() - update_started) * 1000.0

            glfw.set_window_title(self.window, self.scene.window_title())

            render_started = time.perf_counter()
            self.draw_list.clear()
            self.draw_list.set_camera(0.0)
            try:
                self.scene.render(self.draw_list)
            except Exception:
                _log.exception("Scene render failed, returning to launcher")
                self._transition_to(self._make_launcher())
                self.scene.render(self.draw_list)

            if self._show_debug:
                self._debug_overlay.render(self.draw_list)
            render_ms = (time.perf_counter() - render_started) * 1000.0

            submit_started = time.perf_counter()
            self.renderer.render(self.draw_list.vertices)
            should_quit_app = getattr(self.scene, "should_quit_app", None)
            if callable(should_quit_app) and should_quit_app():
                glfw.set_window_should_close(self.window, True)
            frame_end = time.perf_counter()
            submit_ms = (frame_end - submit_started) * 1000.0
            frame_ms = (frame_end - frame_start) * 1000.0
            idle_ms = max(0.0, frame_ms - update_ms - render_ms - submit_ms)
            profile = FrameProfile(
                fps=self._fps,
                frame_ms=frame_ms,
                update_ms=update_ms,
                render_ms=render_ms,
                submit_ms=submit_ms,
                gpu_frame_ms=getattr(self.renderer, "last_gpu_frame_ms", 0.0),
                idle_ms=idle_ms,
                fixed_updates=fixed_updates,
                vertex_count=len(self.draw_list.vertices) // 8,
                scene_name=self.scene.window_title(),
                scene_stack_depth=len(self._scene_stack),
            )
            self._debug_overlay.record_frame(profile)
            capture_frame_profile = getattr(self.scene, "capture_frame_profile", None)
            if callable(capture_frame_profile):
                try:
                    capture_frame_profile(profile)
                except Exception:
                    _log.exception("Scene frame-profile capture failed")


class App:
    def __init__(
        self,
        *,
        startup_scene_factory: Callable[[App], object] | None = None,
        score_repository_path: str | Path | None = None,
    ) -> None:
        self.audio = AudioEngine()
        self.score_repository = ScoreRepository(score_repository_path)
        self.resources = ResourceRegistry()
        self.ctx = SceneContext(score_repository=self.score_repository, audio=self.audio)
        self.window = None
        self.renderer = None
        self.draw_list = None
        self.games = None
        self.scene = None
        self.inputs = InputState()
        self._scene_stack: list = []
        self._glfw_initialized = False
        self._show_debug = False
        self._fps = 0.0
        self._startup_scene_factory = startup_scene_factory
        self._debug_overlay = DebugOverlay()
        self._platform = PlatformBootstrap(self)
        self._runtime = RuntimeLoop(self)

        try:
            self._platform.initialize()
        except Exception:
            self.close()
            raise

    def _apply_scene_result(self, result: Transition | Push | Pop) -> None:
        if isinstance(result, Transition):
            if self.scene is not None:
                self.scene.on_exit()
            self._scene_stack.clear()
            self.scene = result.scene
            self.scene.on_enter()
        elif isinstance(result, Push):
            if self.scene is not None:
                self.scene.on_exit()
                self._scene_stack.append(self.scene)
            self.scene = result.scene
            self.scene.on_enter()
        elif isinstance(result, Pop):
            if self.scene is not None:
                self.scene.on_exit()
            if self._scene_stack:
                self.scene = self._scene_stack.pop()
                self.scene.on_enter()
            else:
                self.scene = self._make_launcher()
                self.scene.on_enter()
        self.audio.play_music(self.scene.music_track())

    def _transition_to(self, new_scene) -> None:
        self._apply_scene_result(Transition(new_scene))

    def run(self) -> None:
        self._runtime.run()

    def close(self) -> None:
        self._platform.close()

    def _make_launcher(self) -> LauncherScene:
        return LauncherScene(
            self.games.all(),
            self._make_leaderboard,
            self._make_settings,
            ctx=self.ctx,
        )

    def _make_leaderboard(self, game: GameDefinition | None = None) -> LeaderboardScene:
        return LeaderboardScene(
            self._make_launcher,
            self.games.all(),
            game or self.games.primary(),
            ctx=self.ctx,
        )

    def _make_settings(self) -> SettingsScene:
        return SettingsScene(
            self._make_launcher,
            ctx=self.ctx,
            on_sound_changed=self.audio.set_enabled,
        )


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    startup_scene_factory = _benchmark_startup_scene_factory(args) if args.benchmark else None
    score_repository_path = _resolve_database_path(args)
    try:
        app = App(
            startup_scene_factory=startup_scene_factory,
            score_repository_path=score_repository_path,
        )
    except RuntimeError as error:
        print(f"Startup error: {error}", file=sys.stderr)
        return 1
    try:
        app.run()
    finally:
        app.close()
    return 0


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="smalloldgames")
    parser.add_argument("--benchmark", action="store_true", help="Start the automated benchmark scene directly.")
    parser.add_argument(
        "--benchmark-output",
        default=None,
        help="Optional JSON output path for benchmark results.",
    )
    parser.add_argument(
        "--benchmark-stage-duration",
        type=float,
        default=2.5,
        help="Duration in seconds for each benchmark stage.",
    )
    parser.add_argument(
        "--benchmark-keep-open",
        action="store_true",
        help="Do not auto-close the app when the benchmark finishes.",
    )
    parser.add_argument(
        "--database-path",
        default=None,
        help="Optional scoreboard database path. Benchmark mode defaults to a temp database if omitted.",
    )
    return parser.parse_args(argv)


def _benchmark_startup_scene_factory(args: argparse.Namespace) -> Callable[[App], BenchmarkScene]:
    def make_scene(app: App) -> BenchmarkScene:
        return BenchmarkScene(
            app._make_launcher,
            ctx=app.ctx,
            stage_duration_seconds=args.benchmark_stage_duration,
            results_path=args.benchmark_output,
            auto_exit_on_finish=not args.benchmark_keep_open,
        )

    return make_scene


def _resolve_database_path(args: argparse.Namespace) -> str | None:
    if args.database_path is not None:
        return args.database_path
    if args.benchmark:
        return str(Path(tempfile.gettempdir()) / "smalloldgames-benchmark-scoreboard.sqlite3")
    return None
