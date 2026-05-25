\# Docker Deployment Guide



This document describes how to run the Safety Helmet AI Backend with Docker and Docker Compose.



\## 1. Project structure



Main backend entrypoint:



```text

app/main.py

```



Docker-related files:



```text

Dockerfile

docker-compose.yml

.dockerignore

requirements-prod.txt

```



\## 2. Build and start service



```bash

docker compose up -d --build

```



\## 3. Check container status



```bash

docker compose ps

```



Expected status:



```text

safety-helmet-ai-backend   Up

```



\## 4. View logs



```bash

docker compose logs -f ai-backend

```



\## 5. Health check



```bash

curl http://127.0.0.1:8000/health

```



\## 6. API documentation



Open in browser:



```text

http://127.0.0.1:8000/docs

```



\## 7. Stop service



```bash

docker compose down

```



\## 8. Restart service



```bash

docker compose restart

```



\## 9. Rebuild after code changes



```bash

docker compose up -d --build

```



\## 10. Database persistence



The SQLite database is stored in:



```text

./data/app.db

```



Inside the container, it is mounted to:



```text

/app/data/app.db

```



The database path is configured in `docker-compose.yml`:



```yaml

environment:

&#x20; - DATABASE\_URL=sqlite:////app/data/app.db

```

