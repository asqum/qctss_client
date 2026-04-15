# QCTSS Client SDK

A Python SDK for interacting with the QCTSS platform.

## Features

- **Job Management**: Submit, monitor, and manage quantum computing jobs
- **QCSetup Management**: Download QCSetup config and wiring files
- **Real-time Updates**: WebSocket-based real-time job status monitoring
- **Robust Error Handling**: Comprehensive error handling with automatic retry logic
- **Flexible Configuration**: Environment-based configuration with sensible defaults
- **Type Safety**: Full type hints and Pydantic model validation
- **Comprehensive Testing**: Unit and integration tests included

## Installation

```bash
pip install git+https://github.com/quantaser/qctss_client.git
```

For development installation:

```bash
git clone https://github.com/quantaser/qctss_client.git
cd qctss_client
pip install -e ".[dev]"
```

## Quick Start

```python
from qctss_client import QCTSSClient
import quan_libs.components import QuAM

client = QCTSSClient(token="my-personal-token")

# Download QCSetup config files
configs = client.download_qcsetup_config_file(["qc1", "qc2"])
for name, config in configs.items():
    print(f"{name}: {config}")

# Download QCSetup wiring files
wirings = client.download_qcsetup_wiring(["qc1", "qc2"])

job_response = client.start_job(
    qc_setup_list=["Long Live ASQPU_DR0_OPX1000_3_2"],
    service_name="QPU Calibration"
)
accessing_port = client.wait_until_running(job_id=job_response.job_id, timeout=300)

machine = QuAM.load()
machine.network['port']= accessing_port

client.close_job(job_id=job_response.job_id)
client.close()
```

## API Reference

### QCTSSClient

#### Constructor

```python
QCTSSClient(
    token: str,
    backend_url: Optional[str] = None,
    timeout: Optional[int] = None,
    max_retries: Optional[int] = None,
    retry_delay: Optional[int] = None
)
```

- `token`: authentication token (required)
- `backend_url`: Backend API URL (overrides env config)
- `timeout`: Request timeout in seconds (default: 30)
- `max_retries`: Max retry attempts (default: 3)
- `retry_delay`: Delay between retries (default: 5)
#### download_qcsetup_config_file

```python
download_qcsetup_config_file(
    qcsetup_names: List[str]
) -> Dict[str, dict]
```

Download QCSetup config files for multiple QCSetups (client token required).

**Parameters**:
- `qcsetup_names`: List of QCSetup names (non-empty)

**Returns**: Dict[str, dict] - key=QCSetup name, value=parsed config dict

**Raises**:
- `QCSetupNotActiveError`: QCSetup status is not 'active' (403)
- `QCSetupNotFoundError`: QCSetup doesn't exist (404)
- `AuthenticationError`: Invalid token
- `TimeoutError`: Request timed out

**Example**:
```python
configs = client.download_qcsetup_config_file(["qc1", "qc2", "qc3"])
for name, config in configs.items():
    print(f"{name}: {config}")
```

#### download_qcsetup_wiring

```python
download_qcsetup_wiring(
    qcsetup_names: List[str]
) -> Dict[str, dict]
```

Download QCSetup wiring files for multiple QCSetups (client token required).

**Parameters**:
- `qcsetup_names`: List of QCSetup names (non-empty)

**Returns**: Dict[str, dict] - key=QCSetup name, value=parsed wiring dict

**Raises**:
- `QCSetupNotActiveError`: QCSetup status is not 'active' (403)
- `QCSetupNotFoundError`: QCSetup doesn't exist (404)
- `AuthenticationError`: Invalid token
- `TimeoutError`: Request timed out

**Example**:
```python
wirings = client.download_qcsetup_wiring(["qc1", "qc2"])
for name, wiring in wirings.items():
    print(f"{name}: {wiring}")
```


#### start_job

```python
start_job(qc_setup_list: List[str], service_name: str) -> JobResponse
```

Submit a new quantum computing job.

**Parameters**:
- `qc_setup_list`: List of QC setup identifiers (non-empty)
- `service_name`: Service name for the job (non-empty)

**Returns**: `JobResponse` with job_id and initial status

**Raises**:
- `ValidationError`: Invalid parameters
- `JobClientError`: Job submission failed
- `TimeoutError`: Request timed out
- `AuthenticationError`: Invalid or expired token

#### get_my_jobs_status

```python
get_my_jobs_status() -> list[JobStatus]
```

Get status of all jobs for current user.

**Parameters**: None

**Returns**: List of `JobStatus` objects with current job information

**Raises**:
- `AuthorizationError`: Not authorized to view jobs
- `TimeoutError`: Request timed out

#### close_job

```python
close_job(job_id: int) -> JobResponse
```

Close/cancel a running job.

