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

## ORM

For a new TypeScript service, default to Prisma. Its schema-first generated client gives complete type coverage from model to query, migration history makes database evolution reviewable, Prisma Studio supports inspection without ad-hoc SQL tooling, and its ecosystem momentum reduces integration risk.

Do not select TypeORM by default just because it resembles decorator-based application code. Choose it only when the incumbent service already uses it or a concrete capability requirement cannot be met by Prisma; record that requirement before introducing a second persistence pattern.

| Need | Prisma default response |
|---|---|
| Typed queries | Generate the client from the schema and keep schema changes in review |
| Schema evolution | Create and apply tracked migrations |
| Local data inspection | Use Prisma Studio against the development database |
| Existing TypeORM service | Preserve the incumbent ORM; do not migrate as a feature side effect |

Route public HTTP request and response conventions to the `api` skill. This reference owns database-engine fidelity and ORM selection, not endpoint contract shape.
