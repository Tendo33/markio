# Redis Vs Memory Runtime

In-memory task runtime is the default local path. Redis adds durability/cache behavior, but it must remain optional unless the product explicitly changes deployment requirements.

Any Redis change must preserve task status semantics, owner isolation, queue controls, and fallback behavior.
