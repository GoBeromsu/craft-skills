# Database operations

## Paired-read contract

Before applying a linked rule, open every cited anchor in `evidence.md`.
Confirm its source class, selected version or capability, status, caveat, and conflict.
Treat the fact as unknown when any required axis is unavailable, partial, unresolved, or mismatched.
Keep source metadata in `evidence.md` rather than copying it here.

## Contents

- [Bulk DML and extraction](#bulk-dml-and-extraction)
- [Online schema change](#online-schema-change)
- [Pooling and workload isolation](#pooling-and-workload-isolation)
- [Read routing and replication](#read-routing-and-replication)
- [Cache capacity](#cache-capacity)
- [Aurora storage](#aurora-storage)
- [Operational stop gates](#operational-stop-gates)

## Bulk DML and extraction

Plan large updates and deletes as bounded transactions, with measured replication, undo or dead-version, lock, and throughput signals between batches.
Gain bounded interference and a pause point; pay longer total elapsed time and verify that backlog and storage pressure recover between batches.
[E-THREADS-BULK-DML](evidence.md#e-threads-bulk-dml)

Prefer a lifecycle operation such as partition removal only when the data boundary already matches a verified partition boundary.
Gain metadata-scale removal and avoid row-by-row vacuum work; pay partitioning design and lock-sensitive operations.
[E-PG-PARTITION-18](evidence.md#e-pg-partition-18) [E-THREADS-BULK-DML](evidence.md#e-threads-bulk-dml)

Treat large `SELECT` and export jobs as shared-resource consumers even when they do not write rows.
Project only required columns, bound or resume the extraction, and isolate it from latency-sensitive work when buffer, snapshot, or replica evidence supports that choice.
Gain reduced cache and concurrency interference; pay operational coordination and possible replica-freshness limits.
[E-THREADS-AURORA-LAG](evidence.md#e-threads-aurora-lag)

## Online schema change

Classify the selected engine, version, table size, lock behavior, replication configuration, foreign keys, and triggers before choosing an online schema-change method.
Do not execute a schema change automatically.
Stop when any required capability or deployment evidence is unknown.
[E-STRONG-MIGRATIONS](evidence.md#e-strong-migrations) [E-GHOST-LIMITS](evidence.md#e-ghost-limits)

Split a constraint change into compatible stages when the selected migration tooling and engine support it.
Gain shorter blocking windows; pay an interim period with validation or enforcement not yet complete, and verify the backfill and final validation before declaring the invariant active.
[E-STRONG-MIGRATIONS](evidence.md#e-strong-migrations)

Use a concurrent index build only where the selected PostgreSQL capability supports it.
Gain lower blocking; pay a longer build and operational monitoring, and stop on lock, replication, or capacity signals outside the approved envelope.
[E-STRONG-MIGRATIONS](evidence.md#e-strong-migrations)

Use gh-ost only after confirming its version, MySQL prerequisites, row-based replication settings, and absence of its documented foreign-key and trigger path.
Gain an online-copy mechanism; pay binlog, copy, cutover, and operational complexity.
[E-GHOST-LIMITS](evidence.md#e-ghost-limits)

## Pooling and workload isolation

Size active database work from measured saturation and queue new transaction starts beyond that point rather than equating more client connections with more throughput.
Treat any connection-count formula as an old starting heuristic, not a cloud or SSD default.
Gain lower contention and cache pressure; pay queue latency and verify throughput, tail latency, memory, and lock behavior under representative load.
[E-PG-CONNECTIONS-WIKI](evidence.md#e-pg-connections-wiki)

Reserve database connections beyond the application pool for monitoring and maintenance.
Account for memory that query operators can consume concurrently rather than setting pool size and per-query memory independently.
[E-PG-CONNECTIONS-WIKI](evidence.md#e-pg-connections-wiki)

Select a PgBouncer pooling mode from the application's required session state, prepared-statement behavior, and transaction boundaries.
Do not put session-dependent behavior behind transaction pooling until the selected PgBouncer feature matrix confirms compatibility.
Gain connection multiplexing; pay restrictions on session semantics.
[E-PGBOUNCER-FEATURES](evidence.md#e-pgbouncer-features)

Separate crawler, batch, or export work from interactive capacity when their measured concurrency or cache effects interfere.
Apply admission control before the database and retain database-side detection and per-workload evidence.
[E-THREADS-CRAWLING](evidence.md#e-threads-crawling)

## Read routing and replication

Route read-after-write to the writer or admit a reader only after observing it has caught up to the required write.
Do not use a practitioner latency observation as an SLA.
AWS documents Aurora reader lag as usually considerably less than 100 ms, while the practitioner source describes a different typical value and a load tail that AWS does not guarantee.
[E-AURORA-PERFORMANCE-PARTIAL](evidence.md#e-aurora-performance-partial) [E-THREADS-AURORA-LAG](evidence.md#e-threads-aurora-lag)

Treat PostgreSQL streaming replication as asynchronous unless the selected configuration proves otherwise.
Choose synchronous commit behavior by naming the acknowledged durability and visibility point, then measure added commit latency and standby availability.
Gain a stated failure bound; pay network-dependent commit delay and potential blocked commits.
[E-PG-WARM-STANDBY-18](evidence.md#e-pg-warm-standby-18)

Bound PostgreSQL replication-slot WAL retention and monitor it.
Gain protection from premature WAL recycling; pay the risk that an unconsumed slot fills `pg_wal` and forces intervention or a replica rebuild.
[E-PG-WARM-STANDBY-18](evidence.md#e-pg-warm-standby-18)

Treat MySQL replication as asynchronous unless the selected configuration proves otherwise.
Semi-synchronous replication confirms receipt and relay-log flush at the required replica count, not execution or commit there.
Monitor timeout downgrade because semi-sync reverts to asynchronous replication when acknowledgement does not arrive in time.
[E-MYSQL-SEMISYNC-84](evidence.md#e-mysql-semisync-84)

After a MySQL source failover, stop reuse of the failed source as a replication source until the selected recovery method establishes safety.
The catalog evidence does not provide an Aurora failover procedure, so leave that mechanism unknown.
[E-MYSQL-SEMISYNC-84](evidence.md#e-mysql-semisync-84) [E-AURORA-PERFORMANCE-PARTIAL](evidence.md#e-aurora-performance-partial)

## Cache capacity

Set cache capacity and eviction policy from observed key access, TTL hygiene, memory headroom, and write-failure tolerance.
Gain controlled memory use; pay evictions or rejected writes depending on policy.
[E-REDIS-EVICTION](evidence.md#e-redis-eviction)

Do not use eviction as a safety premise when the cache is the only copy of data.
Reserve headroom for replication or persistence buffers, which are not counted toward Redis eviction memory.
[E-REDIS-EVICTION](evidence.md#e-redis-eviction)

Verify a low hit rate by separating evictions from expirations and rejected writes.
Treat a volatile policy without TTL-bearing keys as a write-rejection risk rather than an eviction policy.
[E-REDIS-EVICTION](evidence.md#e-redis-eviction)

## Aurora storage

Distinguish reusable table space from reclaimable cluster volume after a large Aurora delete.
`DELETE` can leave space reusable without shrinking billed volume, while the documented lifecycle operations have different reclamation behavior.
Gain an accurate storage plan; pay a lock-sensitive redesign or reorganization path, and verify with the appropriate delayed storage metric.
[E-AURORA-PERFORMANCE-PARTIAL](evidence.md#e-aurora-performance-partial)

Do not promise a fixed reclamation duration or total reclamation.
Monitor billed `VolumeBytesUsed` separately from remaining volume capacity, and account for interval collection and background storage work before judging an operation.
[E-AURORA-PERFORMANCE-PARTIAL](evidence.md#e-aurora-performance-partial)

## Operational stop gates

Stop a bulk, DDL, pool, routing, replication, cache, or reclamation change when selected-version evidence, capability evidence, baseline measurements, rollback path, capacity headroom, or approval is missing.
Do not substitute a generic fallback for an unknown mutable behavior.
[E-PG-EXPLAIN-18](evidence.md#e-pg-explain-18) [E-PGBOUNCER-FEATURES](evidence.md#e-pgbouncer-features) [E-AURORA-PERFORMANCE-PARTIAL](evidence.md#e-aurora-performance-partial)
