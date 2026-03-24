"""Lightweight 2-D particle system.

Particles are axis-aligned quads rendered via :class:`DrawList`.
Each :class:`ParticleEmitter` manages a pool of particles with
configurable spawn rate, velocity, lifetime, and color.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from smalloldgames.rendering.primitives import Color, DrawList


@dataclass(slots=True)
class Particle:
    """A single live particle."""

    x: float
    y: float
    vx: float
    vy: float
    life: float  # remaining seconds
    max_life: float
    size: float
    color: Color
    gravity: float = 0.0


@dataclass(slots=True)
class EmitterConfig:
    """Spawn parameters for a :class:`ParticleEmitter`."""

    # Spawn rate
    rate: float = 20.0  # particles per second (0 = burst-only)

    # Lifetime range (seconds)
    life_min: float = 0.3
    life_max: float = 0.8

    # Initial speed range
    speed_min: float = 40.0
    speed_max: float = 120.0

    # Direction cone (radians, 0 = up, pi = full circle)
    angle_min: float = 0.0
    angle_max: float = math.tau

    # Size range
    size_min: float = 2.0
    size_max: float = 5.0

    # Color (start and end for fade)
    color_start: Color = (1.0, 1.0, 1.0, 1.0)
    color_end: Color = (1.0, 1.0, 1.0, 0.0)

    # Physics
    gravity: float = 0.0

    # Pool limit
    max_particles: int = 128


@dataclass(slots=True)
class ParticleEmitter:
    """Spawns and manages a pool of particles at a given position."""

    x: float = 0.0
    y: float = 0.0
    config: EmitterConfig = field(default_factory=EmitterConfig)
    active: bool = True
    _particles: list[Particle] = field(default_factory=list)
    _spawn_accumulator: float = 0.0
    _rng: random.Random = field(default_factory=random.Random)

    @property
    def particle_count(self) -> int:
        return len(self._particles)

    @property
    def alive(self) -> bool:
        """True while emitter is active or has live particles."""
        return self.active or len(self._particles) > 0

    def burst(self, count: int) -> None:
        """Emit *count* particles immediately."""
        for _ in range(count):
            if len(self._particles) >= self.config.max_particles:
                break
            self._spawn_particle()

    def tick(self, dt: float) -> None:
        """Advance simulation: spawn new particles, update existing, cull dead."""
        cfg = self.config

        # Spawn
        if self.active and cfg.rate > 0.0:
            self._spawn_accumulator += dt * cfg.rate
            while self._spawn_accumulator >= 1.0 and len(self._particles) < cfg.max_particles:
                self._spawn_accumulator -= 1.0
                self._spawn_particle()

        # Update
        alive: list[Particle] = []
        for p in self._particles:
            p.life -= dt
            if p.life <= 0.0:
                continue
            p.vy += p.gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            alive.append(p)
        self._particles = alive

    def render(self, draw: DrawList, *, world: bool = True) -> None:
        """Draw all live particles as colored quads."""
        cfg = self.config
        cs = cfg.color_start
        ce = cfg.color_end
        for p in self._particles:
            t = 1.0 - (p.life / p.max_life) if p.max_life > 0.0 else 1.0
            color = (
                cs[0] + (ce[0] - cs[0]) * t,
                cs[1] + (ce[1] - cs[1]) * t,
                cs[2] + (ce[2] - cs[2]) * t,
                cs[3] + (ce[3] - cs[3]) * t,
            )
            half = p.size * 0.5
            draw.quad(p.x - half, p.y - half, p.size, p.size, color, world=world)

    def _spawn_particle(self) -> None:
        cfg = self.config
        rng = self._rng
        angle = rng.uniform(cfg.angle_min, cfg.angle_max)
        speed = rng.uniform(cfg.speed_min, cfg.speed_max)
        life = rng.uniform(cfg.life_min, cfg.life_max)
        size = rng.uniform(cfg.size_min, cfg.size_max)
        self._particles.append(
            Particle(
                x=self.x,
                y=self.y,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                life=life,
                max_life=life,
                size=size,
                color=cfg.color_start,
                gravity=cfg.gravity,
            )
        )
