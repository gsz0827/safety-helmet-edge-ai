# Safety Helmet Edge AI Backend

基于 **FastAPI + ONNX Runtime + Docker + SQLite + Prometheus** 的工业安全帽检测后端系统。

本项目从安全帽检测场景出发，构建了一个面向边缘 AI 部署的后端服务。系统支持模型推理接口、设备管理、摄像头管理、告警记录、健康检查、监控指标暴露，并已完成 Docker、本地 Linux 虚拟机部署和 Windows SSH 远程操作部署流程。

---

## 1. Project Overview

本项目最初实现了基于 YOLOv8 / ONNX Runtime 的安全帽违规检测流程，后续进一步重构为更接近生产环境的 AI 后端项目结构。

当前项目重点包括：

- FastAPI 后端服务
- ONNX Runtime 推理服务封装
- SQLite 数据持久化
- Docker 镜像构建
- Docker Compose 编排部署
- Linux 虚拟机部署
- Windows 通过 SSH 操控 Ubuntu 虚拟机
- `/health` 健康检查接口
- `/docs` Swagger API 文档
- `/metrics` Prometheus 指标接口

---

## 2. Features

- 安全帽 / 未佩戴安全帽检测后端服务
- 基于 FastAPI 提供 REST API
- 支持设备、摄像头、模型、推理、告警相关接口
- 支持 SQLite 数据库持久化
- 支持 Dockerfile 构建生产镜像
- 支持 docker-compose 一键启动
- 支持 Linux 服务器 / Ubuntu 虚拟机部署
- 支持 Windows PowerShell 通过 SSH 远程管理 Ubuntu
- 支持 Prometheus `/metrics` 监控指标
- 支持 Swagger UI 自动接口文档
- 生产镜像已优化，移除训练环境中的重依赖

---

## 3. Tech Stack

| Layer | Technology |
|---|---|
| Backend Framework | FastAPI |
| ASGI Server | Uvicorn |
| Model Runtime | ONNX Runtime |
| Database | SQLite / SQLAlchemy |
| Data Validation | Pydantic |
| Monitoring | Prometheus Client |
| Containerization | Docker |
| Orchestration | Docker Compose |
| Deployment Target | Windows / Ubuntu Linux VM |
| Remote Access | OpenSSH |
| Language | Python 3.11 |

---

## 4. Project Structure

```text
safety-helmet-edge-ai/
├── app/
│   ├── api/
│   │   ├── routes_alarms.py
│   │   ├── routes_cameras.py
│   │   ├── routes_devices.py
│   │   ├── routes_inference.py
│   │   └── routes_models.py
│   ├── core/
│   ├── db/
│   ├── schemas/
│   ├── services/
│   ├── __init__.py
│   └── main.py
├── edge/
│   ├── alarm_database.py
│   ├── alarm_manager.py
│   ├── camera_stream.py
│   ├── config_loader.py
│   ├── mqtt_publisher.py
│   ├── multi_camera_manager.py
│   ├── onnx_detector.py
│   └── visualizer.py
├── ml/
├── deploy/
├── docs/
├── scripts/
├── tests/
├── tools/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-prod.txt
├── .dockerignore
└── README.md
```

---

## 5. API Endpoints

启动服务后，可以访问：

```text
http://127.0.0.1:8000/docs
```

常用接口：

| Endpoint | Description |
|---|---|
| `/health` | 服务健康检查 |
| `/docs` | Swagger API 文档 |
| `/metrics` | Prometheus 指标 |
| `/api/v1/inference` | 推理相关接口 |
| `/api/v1/devices` | 设备管理接口 |
| `/api/v1/cameras` | 摄像头管理接口 |
| `/api/v1/alarms` | 告警管理接口 |
| `/api/v1/models` | 模型管理接口 |

---

## 6. Local Development

### 6.1 Create virtual environment

Windows PowerShell:

```powershell
python -m venv venv
```

Activate:

```powershell
.\venv\Scripts\activate
```

Or use the interpreter directly:

```powershell
.\venv\Scripts\python.exe
```

### 6.2 Install dependencies

```powershell
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 6.3 Run FastAPI locally

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open API docs:

```text
http://127.0.0.1:8000/docs
```

Health check:

```powershell
curl.exe http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "industrial-ai-safety-backend",
  "version": "0.1.0",
  "env": "dev"
}
```

---

## 7. Docker Deployment on Windows

### 7.1 Build Docker image

```powershell
docker build -t safety-helmet-ai-backend:0.1 .
```

### 7.2 Run container directly

```powershell
docker run --rm -p 8000:8000 safety-helmet-ai-backend:0.1
```

Visit:

```text
http://127.0.0.1:8000/docs
```

Health check:

```powershell
curl.exe http://127.0.0.1:8000/health
```

---

## 8. Docker Compose Deployment

Recommended way:

```powershell
docker compose up -d --build
```

Check container status:

```powershell
docker compose ps
```

View logs:

```powershell
docker compose logs -f ai-backend
```

Stop service:

```powershell
docker compose down
```

Restart service:

```powershell
docker compose restart
```

Rebuild after code changes:

```powershell
docker compose up -d --build
```

---

## 9. SQLite Persistence in Docker

The application uses SQLite for lightweight local persistence.

In Docker Compose, the database is configured as:

```yaml
environment:
  - DATABASE_URL=sqlite:////app/data/app.db
