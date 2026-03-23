from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from smalloldgames.rendering.primitives import DrawList


@dataclass(slots=True)
class FrameProfile:
    fps: float = 0.0
    frame_ms: float = 0.0
    update_ms: float = 0.0
    render_ms: float = 0.0
    submit_ms: float = 0.0
    gpu_frame_ms: float = 0.0
    idle_ms: float = 0.0
    fixed_updates: int = 0
    vertex_count: int = 0
    scene_name: str = ""
    scene_stack_depth: int = 0


class DebugOverlay:
    def __init__(self, *, history_size: int = 48) -> None:
        self.profile = FrameProfile()
        self._frame_history: deque[float] = deque(maxlen=history_size)

    def record_frame(self, profile: FrameProfile) -> None:
        self.profile = profile
        self._frame_history.append(profile.frame_ms)

    def render(self, draw: DrawList) -> None:
        profile = self.profile
        panel_x = 12.0
        panel_y = 826.0
        panel_width = 320.0
        panel_height = 114.0
        graph_x = panel_x + 10.0
        graph_y = panel_y + 12.0
        graph_height = 34.0
        bar_width = 6.0
        bar_gap = 2.0
        visible_history = list(self._frame_history)[-18:]
        max_frame_ms = max(20.0, *(visible_history or [0.0]))

        draw.quad(panel_x, panel_y, panel_width, panel_height, (0.03, 0.05, 0.08, 0.80), world=False)
        for index, frame_ms in enumerate(visible_history):
            bar_height = min(graph_height, (frame_ms / max_frame_ms) * graph_height)
            draw.quad(
                graph_x + index * (bar_width + bar_gap),
                graph_y,
                bar_width,
                bar_height,
                _frame_bar_color(frame_ms),
                world=False,
            )
        draw.text(panel_x + 10.0, panel_y + 84.0, _header_line(profile), scale=2.0, color=(0.90, 0.97, 0.95, 1.0))
        draw.text(panel_x + 10.0, panel_y + 60.0, _timing_line(profile), scale=2.0, color=(0.72, 0.90, 0.84, 1.0))
        draw.text(panel_x + 10.0, panel_y + 36.0, _workload_line(profile), scale=2.0, color=(0.98, 0.88, 0.56, 1.0))


def _header_line(profile: FrameProfile) -> str:
    return f"FPS {int(profile.fps):03d}  FT {profile.frame_ms:04.1f}MS"


def _timing_line(profile: FrameProfile) -> str:
    gpu_value = profile.gpu_frame_ms if profile.gpu_frame_ms > 0.0 else profile.submit_ms
    return f"UPD {profile.update_ms:03.1f}  REN {profile.render_ms:03.1f}  GPU {gpu_value:03.1f}"


def _workload_line(profile: FrameProfile) -> str:
    scene_name = profile.scene_name.upper()[:12] if profile.scene_name else "UNKNOWN"
    return f"VTX {profile.vertex_count:04d}  FIX {profile.fixed_updates:02d}  {scene_name}"


def _frame_bar_color(frame_ms: float) -> tuple[float, float, float, float]:
    if frame_ms <= 8.4:
        return (0.22, 0.86, 0.58, 0.92)
    if frame_ms <= 16.7:
        return (0.96, 0.82, 0.25, 0.92)
    return (0.95, 0.40, 0.33, 0.92)
