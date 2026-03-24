"""Shared engine utilities."""

from .animation import Animation, AnimationSet, AnimationState
from .audio import AudioEngine
from .camera import Camera
from .collision import AABB, SpatialHash, aabb_overlaps, aabb_overlaps_raw, covered_cells
from .components import Lifetime, Position, Size, Velocity
from .ecs import ComponentListProxy, EntityId, System, World, run_systems
from .game_registry import GameDefinition, GameRegistry, load_game_definition
from .game_state import FLOW_CONTINUE, GameFlowMixin
from .input import GameAction, InputState, TouchRegion
from .particles import EmitterConfig, ParticleEmitter
from .persistence import PersistenceMixin
from .physics import apply_gravity, bounce_x, clamp, integrate_velocity, wrap_x
from .resources import ResourceRegistry
from .scene import Pop, Push, Scene, SceneContext, SceneResult, Transition
from .touch import TouchButton, build_touch_regions, render_touch_buttons
from .ui import draw_fullscreen_scrim, draw_gradient_background, draw_overlay_panel, draw_score_hud

__all__ = [
    "AABB",
    "FLOW_CONTINUE",
    "Animation",
    "AnimationSet",
    "AnimationState",
    "AudioEngine",
    "Camera",
    "ComponentListProxy",
    "EmitterConfig",
    "EntityId",
    "GameAction",
    "GameDefinition",
    "GameFlowMixin",
    "GameRegistry",
    "InputState",
    "Lifetime",
    "ParticleEmitter",
    "PersistenceMixin",
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
    "TouchButton",
    "TouchRegion",
    "Transition",
    "Velocity",
    "World",
    "aabb_overlaps",
    "aabb_overlaps_raw",
    "apply_gravity",
    "bounce_x",
    "build_touch_regions",
    "clamp",
    "covered_cells",
    "draw_fullscreen_scrim",
    "draw_gradient_background",
    "draw_overlay_panel",
    "draw_score_hud",
    "integrate_velocity",
    "load_game_definition",
    "render_touch_buttons",
    "run_systems",
    "wrap_x",
]
