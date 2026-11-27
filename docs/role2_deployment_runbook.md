# InsightHub — Role 2: Deployment & Operations Runbook

**Author:** Role 2 – Cloud Environment Engineer  
**Scope:** Operational runbook for deploying, verifying, and testing the InsightHub Streamlit dashboard across local Python, Docker, and Floci Cloud Run environments.

> [!NOTE]  
> All operations in this runbook target the local **Floci GCP emulator** (`floci/floci-gcp:latest`) and local Docker daemon. No operations deploy to or alter real GCP cloud infrastructure.

---

## 1. Quick Reference: Endpoints & Resources

| Service / Component | Endpoint / Identifier | Description |
|---|---|---|
| **Floci GCP Emulator** | `http://localhost:4588` | Local emulator hosting BigQuery, GCS, and Cloud Run |
| **BigQuery REST API** | `http://localhost:4588/bigquery/v2/projects/floci-local/queries` | SQL query execution endpoint |
| **Local Streamlit Dashboard** | `http://localhost:8501` | Host `.venv` application instance |
| **Dockerized Dashboard Container** | `http://localhost:8502` | Container `insighthub-dashboard-test` |
| **Cloud Run Ingress URL** | `http://insighthub-dashboard-1efb2c36c23f.us-central1.run.localhost.floci.io:4588` | Floci Cloud Run service ingress |
| **Cloud Run Container Direct Port** | `http://localhost:58085` | Direct loopback port to Cloud Run container |

---

## 2. Read-Only Health & Verification Commands

These commands inspect the system state without creating, modifying, or deleting any resources.

### 2.1 Verify Docker & Floci Health
```bash
# Check running containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check Floci container health check
docker inspect 632223fc5cb0 --format "{{.State.Health.Status}}"

# Check Floci HTTP endpoint
python -c "import urllib.request; resp = urllib.request.urlopen('http://localhost:4588/health'); print('Floci Health:', resp.status)"
```

### 2.2 Verify BigQuery Table & Data
```bash
# Verify 50 records in students_demo
python -c "import urllib.request, json; bt = chr(96); req = urllib.request.Request('http://localhost:4588/bigquery/v2/projects/floci-local/queries', data=json.dumps({'query': f'SELECT COUNT(*) FROM {bt}floci-local.insighthub_test.students_demo{bt}', 'useLegacySql': False}).encode('utf-8'), headers={'Content-Type': 'application/json'}); print(urllib.request.urlopen(req).read().decode('utf-8'))"

# Verify department breakdown
python -c "import urllib.request, json; bt = chr(96); req = urllib.request.Request('http://localhost:4588/bigquery/v2/projects/floci-local/queries', data=json.dumps({'query': f'SELECT department, COUNT(*) FROM {bt}floci-local.insighthub_test.students_demo{bt} GROUP BY department ORDER BY department', 'useLegacySql': False}).encode('utf-8'), headers={'Content-Type': 'application/json'}); print(urllib.request.urlopen(req).read().decode('utf-8'))"
```

### 2.3 Verify Cloud Run Services
```bash
# List all Cloud Run services in Floci
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:4588/v2/projects/floci-local/locations/us-central1/services').read().decode('utf-8'))"

# Inspect insighthub-dashboard service status
python -c "import urllib.request, json; data = json.loads(urllib.request.urlopen('http://localhost:4588/v2/projects/floci-local/locations/us-central1/services/insighthub-dashboard').read().decode('utf-8')); print('Ready State:', data.get('terminalCondition', {}).get('state'))"

# Inspect Cloud Run container logs
docker logs 84ce5ea503ee --tail 30
```

---

## 3. Resource Management & Execution Commands

### 3.1 Local Environment Setup & Execution (Host `.venv`)
```bash
# From project root (Insight-hub-main/Insight-hub-main):
# 1. Create virtual environment (if not already created)
python -m venv .venv

# 2. Install pinned dependencies
.\.venv\Scripts\pip.exe install -r requirements.txt

# 3. Launch Streamlit locally
.\.venv\Scripts\python.exe -m streamlit run app.py --server.headless true --server.port 8501
```

### 3.2 Building the Docker Image
```bash
# Build the production image from project root
docker build -t insighthub-dashboard:latest .

# Verify the built image
docker images insighthub-dashboard:latest
```

### 3.3 Running the Standalone Docker Container
```bash
# Launch container on port 8502 connecting to Floci via host gateway
docker run -d \
  --name insighthub-dashboard-test \
  -p 8502:8501 \
  -e PORT=8501 \
  -e BIGQUERY_API_BASE_URL=http://host.docker.internal:4588/bigquery/v2/projects/floci-local/queries \
  insighthub-dashboard:latest
```

### 3.4 Deploying to Floci Cloud Run
```bash
# Submit Cloud Run v2 service creation request
python -c "import urllib.request, json; payload = {'template': {'containers': [{'image': 'insighthub-dashboard:latest', 'env': [{'name': 'PORT', 'value': '8080'}, {'name': 'BIGQUERY_API_BASE_URL', 'value': 'http://172.17.0.2:4588/bigquery/v2/projects/floci-local/queries'}]}]}}; req = urllib.request.Request('http://localhost:4588/v2/projects/floci-local/locations/us-central1/services?serviceId=insighthub-dashboard', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST'); print(urllib.request.urlopen(req).read().decode('utf-8'))"
```

---

## 4. Accessing the Cloud Run Dashboard: Known Issue & Workaround

### The Problem
Accessing the assigned Cloud Run URL `http://insighthub-dashboard-1efb2c36c23f.us-central1.run.localhost.floci.io:4588` loads the initial HTML shell, but the dashboard stays on the skeleton screen because the Floci reverse proxy strips WebSocket upgrade headers and returns `HTTP 200 OK` instead of `HTTP 101 Switching Protocols`.

### The Workaround
To interact with the live Cloud Run container in a browser:
1. Identify the container's mapped loopback port:
   ```bash
   docker port $(docker ps -q --filter "name=floci-gcp-cloudrun-insighthub-dashboard") 8080
   ```
   *(Example output: `127.0.0.1:58085`)*
2. Open that URL directly in any web browser:
   `http://localhost:58085`
3. The dashboard connects via WebSocket directly to Uvicorn, rendering all KPI cards, metrics, and interactive charts immediately.

---

## 5. Troubleshooting & Diagnostics

| Symptom | Cause | Diagnostic Command | Remediation |
|---|---|---|---|
| Dashboard says `Failed to connect to BigQuery` | Floci is down or port 4588 unreachable | `curl http://localhost:4588/health` | Start Floci container (`docker start floci-gcp`) |
| Query returns `Table not found` | Dataset or table name misspelled | Check `table_schema_students_demo.json` | Use qualified identifier `` `floci-local.insighthub_test.students_demo` `` |
| Cloud Run container fails to query BigQuery | Wrong base URL injected | `docker exec <container_id> env` | Ensure `BIGQUERY_API_BASE_URL` uses `172.17.0.2:4588` or `host.docker.internal:4588` |
| Cloud Run service deployment hangs | Docker socket not mounted in Floci | `docker inspect floci-gcp -f '{{.HostConfig.Binds}}'` | Confirm `/var/run/docker.sock` is mounted |
