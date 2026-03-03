from __future__ import annotations

from pydantic import BaseModel, Field


class TwoLevels(BaseModel):
    name: str = Field(
        default="main-db",
        title="Database name",
        description=(
            "A human-readable identifier for this database configuration, used in"
            " log messages, monitoring dashboards, and administrative tooling to"
            " distinguish between multiple database connections within the same"
            " application. The name should be unique across all configured databases"
            " and follow a consistent naming convention such as 'primary-db',"
            " 'analytics-readonly', or 'user-sessions'. This value does not affect"
            " the actual database connection and is purely for organizational"
            " purposes."
        ),
    )

    connection_string: str = Field(
        title="Connection string",
        description=(
            "Full database connection URI following the standard format"
            " 'driver://user:password@host:port/dbname'. For PostgreSQL, a typical"
            " value looks like 'postgresql://app_user:secret@db.internal:5432/myapp'."
            " The connection string may include query parameters for SSL mode,"
            " connection timeout, and application name, for example"
            " '?sslmode=require&connect_timeout=10&application_name=myservice'."
            " This value is required and has no default because it contains"
            " environment-specific credentials that should be injected from a"
            " secrets manager. Never log or expose this value in error messages."
        ),
    )

    read_only: bool = Field(
        default=False,
        title="Read-only mode",
        description=(
            "When enabled, all database sessions opened through this configuration"
            " are set to read-only mode at the transaction level. The database will"
            " reject any INSERT, UPDATE, DELETE, or DDL statements, providing a"
            " safety net against accidental writes to replica databases or shared"
            " analytics instances. This is particularly useful for reporting"
            " workloads and background jobs that should only query data. Note that"
            " some ORMs create temporary tables internally, which may fail in"
            " strict read-only mode; consult your ORM documentation for"
            " compatibility details."
        ),
    )

    max_retries: int = Field(
        default=3,
        title="Maximum retries",
        description=(
            "Number of times to automatically retry a failed database operation"
            " before propagating the exception to the caller. Retries apply only"
            " to transient errors such as connection resets, lock timeouts, and"
            " serialization failures; permanent errors like constraint violations"
            " or syntax errors are raised immediately. Each retry uses exponential"
            " backoff starting at 100ms, doubling with each attempt up to a maximum"
            " delay of 5 seconds. Setting this to 0 disables retries entirely,"
            " which may be appropriate for latency-sensitive operations where fast"
            " failure is preferred over eventual success."
        ),
    )

    query_timeout: float = Field(
        default=30.0,
        title="Query timeout",
        description=(
            "Maximum number of seconds a single SQL query is allowed to execute"
            " before being cancelled by the client. This is enforced via the"
            " database's statement_timeout parameter (PostgreSQL) or equivalent"
            " mechanism for other databases. Long-running queries that exceed this"
            " limit are terminated server-side and the client receives a"
            " QueryCancelled exception. This setting protects against runaway"
            " queries that could lock tables or consume excessive resources."
            " Analytical or batch queries that legitimately require more time should"
            " use a dedicated database configuration with a higher timeout."
        ),
    )

    table_schemas: dict[str, list[str]] = Field(
        default={
            "users": ["id", "name", "email", "created_at", "updated_at"],
            "orders": ["id", "user_id", "total", "status", "placed_at"],
            "products": ["id", "name", "price", "category", "stock"],
            "sessions": ["id", "user_id", "token", "expires_at"],
            "audit_log": ["id", "actor", "action", "target", "timestamp"],
            "permissions": ["id", "role", "resource", "level"],
            "settings": ["key", "value", "updated_by", "updated_at"],
            "migrations": ["id", "name", "applied_at", "checksum"],
            "notifications": ["id", "user_id", "message", "read", "sent_at"],
            "api_keys": ["id", "user_id", "key_hash", "label", "created_at"],
        },
        title="Table schemas",
        description=(
            "A mapping of table names to their expected column names, used for"
            " schema validation during application startup. The application checks"
            " that each listed table exists in the database and contains at least"
            " the columns specified here. Additional columns in the database are"
            " ignored, but missing columns cause startup to fail with a descriptive"
            " error. This early validation catches schema drift caused by"
            " unapplied migrations or environment misconfiguration before the"
            " application begins serving traffic. Column order is not significant."
            " Column types are not validated here; use the migration system for"
            " full schema enforcement."
        ),
    )

    extensions: list[str] = Field(
        default=[
            "pg_stat_statements",
            "pg_trgm",
            "uuid-ossp",
            "hstore",
            "citext",
            "btree_gist",
            "pg_cron",
            "postgis",
            "pgcrypto",
            "timescaledb",
        ],
        title="Database extensions",
        description=(
            "List of PostgreSQL extensions that the application requires. During"
            " startup, the application issues 'CREATE EXTENSION IF NOT EXISTS' for"
            " each entry, which is a no-op if the extension is already installed."
            " This requires the database user to have the CREATE privilege on the"
            " target database, or the extensions must be pre-installed by a"
            " superuser. Extensions are loaded in the order listed, which matters"
            " when one extension depends on another. If any extension fails to"
            " load, startup is aborted with an error indicating which extension"
            " could not be installed and the underlying database error message."
        ),
    )

    pool: ConnectionPool = Field(
        title="Connection pool",
        description=(
            "Configuration for the connection pool that manages database"
            " connections on behalf of the application. The pool maintains a set"
            " of pre-established connections that are reused across requests,"
            " avoiding the overhead of creating a new connection for each query."
            " Proper pool sizing is critical for performance: too few connections"
            " cause request queuing and increased latency, while too many can"
            " overwhelm the database server and trigger connection limits."
        ),
    )


