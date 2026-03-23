from __future__ import annotations

import argparse
import tempfile
import time
from pathlib import Path

from smalloldgames.engine import InputState, ResourceRegistry
from smalloldgames.engine.app import main as app_main
from smalloldgames.engine.debug_overlay import FrameProfile
from smalloldgames.games.benchmark_game import BenchmarkScene
from smalloldgames.rendering.primitives import DrawList


class _HeadlessExitScene:
    def update(self, dt: float, inputs: InputState):
        return None

    def render(self, draw: DrawList) -> None:
        return None

    def window_title(self) -> str:
        return "Small Old Games - Headless Benchmark Exit"

    def music_track(self) -> str | None:
        return None

    def on_enter(self) -> None:
        return None

    def on_exit(self) -> None:
        return None


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.interactive:
        return _run_interactive(args)
    return _run_headless(args)


def _run_headless(args: argparse.Namespace) -> int:
    print("[benchmark] mode=headless")
    scene = BenchmarkScene(
        lambda: _HeadlessExitScene(),
        stage_duration_seconds=args.benchmark_stage_duration,
        results_path=args.benchmark_output,
        auto_exit_on_finish=True,
    )
    resources = ResourceRegistry()
    draw_list = resources.create_draw_list(540, 960)
    inputs = InputState()
    dt = 1.0 / 60.0
    max_frames = max(60, int((args.benchmark_stage_duration * 60.0 * 8.0) + 60.0))

    for _ in range(max_frames):
        frame_start = time.perf_counter()
        update_start = time.perf_counter()
        scene.update(dt, inputs)
        update_ms = (time.perf_counter() - update_start) * 1000.0

        render_start = time.perf_counter()
        draw_list.clear()
        draw_list.set_camera(0.0)
        scene.render(draw_list)
        render_ms = (time.perf_counter() - render_start) * 1000.0

        frame_ms = (time.perf_counter() - frame_start) * 1000.0
        scene.capture_frame_profile(
            FrameProfile(
                fps=1000.0 / frame_ms if frame_ms > 0.0 else 0.0,
                frame_ms=frame_ms,
                update_ms=update_ms,
                render_ms=render_ms,
                submit_ms=0.0,
                idle_ms=0.0,
                fixed_updates=1,
                vertex_count=len(draw_list.vertices) // 8,
                scene_name=scene.window_title(),
                scene_stack_depth=0,
            )
        )
        if scene.finished:
            print(f"[benchmark] headless result file {scene.saved_results_path}")
            return 0
        inputs.end_frame()

    print("[benchmark] headless runner hit frame cap before completion")
    return 1


def _run_interactive(args: argparse.Namespace) -> int:
    forwarded = [
        "--benchmark",
        "--benchmark-stage-duration",
        str(args.benchmark_stage_duration),
    ]
    if args.benchmark_output is not None:
        forwarded.extend(["--benchmark-output", args.benchmark_output])
    if args.database_path is not None:
        forwarded.extend(["--database-path", args.database_path])
    if args.keep_open:
        forwarded.append("--benchmark-keep-open")
    return app_main(forwarded)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="smalloldgames-benchmark")
    parser.add_argument(
        "--benchmark-output",
        default=str(Path(tempfile.gettempdir()) / "smalloldgames-benchmark.json"),
        help="Path for the latest benchmark JSON report.",
    )
    parser.add_argument(
        "--benchmark-stage-duration",
        type=float,
        default=2.5,
        help="Duration in seconds for each benchmark stage.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run through the full GLFW/Vulkan app instead of the headless draw-list runner.",
    )
    parser.add_argument(
        "--keep-open",
        action="store_true",
        help="Interactive mode only: keep the window open when the benchmark finishes.",
    )
    parser.add_argument(
        "--database-path",
        default=None,
        help="Interactive mode only: optional scoreboard database path override.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
