\# Linux Deployment Guide



This document describes how to deploy the Safety Helmet AI Backend on a Linux server.



\## 1. Install Docker



```bash

sudo apt update

sudo apt install -y docker.io docker-compose-plugin git

```



Start Docker:



```bash

sudo systemctl enable docker

sudo systemctl start docker

```



Check Docker:



```bash

docker --version

docker compose version

```



\## 2. Clone the project



```bash

git clone https://github.com/gsz0827/safety-helmet-edge-ai.git

cd safety-helmet-edge-ai

```



\## 3. Start service



```bash

docker compose up -d --build

```



\## 4. Check container status



```bash

docker compose ps

```



\## 5. View logs



```bash

docker compose logs -f ai-backend

```



\## 6. Health check



```bash

curl http://127.0.0.1:8000/health

```



\## 7. Access API docs



Open in browser:



```text

http://SERVER\_IP:8000/docs

```



\## 8. Stop service



```bash

docker compose down

```



\## 9. Restart service



```bash

docker compose restart

```



\## 10. Database persistence



The SQLite database is stored on the host machine:



```text

./data/app.db

```



Inside the container:



```text

/app/data/app.db

```



The database URL is configured in `docker-compose.yml`:



```yaml

DATABASE\_URL=sqlite:////app/data/app.db

```

