from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum

import glfw


class InputAction(IntEnum):
    RELEASE = 0
    PRESS = 1
    REPEAT = 2


ACTION_RELEASE = InputAction.RELEASE
ACTION_PRESS = InputAction.PRESS
ACTION_REPEAT = InputAction.REPEAT


class GameAction(IntEnum):
    """Semantic input actions that decouple game logic from raw key codes."""

    # Navigation (edge-triggered, menus and in-game)
    NAV_LEFT = 1
    NAV_RIGHT = 2
    NAV_UP = 3
    NAV_DOWN = 4
    CONFIRM = 5
    BACK = 6

    # Gameplay (continuous hold)
    MOVE_LEFT = 10
    MOVE_RIGHT = 11
    MOVE_UP = 12
    MOVE_DOWN = 13
    FIRE = 14

    # Game flow
    PAUSE = 20
    RESTART = 21
    QUIT = 22
    DEBUG_TOGGLE = 23
    POST_PROCESS_TOGGLE = 24

    # Shortcut keys
    LEADERBOARD = 30
    SETTINGS = 31
    SOUND_TOGGLE = 32
    TOUCH_TOGGLE = 33
    BALANCE = 34
    EDIT_NAME = 35
    SAVE_CONFIG = 36
    LOAD_CONFIG = 37


# Default keyboard mapping: action -> set of GLFW key codes
_DEFAULT_KEY_MAP: dict[GameAction, frozenset[int]] = {
    GameAction.NAV_LEFT: frozenset({glfw.KEY_LEFT, glfw.KEY_A}),
    GameAction.NAV_RIGHT: frozenset({glfw.KEY_RIGHT, glfw.KEY_D}),
    GameAction.NAV_UP: frozenset({glfw.KEY_UP, glfw.KEY_W}),
    GameAction.NAV_DOWN: frozenset({glfw.KEY_DOWN, glfw.KEY_S}),
    GameAction.CONFIRM: frozenset({glfw.KEY_ENTER, glfw.KEY_SPACE}),
    GameAction.BACK: frozenset({glfw.KEY_ESCAPE, glfw.KEY_BACKSPACE}),
    GameAction.MOVE_LEFT: frozenset({glfw.KEY_LEFT, glfw.KEY_A}),
    GameAction.MOVE_RIGHT: frozenset({glfw.KEY_RIGHT, glfw.KEY_D}),
    GameAction.MOVE_UP: frozenset({glfw.KEY_UP, glfw.KEY_W}),
    GameAction.MOVE_DOWN: frozenset({glfw.KEY_DOWN, glfw.KEY_S}),
    GameAction.FIRE: frozenset({glfw.KEY_SPACE, glfw.KEY_UP, glfw.KEY_W}),
    GameAction.PAUSE: frozenset({glfw.KEY_P}),
    GameAction.RESTART: frozenset({glfw.KEY_R}),
    GameAction.QUIT: frozenset({glfw.KEY_Q}),
    GameAction.DEBUG_TOGGLE: frozenset({glfw.KEY_F3}),
    GameAction.POST_PROCESS_TOGGLE: frozenset({glfw.KEY_F4}),
    GameAction.LEADERBOARD: frozenset({glfw.KEY_L, glfw.KEY_TAB}),
    GameAction.SETTINGS: frozenset({glfw.KEY_P}),
    GameAction.SOUND_TOGGLE: frozenset({glfw.KEY_S}),
    GameAction.TOUCH_TOGGLE: frozenset({glfw.KEY_T}),
    GameAction.BALANCE: frozenset({glfw.KEY_B}),
    GameAction.EDIT_NAME: frozenset({glfw.KEY_E}),
    GameAction.SAVE_CONFIG: frozenset({glfw.KEY_F5}),
    GameAction.LOAD_CONFIG: frozenset({glfw.KEY_F9}),
}

# Reverse map: key code -> set of actions (built once at import time)
_KEY_TO_ACTIONS: dict[int, list[GameAction]] = {}
for _action, _keys in _DEFAULT_KEY_MAP.items():
    for _key in _keys:
        _KEY_TO_ACTIONS.setdefault(_key, []).append(_action)


