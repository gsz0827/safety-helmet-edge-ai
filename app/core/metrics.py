from prometheus_client import Counter, Histogram


HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)

AI_INFERENCE_REQUESTS_TOTAL = Counter(
    "ai_inference_requests_total",
    "Total AI inference requests",
)

AI_INFERENCE_ERRORS_TOTAL = Counter(
    "ai_inference_errors_total",
    "Total AI inference errors",
)

AI_INFERENCE_DURATION_SECONDS = Histogram(
    "ai_inference_duration_seconds",
    "AI inference duration in seconds",
)

ALARM_CREATED_TOTAL = Counter(
    "alarm_created_total",
    "Total alarm records created",
    ["source", "event_type"],
)