class ConnectionPool(BaseModel):
    min_size: int = Field(
        default=2,
        title="Minimum pool size",
        description=(
            "Minimum number of database connections that the pool keeps open at"
            " all times, even when there is no active demand. These connections"
            " are established during application startup and serve as a warm"
            " baseline to handle the initial burst of requests without connection"
            " establishment latency. Setting this too high wastes database"
            " resources during idle periods; setting it too low introduces latency"
            " spikes after periods of inactivity when the pool needs to create new"
            " connections to meet sudden demand."
        ),
    )

    max_size: int = Field(
        default=20,
        title="Maximum pool size",
        description=(
            "Upper bound on the total number of database connections the pool is"
            " allowed to hold, including both idle and in-use connections. This"
            " value should not exceed the database server's max_connections setting"
            " divided by the number of application instances, leaving headroom"
            " for administrative connections and monitoring tools. When all"
            " connections are in use, new requests either block or fail depending"
            " on the overflow_strategy setting. A typical starting point is 10-20"
            " connections per application instance for OLTP workloads."
        ),
    )

    max_idle_time: float = Field(
        default=300.0,
        title="Maximum idle time",
        description=(
            "Maximum number of seconds a connection can remain idle in the pool"
            " before being closed and removed. This prevents the accumulation of"
            " stale connections that may have been silently terminated by network"
            " equipment such as firewalls, load balancers, or the database server's"
            " own idle timeout. The value should be less than the database server's"
            " idle_in_transaction_session_timeout and any intermediate firewall"
            " TCP keepalive timeout. A value of 300 seconds (5 minutes) works well"
            " for most deployments."
        ),
    )

    acquire_timeout: float = Field(
        default=10.0,
        title="Acquire timeout",
        description=(
            "Maximum number of seconds a request will wait to acquire a connection"
            " from the pool before raising a timeout exception. This prevents"
            " requests from blocking indefinitely when the pool is exhausted due to"
            " slow queries or a sudden traffic spike. The timeout starts when the"
            " caller requests a connection and includes any time spent waiting in"
            " the queue as well as establishing a new connection if the pool is"
            " below max_size. When this timeout fires, the caller receives an"
            " PoolAcquireTimeout exception that should be translated to an HTTP 503"
            " Service Unavailable response."
        ),
    )

    recycle_interval: int = Field(
        default=3600,
        title="Connection recycle interval",
        description=(
            "Maximum lifetime of a connection in seconds, measured from the time it"
            " was first established. After this interval, the connection is closed"
            " and a fresh one is created in its place the next time a connection is"
            " needed. This proactive recycling helps work around issues such as"
            " memory leaks in database drivers, DNS changes for database endpoints"
            " behind a load balancer, and stale prepared statement caches."
            " Connections are recycled lazily when returned to the pool, so active"
            " long-running queries are not interrupted. The default of 3600 seconds"
            " (1 hour) balances connection freshness with setup overhead."
        ),
    )

    health_check_query: str = Field(
        default="SELECT 1",
        title="Health check query",
        description=(
            "A lightweight SQL query executed to verify that a connection is still"
            " alive before handing it to the application. This check runs each time"
            " a connection is acquired from the pool, adding a small amount of"
            " latency (typically under 1ms on a local network) in exchange for"
            " preventing the application from receiving broken connections. The"
            " query should be as simple as possible and not access any user tables."
            " 'SELECT 1' is the conventional choice for PostgreSQL and MySQL."
            " For Oracle databases, use 'SELECT 1 FROM DUAL' instead."
        ),
    )

    overflow_strategy: str = Field(
        default="block",
        title="Overflow strategy",
        description=(
            "Defines the behavior when a connection is requested but the pool has"
            " reached its max_size limit. In 'block' mode, the caller waits up to"
            " acquire_timeout seconds for a connection to become available, which"
            " is the safest option and prevents database overload. In 'create' mode,"
            " a temporary overflow connection is created beyond max_size and closed"
            " immediately after use, trading database load for lower request"
            " latency. In 'error' mode, an exception is raised immediately without"
            " waiting, which is useful for fail-fast scenarios where queuing is"
            " unacceptable. The 'block' strategy is recommended for most workloads."
        ),
    )

    per_host_limits: dict[str, int] = Field(
        default={
            "primary": 15,
            "replica-1": 10,
            "replica-2": 10,
            "replica-3": 10,
            "analytics": 5,
            "migration-runner": 2,
            "backup-agent": 1,
            "monitoring": 3,
            "admin-console": 2,
            "batch-worker": 8,
        },
        title="Per-host connection limits",
        description=(
            "A mapping of database host identifiers to the maximum number of pool"
            " connections that may be directed to each host. This is used in"
            " multi-host topologies where the primary handles writes and replicas"
            " serve read traffic. The sum of all per-host limits should not exceed"
            " max_size. Hosts not listed here are not eligible for connection"
            " routing. The 'primary' host receives a higher allocation because it"
            " handles all write operations, while replicas share read traffic."
            " Specialized hosts like 'analytics' and 'migration-runner' receive"
            " smaller allocations to prevent them from starving production traffic."
        ),
    )


TwoLevels.model_rebuild()
