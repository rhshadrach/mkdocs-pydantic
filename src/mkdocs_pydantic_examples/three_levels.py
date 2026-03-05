from __future__ import annotations

from pydantic import BaseModel, Field


class ThreeLevels(BaseModel):
    service_name: str = Field(
        default="my-service",
        title="Service name",
        description=(
            "Unique identifier for this service within the deployment platform."
            " The name is used as the key in service registries, as a prefix for"
            " log entries and metric names, and as the label in container"
            " orchestration systems such as Kubernetes. It must consist of"
            " lowercase alphanumeric characters and hyphens only, start with a"
            " letter, and be no longer than 63 characters to comply with DNS"
            " naming rules used for internal service discovery."
        ),
        min_length=1,
        max_length=63,
        pattern=r"^[a-z][a-z0-9-]*$",
        examples=["my-service", "auth-api", "payment-gateway"],
    )

    replicas: int = Field(
        default=3,
        title="Replica count",
        description=(
            "Number of identical service instances to run concurrently. Traffic is"
            " distributed across replicas by the load balancer using a"
            " least-connections algorithm. Running at least 2 replicas is required"
            " for high availability so that one instance can handle traffic while"
            " the other is being updated during rolling deployments. For services"
            " with strict latency requirements, 3 or more replicas are recommended"
            " to absorb traffic spikes and tolerate the loss of a single instance"
            " without degraded performance for end users."
        ),
        ge=1,
    )

    environment: str = Field(
        default="production",
        title="Environment",
        description=(
            "Name of the deployment environment this configuration targets."
            " Standard values are 'development', 'staging', and 'production'."
            " The environment string is injected into log metadata, included in"
            " metric labels, and used to select environment-specific configuration"
            " overlays such as database endpoints, feature flags, and rate limits."
            " Certain safety checks are relaxed in non-production environments;"
            " for example, self-signed TLS certificates are accepted in"
            " 'development' but rejected in 'production'."
        ),
    )

    env_vars: dict[str, str] = Field(
        default={
            "APP_ENV": "production",
            "LOG_FORMAT": "json",
            "CACHE_TTL": "3600",
            "MAX_WORKERS": "4",
            "GRACEFUL_SHUTDOWN_TIMEOUT": "30",
            "FEATURE_FLAGS_ENDPOINT": "https://flags.internal/api",
            "SENTRY_DSN": "https://key@sentry.io/123",
            "CORS_MAX_AGE": "86400",
            "SESSION_EXPIRY": "7200",
            "RATE_LIMIT_WINDOW": "60",
        },
        title="Environment variables",
        description=(
            "Key-value pairs injected as environment variables into every replica's"
            " container at startup. These variables are available to the application"
            " process and are commonly used for configuration that varies across"
            " environments, such as upstream service URLs, cache durations, and"
            " feature flag endpoints. Values are always strings; the application is"
            " responsible for parsing numeric or boolean values. Variables listed"
            " here take precedence over any identically named variables defined in"
            " the container image. Sensitive values such as API keys and database"
            " passwords should use secret references rather than plain text entries."
        ),
    )

    resource_limits: dict[str, float] = Field(
        default={
            "cpu_cores": 2.0,
            "memory_gb": 4.0,
            "ephemeral_storage_gb": 10.0,
            "gpu_count": 0.0,
        },
        title="Resource limits",
        description=(
            "Hard resource limits enforced by the container runtime for each"
            " replica. If a replica exceeds its memory limit, the kernel's"
            " out-of-memory killer terminates the process and the orchestrator"
            " automatically restarts it. CPU limits are enforced via CFS bandwidth"
            " throttling, which introduces latency rather than termination when"
            " exceeded. Ephemeral storage covers temporary files, logs, and"
            " container layer writes; exceeding this limit causes pod eviction in"
            " Kubernetes. GPU count is specified as a float to support fractional"
            " GPU sharing via MIG (Multi-Instance GPU) or time-slicing."
        ),
    )

    enabled_features: list[str] = Field(
        default=[
            "health-check",
            "graceful-shutdown",
            "structured-logging",
            "distributed-tracing",
            "circuit-breaker",
            "retry-with-backoff",
            "request-deduplication",
            "canary-deployments",
            "blue-green-routing",
            "auto-scaling",
        ],
        title="Enabled features",
        description=(
            "List of platform feature flags that are activated for this service."
            " Features are identified by their kebab-case slug and control runtime"
            " behaviors such as health-check probes, graceful shutdown handling,"
            " structured JSON logging, and distributed tracing instrumentation."
            " Deployment-related features like canary-deployments and"
            " blue-green-routing affect how new versions are rolled out."
            " auto-scaling enables the horizontal pod autoscaler which adjusts"
            " replica count based on CPU and memory utilization metrics. Features"
            " not listed here are disabled by default. The platform team maintains"
            " the canonical list of available feature slugs in the internal wiki."
        ),
    )

    networking: Networking = Field(
        title="Networking",
        description=(
            "Controls how the service is exposed to internal and external traffic,"
            " including ingress routing, TLS termination, firewall rules, DNS"
            " resolution, and security headers. These settings are applied by the"
            " platform's networking layer and affect all replicas uniformly."
            " Changes to networking configuration trigger a rolling restart of the"
            " ingress controller but do not restart the service replicas themselves."
        ),
    )


