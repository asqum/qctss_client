# QCTSS Client SDK

A Python SDK for interacting with the QCTSS platform.

## Features

- **Job Management**: Submit, monitor, and manage quantum computing jobs
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

# Initialize client
# personal token can be generated from QCTSS web portal
client = QCTSSClient(token="your-personal-token")

# check existing job status if you want to know the status of existing running / queued jobs
job_statuses = client.get_my_jobs_status()
for status in job_statuses:
    print(f"Job {status.job_id} status: {status.status}")

# Submit a job
job_response = client.start_job(
    qc_setup_list=["setup1", "setup2"],
    service_name="service_name"
)
# get your job id in order to track it later
print(f"Job submitted: with id:{job_response.job_id}")

# monitor job with real-time updates
# timeout is the max time(in seconds) you want to wait before starting to run job
# after job started, you can have the assessing port to access the controller of the qcsetups of the job
accessing_port = client.wait_until_running(job_id=job_response.job_id, timeout=300)

# for QM controller access set the port bleow to start the pulse control.
import quan_libs.components import QuAM
machine = QuAM.load()
machine.network['port']= accessing_port
# start your pulse control logic here ...

# close the job
client.close_job(job_id=job_response.job_id)
# Clean up
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

- `token`: JWT authentication token (required)
- `backend_url`: Backend API URL (overrides env config)
- `timeout`: Request timeout in seconds (default: 30)
- `max_retries`: Max retry attempts (default: 3)
- `retry_delay`: Delay between retries (default: 5)

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