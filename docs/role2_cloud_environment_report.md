# InsightHub — Role 2: Cloud Environment Engineer Report

**Author:** Role 2 – Cloud Environment Engineer  
**Project:** InsightHub  
**Integration Status:** Complete & Verified on Local Floci GCP Emulator  
**Scope Note:** All cloud operations described herein were executed against the verified local Floci GCP emulator (`floci/floci-gcp:0.13.0`) and host Docker environment. **Actual GCP cloud deployment was NOT performed.**

---

## 1. Executive Summary & Shared Integration Baseline

The cloud environment for InsightHub has been successfully provisioned, verified, and integrated with the application stack:

| Parameter | Baseline Value | Status |
|---|---|---|
| **BigQuery Emulator Project** | `floci-local` | Active & Verified |
| **BigQuery Dataset** | `insighthub_test` | Created |
| **BigQuery Table** | `students_demo` (50 records) | Materialized & Ingested |
| **Data Access Mechanism** | GoogleSQL via REST API (`POST /bigquery/v2/projects/floci-local/queries`) | Verified in `app.py` |
| **Application Entrypoint** | `app.py` (Streamlit 1.30+ architecture) | Operational |
| **Docker Base Image** | `python:3.11-slim` | Configured |
| **Docker Image Built** | `insighthub-dashboard:latest` (ID: `sha256:b2f7aa71ccec...`, 951 MB) | Built & Cached |
| **Local Verification Container** | `insighthub-dashboard-test` (`0.0.0.0:8502->8501/tcp`) | Running & Verified |
| **Cloud Run Service** | `insighthub-dashboard` (v2 API, revision `insighthub-dashboard-00001`) | Ready (`CONDITION_SUCCEEDED`) |
| **Cloud Run Container** | `84ce5ea503ee` (published on `127.0.0.1:58085->8080/tcp`) | Running & Verified |

---

## 2. Infrastructure & Environment Verification

### 2.1 Floci Emulator & Docker Setup
- **Main Container:** `floci-gcp` (`floci/floci-gcp:latest`, container ID: `632223fc5cb0`)
- **Port:** `0.0.0.0:4588->4588/tcp`
- **Bridge Network IP:** `172.17.0.2`
- **Docker Socket Passthrough:** `/var/run/docker.sock` mounted directly into `floci-gcp`, allowing sibling container management for Cloud Run emulation.
- **DuckDB Storage Engine:** `floci-gcp-bigquery-duck` running on internal port `3000`.

### 2.2 Google Cloud Storage (GCS)
- **Bucket Created:** `insighthub-role2-test-20261127`
- **Upload Verification:** Uploaded `data/insighthub_cleaned_data.csv` as `students.csv` via `POST /storage/v1/b/insighthub-role2-test-20261127/o?uploadType=media&name=students.csv`.
- **Download Verification:** Verified object retrieval via `GET /storage/v1/b/insighthub-role2-test-20261127/o`. Returned object metadata with exact byte length matching the cleaned dataset.
- **Evidence Reference:** `evidence/role2/gcs_verification/gcs_bucket_objects.json`

### 2.3 BigQuery Dataset & Table Ingestion
- **Dataset:** `insighthub_test`
- **Table:** `students_demo`
- **Schema (9 columns):**
  - `student_id` (INTEGER)
  - `student_name` (STRING)
  - `department` (STRING)
  - `attendance_percentage` (FLOAT)
  - `internal_marks` (FLOAT)
  - `backlogs` (INTEGER)
  - `cgpa` (FLOAT)
  - `passed` (BOOLEAN)
  - `grade` (STRING)
- **Ingestion Execution:** Cleaned data (50 rows) ingested using Floci streaming API (`POST /_floci-gcp/bigquery/projects/floci-local/datasets/insighthub_test/tables/students_demo/data`) in batches of 10. Completed with `HTTP 200` and 0 errors.
- **Evidence Reference:** `evidence/role2/bigquery_verification/table_schema_students_demo.json`

### 2.4 BigQuery Query Verification Results
Executed GoogleSQL queries via Floci REST endpoint:
1. **Total Student Count Query:**
   ```sql
   SELECT COUNT(*) AS total_students
   FROM `floci-local.insighthub_test.students_demo`
   ```
   - **Observed Result:** Exactly `50` records (`rows: [{'f': [{'v': '50'}]}]`).
   - **Evidence Reference:** `evidence/role2/bigquery_verification/query_count_result.json`

2. **Department Distribution Query:**
   ```sql
   SELECT department, COUNT(*) AS student_count
   FROM `floci-local.insighthub_test.students_demo`
   GROUP BY department
   ORDER BY department
   ```
   - **Observed Department Counts:**
     - **AIML:** 13
     - **CSE:** 16
     - **ECE:** 9
     - **ISE:** 12
     - **Total:** 50
   - **Evidence Reference:** `evidence/role2/bigquery_verification/query_department_counts.json`

---

## 3. Application Migration & Dockerization

### 3.1 Streamlit REST Integration
- Replaced the initial SQLite data access layer in `app.py` with standard library `urllib.request` calls against the BigQuery queries API.
- Implemented environment variable `BIGQUERY_API_BASE_URL` with fallback default to `http://localhost:4588/bigquery/v2/projects/floci-local/queries`.
- Zero additional pip dependencies introduced; runs purely on `requirements.txt` (`streamlit`, `pandas`, `matplotlib`).

### 3.2 Docker Configuration
- **Dockerfile:**
  - Base: `python:3.11-slim`
  - Working Directory: `/app`
  - Exposed Port: `8501`
  - Entrypoint Command: `streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true`
  - Dynamic Port Injection: Dynamically binds to `${PORT:-8501}` at container runtime.
