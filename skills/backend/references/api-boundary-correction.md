# API Boundary Correction

Operator correction: do not teach agents to hardcode `/api/v1`; teach them to keep the
common API base, prefix, and version boundary in one composition point. Backend handlers,
controllers, and child routers own resource-local paths only.
