"""Training job logs CLI commands"""

import click
import boto3
from rich.console import Console
from rich.syntax import Syntax

from .config import get_api_base_url, get_tenant_id
from fastuner.config import get_settings

console = Console()
settings = get_settings()


@click.group()
def logs():
    """View training job logs"""
    pass


@logs.command("training")
@click.argument("sagemaker_job_name")
@click.option("--tail", default=100, help="Number of lines to show (default: 100)")
def training_logs(sagemaker_job_name: str, tail: int):
    """
    Fetch CloudWatch logs for a SageMaker training job.

    Example:
        fastuner logs training ft-default--job-6230-20251207-040030
    """
    try:
        # Get CloudWatch logs
        logs_client = boto3.client("logs", region_name=settings.aws_region)

        # SageMaker log group and stream naming convention
        log_group = f"/aws/sagemaker/TrainingJobs"
        log_stream = f"{sagemaker_job_name}/algo-1-1702000000000"  # Pattern

        # List log streams for this job
        console.print(f"[yellow]Fetching logs for {sagemaker_job_name}...[/yellow]")

        try:
            streams_response = logs_client.describe_log_streams(
                logGroupName=log_group,
                logStreamNamePrefix=sagemaker_job_name,
                orderBy="LastEventTime",
                descending=True,
                limit=5
            )

            if not streams_response.get("logStreams"):
                console.print(f"[red]No logs found for {sagemaker_job_name}[/red]")
                console.print("[yellow]Job may still be starting or logs not yet available[/yellow]")
                return

            # Get the most recent log stream
            log_stream_name = streams_response["logStreams"][0]["logStreamName"]
            console.print(f"[dim]Log stream: {log_stream_name}[/dim]\n")

            # Fetch logs
            logs_response = logs_client.get_log_events(
                logGroupName=log_group,
                logStreamName=log_stream_name,
                limit=tail,
                startFromHead=False  # Get most recent
            )

            events = logs_response.get("events", [])

            if not events:
                console.print("[yellow]No log events found[/yellow]")
                return

            # Display logs
            console.print(f"[bold]Last {len(events)} log lines:[/bold]\n")
            for event in events:
                message = event["message"].rstrip()
                # Color code based on log level
                if "ERROR" in message or "Error" in message:
                    console.print(f"[red]{message}[/red]")
                elif "WARNING" in message or "Warning" in message:
                    console.print(f"[yellow]{message}[/yellow]")
                elif "INFO" in message:
                    console.print(f"[dim]{message}[/dim]")
                else:
                    console.print(message)

        except logs_client.exceptions.ResourceNotFoundException:
            console.print(f"[red]Log group not found: {log_group}[/red]")
            console.print("[yellow]Job may still be starting or logs not yet created[/yellow]")

    except Exception as e:
        console.print(f"[red]Error fetching logs: {e}[/red]")
        raise click.Abort()
