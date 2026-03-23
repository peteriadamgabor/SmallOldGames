from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

from smalloldgames.assets import COMBINED_ATLAS
from smalloldgames.data.benchmark_results import save_benchmark_result
from smalloldgames.engine import GameAction, InputState, Scene, SceneContext, SceneResult, Transition
from smalloldgames.engine.debug_overlay import FrameProfile
from smalloldgames.menus.common import ACCENT, GOOD, TEXT_LIGHT, TEXT_MUTED, draw_menu_background
from smalloldgames.rendering.primitives import DrawList

BLACK_HOLE_SPRITE = COMBINED_ATLAS.sprites["black_hole"]
CLOUD_SPRITE = COMBINED_ATLAS.sprites["cloud"]
HOPPER_SPRITE = COMBINED_ATLAS.sprites["hopper"]
MONSTER_SPRITE = COMBINED_ATLAS.sprites["monster"]
PLATFORM_SPRITE = COMBINED_ATLAS.sprites["platform_stable"]


@dataclass(frozen=True, slots=True)
class BenchmarkStageSpec:
    name: str
    subtitle: str
    quad_count: int
    sprite_count: int
    text_rows: int
    duration_seconds: float


@dataclass(frozen=True, slots=True)
class BenchmarkStageResult:
    index: int
    name: str
    subtitle: str
    duration_seconds: float
    sample_count: int
    avg_fps: float
    avg_frame_ms: float
    p95_frame_ms: float
    avg_update_ms: float
    avg_render_ms: float
    avg_submit_ms: float
    avg_gpu_frame_ms: float
    p95_gpu_frame_ms: float
    avg_vertices: float
    max_vertices: int
    completed: bool


class BenchmarkSummary(TypedDict):
    sample_count: int
    avg_fps: float
    avg_frame_ms: float
    p95_frame_ms: float
    avg_update_ms: float
    avg_render_ms: float
    avg_submit_ms: float
    avg_gpu_frame_ms: float
    p95_gpu_frame_ms: float
    avg_vertices: float
    max_vertices: int