- **.dockerignore:**
  - Excludes `.venv/`, `venv/`, `__pycache__/`, `*.pyc`, `.git/`, `.pytest_cache/`, `.streamlit/`, `data/`, `notebooks/`, `.env*`.
- **Image Built:** `insighthub-dashboard:latest`
  - Size: 951 MB
  - Architecture: `linux/amd64`
  - Evidence Reference: `evidence/role2/docker_verification/docker_image_inspect.json`

### 3.3 Standalone Docker Container Verification
- **Container Launched:** `insighthub-dashboard-test`
- **Port Mapping:** `0.0.0.0:8502 -> 8501/tcp`
- **Injected Environment:** `BIGQUERY_API_BASE_URL=http://host.docker.internal:4588/bigquery/v2/projects/floci-local/queries`
- **Verification:** Verified in-container query execution and external HTTP reachability at `http://localhost:8502`.
- **Evidence Reference:** `evidence/role2/docker_verification/docker_container_inspect.json`, `docker_container_logs.txt`

---

## 4. Cloud Run v2 Deployment & Verification

### 4.1 Service Deployment
- **API Endpoint:** `POST http://localhost:4588/v2/projects/floci-local/locations/us-central1/services?serviceId=insighthub-dashboard`
- **Service Name:** `insighthub-dashboard`
- **Resource ID:** `projects/floci-local/locations/us-central1/services/insighthub-dashboard`
- **Revision Name:** `insighthub-dashboard-00001`
- **Ready Condition:** `type: Ready`, `state: CONDITION_SUCCEEDED`
- **Assigned Ingress URL:** `http://insighthub-dashboard-1efb2c36c23f.us-central1.run.localhost.floci.io:4588`
- **Evidence Reference:** `evidence/role2/cloudrun_verification/cloudrun_service_inspect.json`

### 4.2 Cloud Run Container Runtime
- **Container ID:** `84ce5ea503ee5eed199ad55d88f6b6e85e8704529ab9731d16e772944149b1de`
- **Status:** `Up` (Running on bridge IP `172.17.0.6`)
- **Published Port:** Bound dynamically to host loopback `127.0.0.1:58085 -> 8080/tcp`
- **Injected Environment Variables:**
  - `PORT=8080`
  - `BIGQUERY_API_BASE_URL=http://172.17.0.2:4588/bigquery/v2/projects/floci-local/queries`
  - `K_SERVICE=insighthub-dashboard`
  - `K_REVISION=insighthub-dashboard-00001`
- **In-Container BigQuery Verification:** Executed `SELECT COUNT(*) AS total_students` directly inside container `84ce5ea503ee`. Returned `HTTP 200` with exactly 50 records.
- **Evidence Reference:** `evidence/role2/cloudrun_verification/cloudrun_container_inspect.json`, `cloudrun_container_logs.txt`

---

## 5. Technical Diagnostics: Ingress WebSocket Limitation & Workaround

### 5.1 Observed Behavior
When navigating to the Cloud Run assigned URL `http://insighthub-dashboard-1efb2c36c23f.us-central1.run.localhost.floci.io:4588`, the browser serves the initial HTML document (`HTTP 200 OK`, 7,863 bytes), but remains stuck on the Streamlit loading skeleton.

### 5.2 Root-Cause Analysis
1. **Floci Ingress Proxy Limitation:**
   - Floci's Quarkus/Vert.x reverse proxy routes inbound HTTP requests based on the `Host` header.
   - It **does not support HTTP `101 Switching Protocols` / WebSocket connection upgrading**.
   - When the Streamlit frontend attempts a WebSocket handshake to `/_stcore/stream`, Floci strips the hop-by-hop `Upgrade` headers and proxies a standard HTTP GET, resulting in an `HTTP 200 OK` HTML fallback instead of `HTTP 101 Switching Protocols`.
   - The browser's `new WebSocket()` terminates the connection upon receiving HTTP 200, retrying indefinitely.

2. **Direct Container WebSocket Handshake:**
   - Connecting directly to the container's mapped loopback port (`127.0.0.1:58085/_stcore/stream`) returned `HTTP/1.1 101 Switching Protocols`.
   - Streamlit's internal Uvicorn server handles WebSockets correctly.

### 5.3 Verified Workaround
To interact with the live Cloud Run container in a browser:
- Open `http://localhost:58085` (or whatever ephemeral host port Floci mapped for the container).
- Full bi-directional WebSocket communication succeeds, and the complete interactive dashboard renders with all KPI cards and charts.

---

## 6. Team Integration Handover

### Role 1 (Architecture & System Design)
- Current design demonstrates containerized parity between local execution, standalone Docker execution, and Cloud Run execution.
- If true GCP deployment is planned in later stages, Cloud Run natively supports WebSockets; no proxy limitations exist on production Google Cloud Run.

### Role 3 (Data Pipeline & Ingestion Validation)
- Dataset table `floci-local:insighthub_test.students_demo` contains 50 records cleaned from raw data using `seed=42`.
- Any updates to schema or streaming ingestion can target `POST /_floci-gcp/bigquery/projects/floci-local/datasets/insighthub_test/tables/<table_name>/data`.

### Role 4 (Analytics & Dashboard Visualization)
- Queries in `app.py` use GoogleSQL standard SQL syntax (`useLegacySql: false`).
- Team members can run ad-hoc queries directly against `http://localhost:4588/bigquery/v2/projects/floci-local/queries`.

### Open Decisions Requiring Team Agreement
1. Final production table name (`students_demo` vs production `students`).
2. Authentication mechanism when transitioning from Floci emulator (unauthenticated) to production GCP (Service Account OAuth2 Bearer tokens).
