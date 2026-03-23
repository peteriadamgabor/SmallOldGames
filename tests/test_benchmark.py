from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from smalloldgames.data.benchmark_results import save_benchmark_result
from smalloldgames.engine import GameAction
from smalloldgames.engine.debug_overlay import FrameProfile
from smalloldgames.engine.input import InputState
from smalloldgames.benchmark import main as benchmark_main
from smalloldgames.games.benchmark import BenchmarkScene


class BenchmarkTests(unittest.TestCase):
    def test_save_benchmark_result_writes_latest_and_archive_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "benchmark_latest.json"
            latest, archive = save_benchmark_result({"finished_at": "2026-03-23T12:00:00+00:00", "status": "ok"}, path=target)

            self.assertEqual(latest, target)
            self.assertTrue(latest.exists())
            self.assertTrue(archive.exists())
            self.assertEqual(json.loads(latest.read_text(encoding="utf-8"))["status"], "ok")

    def test_benchmark_scene_runs_all_stages_and_saves_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            printed: list[str] = []
            scene = BenchmarkScene(
                lambda: None,
                stage_duration_seconds=0.02,
                results_path=Path(temp_dir) / "benchmark_latest.json",
                printer=printed.append,
            )

            for frame_index in range(12):
                scene.capture_frame_profile(
                    FrameProfile(
                        fps=120.0 - frame_index,
                        frame_ms=8.0 + frame_index * 0.1,
                        update_ms=1.0,
                        render_ms=0.6,
                        submit_ms=0.4,
                        gpu_frame_ms=2.0 + frame_index * 0.05,
                        idle_ms=5.0,
                        fixed_updates=1,
                        vertex_count=200 + frame_index * 10,
                        scene_name="Benchmark",
                        scene_stack_depth=0,
                    )
                )
                scene.update(0.01, InputState())

            self.assertTrue(scene.finished)
            self.assertFalse(scene.cancelled)
            self.assertIsNotNone(scene.saved_results_path)
            report = json.loads(scene.saved_results_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "completed")
            self.assertEqual(report["stage_count"], 4)
            self.assertEqual(len(report["stages"]), 4)
            self.assertGreater(report["overall"]["avg_gpu_frame_ms"], 0.0)
            self.assertTrue(any("saved results" in line for line in printed))

    def test_benchmark_scene_can_save_partial_run_on_back(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            printed: list[str] = []
            scene = BenchmarkScene(
                lambda: None,
                stage_duration_seconds=0.20,
                results_path=Path(temp_dir) / "benchmark_latest.json",
                printer=printed.append,
            )
            scene.capture_frame_profile(
                FrameProfile(
                    fps=90.0,
                    frame_ms=11.0,
                    update_ms=1.4,
                    render_ms=0.9,
                    submit_ms=0.5,
                    idle_ms=8.2,
                    fixed_updates=1,
                    vertex_count=320,
                    scene_name="Benchmark",
                    scene_stack_depth=0,
                )
            )
            inputs = InputState()
            inputs.actions_pressed.add(GameAction.BACK)
            scene.update(0.01, inputs)

            self.assertTrue(scene.finished)
            self.assertTrue(scene.cancelled)
            report = json.loads(scene.saved_results_path.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "cancelled")
            self.assertEqual(len(report["stages"]), 1)
            self.assertFalse(report["stages"][0]["completed"])
            self.assertTrue(any("partial results" in line for line in printed))

    def test_benchmark_scene_can_request_auto_exit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            scene = BenchmarkScene(
                lambda: None,
                stage_duration_seconds=0.01,
                results_path=Path(temp_dir) / "benchmark_latest.json",
                auto_exit_on_finish=True,
                printer=lambda *_args, **_kwargs: None,
            )

            for _ in range(8):
                scene.capture_frame_profile(
                    FrameProfile(
                        fps=120.0,
                        frame_ms=8.0,
                        update_ms=1.0,
                        render_ms=0.5,
                        submit_ms=0.4,
                        idle_ms=6.1,
                        fixed_updates=1,
                        vertex_count=100,
                        scene_name="Benchmark",
                        scene_stack_depth=0,
                    )
                )
                scene.update(0.01, InputState())

            self.assertTrue(scene.finished)
            self.assertTrue(scene.should_quit_app())

    def test_benchmark_module_runs_headless_and_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "benchmark.json"
            result = benchmark_main(["--benchmark-stage-duration", "0.01", "--benchmark-output", str(output_path)])

            self.assertEqual(result, 0)
            self.assertTrue(output_path.exists())
            self.assertEqual(json.loads(output_path.read_text(encoding="utf-8"))["status"], "completed")

    def test_benchmark_module_can_forward_to_interactive_app(self) -> None:
        with patch("smalloldgames.benchmark.app_main", return_value=0) as app_main:
            result = benchmark_main(["--interactive", "--benchmark-stage-duration", "0.2"])

        self.assertEqual(result, 0)
        forwarded = app_main.call_args.args[0]
        self.assertEqual(forwarded[:3], ["--benchmark", "--benchmark-stage-duration", "0.2"])
        self.assertIn("--benchmark-output", forwarded)


if __name__ == "__main__":
    unittest.main()