class Networking(BaseModel):
    ingress_host: str = Field(
        default="api.example.com",
        title="Ingress hostname",
        description=(
            "The fully qualified domain name used to route external traffic to this"
            " service through the ingress controller. The platform automatically"
            " provisions a DNS record pointing this hostname to the ingress load"
            " balancer's external IP. If enable_tls is true, a TLS certificate is"
            " also provisioned automatically via Let's Encrypt or the organization's"
            " internal certificate authority. Multiple services may share the same"
            " hostname and be distinguished by path-based routing rules configured"
            " separately in the ingress resource."
        ),
    )

    listen_port: int = Field(
        default=8080,
        title="Listen port",
        description=(
            "TCP port number on which the application process listens for incoming"
            " HTTP requests inside the container. The ingress controller forwards"
            " traffic from its public-facing port (typically 443 for HTTPS) to this"
            " internal port. The health check probes also target this port on the"
            " paths /healthz and /readyz. This value must match the port your"
            " application binds to at startup; a mismatch causes the readiness"
            " probe to fail and prevents the replica from receiving traffic."
        ),
        alias="port",
        ge=1,
        le=65535,
    )

    enable_tls: bool = Field(
        default=True,
        title="Enable TLS",
        description=(
            "Controls whether the ingress controller terminates TLS for traffic"
            " destined to this service. When enabled, the controller handles"
            " certificate provisioning, renewal, and termination, presenting a"
            " valid certificate to external clients and forwarding decrypted HTTP"
            " traffic to the service over the internal cluster network. When"
            " disabled, traffic between the client and the ingress controller is"
            " unencrypted, which is only acceptable for internal development"
            " environments. End-to-end encryption from ingress to pod can be"
            " configured separately via mutual TLS policies."
        ),
        deprecated="TLS is now always enabled. This field will be removed in v3.0.",
    )

    allowed_cidrs: list[str] = Field(
        default=["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"],
        title="Allowed CIDR blocks",
        description=(
            "List of CIDR blocks whose traffic is permitted to reach this service."
            " Requests originating from IP addresses outside these ranges are"
            " rejected at the network level with a TCP RST before reaching the"
            " application. The default values cover the three RFC 1918 private"
            " address ranges, which restricts access to clients within the same"
            " private network. To expose the service to the public internet, add"
            " '0.0.0.0/0' to this list, but ensure that authentication and rate"
            " limiting are properly configured before doing so."
        ),
    )

    dns_servers: list[str] = Field(
        default=["10.0.0.2", "10.0.0.3"],
        title="DNS servers",
        description=(
            "IP addresses of DNS servers used by the service for resolving"
            " hostnames of upstream dependencies. These override the default DNS"
            " configuration provided by the container runtime. Custom DNS servers"
            " are typically used to enable internal service discovery via a private"
            " DNS zone, such as resolving 'database.internal' to the current"
            " primary database IP. At least two servers should be specified for"
            " redundancy, as DNS resolution failures cascade into connection"
            " failures for all upstream calls."
        ),
    )

    header_overrides: dict[str, str] = Field(
        default={
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            "Cache-Control": "no-store",
            "Pragma": "no-cache",
            "X-Request-ID": "auto",
        },
        title="Response header overrides",
        description=(
            "HTTP headers injected into every response by the ingress proxy before"
            " it reaches the client. These headers enforce browser security"
            " policies and control caching behavior at the edge. The defaults"
            " implement a strict security posture: X-Frame-Options DENY prevents"
            " clickjacking, Strict-Transport-Security enforces HTTPS for two years"
            " including subdomains, and Content-Security-Policy restricts resource"
            " loading to the same origin. The special value 'auto' for X-Request-ID"
            " instructs the proxy to generate a unique request identifier if the"
            " client did not provide one, enabling end-to-end request tracing"
            " across services. Headers set here override any identically named"
            " headers produced by the application itself."
        ),
    )

    monitoring: Monitoring = Field(
        title="Monitoring",
        description=(
            "Configuration for the service's observability stack, including"
            " Prometheus metric scraping, OpenTelemetry distributed tracing, alert"
            " threshold definitions, and notification routing. These settings are"
            " consumed by the platform's monitoring infrastructure and do not"
            " require any application-side code changes. Changes take effect within"
            " one scrape interval after the configuration is applied."
        ),
    )


