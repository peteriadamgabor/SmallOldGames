from __future__ import annotations

import unittest

from smalloldgames.engine import ComponentListProxy, System, World, run_systems
from smalloldgames.games.sketch_hopper import BlackHole, Cloud, ImpactEffect, Monster, Pickup, SketchHopperScene


class WorldTests(unittest.TestCase):
    def test_query_returns_entities_with_requested_components(self) -> None:
        world = World()
        monster = Monster(x=10.0, y=20.0, width=30.0, height=18.0, velocity_x=4.0)
        pickup = Pickup(x=30.0, y=40.0, width=20.0, height=24.0, kind="jetpack")

        monster_entity = world.create(monster)
        world.create(pickup)

        rows = list(world.query(Monster))
        self.assertEqual(rows, [(monster_entity, monster)])

    def test_component_list_proxy_tracks_world_store(self) -> None:
        world = World()
        proxy = ComponentListProxy(world, Pickup)
        pickup = Pickup(x=30.0, y=40.0, width=20.0, height=24.0, kind="jetpack")

        proxy.append(pickup)
        self.assertEqual(proxy, [pickup])

        proxy.remove(pickup)
        self.assertEqual(proxy, [])

    def test_scene_clouds_and_impacts_are_world_backed(self) -> None:
        scene = SketchHopperScene(lambda: None, seed=7)

        scene.clouds.append(Cloud(x=0.0, y=10.0, width=20.0, height=10.0, parallax=0.3, drift_x=4.0))
        scene.impact_effects.append(ImpactEffect(x=10.0, y=20.0, timer=0.4, duration=0.4, color=(1.0, 1.0, 1.0, 1.0)))

        self.assertEqual(len(scene.dynamic_world.components(Cloud)), len(scene.clouds))
        self.assertEqual(len(scene.dynamic_world.components(ImpactEffect)), len(scene.impact_effects))

    def test_internal_projectile_spawn_adds_projectile_entity(self) -> None:
        scene = SketchHopperScene(lambda: None, seed=7)

        scene._shoot()
        rows = list(scene.dynamic_world.query(scene.projectiles.component_type))

        self.assertEqual(len(rows), 1)

    def test_internal_impact_spawn_adds_impact_entity(self) -> None:
        scene = SketchHopperScene(lambda: None, seed=7)

        scene._spawn_impact(20.0, 30.0, (1.0, 1.0, 1.0, 1.0))
        rows = list(scene.dynamic_world.query(ImpactEffect))

        self.assertEqual(len(rows), 1)

    def test_monster_pickup_and_black_hole_entities_use_domain_objects_as_world_state(self) -> None:
        scene = SketchHopperScene(lambda: None, seed=7)
        initial_monsters = len(list(scene.dynamic_world.query(Monster)))
        initial_pickups = len(list(scene.dynamic_world.query(Pickup)))
        initial_black_holes = len(list(scene.dynamic_world.query(BlackHole)))

        scene.monsters.append(Monster(x=10.0, y=20.0, width=30.0, height=18.0, velocity_x=5.0))
        scene.pickups.append(Pickup(x=30.0, y=40.0, width=20.0, height=24.0, kind="jetpack"))
        scene.black_holes.append(BlackHole(x=50.0, y=60.0, width=32.0, height=32.0, pulse_phase=0.0, pulse_speed=1.0))

        self.assertEqual(len(list(scene.dynamic_world.query(Monster))), initial_monsters + 1)
        self.assertEqual(len(list(scene.dynamic_world.query(Pickup))), initial_pickups + 1)
        self.assertEqual(len(list(scene.dynamic_world.query(BlackHole))), initial_black_holes + 1)

    def test_run_systems_applies_formal_system_protocol(self) -> None:
        world = World()
        calls: list[float] = []

        class DummySystem:
            def update(self, world: World, dt: float) -> None:
                world.create(("tick", dt))
                calls.append(dt)

        systems: list[System] = [DummySystem()]
        run_systems(world, systems, 0.25)

        self.assertEqual(calls, [0.25])
        self.assertEqual(len(list(world.query(tuple))), 1)


if __name__ == "__main__":
    unittest.main()
