"""Command line interface for QCTSS Client SDK"""

import argparse
import json
import sys
from typing import Any, Literal

from .__init__ import __version__
from .client import QCTSSClient
from .client.subscribe import CLIJobMonitor
from .exceptions import QCTSSException
from .utils import DATETIME_STR_FORMAT


class QCTSSClientCLINameSpace(argparse.Namespace):
    """Custom namespace for QCTSSClient CLI arguments"""

    token: str
    """JWT authentication token"""
    backend_url: str
    """Backend API URL (overrides env config)"""
    timeout: int
    """Request timeout in seconds"""

    command: Literal["start-job", "list-jobs", "close-job", "monitor-job"]
    """The command to execute (start-job, list-jobs, close-job, monitor-job)."""

    service: str
    """The service name for start-job command."""
    qc_setups: list[str]
    """List of QC setup identifiers for start-job command."""

    job_id: int
    """The job ID for close-job and monitor-job commands."""


def _print_json(data: Any) -> None:
    """Print data as formatted JSON.

    Args:
        data (Any): Data to be printed as JSON.
    """
    print(json.dumps(data, indent=2))


def _handle_start_job(args: QCTSSClientCLINameSpace, client: QCTSSClient) -> None:
    """Handle the start-job command.

    Args:
        args (QCTSSClientCLINameSpace): Parsed command-line arguments.
        client (QCTSSClient): Initialized QCTSSClient instance.
    """

    job = client.start_job(qc_setup_list=args.qc_setups, service_name=args.service)
    _print_json(
        {
            "job_id": job.job_id,
            "status": job.status,
            "message": job.message,
        }
    )


def _handle_list_jobs(args: QCTSSClientCLINameSpace, client: QCTSSClient) -> None:
    """Handle the list-jobs command.

    Args:
        args (QCTSSClientCLINameSpace): Parsed command-line arguments.
        client (QCTSSClient): Initialized QCTSSClient instance.
    """

    statuses = client.get_my_jobs_status()
    jobs_data = [
        {
            "job_id": status.job_id,
            "status": status.status,
            "qc_setup_list": status.qc_setup_list,
            "service_name": status.service_name,
            "queue_position": status.queue_position,
            "created_at": (
                status.created_at.strftime(DATETIME_STR_FORMAT)
                if status.created_at
                else None
            ),
            "updated_at": (
                status.updated_at.strftime(DATETIME_STR_FORMAT)
                if status.updated_at
                else None
            ),
        }
        for status in statuses
    ]
    _print_json(jobs_data)


def _handle_close_job(args: QCTSSClientCLINameSpace, client: QCTSSClient) -> None:
    """Handle the close-job command.

    Args:
        args (QCTSSClientCLINameSpace): Parsed command-line arguments.
        client (QCTSSClient): Initialized QCTSSClient instance.
    """

    result = client.close_job(args.job_id)
    _print_json(
        {
            "job_id": result.job_id,
            "status": result.status,
            "message": result.message,
        }
    )


def _build_parser() -> argparse.ArgumentParser:
    """Create and configure the CLI argument parser."""

    parser = argparse.ArgumentParser(
        description="QCTSS Client Command Line Interface", prog="qctss-client"
    )
    parser.add_argument(
        "--version", action="version", version=f"qctss-client {__version__}"
    )

    parser.add_argument("--token", required=True, help="JWT authentication token")
    parser.add_argument("--backend-url", help="Backend API URL (overrides env config)")
    parser.add_argument("--timeout", type=int, help="Request timeout in seconds")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    start_parser = subparsers.add_parser("start-job", help="Submit a new job")
    start_parser.add_argument("qc_setups", nargs="+", help="QC setup identifiers")
    start_parser.add_argument("--service", required=True, help="Service name")

    subparsers.add_parser("list-jobs", help="List all your jobs")

    close_parser = subparsers.add_parser("close-job", help="Close a job")
    close_parser.add_argument("job_id", type=int, help="Job ID to close")

    monitor_parser = subparsers.add_parser(
        "monitor-job", help="Monitor job with WebSocket"
    )
    monitor_parser.add_argument("job_id", type=int, help="Job ID to monitor")
    monitor_parser.add_argument(
        "--monitor-timeout",
        type=int,
        default=300,
        help="Monitor timeout in seconds (default: 300)",
    )

    return parser


def main() -> int:
    """Main CLI entry point"""

    parser = _build_parser()
    args = parser.parse_args(namespace=QCTSSClientCLINameSpace())

    if not args.command:
        parser.print_help()
        return 1

    try:
        # Initialize client
        client_args: dict[str, Any] = {"token": args.token}
        if args.backend_url:
            client_args["backend_url"] = args.backend_url
        if args.timeout:
            client_args["timeout"] = args.timeout

        client = QCTSSClient(**client_args)

        try:
            if args.command == "start-job":
                _handle_start_job(args, client)

            elif args.command == "list-jobs":
                _handle_list_jobs(args, client)

            elif args.command == "close-job":
                _handle_close_job(args, client)

            elif args.command == "monitor-job":
                # Event to control monitoring

                cli_monitor = CLIJobMonitor(
                    job_id=args.job_id, timeout=args.monitor_timeout
                )
                client.subscribe_job_updates(
                    args.job_id,
                    callback=cli_monitor.on_status_update,
                    handle_error=cli_monitor.on_error,
                )
                cli_monitor.wait()

        finally:
            client.close()

        return 0

    except QCTSSException as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
