from __future__ import annotations

import contextlib
import logging
import tomllib
from dataclasses import dataclass, fields
from pathlib import Path
from typing import get_type_hints

_log = logging.getLogger(__name__)

from smalloldgames.assets import CONFIG_DIR


@dataclass(frozen=True, slots=True)
class SketchHopperConfig:
    world_width: float = 540.0
    world_height: float = 960.0
    player_width: float = 58.0
    player_height: float = 58.0
    player_start_y: float = 180.0
    gravity: float = -1900.0
    move_speed: float = 315.0
    jump_velocity: float = 1010.0
    boots_jump_velocity: float = 1180.0
    boots_charges: int = 3
    spring_jump_velocity: float = 1420.0
    trampoline_jump_velocity: float = 1680.0
    rocket_velocity: float = 1560.0
    rocket_duration: float = 0.95
    propeller_velocity: float = 1220.0
    propeller_duration: float = 0.78
    shield_duration: float = 6.0
    jetpack_move_speed_multiplier: float = 1.08
    game_over_fall_margin: float = 140.0
    camera_follow_offset: float = 0.36

    platform_width: float = 92.0
    platform_height: float = 18.0
    difficulty_ramp_height: float = 2600.0
    path_max_shift: float = 126.0
    initial_platform_start_y: float = 60.0
    initial_platform_end_y: float = 1200.0
    initial_platform_gap_min: float = 82.0
    initial_platform_gap_max: float = 110.0
    initial_route_shift: float = 90.0
    platform_spawn_ahead: float = 260.0
    platform_spawn_gap_min: float = 78.0
    platform_spawn_gap_max: float = 110.0
    extra_platform_chance: float = 0.7
    second_extra_platform_chance: float = 0.24
    overlap_x_padding: float = 18.0
    overlap_y_padding: float = 12.0
    anchor_spring_chance_base: float = 0.12
    anchor_spring_chance_difficulty: float = 0.05
    anchor_moving_chance_base: float = 0.24
    anchor_moving_chance_difficulty: float = 0.12
    extra_broken_chance_base: float = 0.24
    extra_broken_chance_difficulty: float = 0.16
    extra_moving_chance_base: float = 0.44
    extra_moving_chance_difficulty: float = 0.18
    extra_spring_chance_base: float = 0.56
    extra_spring_chance_difficulty: float = 0.08
    extra_fake_chance_base: float = 0.09
    extra_fake_chance_difficulty: float = 0.09
    extra_vanish_chance_base: float = 0.12
    extra_vanish_chance_difficulty: float = 0.08
    extra_trampoline_chance_base: float = 0.08
    extra_trampoline_chance_difficulty: float = 0.07
    anchor_moving_speed_min: float = 45.0
    anchor_moving_speed_max: float = 80.0
    extra_moving_speed_min: float = 60.0
    extra_moving_speed_max: float = 110.0
    spring_feedback_duration: float = 0.18
    spring_min_height: float = 420.0
    moving_platform_min_height: float = 900.0
    broken_platform_min_height: float = 1500.0
    fake_platform_min_height: float = 2400.0
    vanish_platform_min_height: float = 1900.0
    trampoline_min_height: float = 3200.0

    projectile_speed: float = 820.0
    projectile_cooldown: float = 0.22
    enemy_projectile_speed: float = 360.0

    monster_width: float = 62.0
    monster_height: float = 36.0
    monster_spawn_gap_min: float = 320.0
    monster_spawn_gap_max: float = 430.0
    monster_spawn_chance: float = 0.72
    monster_visible_min_offset: float = 120.0
    monster_visible_max_offset: float = 220.0
    monster_top_up_attempts: int = 3
    monster_top_up_start_ratio: float = 0.74
    monster_top_up_step_y: float = 110.0
    monster_avoid_platform_x: float = 58.0
    monster_avoid_platform_y: float = 70.0
    monster_speed_min: float = 42.0
    monster_speed_max: float = 74.0
    monster_bob_chance: float = 0.48
    monster_bob_y_jitter: float = 10.0
    monster_bob_amplitude_min: float = 10.0
    monster_bob_amplitude_max: float = 22.0
    monster_bob_speed_min: float = 2.8
    monster_bob_speed_max: float = 4.6
    min_visible_monsters: int = 1
    monster_min_height: float = 2200.0
    monster_top_up_min_camera_y: float = 2600.0

    ufo_width: float = 72.0
    ufo_height: float = 34.0
    ufo_min_height: float = 4800.0
    ufo_spawn_gap_min: float = 760.0
    ufo_spawn_gap_max: float = 980.0
    ufo_spawn_chance: float = 0.54
    ufo_speed_min: float = 68.0
    ufo_speed_max: float = 96.0
    ufo_shot_interval_min: float = 1.8
    ufo_shot_interval_max: float = 3.4
    ufo_shot_min_height: float = 5600.0

    jetpack_width: float = 30.0
    jetpack_height: float = 32.0
    jetpack_velocity: float = 1380.0
    jetpack_duration: float = 1.10
    boots_width: float = 30.0
    boots_height: float = 24.0
    rocket_width: float = 26.0
    rocket_height: float = 42.0
    shield_width: float = 30.0
    shield_height: float = 30.0
    propeller_width: float = 30.0
    propeller_height: float = 34.0
    min_visible_pickups: int = 1
    pickup_min_height: float = 760.0
    pickup_top_up_min_camera_y: float = 520.0
    pickup_spawn_chance_base: float = 0.012
    pickup_spawn_chance_difficulty: float = 0.018
    pickup_min_gap_y: float = 880.0
    pickup_spawn_offset_y: float = 8.0
    pickup_overlap_x: float = 28.0
    pickup_overlap_y: float = 60.0
    pickup_top_up_visible_min_offset: float = 80.0
    pickup_top_up_visible_max_offset: float = 160.0
    pickup_top_up_min_camera_buffer: float = 260.0
    pickup_top_up_min_player_buffer: float = 160.0
    pickup_top_up_max_camera_buffer: float = 220.0
    shield_min_height: float = 2800.0
    shield_spawn_chance_base: float = 0.004
    shield_spawn_chance_difficulty: float = 0.007
    boots_min_height: float = 1600.0
    boots_spawn_chance_base: float = 0.006
    boots_spawn_chance_difficulty: float = 0.010
    propeller_min_height: float = 2200.0
    propeller_spawn_chance_base: float = 0.005
    propeller_spawn_chance_difficulty: float = 0.009
    rocket_min_height: float = 4200.0
    rocket_spawn_chance_base: float = 0.003
    rocket_spawn_chance_difficulty: float = 0.006

    black_hole_size: float = 74.0
    black_hole_pull_radius: float = 170.0
    black_hole_pull_strength: float = 420.0
    black_hole_spawn_gap_min: float = 520.0
    black_hole_spawn_gap_max: float = 760.0
    black_hole_spawn_chance: float = 0.72
    black_hole_min_height: float = 5200.0

    cloud_max_parallax: float = 0.56

    theme_height_1: float = 1800.0
    theme_height_2: float = 4200.0
    theme_height_3: float = 7200.0
    theme_monster_spawn_bonus: float = 0.08
    theme_platform_gap_bonus: float = 6.0
    theme_black_hole_spawn_bonus: float = 0.05

    feedback_message_duration: float = 1.1
    effect_flash_duration: float = 0.18
    effect_flash_alpha: float = 0.16
    shake_decay: float = 4.6


