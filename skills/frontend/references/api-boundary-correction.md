# API Boundary Correction

Operator correction: frontend code should not repeat backend API base, prefix, version,
proxy, or BFF routing details inside components and feature code. Put that shared boundary
in one framework-appropriate place, such as a Vite API client, Next.js rewrite, Route
Handler, or server fetch layer.
