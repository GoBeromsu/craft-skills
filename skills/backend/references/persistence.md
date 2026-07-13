# Persistence choices

Choose the database workflow and ORM for production fidelity, not for the shortest local setup. Keep the application's persistence contract independent of the particular development process, then make development exercise the same database behavior production relies on.

## Development database

Use the real database engine in every environment. Run only the database in a development container and run the application with its normal hot-reload command against that container. This preserves development/production parity while keeping code iteration fast.

Do not introduce an H2-style in-memory substitute merely to avoid local database setup. Containers already provide repeatable database initialization, so the substitute adds a dialect boundary without removing meaningful setup work. Queries, migrations, constraints, transaction behavior, and generated SQL should meet the same engine in development and production.

| Decision | Default | Escape hatch |
|---|---|---|
| Development engine | Same engine and major version as production | Use a substitute only for an isolated test whose behavior is explicitly engine-independent |
| Application process in development | Local hot reload | Containerize the application only when the repository's tooling requires it |
| Database lifecycle | Containerized database with durable named volume and repeatable initialization | Disposable test database per test run |

Run migrations against the development engine before relying on a schema change. A passing in-memory test does not prove production SQL compatibility.

## Role and destructive target contract

Detect the production engine and major version from the repository's runtime manifests, deployment configuration, or managed-database declaration. Development and integration environments use that detected engine and major; do not replace it with a fixed image tag or an in-memory substitute.

Inspect application configuration, migration commands, and deployment wiring to distinguish the runtime application role from the privileged migration/admin role. Preserve that split: exercise application behavior and authorization through the runtime application role, and use the privileged migration/admin role only for explicitly owned schema migration or narrow bootstrap operations. A convenient admin URL is not an application runtime credential.

Before reset, truncate, broad seed, or any other destructive data lifecycle action, require repository-owned guard evidence or target identity proving a dedicated disposable non-production target. A URL, database name, hostname, or environment label alone is not proof. If target identity or role ownership is ambiguous, stop the destructive action and retain the database unchanged.

## ORM

For a truly greenfield TypeScript service, Prisma is a default choice: its schema-first generated client gives complete type coverage from model to query, migration history makes database evolution reviewable, and Prisma Studio supports inspection without ad-hoc SQL tooling.

Do not select TypeORM by default merely because it resembles decorator-based application code. An incumbent service keeps its existing ORM, whether TypeORM or another choice; introduce or migrate persistence tooling only under explicit migration scope or a recorded capability requirement.

| Need | Prisma default response |
|---|---|
| Typed queries | Generate the client from the schema and keep schema changes in review |
| Schema evolution | Create and apply tracked migrations |
| Local data inspection | Use Prisma Studio against the development database |
| Existing ORM | Preserve the incumbent ORM; do not migrate as a feature side effect |

Route public HTTP request and response conventions to the `api` skill. This reference owns database-engine fidelity, database-role separation, destructive-target proof, and ORM selection, not endpoint contract shape.
