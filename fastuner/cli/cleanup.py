"""CLI commands for ephemerality management"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import json

from fastuner.core.ephemerality import EphemeralityManager
from fastuner.database import SessionLocal

console = Console()


@click.group()
def cleanup():
    """Manage ephemeral resource cleanup"""
    pass


@cleanup.command()
@click.option("--dry-run", is_flag=True, help="Only report stale deployments without deleting")
def run(dry_run):
    """Run cleanup cycle to delete stale deployments"""
    try:
        manager = EphemeralityManager()

        if dry_run:
            console.print("[yellow]Running in DRY RUN mode - no resources will be deleted[/yellow]\n")

        with console.status("[bold blue]Finding stale deployments...", spinner="dots"):
            summary = manager.run_cleanup_cycle(dry_run=dry_run)

        # Display results
        if summary["stale_count"] == 0:
            console.print("[green]✓[/green] No stale deployments found")
            return

        console.print(f"\n[yellow]Found {summary['stale_count']} stale deployment(s)[/yellow]\n")

        # Create results table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Deployment ID", style="dim")
        table.add_column("Endpoint Name")
        table.add_column("Tenant ID", style="dim")

        if dry_run:
            table.add_column("Last Used")
            table.add_column("TTL (sec)")

            for result in summary["results"]:
                table.add_row(
                    result["deployment_id"][:12] + "...",
                    result["endpoint_name"],
                    result["tenant_id"][:8] + "...",
                    result.get("last_used_at", "N/A"),
                    str(result.get("ttl_seconds", "N/A")),
                )
        else:
            table.add_column("Status")
            table.add_column("Error")

            for result in summary["results"]:
                status = "[green]✓ Cleaned[/green]" if result["success"] else "[red]✗ Failed[/red]"
                error = result.get("error", "")[:50] if result.get("error") else ""

                table.add_row(
                    result["deployment_id"][:12] + "...",
                    result["endpoint_name"],
                    result["tenant_id"][:8] + "...",
                    status,
                    error,
                )

        console.print(table)

        # Summary
        if not dry_run:
            console.print(
                f"\n[green]✓[/green] Cleaned: {summary['cleaned_count']} | "
                f"[red]✗[/red] Failed: {summary['failed_count']}"
            )

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()


@cleanup.command()
@click.option("--tenant-id", help="Filter by tenant ID")
def cost_report(tenant_id):
    """Generate cost report for active deployments"""
    try:
        db = SessionLocal()
        manager = EphemeralityManager()

        with console.status("[bold blue]Generating cost report...", spinner="dots"):
            report = manager.get_cost_report(db, tenant_id=tenant_id)

        db.close()

        # Display header
        header = f"💰 Cost Report"
        if tenant_id:
            header += f" (Tenant: {tenant_id[:12]}...)"

        console.print(Panel(header, style="bold cyan"))

        # Summary
        console.print(f"\n[cyan]Active Deployments:[/cyan] {report['active_count']}")
        console.print(f"[cyan]Total Hourly Cost:[/cyan] ${report['total_hourly_cost']}")
        console.print(f"[cyan]Est. Monthly Cost:[/cyan] ${report['estimated_monthly_cost']}\n")

        if report["active_count"] == 0:
            console.print("[dim]No active deployments[/dim]")
            return

        # Deployment table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Endpoint", style="dim")
        table.add_column("Instance")
        table.add_column("Count")
        table.add_column("$/hour", justify="right")
        table.add_column("Last Used", style="dim")
        table.add_column("Idle Time")

        for deployment in report["deployments"]:
            # Format idle time
            idle_time = "N/A"
            if deployment["time_since_use_seconds"] is not None:
                seconds = deployment["time_since_use_seconds"]
                if seconds < 60:
                    idle_time = f"{int(seconds)}s"
                elif seconds < 3600:
                    idle_time = f"{int(seconds/60)}m"
                else:
                    idle_time = f"{int(seconds/3600)}h"

            # Format last used
            last_used = "Never"
            if deployment["last_used_at"]:
                last_used = deployment["last_used_at"].split("T")[1][:8]  # Show time only

            table.add_row(
                deployment["endpoint_name"][:30],
                deployment["instance_type"],
                str(deployment["instance_count"]),
                f"${deployment['hourly_cost']:.3f}",
                last_used,
                idle_time,
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()


@cleanup.command()
def status():
    """Show cleanup configuration and status"""
    try:
        db = SessionLocal()
        manager = EphemeralityManager()

        stale_deployments = manager.find_stale_deployments(db)
        report = manager.get_cost_report(db)

        db.close()

        # Configuration panel
        config_table = Table(show_header=False, box=None)
        config_table.add_column("Key", style="cyan")
        config_table.add_column("Value")

        config_table.add_row("Active Deployments", str(report["active_count"]))
        config_table.add_row("Stale Deployments", str(len(stale_deployments)))
        config_table.add_row("Total Hourly Cost", f"${report['total_hourly_cost']}")

        console.print(Panel(config_table, title="Cleanup Status", style="bold cyan"))

        if len(stale_deployments) > 0:
            console.print(
                f"\n[yellow]⚠[/yellow] {len(stale_deployments)} deployment(s) ready for cleanup. "
                f"Run [cyan]fastuner cleanup run[/cyan] to clean them up."
            )
        else:
            console.print("\n[green]✓[/green] No stale deployments found")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Abort()
