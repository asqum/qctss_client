# QC-Test Space Client SDK Documentation

A Python SDK for interacting with the QCTSS platform.

_**Currently, our platform and website are not publicly accessible, You will need to contact the QC-Test Space team for VPN access.**_

---

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

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/asqum/qctss_client/blob/main/LICENSE) file for details.

## Relative Links

- [RCCI QC-Test Space](https://rcci.sinica.edu.tw/facility.php?id=7)
- [GitHub Repository](https://github.com/asqum/qctss_client)
- QC-Test Space Website (Inner)
  - You need to contact the QC-Test Website team to get VPN access to the inner website.

## Support

- Contact: [takehuge@as.edu.tw](mailto:takehuge@as.edu.tw)
- Maintainers:
  - [tina@quantaser.com](mailto:tina@quantaser.com)
  - [harui2019@as.edu.tw](mailto:harui2019@as.edu.tw)
- Issues: [GitHub Issues](https://github.com/asqum/qctss_client/issues)

## Basic Usage

```{toctree}
:maxdepth: 1
:caption: Tutorials

Quick Start <basic_usage/quick_start/index>
Check Job Status <basic_usage/check_job>
Make Reservation <basic_usage/make_reservation/index>
Handle Error and Error Response <basic_usage/error_handle>

```

## API Reference

See the [API Reference](apidoc/index) for detailed information on available classes and methods.

```{toctree}
:maxdepth: 1
:caption: API Reference

API Reference <apidoc/index>

```