def validate_config(config: SketchHopperConfig) -> list[str]:
    """Return a list of validation error messages. Empty list means valid."""
    errors: list[str] = []
    for field in fields(config):
        value = getattr(config, field.name)
        if field.name.endswith(("_width", "_height", "_size")) and isinstance(value, (int, float)) and value <= 0:
            errors.append(f"{field.name} must be positive, got {value}")
        if field.name.endswith(("_duration", "_cooldown", "_interval_min", "_interval_max")) and isinstance(value, (int, float)) and value <= 0:
            errors.append(f"{field.name} must be positive, got {value}")
        if field.name.endswith("_chance") and isinstance(value, float) and not (0.0 <= value <= 1.0):
            errors.append(f"{field.name} must be between 0 and 1, got {value}")
        if field.name.endswith("_charges") and isinstance(value, int) and value < 0:
            errors.append(f"{field.name} must be non-negative, got {value}")
    if config.gravity >= 0:
        errors.append(f"gravity must be negative, got {config.gravity}")
    if config.jump_velocity <= 0:
        errors.append(f"jump_velocity must be positive, got {config.jump_velocity}")
    if config.move_speed <= 0:
        errors.append(f"move_speed must be positive, got {config.move_speed}")
    if config.platform_spawn_gap_min > config.platform_spawn_gap_max:
        errors.append(
            f"platform_spawn_gap_min ({config.platform_spawn_gap_min}) "
            f"must not exceed platform_spawn_gap_max ({config.platform_spawn_gap_max})"
        )
    if config.monster_spawn_gap_min > config.monster_spawn_gap_max:
        errors.append(
            f"monster_spawn_gap_min ({config.monster_spawn_gap_min}) "
            f"must not exceed monster_spawn_gap_max ({config.monster_spawn_gap_max})"
        )
    return errors


