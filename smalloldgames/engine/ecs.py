from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Generic, TypeVar

EntityId = int
T = TypeVar("T")


class World:
    """Minimal ECS-style world with typed component stores."""

    def __init__(self) -> None:
        self._next_entity_id = 1
        self._entities: set[EntityId] = set()
        self._stores: dict[type[object], dict[EntityId, object]] = {}

    def create(self, *components: object) -> EntityId:
        entity_id = self._next_entity_id
        self._next_entity_id += 1
        self._entities.add(entity_id)
        for component in components:
            self.add_component(entity_id, component)
        return entity_id

    def add_component(self, entity_id: EntityId, component: object) -> None:
        self._entities.add(entity_id)
        store = self._stores.setdefault(type(component), {})
        store[entity_id] = component

    def remove_entity(self, entity_id: EntityId) -> None:
        self._entities.discard(entity_id)
        for store in self._stores.values():
            store.pop(entity_id, None)

    def components(self, component_type: type[T]) -> dict[EntityId, T]:
        store = self._stores.setdefault(component_type, {})
        return store  # type: ignore[return-value]

    def clear_component_type(self, component_type: type[object]) -> None:
        for entity_id in list(self.components(component_type)):
            self.remove_entity(entity_id)

    def replace_component_type(self, component_type: type[T], components: Iterable[T]) -> None:
        self.clear_component_type(component_type)
        for component in components:
            self.create(component)

    def entity_for_component(self, component_type: type[T], component: T) -> EntityId | None:
        for entity_id, candidate in self.components(component_type).items():
            if candidate is component:
                return entity_id
        return None

    def remove_component_instance(self, component_type: type[T], component: T) -> bool:
        entity_id = self.entity_for_component(component_type, component)
        if entity_id is None:
            return False
        self.remove_entity(entity_id)
        return True

    def query(self, *component_types: type[object]) -> Iterator[tuple[object, ...]]:
        if not component_types:
            return iter(())
        entity_ids = set(self.components(component_types[0]))
        for component_type in component_types[1:]:
            entity_ids &= set(self.components(component_type))
        rows: list[tuple[object, ...]] = []
        for entity_id in sorted(entity_ids):
            rows.append((entity_id, *(self.components(component_type)[entity_id] for component_type in component_types)))
        return iter(rows)


class ComponentListProxy(Generic[T]):
    """List-like adapter exposing one component type from a world."""

    def __init__(self, world: World, component_type: type[T]) -> None:
        self.world = world
        self.component_type = component_type

    def __iter__(self) -> Iterator[T]:
        return iter(list(self.world.components(self.component_type).values()))

    def __len__(self) -> int:
        return len(self.world.components(self.component_type))

    def __getitem__(self, index: int) -> T:
        return list(self)[index]

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ComponentListProxy):
            return list(self) == list(other)
        if isinstance(other, list):
            return list(self) == other
        return NotImplemented

    def __repr__(self) -> str:
        return repr(list(self))

    def append(self, component: T) -> None:
        self.world.create(component)

    def remove(self, component: T) -> None:
        if not self.world.remove_component_instance(self.component_type, component):
            raise ValueError("component not present in world")

    def clear(self) -> None:
        self.world.clear_component_type(self.component_type)

    def replace(self, components: Iterable[T]) -> None:
        self.world.replace_component_type(self.component_type, components)
