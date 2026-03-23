from __future__ import annotations

from .shared import BlackHole, Cloud, Monster, Pickup, Projectile


class CleanupSystem:
    def _trim_platforms(self) -> None:
        floor = self.camera_y - 200.0
        self.platforms = [
            platform
            for platform in self.platforms
            if platform.y + platform.height >= floor and (not platform.broken or platform.state_timer > 0.0)
        ]

    def _trim_clouds(self) -> None:
        dead_entities: list[int] = []
        for entity_id, cloud in self.dynamic_world.components(Cloud).items():
            if cloud.y + cloud.height < cloud.parallax * self.camera_y - 160.0:
                dead_entities.append(entity_id)
        for entity_id in dead_entities:
            self.dynamic_world.remove_entity(entity_id)

    def _trim_pickups(self) -> None:
        floor = self.camera_y - 120.0
        ceiling = self.camera_y + self.world_height + 120.0
        dead_entities: list[int] = []
        for entity_id, pickup in self.dynamic_world.components(Pickup).items():
            if pickup.y + pickup.height < floor or pickup.y > ceiling:
                dead_entities.append(entity_id)
        for entity_id in dead_entities:
            self.dynamic_world.remove_entity(entity_id)

    def _trim_black_holes(self) -> None:
        floor = self.camera_y - 220.0
        ceiling = self.camera_y + self.world_height + 220.0
        dead_entities: list[int] = []
        for entity_id, hole in self.dynamic_world.components(BlackHole).items():
            if hole.y + hole.height < floor or hole.y > ceiling:
                dead_entities.append(entity_id)
        for entity_id in dead_entities:
            self.dynamic_world.remove_entity(entity_id)

    def _trim_monsters(self) -> None:
        floor = self.camera_y - 220.0
        ceiling = self.camera_y + self.world_height + 260.0
        dead_entities: list[int] = []
        for entity_id, monster in self.dynamic_world.components(Monster).items():
            if monster.y + monster.height < floor or monster.y > ceiling:
                dead_entities.append(entity_id)
        for entity_id in dead_entities:
            self.dynamic_world.remove_entity(entity_id)

    def _trim_projectiles(self) -> None:
        floor = self.camera_y - 40.0
        ceiling = self.camera_y + self.world_height + 80.0
        dead_entities: list[int] = []
        for entity_id, projectile in self.dynamic_world.components(Projectile).items():
            if projectile.y + projectile.height < floor or projectile.y > ceiling:
                dead_entities.append(entity_id)
        for entity_id in dead_entities:
            self.dynamic_world.remove_entity(entity_id)
