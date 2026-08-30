# Database diagnosis

## Paired-read contract

Before applying a linked rule, open every cited anchor in `evidence.md`.
Confirm its source class, selected version or capability, status, caveat, and conflict.
Treat the fact as unknown when any required axis is unavailable, partial, unresolved, or mismatched.
Keep source metadata in `evidence.md` rather than copying it here.

## Diagnose from workload evidence

Rank PostgreSQL statement families by `total_exec_time` before narrowing to individual slow calls.
A frequently executed inexpensive statement can dominate aggregate load, so inspect calls, mean and tail execution time, rows, blocks, temporary blocks, and WAL together.
Treat a nonzero `dealloc` count as incomplete statement ranking rather than a clean workload result.
Do not interpret zero I/O or planning-time fields as measured zero until the relevant tracking setting is confirmed.
[E-PG-PGSTAT-18](evidence.md#e-pg-pgstat-18)

Capture the plan, parameters, cardinality, concurrency, lock state, and buffer or I/O evidence before changing SQL, indexes, or settings.
Use `EXPLAIN ANALYZE` only when executing the statement is safe; analyze a mutating statement inside a transaction that is rolled back.
[E-PG-EXPLAIN-18](evidence.md#e-pg-explain-18)

## Read a PostgreSQL plan

Treat a selective predicate appearing as `Seq Scan` plus `Filter` as a hypothesis that the access path does not restrict reads early enough.
Gain earlier row elimination by testing an index or predicate rewrite.
Pay index-maintenance and write costs only when representative plans and workload evidence show that the condition is selective enough.
[E-PG-EXPLAIN-18](evidence.md#e-pg-explain-18)

Distinguish `Index Cond` from a post-index `Filter`.
When rows are discarded after lookup, test an index whose leading access conditions match the query and verify the changed plan rather than assuming that any composite index helps.
Gain less discarded work at the cost of index storage and write amplification.
[E-PG-EXPLAIN-18](evidence.md#e-pg-explain-18)

Investigate an explicit `Sort`, a disk-backed sort, or a hash with more than one batch as evidence of an unsuitable order, excessive input, or memory pressure.
Gain by reducing input or aligning an index with the required order.
Accept memory changes only after measuring concurrent demand because per-operation memory can multiply across the workload.
[E-PG-EXPLAIN-18](evidence.md#e-pg-explain-18)

Use `Rows Removed by Filter`, buffer counts, and heap-fetch evidence to locate work that was read but not returned.
Do not infer scan volume from emitted-row estimates alone, and do not treat a parent cost as independent of child cost.
[E-PG-EXPLAIN-18](evidence.md#e-pg-explain-18)

## Diagnose deadlocks and lock pressure

On MySQL deadlock errors, capture the latest InnoDB deadlock report and enable complete deadlock logging only when recurrent incidents require it.
Align multi-table and range-update lock order, index locking predicates, keep write transactions short, and make the application retry the aborted transaction.
Gain fewer cycles and narrower lock ranges at the cost of retry-path complexity and added index maintenance.
[E-MYSQL-DEADLOCK-84](evidence.md#e-mysql-deadlock-84)

Do not treat isolation reduction as a universal write-deadlock cure because it does not eliminate write deadlocks.
Consider `READ COMMITTED` for locking-read contention only when selected MySQL 8.4 evidence matches and the application accepts weaker snapshot and repeatable-read semantics.
Gain fewer retained read and gap locks where applicable; pay changed consistency and anomaly behavior plus the still-required whole-transaction retry path.
Accept that tradeoff only after invariant analysis and matching-workload evidence, then verify it with representative concurrency, deadlock-rate, and semantic tests.
When disabling InnoDB deadlock detection, explicitly accept timeout-based victim selection and verify the resulting wait behavior.
[E-MYSQL-DEADLOCK-84](evidence.md#e-mysql-deadlock-84)

## Diagnose space and transaction-age risk

For PostgreSQL growth, inspect dead tuples, vacuum history, transaction age, and the workload that creates dead versions.
Use standard vacuum to make space reusable and preserve normal concurrency.
Treat OS-space reclamation as a separate requirement because standard vacuum generally does not return internal free space to the operating system.
[E-PG-VACUUM-18](evidence.md#e-pg-vacuum-18)

Treat `VACUUM FULL` as a planned stop-gated rewrite, not routine maintenance.
Its gain is compaction; its costs include an `ACCESS EXCLUSIVE` lock and approximately table-sized extra disk, so proceed only after a maintenance window, capacity check, rollback plan, and impact approval.
[E-PG-VACUUM-18](evidence.md#e-pg-vacuum-18)

Escalate wraparound warnings by measuring database and table transaction age, then resolve old prepared transactions, long-running transactions, and obsolete replication slots before a database-wide standard vacuum.
Do not drop a live slot without confirming rebuild consequences, and do not use `VACUUM FULL`, `VACUUM FREEZE`, or single-user mode as the recovery shortcut.
[E-PG-VACUUM-18](evidence.md#e-pg-vacuum-18)

Refresh parent statistics for partitioned tables when their data distribution changes, because child activity does not trigger parent autoanalysis.
[E-PG-VACUUM-18](evidence.md#e-pg-vacuum-18)

## Diagnose interference

When connection and CPU spikes arrive without a deployment, correlate access logs, user agents, query families, pool waits, and database load.
Classify zero-think-time crawlers separately from interactive traffic, then use upstream admission control and dedicated read or pool capacity where measured interference justifies it.
[E-THREADS-CRAWLING](evidence.md#e-threads-crawling)

When a large read slows unrelated work, measure its buffer churn, snapshot lifetime, temporary I/O, and competing workload.
Reduce selected columns and scanned rows, provide a supporting access path, limit the extraction, or isolate it on a read path only after checking replica lag and freshness needs.
[E-THREADS-AURORA-LAG](evidence.md#e-threads-aurora-lag)

When a notification or batch release correlates with connection and CPU spikes, spread the producer schedule and validate that the change reduces the database concurrency peak rather than merely moving it.
[E-THREADS-PUSH](evidence.md#e-threads-push)
