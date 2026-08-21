# QC-Test Space Client SDK

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
pip install git+https://github.com/asqum/qctss_client.git
```

For development installation:

```bash
git clone https://github.com/asqum/qctss_client.git
cd qctss_client
pip install -e ".[dev]"
```

## Documentation

[https://asqum.github.io/qctss_client/](https://asqum.github.io/qctss_client/)

### Token Permissions

`qctss-client` uses **client token** (type='client'), with the following permissions:

- ✅ Download config and wiring for active QCSetups
- ✅ Submit, monitor, and close jobs
- ❌ Cannot upload config/wiring (requires `qctss-admin` with admin token)
- ❌ Cannot access billing data

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

- Contact: [takehuge@as.edu.tw](mailto:takehuge@as.edu.tw)
- Maintainers:
  - [tina@quantaser.com](mailto:tina@quantaser.com)
  - [harui2019@as.edu.tw](mailto:harui2019@as.edu.tw)
- Issues: [GitHub Issues](https://github.com/asqum/qctss_client/issues)
