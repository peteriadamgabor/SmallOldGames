# ADR: ECS Direction

## Status

Accepted

## Context

`smalloldgames.engine.ecs` is currently used as a lightweight typed world store, with the deepest usage in Sketch Hopper. Before Phase 5, the codebase had world/query helpers but no formal notion of a `System`, which left the engine in an awkward middle state: more structured than plain lists, but not explicit enough to support reusable update pipelines.

## Decision

The engine will keep the current lightweight ECS approach and formalize it incrementally instead of replacing it or forcing every game into a fully data-driven architecture.

Concretely:

- `World` remains the central typed component store.
- Engine code introduces a formal `System` protocol with `update(world, dt)`.
- Scene-owned orchestration remains valid. A scene may run systems directly or continue to own bespoke logic while migrating gradually.
- Game-specific domain objects remain acceptable as components when that keeps gameplay code simpler.

## Consequences

Positive:

- New engine or gameplay systems can share a stable contract without a large rewrite.
- Tests can target system behavior independently of full scenes.
- The current Sketch Hopper decomposition aligns with a clearer ECS direction.

Tradeoffs:

- The engine is still not a full archetype ECS, and that is intentional.
- Some logic will remain scene-owned until there is enough leverage to extract it cleanly.

## Rejected Alternatives

Full ECS rewrite now:

- Too disruptive for the current project size and testing surface.

Remove ECS abstractions entirely:

- Would throw away useful typed-world behavior that is already paying for itself in gameplay code.