class BenchmarkScene:
    def __init__(
        self,
        on_exit: Callable[[], Scene],
        *,
        ctx: SceneContext | None = None,
        stage_duration_seconds: float = 2.5,
        results_path: str | Path | None = None,
        auto_exit_on_finish: bool = False,
        printer: Callable[[str], object] | None = None,
        stages: tuple[BenchmarkStageSpec, ...] | None = None,
    ) -> None:
        self.exit_scene_factory = on_exit
        self.ctx = ctx
        self.printer = print if printer is None else printer
        self.results_path = Path(results_path) if results_path is not None else None
        self.auto_exit_on_finish = auto_exit_on_finish
        self.stages = stages or _default_stages(stage_duration_seconds)
        self.reset()

    def reset(self) -> None:
        self.started_at = datetime.now(UTC)
        self.finished_at = self.started_at
        self.stage_index = 0
        self.stage_elapsed = 0.0
        self.animation_time = 0.0
        self.finished = False
        self.cancelled = False
        self.stage_results: list[BenchmarkStageResult] = []
        self._stage_samples: list[FrameProfile] = []
        self._all_samples: list[FrameProfile] = []
        self.saved_results_path: Path | None = None
        self.saved_archive_path: Path | None = None
        self.report: dict | None = None
        self.quit_requested = False
        self.printer(f"[benchmark] starting run with {len(self.stages)} stages")

    def update(self, dt: float, inputs: InputState) -> SceneResult:
        if inputs.action_pressed(GameAction.BACK):
            if not self.finished:
                self._finish(cancelled=True)
                return None
            return Transition(self.exit_scene_factory())

        if self.finished:
            if inputs.action_pressed(GameAction.CONFIRM, GameAction.RESTART):
                self.reset()
            return None

        self.animation_time += dt
        self.stage_elapsed += dt
        if self.stage_elapsed >= self._current_stage().duration_seconds:
            self._complete_stage()
        return None

    def render(self, draw: DrawList) -> None:
        draw_menu_background(draw)
        draw.text(draw.width * 0.5, 880, "BENCHMARK", scale=5, color=TEXT_LIGHT, centered=True)
        draw.text(draw.width * 0.5, 842, "AUTOMATED STRESS RUN", scale=2, color=TEXT_MUTED, centered=True)

        if self.finished:
            self._render_summary(draw)
            return

        stage = self._current_stage()
        progress = min(1.0, self.stage_elapsed / stage.duration_seconds) if stage.duration_seconds > 0.0 else 1.0

        draw.quad(36.0, 766.0, 468.0, 92.0, (0.06, 0.08, 0.15, 0.78), world=False)
        draw.text(56.0, 824.0, f"STAGE {self.stage_index + 1}/{len(self.stages)}  {stage.name}", scale=3, color=ACCENT)
        draw.text(56.0, 796.0, stage.subtitle, scale=2, color=TEXT_MUTED)
        draw.text(56.0, 772.0, "ESC SAVES PARTIAL RESULT   ENTER RESTARTS AFTER FINISH", scale=1, color=TEXT_MUTED)
        draw.quad(56.0, 750.0, 428.0, 10.0, (0.12, 0.15, 0.22, 1.0), world=False)
        draw.quad(56.0, 750.0, 428.0 * progress, 10.0, GOOD, world=False)

        self._render_stage_content(draw, stage)

    @staticmethod
    def music_track() -> str | None:
        return None

    @staticmethod
    def window_title() -> str:
        return "Small Old Games - Benchmark"

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def capture_frame_profile(self, profile: FrameProfile) -> None:
        if self.finished:
            return
        self._stage_samples.append(profile)

    def should_quit_app(self) -> bool:
        return self.quit_requested

    def _render_stage_content(self, draw: DrawList, stage: BenchmarkStageSpec) -> None:
        for index in range(stage.quad_count):
            size = 8.0 + (index % 4) * 6.0
            x = (index * 29.0 + self.animation_time * (22.0 + (index % 5) * 6.0)) % (draw.width + size) - size
            y = 132.0 + ((index * 47.0 + self.animation_time * (18.0 + (index % 7) * 5.0)) % 584.0)
            draw.quad(x, y, size, size, _quad_color(index), world=False)

        sprites = (CLOUD_SPRITE, PLATFORM_SPRITE, HOPPER_SPRITE, MONSTER_SPRITE, BLACK_HOLE_SPRITE)
        for index in range(stage.sprite_count):
            sprite = sprites[index % len(sprites)]
            width = 18.0 + (index % 4) * 10.0
            height = width if sprite is not PLATFORM_SPRITE else width * 0.42
            x = (index * 41.0 + self.animation_time * (34.0 + (index % 6) * 4.0)) % (draw.width + width) - width
            y = 126.0 + ((index * 63.0 + self.animation_time * (16.0 + (index % 5) * 3.0)) % 570.0)
            if sprite is HOPPER_SPRITE:
                y += math.sin(self.animation_time * 4.0 + index * 0.3) * 10.0
            draw.sprite(x, y, sprite, width=width, height=height, world=False, flip_x=index % 2 == 0)

        for row in range(stage.text_rows):
            line = f"{stage.name} LOAD {row + 1:02d}"
            x = 42.0 + (row % 3) * 150.0
            y = 154.0 + ((row * 24.0 + self.animation_time * 12.0) % 520.0)
            draw.text(x, y, line, scale=2, color=TEXT_LIGHT if row % 2 == 0 else TEXT_MUTED)

    def _render_summary(self, draw: DrawList) -> None:
        draw.quad(30.0, 190.0, 480.0, 606.0, (0.05, 0.08, 0.14, 0.82), world=False)
        title = "BENCHMARK COMPLETE" if not self.cancelled else "BENCHMARK CANCELLED"
        draw.text(draw.width * 0.5, 760, title, scale=4, color=GOOD if not self.cancelled else ACCENT, centered=True)
        draw.text(
            draw.width * 0.5,
            726,
            "ENTER RUNS AGAIN   ESC RETURNS TO LAUNCHER",
            scale=2,
            color=TEXT_MUTED,
            centered=True,
        )

        y = 676.0
        for result in self.stage_results[-4:]:
            line = (
                f"S{result.index + 1} {result.name:<10} "
                f"FPS {int(result.avg_fps):03d}  "
                f"AVG {result.avg_frame_ms:04.1f}  "
                f"P95 {result.p95_frame_ms:04.1f}  "
                f"GPU {result.avg_gpu_frame_ms:04.1f}"
            )
            draw.text(48.0, y, line, scale=2, color=TEXT_LIGHT)
            y -= 34.0

        latest_name = self.saved_results_path.name if self.saved_results_path is not None else "pending"
        draw.text(48.0, 252.0, f"RESULT FILE {latest_name}", scale=2, color=ACCENT)
        draw.text(48.0, 224.0, "JSON LATEST + TIMESTAMPED ARCHIVE WRITTEN TO .SMALLOLDGAMES", scale=1, color=TEXT_MUTED)

    def _complete_stage(self) -> None:
        stage = self._current_stage()
        result = _summarize_stage(stage, self.stage_index, self._stage_samples, completed=True)
        self.stage_results.append(result)
        self._all_samples.extend(self._stage_samples)
        self.printer(
            f"[benchmark] stage {self.stage_index + 1}/{len(self.stages)} {stage.name}: "
            f"avg_fps={result.avg_fps:.1f} avg_ms={result.avg_frame_ms:.2f} "
            f"p95_ms={result.p95_frame_ms:.2f} gpu_ms={result.avg_gpu_frame_ms:.2f}"
        )
        self._stage_samples = []
        self.stage_elapsed = 0.0
        self.stage_index += 1
        if self.stage_index >= len(self.stages):
            self._finish(cancelled=False)

    def _finish(self, *, cancelled: bool) -> None:
        if self.finished:
            return
        if self._stage_samples and self.stage_index < len(self.stages):
            stage = self._current_stage()
            partial = _summarize_stage(stage, self.stage_index, self._stage_samples, completed=False)
            self.stage_results.append(partial)
            self._all_samples.extend(self._stage_samples)
            self._stage_samples = []
        self.finished = True
        self.cancelled = cancelled
        self.finished_at = datetime.now(UTC)
        self.report = self._build_report()
        self.saved_results_path, self.saved_archive_path = save_benchmark_result(self.report, path=self.results_path)
        self.quit_requested = self.auto_exit_on_finish
        self.printer(f"[benchmark] saved {'partial ' if cancelled else ''}results to {self.saved_results_path}")
        overall = self.report["overall"]
        self.printer(
            f"[benchmark] overall avg_fps={overall['avg_fps']:.1f} "
            f"avg_ms={overall['avg_frame_ms']:.2f} p95_ms={overall['p95_frame_ms']:.2f} "
            f"gpu_ms={overall['avg_gpu_frame_ms']:.2f}"
        )

    def _build_report(self) -> dict:
        overall = _summarize_samples(self._all_samples)
        return {
            "status": "cancelled" if self.cancelled else "completed",
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "stage_count": len(self.stages),
            "stages": [asdict(result) for result in self.stage_results],
            "overall": {
                "sample_count": overall["sample_count"],
                "avg_fps": overall["avg_fps"],
                "avg_frame_ms": overall["avg_frame_ms"],
                "p95_frame_ms": overall["p95_frame_ms"],
                "avg_update_ms": overall["avg_update_ms"],
                "avg_render_ms": overall["avg_render_ms"],
                "avg_submit_ms": overall["avg_submit_ms"],
                "avg_gpu_frame_ms": overall["avg_gpu_frame_ms"],
                "p95_gpu_frame_ms": overall["p95_gpu_frame_ms"],
                "avg_vertices": overall["avg_vertices"],
                "max_vertices": overall["max_vertices"],
            },
        }

    def _current_stage(self) -> BenchmarkStageSpec:
        return self.stages[min(self.stage_index, len(self.stages) - 1)]