class Monitoring(BaseModel):
    metrics_path: str = Field(
        default="/metrics",
        title="Metrics path",
        description=(
            "HTTP endpoint path where the application exposes Prometheus-compatible"
            " metrics in the text exposition format. The monitoring system's scraper"
            " sends GET requests to this path at regular intervals defined by"
            " scrape_interval. The endpoint should return metrics without requiring"
            " authentication, but access is restricted to cluster-internal traffic"
            " via network policies. If your application framework provides a"
            " metrics middleware (such as prometheus_client for Python or"
            " promhttp for Go), it typically registers this path automatically."
        ),
    )

    scrape_interval: int = Field(
        default=15,
        title="Scrape interval",
        description=(
            "Number of seconds between consecutive metric collection requests from"
            " the Prometheus scraper. Lower values provide higher resolution time"
            " series data but increase storage requirements and network overhead"
            " proportionally. The default of 15 seconds provides a good balance"
            " for most services. For high-frequency trading or real-time systems"
            " where sub-second anomaly detection is needed, consider 5 seconds."
            " For batch processing jobs or low-traffic services, 30 or 60 seconds"
            " may be sufficient and reduces monitoring infrastructure costs."
        ),
        gt=0,
        multiple_of=5,
        json_schema_extra={"unit": "seconds"},
    )

    enable_tracing: bool = Field(
        default=True,
        title="Enable tracing",
        description=(
            "Controls whether the service emits distributed tracing spans via the"
            " OpenTelemetry protocol. When enabled, the platform's tracing sidecar"
            " collects spans from the application and forwards them to the central"
            " trace collector (Jaeger or Tempo). Traces allow engineers to follow a"
            " single request as it traverses multiple services, identifying latency"
            " bottlenecks and failure points. Disabling tracing reduces CPU and"
            " memory overhead by approximately 2-5%, which may be worthwhile for"
            " extremely high-throughput services where the observability trade-off"
            " is not justified."
        ),
    )

    trace_sample_rate: float = Field(
        default=0.1,
        title="Trace sample rate",
        description=(
            "Fraction of incoming requests that are selected for distributed"
            " tracing, expressed as a value between 0.0 (no requests traced) and"
            " 1.0 (all requests traced). A value of 0.1 means approximately 10%"
            " of requests generate full trace data. Sampling reduces the storage"
            " and processing costs of tracing while still providing statistical"
            " visibility into latency distributions and error patterns. For"
            " debugging specific issues, temporarily increase this to 1.0 to"
            " capture every request. Requests flagged with the X-Trace-Force header"
            " are always traced regardless of this setting, allowing on-demand"
            " debugging without configuration changes."
        ),
        ge=0.0,
        le=1.0,
    )

    alert_thresholds: dict[str, float] = Field(
        default={
            "error_rate_percent": 5.0,
            "p99_latency_ms": 500.0,
            "p95_latency_ms": 200.0,
            "cpu_usage_percent": 80.0,
            "memory_usage_percent": 85.0,
            "disk_usage_percent": 90.0,
            "queue_depth": 1000.0,
            "connection_pool_exhaustion_percent": 75.0,
            "restart_count_per_hour": 3.0,
            "request_rate_spike_factor": 5.0,
        },
        title="Alert thresholds",
        description=(
            "Mapping of metric names to the threshold values that trigger alerts"
            " when exceeded. Each key corresponds to a Prometheus query defined"
            " in the platform's alerting rule templates. Alerts fire when the"
            " metric's value crosses the threshold for a sustained period defined"
            " by the alert rule's 'for' clause, typically 5 minutes for latency"
            " metrics and 1 minute for error rates. The error_rate_percent and"
            " latency thresholds are tied to the service's SLO definitions;"
            " cpu_usage and memory_usage track resource saturation;"
            " connection_pool_exhaustion_percent warns before requests start"
            " failing due to pool starvation; request_rate_spike_factor detects"
            " sudden traffic surges relative to the rolling 24-hour average."
        ),
    )

    notification_channels: list[str] = Field(
        default=[
            "slack:#alerts-critical",
            "slack:#alerts-warning",
            "pagerduty:service-oncall",
            "email:ops-team@example.com",
            "webhook:https://status.example.com/api/incidents",
        ],
        title="Notification channels",
        description=(
            "Ordered list of notification destinations that receive alerts when"
            " thresholds are breached. Each entry uses the format 'provider:target'"
            " where the provider determines the delivery mechanism and the target"
            " specifies the recipient. Supported providers include 'slack' for"
            " Slack channel messages, 'pagerduty' for on-call escalation,"
            " 'email' for email delivery, and 'webhook' for HTTP POST callbacks"
            " to external systems. Critical alerts are sent to all channels"
            " simultaneously; warning-level alerts skip PagerDuty to avoid"
            " unnecessary on-call pages. The platform retries failed notifications"
            " up to 3 times with exponential backoff before marking the"
            " notification as undeliverable."
        ),
    )

    log_retention_days: int = Field(
        default=30,
        title="Log retention period",
        description=(
            "Number of days that log data is retained in the centralized logging"
            " system before being automatically deleted. Logs older than this"
            " threshold are purged by a nightly cleanup job. The retention period"
            " must comply with your organization's data retention policies and any"
            " applicable regulatory requirements; for example, financial services"
            " may require 90 days or more. Increasing retention increases storage"
            " costs roughly linearly. Logs that need to be preserved beyond the"
            " retention period should be archived to cold storage separately via"
            " the log export pipeline."
        ),
        ge=1,
        frozen=True,
    )

    dashboard_ids: list[str] = Field(
        default=[
            "svc-overview-001",
            "svc-latency-002",
            "svc-errors-003",
            "svc-throughput-004",
            "svc-resources-005",
        ],
        title="Dashboard IDs",
        description=(
            "Identifiers of Grafana dashboards associated with this service."
            " These IDs are used by the platform's service catalog to generate"
            " direct links to relevant dashboards in incident response runbooks"
            " and on-call handoff documents. Each dashboard provides a different"
            " operational view: the overview dashboard shows key health indicators"
            " at a glance, the latency dashboard breaks down response times by"
            " endpoint and percentile, the errors dashboard groups failures by"
            " type and source, and the resources dashboard tracks CPU, memory,"
            " and disk utilization trends over time."
        ),
    )


ThreeLevels.model_rebuild()
Networking.model_rebuild()
