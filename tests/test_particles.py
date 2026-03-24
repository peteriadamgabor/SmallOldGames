from __future__ import annotations

import unittest

from smalloldgames.engine.particles import EmitterConfig, ParticleEmitter
from smalloldgames.rendering.primitives import DrawList


def _make_draw() -> DrawList:
    return DrawList(width=540, height=960, white_uv=(0.0, 0.0))


class ParticleEmitterTests(unittest.TestCase):
    def test_burst_spawns_particles(self) -> None:
        emitter = ParticleEmitter(config=EmitterConfig(max_particles=50))
        emitter.burst(10)
        self.assertEqual(emitter.particle_count, 10)

    def test_burst_respects_max(self) -> None:
        emitter = ParticleEmitter(config=EmitterConfig(max_particles=5))
        emitter.burst(20)
        self.assertEqual(emitter.particle_count, 5)

    def test_tick_spawns_from_rate(self) -> None:
        emitter = ParticleEmitter(config=EmitterConfig(rate=100.0, max_particles=200))
        emitter.tick(0.1)  # 100 * 0.1 = 10 particles
        self.assertEqual(emitter.particle_count, 10)

    def test_tick_removes_dead(self) -> None:
        emitter = ParticleEmitter(config=EmitterConfig(rate=0.0, life_min=0.1, life_max=0.1))
        emitter.burst(5)
        self.assertEqual(emitter.particle_count, 5)
        emitter.tick(0.2)  # All should die
        self.assertEqual(emitter.particle_count, 0)

    def test_particles_move(self) -> None:
        cfg = EmitterConfig(
            rate=0.0, speed_min=100.0, speed_max=100.0, life_min=1.0, life_max=1.0, angle_min=0.0, angle_max=0.0,
        )
        emitter = ParticleEmitter(x=0.0, y=0.0, config=cfg)
        emitter.burst(1)
        emitter.tick(0.5)
        p = emitter._particles[0]
        self.assertAlmostEqual(p.x, 50.0, places=0)

    def test_gravity_affects_velocity(self) -> None:
        cfg = EmitterConfig(
            rate=0.0, speed_min=0.0, speed_max=0.0, gravity=-100.0,
            life_min=1.0, life_max=1.0,
        )
        emitter = ParticleEmitter(x=0.0, y=100.0, config=cfg)
        emitter.burst(1)
        emitter.tick(0.5)
        p = emitter._particles[0]
        self.assertLess(p.vy, 0.0)

    def test_render_emits_vertices(self) -> None:
        emitter = ParticleEmitter(config=EmitterConfig(rate=0.0))
        emitter.burst(3)
        draw = _make_draw()
        emitter.render(draw)
        self.assertGreater(len(draw.vertices), 0)

    def test_alive_with_active_emitter(self) -> None:
        emitter = ParticleEmitter(active=True)
        self.assertTrue(emitter.alive)

    def test_alive_with_particles(self) -> None:
        emitter = ParticleEmitter(active=False, config=EmitterConfig(rate=0.0, life_min=1.0, life_max=1.0))
        emitter.burst(1)
        emitter.active = False
        self.assertTrue(emitter.alive)

    def test_not_alive_when_empty_and_inactive(self) -> None:
        emitter = ParticleEmitter(active=False)
        self.assertFalse(emitter.alive)

    def test_inactive_emitter_no_spawn(self) -> None:
        emitter = ParticleEmitter(active=False, config=EmitterConfig(rate=100.0))
        emitter.tick(1.0)
        self.assertEqual(emitter.particle_count, 0)

    def test_color_fades(self) -> None:
        cfg = EmitterConfig(
            rate=0.0, life_min=1.0, life_max=1.0,
            color_start=(1.0, 0.0, 0.0, 1.0),
            color_end=(0.0, 0.0, 0.0, 0.0),
        )
        emitter = ParticleEmitter(config=cfg)
        emitter.burst(1)
        emitter.tick(0.5)  # t = 0.5
        draw = _make_draw()
        emitter.render(draw)
        # Just verify it rendered without error
        self.assertGreater(len(draw.vertices), 0)


if __name__ == "__main__":
    unittest.main()
