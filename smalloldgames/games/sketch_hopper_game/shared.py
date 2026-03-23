from __future__ import annotations

from dataclasses import dataclass

from .assets import SKETCH_HOPPER_ATLAS

Color = tuple[float, float, float, float]

SKY_LOW: Color = (0.94, 0.94, 0.87, 1.0)
SKY_HIGH: Color = (0.73, 0.90, 0.98, 1.0)
PLATFORM_STABLE: Color = (0.27, 0.74, 0.22, 1.0)
PLATFORM_MOVING: Color = (0.19, 0.48, 0.93, 1.0)
PLATFORM_BROKEN: Color = (0.63, 0.38, 0.17, 1.0)
SPRING_COIL: Color = (0.74, 0.18, 0.62, 1.0)
SPRING_TOP: Color = (0.96, 0.86, 0.25, 1.0)
PLAYER_BODY: Color = (0.44, 0.82, 0.19, 1.0)
PLAYER_NOSE: Color = (1.0, 0.61, 0.21, 1.0)
PLAYER_FEET: Color = (0.18, 0.15, 0.14, 1.0)
TEXT_DARK: Color = (0.15, 0.18, 0.21, 1.0)
TEXT_PANEL: Color = (0.96, 0.97, 0.96, 0.92)
TEXT_ACCENT: Color = (0.95, 0.67, 0.17, 1.0)

BLACK_HOLE_SPRITE = SKETCH_HOPPER_ATLAS.sprites["black_hole"]
CLOUD_SPRITE = SKETCH_HOPPER_ATLAS.sprites["cloud"]
BOOTS_SPRITE = SKETCH_HOPPER_ATLAS.sprites["boots"]
HOPPER_SPRITE = SKETCH_HOPPER_ATLAS.sprites["hopper"]
ENEMY_SHOT_SPRITE = SKETCH_HOPPER_ATLAS.sprites["enemy_shot"]
JETPACK_SPRITE = SKETCH_HOPPER_ATLAS.sprites["jetpack"]
MONSTER_SPRITE = SKETCH_HOPPER_ATLAS.sprites["monster"]
SPRING_SPRITE = SKETCH_HOPPER_ATLAS.sprites["spring"]
PROJECTILE_SPRITE = SKETCH_HOPPER_ATLAS.sprites["projectile"]
PROPELLER_SPRITE = SKETCH_HOPPER_ATLAS.sprites["propeller"]
PLATFORM_STABLE_SPRITE = SKETCH_HOPPER_ATLAS.sprites["platform_stable"]
PLATFORM_MOVING_SPRITE = SKETCH_HOPPER_ATLAS.sprites["platform_moving"]
PLATFORM_BROKEN_SPRITE = SKETCH_HOPPER_ATLAS.sprites["platform_broken"]
SHIELD_SPRITE = SKETCH_HOPPER_ATLAS.sprites["shield"]
ROCKET_SPRITE = SKETCH_HOPPER_ATLAS.sprites["rocket"]
UFO_SPRITE = SKETCH_HOPPER_ATLAS.sprites["ufo"]

THEMES: tuple[tuple[str, Color, Color, Color], ...] = (
    ("CLASSIC", (0.94, 0.94, 0.87, 1.0), (0.73, 0.90, 0.98, 1.0), (0.95, 0.67, 0.17, 1.0)),
    ("JUNGLE", (0.82, 0.92, 0.77, 1.0), (0.45, 0.77, 0.56, 1.0), (0.94, 0.74, 0.21, 1.0)),
    ("SPACE", (0.13, 0.16, 0.28, 1.0), (0.37, 0.50, 0.86, 1.0), (0.97, 0.84, 0.35, 1.0)),
    ("VOID", (0.09, 0.07, 0.16, 1.0), (0.40, 0.17, 0.52, 1.0), (0.94, 0.56, 0.28, 1.0)),
)

BALANCE_FIELDS: tuple[tuple[str, str, float], ...] = (
    ("SPRING MIN", "spring_min_height", 100.0),
    ("MOVING MIN", "moving_platform_min_height", 100.0),
    ("BROKEN MIN", "broken_platform_min_height", 100.0),
    ("PICKUP MIN", "pickup_min_height", 100.0),
    ("PICKUP BASE", "pickup_spawn_chance_base", 0.002),
    ("PICKUP GAP", "pickup_min_gap_y", 40.0),
    ("MONSTER MIN", "monster_min_height", 100.0),
    ("MONSTER RATE", "monster_spawn_chance", 0.04),
    ("UFO MIN", "ufo_min_height", 120.0),
    ("UFO RATE", "ufo_spawn_chance", 0.04),
    ("BLACK HOLE MIN", "black_hole_min_height", 160.0),
    ("BLACK HOLE RATE", "black_hole_spawn_chance", 0.04),
)


@dataclass(slots=True)
class Platform:
    x: float
    y: float
    width: float
    height: float
    kind: str = "stable"
    velocity_x: float = 0.0
    broken: bool = False
    anchor: bool = False
    spring_timer: float = 0.0
    state_timer: float = 0.0


@dataclass(slots=True)
class Player:
    x: float
    y: float
    width: float
    height: float
    velocity_x: float = 0.0
    velocity_y: float = 0.0


@dataclass(slots=True)
class Projectile:
    x: float
    y: float
    width: float
    height: float
    velocity_y: float
    hostile: bool = False


@dataclass(slots=True)
class Monster:
    x: float
    y: float
    width: float
    height: float
    velocity_x: float
    base_y: float = 0.0
    bob_phase: float = 0.0
    bob_speed: float = 0.0
    bob_amplitude: float = 0.0
    kind: str = "monster"
    score_value: int = 85
    shot_timer: float = 0.0


@dataclass(slots=True)
class Cloud:
    x: float
    y: float
    width: float
    height: float
    parallax: float
    drift_x: float


@dataclass(slots=True)
class Pickup:
    x: float
    y: float
    width: float
    height: float
    kind: str
    phase: float = 0.0


@dataclass(slots=True)
class BlackHole:
    x: float
    y: float
    width: float
    height: float
    pulse_phase: float
    pulse_speed: float


@dataclass(slots=True)
class ImpactEffect:
    x: float
    y: float
    timer: float
    duration: float
    color: Color
    text: str = ""
