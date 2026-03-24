"""Shared engine utilities."""

from .audio import AudioEngine
from .camera import Camera
from .collision import AABB, SpatialHash, aabb_overlaps, aabb_overlaps_raw, covered_cells
from .components import Lifetime, Position, Size, Velocity
from .ecs import ComponentListProxy, EntityId, System, World, run_systems
from .game_registry import GameDefinition, GameRegistry, load_game_definition
from .input import GameAction, InputState, TouchRegion
from .physics import apply_gravity, bounce_x, clamp, integrate_velocity, wrap_x
from .resources import ResourceRegistry
from .scene import Pop, Push, Scene, SceneContext, SceneResult, Transition
from .ui import draw_fullscreen_scrim, draw_overlay_panel, draw_score_hud

__all__ = [
    "AABB",
    "AudioEngine",
    "Camera",
    "ComponentListProxy",
    "EntityId",
    "GameAction",
    "GameDefinition",
    "GameRegistry",
    "InputState",
    "Lifetime",
    "Pop",
    "Position",
    "Push",
    "ResourceRegistry",
    "Scene",
    "SceneContext",
    "SceneResult",
    "Size",
    "SpatialHash",
    "System",
    "TouchRegion",
    "Transition",
    "Velocity",
    "World",
    "aabb_overlaps",
    "aabb_overlaps_raw",
    "apply_gravity",
    "bounce_x",
    "clamp",
    "covered_cells",
    "draw_fullscreen_scrim",
    "draw_overlay_panel",
    "draw_score_hud",
    "integrate_velocity",
    "load_game_definition",
    "run_systems",
    "wrap_x",
]
