# Getting Started with QCTSS Client

This guide walks you through accessing RCCI quantum resources using the `qctss-client` Python package.

---

## 1. Get Your API Token

Log in to the **RCCI QC2 User Dashboard** and navigate to your profile settings.

1. Open the dashboard in your browser (ask your lab admin for the URL).
2. Click your username in the top-right corner → **Profile / API Token**.
3. Copy the token shown. Keep it secret — it authenticates all your requests.

> **Note:** Tokens may expire. Return to the dashboard to regenerate one if you receive a `401 Unauthorized` error.

---

## 2. Install the Package

The package is distributed as a private wheel. Install it with `pip`:

```bash
pip install qctss-client
```

Or, if you have the `.whl` file locally:

```bash
pip install qctss_client-<version>-py3-none-any.whl
```

Verify the installation:

```bash
python -c "import qctss_client; print(qctss_client.__version__)"
```

**Requirements:** Python ≥ 3.9, `requests`, `websocket-client`, `pydantic`

---

## 3. Run a Job

### Minimal Example

```python
from qctss_client import QCTSSClient

# 1. Create the client with your API token
client = QCTSSClient(token="YOUR_API_TOKEN_HERE")

# 2. Submit a job, specifying the QC setup and service
job = client.start_job(
    qc_setup_list=["Long Live ASQPU_DR0_OPX1000_3_2"],  # target QC setup name(s)
    service_name="QPU Calibration",
)
print(f"Job submitted — ID: {job.job_id}, Status: {job.status}")

# 3. Block until the job reaches the "running" state (up to 5 minutes)
port = client.wait_until_running(job_id=job.job_id, timeout=300)
print(f"Job is running on port: {port}")

# 4. (Optional) Load the quantum machine config and connect
# import quan_libs.components as QuAM
# machine = QuAM.load()
# machine.network["port"] = port
# ... run your experiment ...

# 5. Close the job when finished
client.close_job(job_id=job.job_id)

# 6. Release SDK resources
client.close()
```

### Parameter Reference

| Parameter | Type | Description |
|-----------|------|-------------|
| `token` | `str` | Your API token from the dashboard |
| `qc_setup_list` | `List[str]` | One or more target QC setup names |
| `service_name` | `str` | The service you want to run (e.g. `"QPU Calibration"`) |
| `timeout` | `int` (seconds) | How long to wait for the job to start (default: `30`) |

---

## 4. Monitor Job Status

Check all your running and past jobs at any time:

```python
statuses = client.get_my_jobs_status()
for s in statuses:
    print(f"Job {s.job_id}: {s.status}  queue={s.queue_position}  port={s.port_number}")
```

**Possible status values:** `queued` · `running` · `completed` · `failed` · `cancelled` · `timeout`

---

## 5. Cancel a Job

```python
client.cancel_job(job_id=job.job_id, reason="Experiment no longer needed")
```

---

## 6. Error Handling

```python
from qctss_client import (
    QCTSSClient,
    AuthenticationError,
    ValidationError,
    JobClientError,
    TimeoutError,
    WebSocketError,
)

client = QCTSSClient(token="YOUR_API_TOKEN_HERE")

try:
    job = client.start_job(
        qc_setup_list=["Long Live ASQPU_DR0_OPX1000_3_2"],
        service_name="QPU Calibration",
    )
    port = client.wait_until_running(job_id=job.job_id, timeout=300)
    # ... experiment ...
    client.close_job(job_id=job.job_id)

except AuthenticationError:
    print("Invalid or expired token. Please refresh it in the dashboard.")
except ValidationError as e:
    print(f"Bad parameters: {e}")
except TimeoutError:
    print("Job did not start within the timeout. Check queue status.")
except JobClientError as e:
    print(f"Job operation failed: {e}")
except WebSocketError as e:
    print(f"Real-time monitoring error: {e}")
except KeyboardInterrupt:
    print("Interrupted by user.")
finally:
    client.close()
```

---

## 7. Retrieve QC Setup Configuration Files

If you need to inspect a setup's hardware configuration or wiring before submitting:

```python
# Fetch configuration (in-memory dict)
configs = client.download_qcsetup_config_file(["Long Live ASQPU_DR0_OPX1000_3_2"])
print(configs["Long Live ASQPU_DR0_OPX1000_3_2"])

# Fetch wiring information
wirings = client.download_qcsetup_wiring(["Long Live ASQPU_DR0_OPX1000_3_2"])
print(wirings["Long Live ASQPU_DR0_OPX1000_3_2"])
```

---

## 8. Command-Line Interface

A CLI is also available for quick inspection without writing Python:

```bash
# Submit a job
qctss-client --token YOUR_TOKEN start-job "Long Live ASQPU_DR0_OPX1000_3_2" \
    --service "QPU Calibration"

# List all your jobs
qctss-client --token YOUR_TOKEN list-jobs

# Close a job
qctss-client --token YOUR_TOKEN close-job 42

# Monitor a job in real time
qctss-client --token YOUR_TOKEN monitor-job 42 --monitor-timeout 300
```

---

## Quick Reference

```
Dashboard → copy token
    │
    ▼
pip install qctss-client
    │
    ▼
QCTSSClient(token="…")
    │
    ├─ start_job(qc_setup_list=[…], service_name="…")
    │       └─ returns job.job_id
    │
    ├─ wait_until_running(job_id, timeout=300)
    │       └─ returns port number
    │
    ├─ [run your experiment on the returned port]
    │
    ├─ close_job(job_id)
    │
    └─ close()
```