**Parameters**:
- `job_id`: Job identifier (positive integer)

**Returns**: `JobResponse` with updated status

**Raises**:
- `ValidationError`: Invalid job_id
- `JobNotFoundError`: Job doesn't exist
- `InvalidJobStateError`: Job cannot be closed (already finished)
- `AuthorizationError`: Not authorized to close job
- `TimeoutError`: Request timed out

#### subscribe_job_updates

```python
subscribe_job_updates(
    job_id: int, 
    callback: Callable[[JobStatus], None],
    on_error: Optional[Callable[[Exception], None]] = None
) -> None
```

Subscribe to real-time job status updates via WebSocket.

**Parameters**:
- `job_id`: Job identifier to monitor
- `callback`: Function called when status updates are received
- `on_error`: Optional error handler function

**Raises**:
- `ValidationError`: Invalid job_id
- `WebSocketConnectionError`: Failed to establish WebSocket connection
- `WebSocketAuthError`: WebSocket authentication failed

#### wait_until_running

```python
wait_until_running(
    job_id: int,
    timeout: Optional[int] = None,
    on_status: Optional[Callable[[JobStatus], None]] = None
) -> int
```

Wait for job to transition from queued to running status.

This is a convenience method that automatically:
1. Subscribes to WebSocket updates for the job
2. Monitors status changes in real-time
3. Returns when job reaches 'running' state
4. Automatically disconnects WebSocket after job starts

You can press Ctrl+C to cancel waiting and clean up the WebSocket connection.

**Parameters**:
- `job_id`: Job identifier to monitor (positive integer)
- `timeout`: Maximum time to wait in seconds (None = wait forever)
- `on_status`: Optional callback function for status updates during waiting

**Returns**: Port number assigned when job starts running

**Raises**:
- `ValidationError`: Invalid job_id
- `TimeoutError`: Job didn't reach 'running' state within timeout
- `WebSocketError`: WebSocket connection failed
- `KeyboardInterrupt`: User pressed Ctrl+C to cancel waiting

**Example**:
```python
job = client.start_job(["setup1", "setup2"], "quantum_simulation")

try:
    port = client.wait_until_running(job.job_id, timeout=300)
    print(f"Job is running! Access port: {port}")
    
    # Configure your quantum controller with the port
    # ... your quantum control logic ...
    
    client.close_job(job.job_id)
except TimeoutError:
    print("Job took too long to start")
    client.close_job(job.job_id)
except KeyboardInterrupt:
    print("Waiting cancelled by user")
    client.close_job(job.job_id)
```

#### close

```python
close() -> None
```

Close all connections and clean up resources.

### Data Models

#### JobResponse

```python
class JobResponse(BaseModel):
    job_id: int
    status: str
    message: Optional[str] = None
```

#### JobStatus

```python
class JobStatus(BaseModel):
    job_id: int
    status: str
    qc_setup_list: List[str]
    service_name: str
    queue_position: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
```

## Error Handling

The SDK provides comprehensive error handling with specific exceptions for different error conditions:

```python
from qctss_client import (
    QCTSSClient,
    AuthenticationError,
    AuthorizationError,
    JobClientError,
    JobNotFoundError,
    InvalidJobStateError,
    ValidationError,
    WebSocketError,
    TimeoutError
)

try:
    client = QCTSSClient(token="your-token")
    
    # Submit job
    job = client.start_job(["setup1"], "quantum_sim")
    
    # Monitor job
    def handle_update(status):
        print(f"Job {status.job_id}: {status.status}")
    
    def handle_error(error):
        print(f"WebSocket error: {error}")
    
    client.subscribe_job_updates(job.job_id, handle_update, handle_error)
    
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
    
except ValidationError as e:
    print(f"Invalid parameters: {e}")
    
except JobClientError as e:
    print(f"Job operation failed: {e}")
    
except WebSocketError as e:
    print(f"WebSocket error: {e}")
    
except TimeoutError as e:
    print(f"Request timed out: {e}")
    
finally:
    if 'client' in locals():
        client.close()
```

### Exception Hierarchy

```
Exception
└── RCCIException (base)
    ├── ConfigError
    ├── AuthenticationError
    ├── AuthorizationError
    ├── JobClientError
    │   ├── JobNotFoundError
    │   └── InvalidJobStateError
    ├── WebSocketError
    │   ├── WebSocketConnectionError
    │   └── WebSocketAuthError
    ├── ValidationError
    └── TimeoutError
```


## Development

### Setting up Development Environment

```bash
git clone https://github.com/quantaser/qctss_client.git
cd qctss_client
pip install -e ".[dev]"
```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Email: tina@quantaser.com
- Issues: [GitHub Issues](https://github.com/quantaser/qctss_client.git/issues)