def _default_stages(stage_duration_seconds: float) -> tuple[BenchmarkStageSpec, ...]:
    return (
        BenchmarkStageSpec("BASELINE", "LIGHT QUADS AND SPRITES", 18, 12, 4, stage_duration_seconds),
        BenchmarkStageSpec("ACTIVE", "MID-WEIGHT FILL AND TEXT", 72, 48, 10, stage_duration_seconds),
        BenchmarkStageSpec("HEAVY", "DENSE UI AND SPRITE CHURN", 144, 96, 16, stage_duration_seconds),
        BenchmarkStageSpec("OVERDRIVE", "MAXED DRAW LIST PRESSURE", 240, 148, 22, stage_duration_seconds),
    )


def _summarize_stage(
    stage: BenchmarkStageSpec, index: int, samples: list[FrameProfile], *, completed: bool
) -> BenchmarkStageResult:
    summary = _summarize_samples(samples)
    return BenchmarkStageResult(
        index=index,
        name=stage.name,
        subtitle=stage.subtitle,
        duration_seconds=stage.duration_seconds,
        sample_count=summary["sample_count"],
        avg_fps=summary["avg_fps"],
        avg_frame_ms=summary["avg_frame_ms"],
        p95_frame_ms=summary["p95_frame_ms"],
        avg_update_ms=summary["avg_update_ms"],
        avg_render_ms=summary["avg_render_ms"],
        avg_submit_ms=summary["avg_submit_ms"],
        avg_gpu_frame_ms=summary["avg_gpu_frame_ms"],
        p95_gpu_frame_ms=summary["p95_gpu_frame_ms"],
        avg_vertices=summary["avg_vertices"],
        max_vertices=summary["max_vertices"],
        completed=completed,
    )


