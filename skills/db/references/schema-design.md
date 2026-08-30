# Schema and access-path design

## Paired-read contract

Before applying a linked rule, open every cited anchor in `evidence.md`.
Confirm its source class, selected version or capability, status, caveat, and conflict.
Treat the fact as unknown when any required axis is unavailable, partial, unresolved, or mismatched.
Keep source metadata in `evidence.md` rather than copying it here.

## Contents

- [Keys and integrity](#keys-and-integrity)
- [Flexible attributes and documents](#flexible-attributes-and-documents)
- [Access paths and pagination cost](#access-paths-and-pagination-cost)
- [Partitioning](#partitioning)
- [Sharding](#sharding)

## Keys and integrity

Choose a primary key deliberately after the selected engine is known.
For InnoDB, a primary key is the clustered row order and is included in secondary-index records.
Gain direct row access and predictable index size by keeping that key short; pay any natural-key change and lookup cost only when the business identifier is stable and useful for access.
[E-MYSQL-INDEX-84](evidence.md#e-mysql-index-84)

Use an explicit primary key rather than allowing InnoDB to select a nullable-safe unique key or create a hidden row identifier.
Gain visible identity and reviewable secondary-index cost; accept a generated key when no stable natural unique identifier exists.
[E-MYSQL-INDEX-84](evidence.md#e-mysql-index-84)

Treat claims about random-key insert locality as practitioner observation, not an engine guarantee.
Measure representative insert throughput, page behavior, and secondary-index growth on the selected deployment before making a random identifier the write-path key.
[E-MYSQL-INDEX-84](evidence.md#e-mysql-index-84) [E-THREADS-KEYS](evidence.md#e-threads-keys)

Use a database foreign key when database-enforced referential integrity is required within the selected relational boundary.
Gain prevention of orphaned rows; pay write coordination, migration, and cross-boundary coupling costs only where those constraints are acceptable.
When moving integrity into an application or service boundary, name the compensating invariant, reconciliation, and failure handling instead of calling it equivalent.
[E-THREADS-FK](evidence.md#e-threads-fk)

## Flexible attributes and documents

Keep an attribute relational when it needs stable validation, joins, selective indexing, or planner-visible statistics.
Use JSON only when the observed attribute shape changes often enough to justify flexibility, then define validation and access paths for the fields that become operationally important.
Gain schema flexibility; pay weaker implicit constraints and harder indexing, validation, and statistics work.
[E-THREADS-JSON](evidence.md#e-threads-json) [E-STRONG-MIGRATIONS](evidence.md#e-strong-migrations)

Model documents from read paths rather than entity diagrams alone.
Embed data that is consistently read together, and reference data with independently accessed or less-frequent histories.
Gain fewer joins and fewer round trips for the selected path; pay duplication and update coordination when embedded values change.
[E-MONGODB-MODELING](evidence.md#e-mongodb-modeling)

Do not infer document-size or unbounded-array limits from the modeling guidance.
Leave those limits unknown until a matching official source and selected-version evidence are added.
[E-MONGODB-MODELING](evidence.md#e-mongodb-modeling)

## Access paths and pagination cost

Derive every index from measured predicates, joins, ordering, and returned columns.
Gain earlier filtering, ordering, or covering reads only when the plan uses that access path; pay storage, write amplification, and maintenance for every additional index.
Verify with representative plans and workload-level write cost, not an index name alone.
[E-INDEX-LUKE-WHERE](evidence.md#e-index-luke-where) [E-PG-EXPLAIN-18](evidence.md#e-pg-explain-18)

For a deep ordered result set, choose an access path that can seek from the last observed ordering values rather than repeatedly discarding preceding rows.
Gain work that does not grow with page depth; pay the requirement for a stable order and tie-breaker.
Leave public cursor shape and response semantics to `api`.
[E-THREADS-AURORA-LAG](evidence.md#e-threads-aurora-lag)

Avoid `SELECT *` on large or hot paths when the actual fields are known.
Gain lower row width, transfer, and cache pressure; pay explicit projection maintenance as requirements change.
[E-THREADS-AURORA-LAG](evidence.md#e-threads-aurora-lag)

## Partitioning

Consider PostgreSQL partitioning only when table size and dominant queries justify it.
Gain partition pruning, hot-index locality, and fast lifecycle operations when predicates include the partition key; pay routing, maintenance, and uniqueness constraints when they do not.
[E-PG-PARTITION-18](evidence.md#e-pg-partition-18)

Use non-overlapping range boundaries with an inclusive lower bound and exclusive upper bound.
Gain unambiguous routing; pay explicit boundary management and verify every incoming value maps to an existing partition.
[E-PG-PARTITION-18](evidence.md#e-pg-partition-18)

Require partition-key columns in a PostgreSQL partitioned unique or primary-key constraint.
Gain enforceability across partitions; reconsider the partitioning scheme when that identity requirement cannot hold.
[E-PG-PARTITION-18](evidence.md#e-pg-partition-18)

Plan partition attachment and indexes as lock-sensitive operations.
Pre-validate an attaching table with matching checks, and use the documented per-partition concurrent-index attachment pattern when the selected version supports it.
Gain less blocking; pay staging complexity and verify lock behavior on a production-like deployment before execution.
[E-PG-PARTITION-18](evidence.md#e-pg-partition-18)

## Sharding

Choose a Vitess sharding key that colocates the data required by the dominant entity workflow, then enumerate operations that violate that assumption.
Gain horizontal placement and write scaling; pay routing and cross-shard complexity.
[E-VITESS-SHARDING-22](evidence.md#e-vitess-sharding-22)

Do not treat replicas as write scaling.
Use replicas for read capacity and split shards for write capacity only after the selected topology and workload evidence support that action.
[E-VITESS-SHARDING-22](evidence.md#e-vitess-sharding-22)

Treat cross-shard transaction semantics and global uniqueness as unknown under this evidence entry.
Do not select a workaround until matching documentation for the selected Vitess release is paired.
[E-VITESS-SHARDING-22](evidence.md#e-vitess-sharding-22)
