\# System Architecture



```mermaid

flowchart TD

&#x20;   A\[Camera / Image Input] --> B\[Edge AI Inference Module]

&#x20;   B --> C\[ONNX Runtime Detector]

&#x20;   C --> D\[FastAPI Backend]



&#x20;   D --> E\[Inference API]

&#x20;   D --> F\[Device Management API]

&#x20;   D --> G\[Camera Management API]

&#x20;   D --> H\[Alarm Management API]

&#x20;   D --> I\[Model Management API]



&#x20;   D --> J\[(SQLite Database)]

&#x20;   D --> K\[Prometheus Metrics]



&#x20;   L\[Docker Compose] --> D

&#x20;   M\[Ubuntu Linux VM] --> L

&#x20;   N\[Windows PowerShell SSH] --> M



&#x20;   O\[Browser / Swagger UI] --> D

```