def _summarize_samples(samples: list[FrameProfile]) -> BenchmarkSummary:
    if not samples:
        return {
            "sample_count": 0,
            "avg_fps": 0.0,
            "avg_frame_ms": 0.0,
            "p95_frame_ms": 0.0,
            "avg_update_ms": 0.0,
            "avg_render_ms": 0.0,
            "avg_submit_ms": 0.0,
            "avg_gpu_frame_ms": 0.0,
            "p95_gpu_frame_ms": 0.0,
            "avg_vertices": 0.0,
            "max_vertices": 0,
        }

    frame_times = sorted(sample.frame_ms for sample in samples)
    gpu_times = sorted(sample.gpu_frame_ms for sample in samples if sample.gpu_frame_ms > 0.0)
    p95_index = min(len(frame_times) - 1, math.ceil(len(frame_times) * 0.95) - 1)
    gpu_p95_index = min(len(gpu_times) - 1, math.ceil(len(gpu_times) * 0.95) - 1) if gpu_times else 0
    return {
        "sample_count": len(samples),
        "avg_fps": sum(sample.fps for sample in samples) / len(samples),
        "avg_frame_ms": sum(sample.frame_ms for sample in samples) / len(samples),
        "p95_frame_ms": frame_times[p95_index],
        "avg_update_ms": sum(sample.update_ms for sample in samples) / len(samples),
        "avg_render_ms": sum(sample.render_ms for sample in samples) / len(samples),
        "avg_submit_ms": sum(sample.submit_ms for sample in samples) / len(samples),
        "avg_gpu_frame_ms": (sum(gpu_times) / len(gpu_times)) if gpu_times else 0.0,
        "p95_gpu_frame_ms": gpu_times[gpu_p95_index] if gpu_times else 0.0,
        "avg_vertices": sum(sample.vertex_count for sample in samples) / len(samples),
        "max_vertices": max(sample.vertex_count for sample in samples),
    }


def _quad_color(index: int) -> tuple[float, float, float, float]:
    palette = (
        (0.26, 0.80, 0.55, 0.40),
        (0.97, 0.79, 0.28, 0.34),
        (0.42, 0.70, 0.98, 0.34),
        (0.96, 0.44, 0.36, 0.34),
    )
    return palette[index % len(palette)]
