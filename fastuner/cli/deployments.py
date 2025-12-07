"""Deployment management CLI commands"""

import click
import httpx
from rich.console import Console
from rich.table import Table

from .config import get_api_base_url, get_tenant_id

console = Console()


@click.group()
def deployments():
    """Manage deployments (inference endpoints)"""
    pass


@deployments.command("list")
@click.option("--limit", default=100, help="Maximum number of deployments to show")
def list_deployments(limit: int):
    """List all active deployments"""
    api_url = get_api_base_url()
    tenant_id = get_tenant_id()

    try:
        response = httpx.get(
            f"{api_url}/v0/deployments/",
            params={"tenant_id": tenant_id, "limit": limit},
            timeout=30.0,
        )
        response.raise_for_status()
        deployments = response.json()

        if not deployments:
            console.print("[yellow]No active deployments found[/yellow]")
            return

        table = Table(title="Deployments")
        table.add_column("ID", style="cyan")
        table.add_column("Endpoint", style="green")
        table.add_column("Adapter ID", style="magenta")
        table.add_column("Status", style="yellow")
        table.add_column("Instance")
        table.add_column("TTL (hrs)", justify="right")

        for dep in deployments:
            status_color = {
                "creating": "yellow",
                "active": "green",
                "updating": "blue",
                "deleting": "red",
                "failed": "red",
            }.get(dep["status"], "white")

            ttl_hours = dep["ttl_seconds"] / 3600

            table.add_row(
                dep["id"][:8] + "...",
                dep["endpoint_name"][:30],
                dep["adapter_id"][:8] + "...",
                f"[{status_color}]{dep['status']}[/{status_color}]",
                dep["instance_type"],
                f"{ttl_hours:.1f}",
            )

        console.print(table)

    except httpx.HTTPStatusError as e:
        console.print(f"❌ [red]Error: {e.response.status_code}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")
        raise click.Abort()


@deployments.command("get")
@click.argument("deployment_id")
def get_deployment(deployment_id: str):
    """Get detailed information about a deployment"""
    api_url = get_api_base_url()
    tenant_id = get_tenant_id()

    try:
        response = httpx.get(
            f"{api_url}/v0/deployments/{deployment_id}",
            params={"tenant_id": tenant_id},
            timeout=30.0,
        )
        response.raise_for_status()
        dep = response.json()

        console.print(f"\n[bold]Deployment[/bold]")
        console.print(f"ID: [cyan]{dep['id']}[/cyan]")
        console.print(f"Endpoint: {dep['endpoint_name']}")
        console.print(f"Status: {dep['status']}")
        console.print(f"Adapter ID: {dep['adapter_id']}")
        console.print(f"\n[bold]Configuration:[/bold]")
        console.print(f"  Instance Type: {dep['instance_type']}")
        console.print(f"  Instance Count: {dep['instance_count']}")
        console.print(f"  TTL: {dep['ttl_seconds']} seconds ({dep['ttl_seconds']/3600:.1f} hours)")
        console.print(f"\n[bold]Last Used:[/bold] {dep['last_used_at']}")

        if dep.get('endpoint_arn'):
            console.print(f"\n[bold]AWS ARN:[/bold] {dep['endpoint_arn']}")

    except httpx.HTTPStatusError as e:
        console.print(f"❌ [red]Error: {e.response.status_code}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")
        raise click.Abort()


@deployments.command("create")
@click.option("--adapter-id", required=True, help="Adapter ID to deploy")
@click.option("--instance-type", default="ml.g5.2xlarge", help="SageMaker instance type")
@click.option("--instance-count", default=1, type=int, help="Number of instances")
@click.option("--ttl-hours", default=1.0, type=float, help="Time-to-live in hours")
def create_deployment(adapter_id: str, instance_type: str, instance_count: int, ttl_hours: float):
    """Create a new deployment"""
    api_url = get_api_base_url()
    tenant_id = get_tenant_id()

    payload = {
        "adapter_id": adapter_id,
        "instance_type": instance_type,
        "instance_count": instance_count,
        "ttl_seconds": int(ttl_hours * 3600),
    }

    try:
        response = httpx.post(
            f"{api_url}/v0/deployments/",
            json=payload,
            params={"tenant_id": tenant_id},
            timeout=60.0,
        )
        response.raise_for_status()

        result = response.json()
        console.print(f"✅ [green]Deployment created successfully![/green]")
        console.print(f"Deployment ID: [cyan]{result['id']}[/cyan]")
        console.print(f"Endpoint: {result['endpoint_name']}")
        console.print(f"Status: {result['status']}")

    except httpx.HTTPStatusError as e:
        console.print(f"❌ [red]Error: {e.response.status_code}[/red]")
        try:
            error_detail = e.response.json()
            console.print(f"[red]{error_detail}[/red]")
        except:
            console.print(f"[red]{e.response.text}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")
        raise click.Abort()


@deployments.command("delete")
@click.argument("deployment_id")
@click.confirmation_option(prompt="Are you sure you want to delete this deployment?")
def delete_deployment(deployment_id: str):
    """Delete a deployment and tear down the endpoint"""
    api_url = get_api_base_url()
    tenant_id = get_tenant_id()

    try:
        response = httpx.delete(
            f"{api_url}/v0/deployments/{deployment_id}",
            params={"tenant_id": tenant_id},
            timeout=60.0,
        )
        response.raise_for_status()
        console.print(f"✅ [green]Deployment {deployment_id} deleted successfully[/green]")

    except httpx.HTTPStatusError as e:
        console.print(f"❌ [red]Error: {e.response.status_code}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")
        raise click.Abort()