```

The host directory is mounted into the container:

```yaml
volumes:
  - ./data:/app/data
```

So the database file is persisted at:

```text
./data/app.db
```

Inside the container:

```text
/app/data/app.db
```

This prevents database data from being lost when the container restarts.

---

## 10. Production Docker Image

The project uses a separate production dependency file:

```text
requirements-prod.txt
```

This avoids installing training-only dependencies such as heavy YOLO / PyTorch packages in the deployment image.

Production dependencies include:

```text
fastapi
uvicorn[standard]
python-multipart
pydantic-settings
sqlalchemy
prometheus-client
numpy
opencv-python-headless
PyYAML
paho-mqtt
onnxruntime
```

The production image was optimized from several GB to about 1 GB by removing unnecessary training dependencies.

---

## 11. Linux VM Deployment

This project has been tested on an Ubuntu virtual machine.

### 11.1 Install Docker on Ubuntu

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg git
```

Add Docker official repository:

```bash
sudo install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

Add Docker apt source:

```bash
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Install Docker Engine and Compose plugin:

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Verify installation:

```bash
docker --version
docker compose version
```

### 11.2 Allow current user to run Docker

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Test Docker:

```bash
docker ps
docker run hello-world
```

---

## 12. Deploy Project on Ubuntu

Clone the repository:

```bash
mkdir -p ~/edge_ai_projects
cd ~/edge_ai_projects
git clone https://github.com/gsz0827/safety-helmet-edge-ai.git
cd safety-helmet-edge-ai
```

Start service:

```bash
docker compose up -d --build
```

Check status:

```bash
docker compose ps
```

Health check inside Ubuntu:

```bash
curl http://127.0.0.1:8000/health
```

Visit from Windows browser:

```text
http://<UBUNTU_VM_IP>:8000/docs
```

Example:

```text
http://192.168.190.128:8000/docs
```

---

## 13. SSH from Windows to Ubuntu VM

Install and start SSH server on Ubuntu:

```bash
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh
sudo systemctl status ssh
```

Check Ubuntu IP:

```bash
hostname -I
```

Connect from Windows PowerShell:

```powershell
ssh gsz@192.168.190.128
```

After login, deploy or manage the project directly from Windows PowerShell.

---

## 14. Useful Commands

### Docker Compose

```bash
docker compose up -d
docker compose up -d --build
docker compose ps
docker compose logs -f ai-backend
docker compose restart
docker compose down
```

### Docker

```bash
docker ps
docker images
docker logs safety-helmet-ai-backend
docker stop safety-helmet-ai-backend
docker image prune
```

### Git

```bash
git status
git add .
git commit -m "update project"
git push origin main
```

---

## 15. Health Check

Local Windows:

```powershell
curl.exe http://127.0.0.1:8000/health
```

Ubuntu VM:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "industrial-ai-safety-backend",
  "version": "0.1.0",
  "env": "dev"
}
```

---

## 16. Troubleshooting

### 16.1 Port 8000 is already in use

Use another host port:

```yaml
ports:
  - "8001:8000"
```

Then visit:

```text
http://127.0.0.1:8001/docs
```

### 16.2 SQLite database cannot open

Make sure `docker-compose.yml` contains:

```yaml
environment:
  - DATABASE_URL=sqlite:////app/data/app.db
volumes:
  - ./data:/app/data
```

Then restart:

```bash
docker compose down
docker compose up -d
```

### 16.3 Docker permission denied on Ubuntu

Run:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Then test:

```bash
docker ps
```

### 16.4 Windows cannot access Ubuntu service

Check Ubuntu IP:

```bash
hostname -I
```

Make sure the service is running:

```bash
docker compose ps
```

Check health inside Ubuntu:

```bash
curl http://127.0.0.1:8000/health
```

Then access from Windows:

```text
http://<UBUNTU_VM_IP>:8000/docs
```

If using VMware, NAT mode usually works for outbound access. For easier host-to-VM access, bridged mode can also be used.

---

## 17. Project Highlights

- Built a complete AI backend service around an industrial safety detection scenario
- Refactored from script-style computer vision code into FastAPI backend architecture
- Separated backend API, edge inference logic, database layer and deployment files
- Added Dockerfile and docker-compose deployment
- Fixed SQLite persistence inside Docker containers
- Optimized production Docker image by separating training and runtime dependencies
- Successfully deployed on Ubuntu Linux VM
- Enabled Windows-to-Ubuntu SSH remote development workflow
- Exposed health check and Prometheus metrics endpoints
- Suitable as an AI backend / edge AI / computer vision deployment portfolio project

---

## 18. Future Improvements

- Add real ONNX model upload and model version management
- Add authentication for API access
- Add PostgreSQL support for production deployment
- Add Redis / message queue for async inference tasks
- Add Nginx reverse proxy
- Add HTTPS support
- Add CI/CD with GitHub Actions
- Add unit and integration tests for all API routes
- Add frontend dashboard for alarms and devices
- Deploy to cloud server or edge device