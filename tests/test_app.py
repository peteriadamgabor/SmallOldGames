from __future__ import annotations

from array import array
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from smalloldgames.engine.debug_overlay import FrameProfile
from smalloldgames.engine.app import WINDOW_HEIGHT, WINDOW_WIDTH, App, RuntimeLoop, _content_rect, _parse_args, _resolve_database_path
from smalloldgames.engine.scene import Pop, Push, Transition


class _FakeScene:
    def __init__(self, *, title: str = "Scene", track: str | None = "launcher", update_result=None) -> None:
        self.title = title
        self.track = track
        self.update_result = update_result
        self.entered = 0
        self.exited = 0
        self.updated: list[float] = []
        self.render_calls = 0
        self.captured_profiles: list[FrameProfile] = []

    def update(self, dt: float, _inputs) -> object:
        self.updated.append(dt)
        return self.update_result

    def render(self, _draw) -> None:
        self.render_calls += 1

    def window_title(self) -> str:
        return self.title

    def music_track(self) -> str | None:
        return self.track

    def on_enter(self) -> None:
        self.entered += 1

    def on_exit(self) -> None:
        self.exited += 1

    def capture_frame_profile(self, profile: FrameProfile) -> None:
        self.captured_profiles.append(profile)


class _FakeDrawList:
    def __init__(self) -> None:
        self.vertices = array("f", [0.0] * 8)
        self.clear_calls = 0
        self.camera = None
        self.text_calls = 0
        self.quad_calls = 0

    def clear(self) -> None:
        self.clear_calls += 1

    def set_camera(self, value: float) -> None:
        self.camera = value

    def measure_text(self, _text: str, *, scale: float) -> float:
        return 24.0 * scale

    def quad(self, *_args, **_kwargs) -> None:
        self.quad_calls += 1

    def text(self, *_args, **_kwargs) -> None:
        self.text_calls += 1


class AppLayoutTests(unittest.TestCase):
    def test_content_rect_letterboxes_wider_window(self) -> None:
        x, y, width, height = _content_rect(1200, 960)
        self.assertEqual(height, 960.0)
        self.assertEqual(width, WINDOW_WIDTH * (960 / WINDOW_HEIGHT))
        self.assertGreater(x, 0.0)
        self.assertEqual(y, 0.0)

    def test_content_rect_letterboxes_taller_window(self) -> None:
        x, y, width, height = _content_rect(540, 1400)
        self.assertEqual(width, 540.0)
        self.assertEqual(height, WINDOW_HEIGHT * (540 / WINDOW_WIDTH))
        self.assertEqual(x, 0.0)
        self.assertGreater(y, 0.0)

    def test_benchmark_database_path_defaults_to_tempfile(self) -> None:
        args = _parse_args(["--benchmark"])
        database_path = _resolve_database_path(args)

        self.assertIsNotNone(database_path)
        self.assertIn("smalloldgames-benchmark-scoreboard.sqlite3", database_path)


class AppSceneResultTests(unittest.TestCase):
    def test_transition_replaces_scene_and_updates_music(self) -> None:
        app = App.__new__(App)
        current = _FakeScene(title="Current", track="a")
        next_scene = _FakeScene(title="Next", track="b")
        app.scene = current
        app._scene_stack = [_FakeScene(title="Stacked")]
        app.audio = SimpleNamespace(play_music=Mock())
        app._make_launcher = lambda: _FakeScene(title="Launcher")

        App._apply_scene_result(app, Transition(next_scene))

        self.assertIs(app.scene, next_scene)
        self.assertEqual(current.exited, 1)
        self.assertEqual(next_scene.entered, 1)
        self.assertEqual(app._scene_stack, [])
        app.audio.play_music.assert_called_once_with("b")

    def test_push_and_pop_manage_scene_stack(self) -> None:
        app = App.__new__(App)
        base = _FakeScene(title="Base", track="base")
        overlay = _FakeScene(title="Overlay", track="overlay")
        app.scene = base
        app._scene_stack = []
        app.audio = SimpleNamespace(play_music=Mock())
        app._make_launcher = lambda: _FakeScene(title="Launcher")

        App._apply_scene_result(app, Push(overlay))
        self.assertIs(app.scene, overlay)
        self.assertEqual(app._scene_stack, [base])
        self.assertEqual(base.exited, 1)
        self.assertEqual(overlay.entered, 1)

        App._apply_scene_result(app, Pop())
        self.assertIs(app.scene, base)
        self.assertEqual(app._scene_stack, [])
        self.assertEqual(overlay.exited, 1)
        self.assertEqual(base.entered, 1)


