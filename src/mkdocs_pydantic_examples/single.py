from __future__ import annotations

from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SingleLevel(BaseModel):
    host: str = Field(
        default="localhost",
        title="Server host",
        description=(
            "Hostname or IP address that the server binds to when starting up."
            " Use '0.0.0.0' to listen on all available network interfaces, which"
            " is typical for containerized deployments. Use '127.0.0.1' or"
            " 'localhost' to restrict access to local connections only, which is"
            " recommended during development. When running behind a reverse proxy"
            " such as nginx or HAProxy, binding to a private interface address is"
            " generally preferred for security."
        ),
    )

    port: int = Field(
        default=8080,
        title="Server port",
        description=(
            "TCP port number on which the server accepts incoming connections."
            " The default of 8080 is a common unprivileged alternative to port 80."
            " Ports below 1024 require elevated privileges on most operating systems."
            " If multiple services run on the same host, ensure each is assigned a"
            " unique port to avoid binding conflicts at startup. In Kubernetes"
            " environments, this value should match the containerPort declared in"
            " the pod specification."
        ),
    )

    debug: bool = Field(
        default=False,
        title="Debug mode",
        description=(
            "When enabled, the server runs in debug mode which activates verbose"
            " logging at the DEBUG level, enables automatic code reloading on file"
            " changes, and exposes detailed error tracebacks in HTTP responses."
            " Debug mode also disables template caching and enables additional"
            " runtime assertions throughout the application. This setting must"
            " never be enabled in production as it can expose sensitive internal"
            " state to end users and significantly degrades performance."
        ),
    )

    workers: float = Field(
        default=1.5,
        title="Worker count",
        description=(
            "Number of worker processes to spawn for handling requests. Integer"
            " values specify an exact count, while fractional values are interpreted"
            " as a multiplier against the number of available CPU cores. For"
            " example, a value of 1.5 on a 4-core machine spawns 6 workers. Each"
            " worker runs in its own process with an independent memory space, so"
            " higher values increase memory consumption proportionally. For"
            " I/O-bound workloads, values between 2.0 and 4.0 per core are typical;"
            " for CPU-bound workloads, 1.0 per core is usually optimal."
        ),
    )

    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        title="Log level",
        description=(
            "Minimum severity level for log messages that will be emitted. Messages"
            " below this threshold are silently discarded. Available levels in"
            " increasing severity are DEBUG, INFO, WARNING, ERROR, and CRITICAL."
            " DEBUG includes detailed diagnostic information useful during"
            " development; INFO covers normal operational events such as startup"
            " and request handling; WARNING indicates unexpected situations that do"
            " not prevent operation; ERROR captures failures in individual"
            " operations; CRITICAL signals conditions that may cause the process to"
            " terminate. In production, INFO or WARNING is recommended to balance"
            " observability with log volume."
        ),
    )

    secret_key: str = Field(
        title="Secret key",
        description=(
            "Cryptographic secret used for signing session cookies, generating"
            " CSRF tokens, and encrypting other sensitive data in transit. This"
            " value must be kept confidential and should be at least 32 characters"
            " of high-entropy random data. Rotating this key invalidates all"
            " existing sessions and tokens, so coordinate rotations with planned"
            " maintenance windows. In multi-instance deployments, all instances"
            " must share the same secret key to ensure sessions are portable across"
            " replicas. Never commit this value to version control; instead, inject"
            " it from a secrets manager or environment variable."
        ),
    )

    tags: list[str] = Field(
        default=[
            "production",
            "us-east-1",
            "web-tier",
            "auto-scaling",
            "monitored",
            "rate-limited",
            "cached",
            "load-balanced",
            "encrypted",
            "redundant",
        ],
        title="Instance tags",
        description=(
            "Freeform string tags attached to this server instance, used for"
            " filtering and grouping in monitoring dashboards, log aggregation"
            " systems, and infrastructure management tools. Tags are matched"
            " case-sensitively and may include environment identifiers, region"
            " codes, service tier labels, and capability flags. The tagging"
            " convention follows the format established by the platform team:"
            " environment first, then region, then functional descriptors."
            " Downstream systems such as Prometheus, Datadog, and PagerDuty"
            " use these tags to route alerts and build service maps."
        ),
    )

    allowed_origins: set[str] = Field(
        default={
            "https://example.com",
            "https://api.example.com",
            "https://staging.example.com",
        },
        title="Allowed CORS origins",
        description=(
            "Set of origin URLs permitted to make cross-origin requests to this"
            " server. The server includes the Access-Control-Allow-Origin header"
            " in responses only when the request's Origin header matches one of"
            " these values exactly, including the scheme and port if non-standard."
            " Wildcards are not supported to prevent overly broad access. For"
            " local development, add 'http://localhost:3000' or similar entries"
            " as needed. Each origin must use HTTPS in production environments."
            " Changes to this set take effect on the next request without requiring"
            " a server restart."
        ),
    )

    rate_limits: dict[str, int] = Field(
        default={
            "/api/auth/login": 10,
            "/api/auth/register": 5,
            "/api/users": 100,
            "/api/search": 50,
            "/api/upload": 20,
            "/api/export": 15,
            "/api/webhooks": 30,
            "/api/reports": 25,
            "/api/health": 1000,
            "/api/metrics": 200,
        },
        title="Endpoint rate limits",
        description=(
            "Mapping of API endpoint paths to their per-minute request limits on a"
            " per-client basis. Clients are identified by their authenticated user"
            " ID when available, falling back to IP address for unauthenticated"
            " requests. When a client exceeds the configured limit, the server"
            " responds with HTTP 429 Too Many Requests and includes a Retry-After"
            " header indicating how many seconds the client should wait. Endpoints"
            " not listed here inherit the global default of 60 requests per minute."
            " Authentication endpoints are deliberately set lower to mitigate"
            " brute-force attacks, while health and metrics endpoints are set"
            " higher to support frequent polling by monitoring infrastructure."
        ),
    )

    data_dir: Path = Field(
        default=Path("/var/lib/app/data"),
        title="Data directory",
        description=(
            "Filesystem path to the directory where the application stores"
            " persistent data including uploaded files, cached assets, and"
            " SQLite databases. The directory is created automatically on first"
            " startup if it does not exist, but the parent directory must be"
            " writable by the application process. In containerized deployments,"
            " this path should point to a mounted persistent volume to ensure data"
            " survives container restarts. The application requires at least 1 GB"
            " of free space in this directory for normal operation, and disk usage"
            " alerts are triggered at 90% capacity."
        ),
    )

    max_request_size: int | None = Field(
        default=None,
        title="Maximum request size",
        description=(
            "Upper limit on the size of incoming HTTP request bodies, specified in"
            " bytes. Requests exceeding this limit are rejected with HTTP 413"
            " Payload Too Large before the body is fully read, protecting the"
            " server from memory exhaustion attacks. A value of None disables the"
            " limit entirely, which may be appropriate for internal services behind"
            " a trusted reverse proxy that enforces its own limits. For public-"
            " facing APIs, a value between 1048576 (1 MB) and 10485760 (10 MB) is"
            " typical. File upload endpoints may need higher limits configured"
            " separately at the reverse proxy layer."
        ),
    )

    timeout: tuple[int, int] = Field(
        default=(30, 120),
        title="Request timeout",
        description=(
            "Timeout values for outbound HTTP connections made by the server,"
            " specified as a (connect, read) tuple in seconds. The connect timeout"
            " limits how long the server waits to establish a TCP connection to an"
            " upstream service; the read timeout limits how long it waits for the"
            " first byte of the response after the connection is established."
            " Setting these values too high can cause worker processes to block on"
            " unresponsive upstream services, reducing overall throughput. Setting"
            " them too low may cause spurious failures during transient network"
            " congestion. The defaults of 30 and 120 seconds are suitable for most"
            " internal service-to-service communication patterns."
        ),
    )
