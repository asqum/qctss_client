"""Command line interface for QCTSS Client SDK"""

import argparse
import json
import sys
import time
import threading
from typing import Optional

from .client import QCTSSClient
from .exceptions import QCTSSException
from .__init__ import __version__


def main() -> int:
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="QCTSS Client Command Line Interface",
        prog="qctss-client"
    )
    
    parser.add_argument(
        "--version",
        action="version", 
        version=f"qctss-client {__version__}"
    )
    
    # Global options
    parser.add_argument(
        "--token", 
        required=True,
        help="JWT authentication token"
    )
    parser.add_argument(
        "--backend-url",
        help="Backend API URL (overrides env config)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="Request timeout in seconds"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Start job command
    start_parser = subparsers.add_parser("start-job", help="Submit a new job")
    start_parser.add_argument(
        "qc_setups",
        nargs="+",
        help="QC setup identifiers"
    )
    start_parser.add_argument(
        "--service",
        required=True,
        help="Service name"
    )
    
    # List all jobs command
    list_parser = subparsers.add_parser("list-jobs", help="List all your jobs")
    
    # Close job command
    close_parser = subparsers.add_parser("close-job", help="Close a job")
    close_parser.add_argument(
        "job_id",
        type=int,
        help="Job ID to close"
    )
    
    # Monitor job command
    monitor_parser = subparsers.add_parser("monitor-job", help="Monitor job with WebSocket")
    monitor_parser.add_argument(
        "job_id",
        type=int,
        help="Job ID to monitor"
    )
    monitor_parser.add_argument(
        "--monitor-timeout",
        type=int,
        default=300,
        help="Monitor timeout in seconds (default: 300)"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # Initialize client
        client_args = {"token": args.token}
        if args.backend_url:
            client_args["backend_url"] = args.backend_url
        if args.timeout:
            client_args["timeout"] = args.timeout
            
        client = QCTSSClient(**client_args)
        
        try:
            if args.command == "start-job":
                job = client.start_job(
                    qc_setup_list=args.qc_setups,
                    service_name=args.service
                )
                print(json.dumps({
                    "job_id": job.job_id,
                    "status": job.status,
                    "message": job.message
                }, indent=2))
                
            elif args.command == "list-jobs":
                statuses = client.get_my_jobs_status()
                jobs_data = []
                for status in statuses:
                    jobs_data.append({
                        "job_id": status.job_id,
                        "status": status.status,
                        "qc_setup_list": status.qc_setup_list,
                        "service_name": status.service_name,
                        "queue_position": status.queue_position,
                        "created_at": status.created_at,
                        "updated_at": status.updated_at
                    })
                print(json.dumps(jobs_data, indent=2))
                
            elif args.command == "close-job":
                result = client.close_job(args.job_id)
                print(json.dumps({
                    "job_id": result.job_id,
                    "status": result.status,
                    "message": result.message
                }, indent=2))
                
            elif args.command == "monitor-job":
                # Event to control monitoring
                stop_event = threading.Event()
                
                def on_status_update(status):
                    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Job {status.job_id}:")
                    print(f"  Status: {status.status}")
                    if status.queue_position:
                        print(f"  Queue Position: {status.queue_position}")
                    
                    # Stop monitoring if job is completed
                    if status.status in ["completed", "failed", "cancelled"]:
                        print(f"  Job finished with status: {status.status}")
                        stop_event.set()
                
                def on_error(error):
                    print(f"\nWebSocket error: {error}", file=sys.stderr)
                    stop_event.set()
                
                print(f"Monitoring job {args.job_id}... (Press Ctrl+C to stop)")
                client.subscribe_job_updates(args.job_id, on_status_update, on_error)
                
                try:
                    stop_event.wait(timeout=args.monitor_timeout)
                except KeyboardInterrupt:
                    print("\nMonitoring stopped by user")
                
        finally:
            client.close()
            
        return 0
        
    except QCTSSException as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())