class RuntimeLoopTests(unittest.TestCase):
    @staticmethod
    def _perf_counters() -> list[float]:
        return [
            0.0000,
            0.0100,
            0.0105,
            0.0110,
            0.0115,
            0.0120,
            0.0125,
            0.0130,
        ]

    def _make_app(self) -> SimpleNamespace:
        app = SimpleNamespace()
        app.window = object()
        app.inputs = SimpleNamespace(end_frame=Mock())
        app.draw_list = _FakeDrawList()
        app.renderer = SimpleNamespace(render=Mock())
        app.audio = SimpleNamespace(play_music=Mock())
        app._fps = 0.0
        app._show_debug = False
        app._debug_overlay = SimpleNamespace(render=Mock(), record_frame=Mock())
        app._scene_stack = []
        app._transition_to = Mock()
        app._apply_scene_result = Mock()
        app._make_launcher = Mock()
        app.scene = _FakeScene()
        return app

    def test_runtime_loop_updates_scene_renders_and_consumes_inputs(self) -> None:
        app = self._make_app()
        loop = RuntimeLoop(app)

        with (
            patch("smalloldgames.engine.app.glfw.window_should_close", side_effect=[False, True]),
            patch("smalloldgames.engine.app.glfw.poll_events"),
            patch("smalloldgames.engine.app.glfw.set_window_title") as set_title,
            patch("smalloldgames.engine.app.time.perf_counter", side_effect=self._perf_counters()),
        ):
            loop.run()

        self.assertEqual(app.scene.updated, [0.008333333333333333])
        app.inputs.end_frame.assert_called_once()
        set_title.assert_called_once_with(app.window, "Scene")
        self.assertEqual(app.draw_list.clear_calls, 1)
        self.assertEqual(app.draw_list.camera, 0.0)
        app.renderer.render.assert_called_once_with(app.draw_list.vertices)
        app._debug_overlay.record_frame.assert_called_once()
        self.assertEqual(len(app.scene.captured_profiles), 1)

    def test_runtime_loop_recovers_from_update_failure(self) -> None:
        app = self._make_app()

        class CrashingScene(_FakeScene):
            def update(self, dt: float, _inputs) -> object:
                raise RuntimeError("boom")

        app.scene = CrashingScene()
        launcher = _FakeScene(title="Launcher")
        app._make_launcher.return_value = launcher
        loop = RuntimeLoop(app)

        with (
            patch("smalloldgames.engine.app.glfw.window_should_close", side_effect=[False, True]),
            patch("smalloldgames.engine.app.glfw.poll_events"),
            patch("smalloldgames.engine.app.glfw.set_window_title"),
            patch("smalloldgames.engine.app.time.perf_counter", side_effect=self._perf_counters()),
        ):
            loop.run()

        result = app._apply_scene_result.call_args.args[0]
        self.assertIsInstance(result, Transition)
        self.assertIs(result.scene, launcher)

    def test_runtime_loop_recovers_from_render_failure(self) -> None:
        app = self._make_app()
        bad_scene = _FakeScene()
        bad_scene.render = Mock(side_effect=RuntimeError("render failed"))
        launcher = _FakeScene(title="Launcher")
        app.scene = bad_scene
        app._make_launcher.return_value = launcher

        def transition_to(scene) -> None:
            app.scene = scene

        app._transition_to = Mock(side_effect=transition_to)
        loop = RuntimeLoop(app)

        with (
            patch("smalloldgames.engine.app.glfw.window_should_close", side_effect=[False, True]),
            patch("smalloldgames.engine.app.glfw.poll_events"),
            patch("smalloldgames.engine.app.glfw.set_window_title"),
            patch("smalloldgames.engine.app.time.perf_counter", side_effect=self._perf_counters()),
        ):
            loop.run()

        app._transition_to.assert_called_once_with(launcher)
        self.assertEqual(launcher.render_calls, 1)

    def test_runtime_loop_renders_debug_overlay_when_enabled(self) -> None:
        app = self._make_app()
        app._show_debug = True
        loop = RuntimeLoop(app)

        with (
            patch("smalloldgames.engine.app.glfw.window_should_close", side_effect=[False, True]),
            patch("smalloldgames.engine.app.glfw.poll_events"),
            patch("smalloldgames.engine.app.glfw.set_window_title"),
            patch("smalloldgames.engine.app.time.perf_counter", side_effect=self._perf_counters()),
        ):
            loop.run()

        app._debug_overlay.render.assert_called_once_with(app.draw_list)
        app._debug_overlay.record_frame.assert_called_once()

    def test_runtime_loop_can_request_app_quit_from_scene(self) -> None:
        app = self._make_app()
        app.scene.should_quit_app = Mock(return_value=True)
        loop = RuntimeLoop(app)

        with (
            patch("smalloldgames.engine.app.glfw.window_should_close", side_effect=[False, True]),
            patch("smalloldgames.engine.app.glfw.poll_events"),
            patch("smalloldgames.engine.app.glfw.set_window_title"),
            patch("smalloldgames.engine.app.glfw.set_window_should_close") as set_window_should_close,
            patch("smalloldgames.engine.app.time.perf_counter", side_effect=self._perf_counters()),
        ):
            loop.run()

        set_window_should_close.assert_called_once_with(app.window, True)


if __name__ == "__main__":
    unittest.main()