SECTIONS: dict[str, tuple[str, ...]] = {
    "player": (
        "world_width",
        "world_height",
        "player_width",
        "player_height",
        "player_start_y",
        "gravity",
        "move_speed",
        "jump_velocity",
        "boots_jump_velocity",
        "boots_charges",
        "spring_jump_velocity",
        "trampoline_jump_velocity",
        "rocket_velocity",
        "rocket_duration",
        "propeller_velocity",
        "propeller_duration",
        "shield_duration",
        "jetpack_move_speed_multiplier",
        "game_over_fall_margin",
        "camera_follow_offset",
    ),
    "platforms": (
        "platform_width",
        "platform_height",
        "difficulty_ramp_height",
        "path_max_shift",
        "initial_platform_start_y",
        "initial_platform_end_y",
        "initial_platform_gap_min",
        "initial_platform_gap_max",
        "initial_route_shift",
        "platform_spawn_ahead",
        "platform_spawn_gap_min",
        "platform_spawn_gap_max",
        "extra_platform_chance",
        "second_extra_platform_chance",
        "overlap_x_padding",
        "overlap_y_padding",
        "anchor_spring_chance_base",
        "anchor_spring_chance_difficulty",
        "anchor_moving_chance_base",
        "anchor_moving_chance_difficulty",
        "extra_broken_chance_base",
        "extra_broken_chance_difficulty",
        "extra_moving_chance_base",
        "extra_moving_chance_difficulty",
        "extra_spring_chance_base",
        "extra_spring_chance_difficulty",
        "extra_fake_chance_base",
        "extra_fake_chance_difficulty",
        "extra_vanish_chance_base",
        "extra_vanish_chance_difficulty",
        "extra_trampoline_chance_base",
        "extra_trampoline_chance_difficulty",
        "anchor_moving_speed_min",
        "anchor_moving_speed_max",
        "extra_moving_speed_min",
        "extra_moving_speed_max",
        "spring_feedback_duration",
        "spring_min_height",
        "moving_platform_min_height",
        "broken_platform_min_height",
        "fake_platform_min_height",
        "vanish_platform_min_height",
        "trampoline_min_height",
    ),
    "projectiles": (
        "projectile_speed",
        "projectile_cooldown",
        "enemy_projectile_speed",
    ),
    "monsters": (
        "monster_width",
        "monster_height",
        "monster_spawn_gap_min",
        "monster_spawn_gap_max",
        "monster_spawn_chance",
        "monster_visible_min_offset",
        "monster_visible_max_offset",
        "monster_top_up_attempts",
        "monster_top_up_start_ratio",
        "monster_top_up_step_y",
        "monster_avoid_platform_x",
        "monster_avoid_platform_y",
        "monster_speed_min",
        "monster_speed_max",
        "monster_bob_chance",
        "monster_bob_y_jitter",
        "monster_bob_amplitude_min",
        "monster_bob_amplitude_max",
        "monster_bob_speed_min",
        "monster_bob_speed_max",
        "min_visible_monsters",
        "monster_min_height",
        "monster_top_up_min_camera_y",
        "ufo_width",
        "ufo_height",
        "ufo_min_height",
        "ufo_spawn_gap_min",
        "ufo_spawn_gap_max",
        "ufo_spawn_chance",
        "ufo_speed_min",
        "ufo_speed_max",
        "ufo_shot_interval_min",
        "ufo_shot_interval_max",
        "ufo_shot_min_height",
    ),
    "pickups": (
        "jetpack_width",
        "jetpack_height",
        "jetpack_velocity",
        "jetpack_duration",
        "boots_width",
        "boots_height",
        "rocket_width",
        "rocket_height",
        "shield_width",
        "shield_height",
        "propeller_width",
        "propeller_height",
        "min_visible_pickups",
        "pickup_min_height",
        "pickup_top_up_min_camera_y",
        "pickup_spawn_chance_base",
        "pickup_spawn_chance_difficulty",
        "pickup_min_gap_y",
        "pickup_spawn_offset_y",
        "pickup_overlap_x",
        "pickup_overlap_y",
        "pickup_top_up_visible_min_offset",
        "pickup_top_up_visible_max_offset",
        "pickup_top_up_min_camera_buffer",
        "pickup_top_up_min_player_buffer",
        "pickup_top_up_max_camera_buffer",
        "shield_min_height",
        "shield_spawn_chance_base",
        "shield_spawn_chance_difficulty",
        "boots_min_height",
        "boots_spawn_chance_base",
        "boots_spawn_chance_difficulty",
        "propeller_min_height",
        "propeller_spawn_chance_base",
        "propeller_spawn_chance_difficulty",
        "rocket_min_height",
        "rocket_spawn_chance_base",
        "rocket_spawn_chance_difficulty",
    ),
    "hazards": (
        "black_hole_size",
        "black_hole_pull_radius",
        "black_hole_pull_strength",
        "black_hole_spawn_gap_min",
        "black_hole_spawn_gap_max",
        "black_hole_spawn_chance",
        "black_hole_min_height",
    ),
    "background": ("cloud_max_parallax",),
    "themes": (
        "theme_height_1",
        "theme_height_2",
        "theme_height_3",
        "theme_monster_spawn_bonus",
        "theme_platform_gap_bonus",
        "theme_black_hole_spawn_bonus",
    ),
    "feedback": (
        "feedback_message_duration",
        "effect_flash_duration",
        "effect_flash_alpha",
        "shake_decay",
    ),
}


