from __future__ import annotations

import sys
import time

import glfw

from smalloldgames.assets import SHADERS_DIR, font_glyphs_from_atlas
from smalloldgames.data.storage import ScoreRepository
from smalloldgames.games.sketch_hopper import SketchHopperScene
from smalloldgames.games.sketch_hopper_game.assets import SKETCH_HOPPER_ATLAS
from smalloldgames.menus import LeaderboardScene, LauncherScene
from smalloldgames.rendering.primitives import DrawList
from smalloldgames.rendering.vulkan_renderer import VulkanRenderer

from .audio import AudioEngine
from .game_registry import GameDefinition, GameRegistry
from .input import InputState
from .scene import Scene

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


class App:
    def __init__(self) -> None:
        self.audio = AudioEngine()
        self.score_repository = ScoreRepository()
        self.window = None
        self.renderer = None
        self.draw_list = None
        self.games = None
        self.scene = None
        self.inputs = InputState()
        self._glfw_initialized = False

        try:
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

            glfw.set_key_callback(self.window, self._on_key)
            glfw.set_cursor_pos_callback(self.window, self._on_cursor_pos)
            glfw.set_mouse_button_callback(self.window, self._on_mouse_button)

            shader_dir = SHADERS_DIR
            self.renderer = VulkanRenderer(self.window, shader_dir=shader_dir, sprite_atlas=SKETCH_HOPPER_ATLAS)
            self.draw_list = DrawList(
                WINDOW_WIDTH,
                WINDOW_HEIGHT,
                white_uv=SKETCH_HOPPER_ATLAS.white_uv,
                font_glyphs=font_glyphs_from_atlas(SKETCH_HOPPER_ATLAS),
            )
            self.games = GameRegistry(
                (
                    GameDefinition(
                        id="sketch_hopper",
                        title="SKETCH HOPPER",
                        subtitle="ENDLESS JUMPER",
                        detail="PRESS ENTER OR SPACE",
                        score_key="sketch_hopper",
                        art_variant="hopper",
                        music_track="sketch_hopper",
                        make_scene=self._make_sketch_hopper,
                    ),
                )
            )
            self.scene = self._make_launcher()
            self.audio.play_music(self.scene.music_track())
        except Exception:
            self.close()
            raise

    def run(self) -> None:
        last_time = time.perf_counter()
        accumulator = 0.0
        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            now = time.perf_counter()
            frame_time = min(now - last_time, MAX_FRAME_DT)
            last_time = now
            accumulator += frame_time

            consumed_inputs = False
            while accumulator >= FIXED_DT:
                replacement = self.scene.update(FIXED_DT, self.inputs)
                accumulator -= FIXED_DT
                if not consumed_inputs:
                    self.inputs.end_frame()
                    consumed_inputs = True
                if replacement is not None:
                    self.scene = replacement
                    self.audio.play_music(self.scene.music_track())
                    accumulator = 0.0
                    break

            glfw.set_window_title(self.window, self.scene.window_title())

            self.draw_list.clear()
            self.draw_list.set_camera(0.0)
            self.scene.render(self.draw_list)
            self.renderer.render(self.draw_list.vertices)

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

    def _make_sketch_hopper(self) -> SketchHopperScene:
        return SketchHopperScene(self._make_launcher, score_repository=self.score_repository, audio=self.audio)

    def _make_launcher(self) -> LauncherScene:
        return LauncherScene(self.games.all(), self._make_leaderboard, score_repository=self.score_repository)

    def _make_leaderboard(self, game: GameDefinition | None = None) -> LeaderboardScene:
        return LeaderboardScene(self._make_launcher, game or self.games.primary(), score_repository=self.score_repository)

    def _on_key(self, _window: glfw._GLFWwindow, key: int, _scancode: int, action: int, _mods: int) -> None:
        self.inputs.on_key(key, action)
        if key == glfw.KEY_Q and action == glfw.PRESS:
            glfw.set_window_should_close(self.window, True)

    def _on_cursor_pos(self, _window: glfw._GLFWwindow, xpos: float, ypos: float) -> None:
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

    def _on_mouse_button(self, _window: glfw._GLFWwindow, button: int, action: int, _mods: int) -> None:
        if button == glfw.MOUSE_BUTTON_LEFT:
            self.inputs.on_pointer(action)


def main() -> int:
    try:
        app = App()
    except RuntimeError as error:
        print(f"Startup error: {error}", file=sys.stderr)
        return 1
    try:
        app.run()
    finally:
        app.close()
    return 0
