"""Shared engine utilities."""

from .audio import AudioEngine
from .components import Lifetime, Position, Size, Velocity
from .ecs import ComponentListProxy, EntityId, System, World, run_systems
from .game_registry import GameDefinition, GameRegistry, load_game_definition
from .input import GameAction, InputState
from .resources import ResourceRegistry
from .scene import Pop, Push, Scene, SceneContext, SceneResult, Transition

__all__ = [
    "AudioEngine",
    "ComponentListProxy",
    "EntityId",
    "GameAction",
    "GameDefinition",
    "GameRegistry",
    "InputState",
    "Lifetime",
    "Position",
    "Pop",
    "Push",
    "ResourceRegistry",
    "Scene",
    "SceneContext",
    "SceneResult",
    "System",
    "Transition",
    "Size",
    "Velocity",
    "World",
    "load_game_definition",
    "run_systems",
]