DEFAULT_SKETCH_HOPPER_CONFIG_PATH = CONFIG_DIR / "sketch_hopper.toml"
DEFAULT_SKETCH_HOPPER_OVERRIDE_PATH = Path.home() / ".smalloldgames" / "sketch_hopper.toml"


def load_sketch_hopper_config(
    path: str | Path | None = None,
    *,
    override_path: str | Path | None = None,
) -> SketchHopperConfig:
    config = SketchHopperConfig()
    base_path = Path(path) if path is not None else DEFAULT_SKETCH_HOPPER_CONFIG_PATH
    config = _merge_file(config, base_path)
    if path is None:
        user_path = Path(override_path) if override_path is not None else DEFAULT_SKETCH_HOPPER_OVERRIDE_PATH
        config = _merge_file(config, user_path)
    elif override_path is not None:
        config = _merge_file(config, Path(override_path))
    errors = validate_config(config)
    for error in errors:
        _log.warning("Config validation: %s", error)
    return config


def save_sketch_hopper_config(config: SketchHopperConfig, path: str | Path | None = None) -> Path:
    config_path = Path(path) if path is not None else DEFAULT_SKETCH_HOPPER_OVERRIDE_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for section, keys in SECTIONS.items():
        lines.append(f"[{section}]")
        for key in keys:
            lines.append(f"{key} = {_format_toml_value(getattr(config, key))}")
        lines.append("")
    config_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return config_path


def reset_sketch_hopper_config(path: str | Path | None = None) -> None:
    config_path = Path(path) if path is not None else DEFAULT_SKETCH_HOPPER_OVERRIDE_PATH
    with contextlib.suppress(FileNotFoundError):
        config_path.unlink()


def _merge_file(config: SketchHopperConfig, config_path: Path) -> SketchHopperConfig:
    if not config_path.exists():
        return config
    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return config
    field_types = get_type_hints(SketchHopperConfig)
    merged: dict[str, object] = {field.name: getattr(config, field.name) for field in fields(config)}
    for section in data.values():
        if not isinstance(section, dict):
            continue
        for key, value in section.items():
            if key in merged:
                coerced = _coerce_config_value(value, field_types[key])
                if coerced is not None:
                    merged[key] = coerced
    return SketchHopperConfig(**merged)


def _format_toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    raise TypeError(f"Unsupported TOML value: {value!r}")


def _coerce_config_value(value: object, expected_type: type[object]) -> object | None:
    if expected_type is bool:
        return value if isinstance(value, bool) else None
    if expected_type is int:
        if isinstance(value, bool) or not isinstance(value, int):
            return None
        return value
    if expected_type is float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return float(value)
    return None
