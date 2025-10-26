from prometheus_client import Counter, Summary, Gauge, CollectorRegistry, generate_latest

REGISTRY = CollectorRegistry(auto_describe=True)

REQUEST_COUNTER = Counter(
    "streamer_requests_total",
    "Total number of requests handled",
    ["endpoint", "method", "status"],
    registry=REGISTRY
)

ERROR_COUNTER = Counter(
    "streamer_errors_total",
    "Total number of 5xx errors",
    ["endpoint"],
    registry=REGISTRY
)

BYTES_STREAMED = Counter(
    "streamer_bytes_streamed_total",
    "Total bytes streamed from MinIO",
    ["video_id"],
    registry=REGISTRY
)