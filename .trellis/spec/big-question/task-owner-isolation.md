# Task Owner Isolation

Async task APIs must not leak private task context across users.

List/detail/cancel/retry paths need to respect the authenticated owner unless the caller is explicitly admin for queue-level operations. If task persistence changes, owner ID must remain part of the durable task record.
