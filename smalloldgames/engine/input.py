from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class InputState:
    held: set[int] = field(default_factory=set)
    pressed: set[int] = field(default_factory=set)
    released: set[int] = field(default_factory=set)
    pointer_x: float = 0.0
    pointer_y: float = 0.0
    pointer_down: bool = False
    pointer_pressed: bool = False
    pointer_released: bool = False

    def on_key(self, key: int, action: int) -> None:
        if key < 0:
            return
        if action == 1:
            if key not in self.held:
                self.pressed.add(key)
            self.held.add(key)
        elif action == 0:
            self.held.discard(key)
            self.released.add(key)
        elif action == 2:
            self.held.add(key)

    def is_down(self, key: int) -> bool:
        return key in self.held

    def was_pressed(self, *keys: int) -> bool:
        return any(key in self.pressed for key in keys)

    def axis(self, negative_keys: tuple[int, ...], positive_keys: tuple[int, ...]) -> float:
        negative = any(key in self.held for key in negative_keys)
        positive = any(key in self.held for key in positive_keys)
        return float(positive) - float(negative)

    def on_cursor_pos(self, x: float, y: float) -> None:
        self.pointer_x = x
        self.pointer_y = y

    def on_pointer(self, action: int) -> None:
        if action == 1:
            if not self.pointer_down:
                self.pointer_pressed = True
            self.pointer_down = True
        elif action == 0:
            self.pointer_down = False
            self.pointer_released = True

    def pointer_in_rect(self, x: float, y: float, width: float, height: float) -> bool:
        return x <= self.pointer_x <= x + width and y <= self.pointer_y <= y + height

    def end_frame(self) -> None:
        self.pressed.clear()
        self.released.clear()
        self.pointer_pressed = False
        self.pointer_released = False