@dataclass(frozen=True, slots=True)
class TouchRegion:
    x: float
    y: float
    width: float
    height: float
    actions: frozenset[GameAction]

    def contains(self, pointer_x: float, pointer_y: float) -> bool:
        return self.x <= pointer_x <= self.x + self.width and self.y <= pointer_y <= self.y + self.height


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

    # Action-level state (derived from key state + mapping)
    actions_held: set[GameAction] = field(default_factory=set)
    actions_pressed: set[GameAction] = field(default_factory=set)
    touch_regions: tuple[TouchRegion, ...] = ()
    touch_actions_held: set[GameAction] = field(default_factory=set)
    touch_actions_pressed: set[GameAction] = field(default_factory=set)

    def on_key(self, key: int, action: int) -> None:
        if key < 0:
            return
        if action == ACTION_PRESS:
            if key not in self.held:
                self.pressed.add(key)
                for game_action in _KEY_TO_ACTIONS.get(key, ()):
                    self.actions_pressed.add(game_action)
            self.held.add(key)
            for game_action in _KEY_TO_ACTIONS.get(key, ()):
                self.actions_held.add(game_action)
        elif action == ACTION_RELEASE:
            self.held.discard(key)
            self.released.add(key)
            for game_action in _KEY_TO_ACTIONS.get(key, ()):
                # Only remove from held if no other mapped key is still held
                keys_for_action = _DEFAULT_KEY_MAP[game_action]
                if not any(k in self.held for k in keys_for_action):
                    self.actions_held.discard(game_action)
        elif action == ACTION_REPEAT:
            self.held.add(key)

    def is_down(self, key: int) -> bool:
        return key in self.held

    def was_pressed(self, *keys: int) -> bool:
        return any(key in self.pressed for key in keys)

    def action_pressed(self, *actions: GameAction) -> bool:
        """Check if any of the given actions were triggered this frame."""
        return any(a in self.actions_pressed or a in self.touch_actions_pressed for a in actions)

    def action_held(self, *actions: GameAction) -> bool:
        """Check if any of the given actions are currently held."""
        return any(a in self.actions_held or a in self.touch_actions_held for a in actions)

    def action_axis(self, negative: GameAction, positive: GameAction) -> float:
        """Return -1, 0, or +1 based on held actions."""
        neg = self.action_held(negative)
        pos = self.action_held(positive)
        return float(pos) - float(neg)

    def axis(self, negative_keys: tuple[int, ...], positive_keys: tuple[int, ...]) -> float:
        negative = any(key in self.held for key in negative_keys)
        positive = any(key in self.held for key in positive_keys)
        return float(positive) - float(negative)

    def on_cursor_pos(self, x: float, y: float) -> None:
        self.pointer_x = x
        self.pointer_y = y

    def on_pointer(self, action: int) -> None:
        if action == ACTION_PRESS:
            if not self.pointer_down:
                self.pointer_pressed = True
            self.pointer_down = True
        elif action == ACTION_RELEASE:
            self.pointer_down = False
            self.pointer_released = True

    def pointer_in_rect(self, x: float, y: float, width: float, height: float) -> bool:
        return x <= self.pointer_x <= x + width and y <= self.pointer_y <= y + height

    def set_touch_regions(self, regions: tuple[TouchRegion, ...]) -> None:
        self.touch_regions = regions
        self.touch_actions_held.clear()
        self.touch_actions_pressed.clear()
        active_regions = [region for region in regions if region.contains(self.pointer_x, self.pointer_y)]
        if self.pointer_down:
            for region in active_regions:
                self.touch_actions_held.update(region.actions)
        if self.pointer_pressed:
            for region in active_regions:
                self.touch_actions_pressed.update(region.actions)

    def end_frame(self) -> None:
        self.pressed.clear()
        self.released.clear()
        self.actions_pressed.clear()
        self.touch_actions_pressed.clear()
        self.pointer_pressed = False
        self.pointer_released = False
