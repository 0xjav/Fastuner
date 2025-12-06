"""Dataset management CLI commands"""

import click
import httpx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

from .config import get_api_base_url, get_tenant_id

console = Console()


@click.group()
def datasets():
    """Manage datasets"""
    pass


@datasets.command("upload")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--name", required=True, help="Dataset name")
@click.option(
    "--task-type",
    type=click.Choice(["text_generation", "classification", "qa"]),
    required=True,
    help="Task type for the dataset",
)
def upload_dataset(file_path: str, name: str, task_type: str):
    """
    Upload a dataset for fine-tuning.

    Example:
        fastuner datasets upload data.jsonl --name "sentiment" --task-type classification
    """
    api_url = get_api_base_url()
    tenant_id = get_tenant_id()

    file_path_obj = Path(file_path)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Uploading and validating dataset...", total=None)

        try:
            with open(file_path_obj, "rb") as f:
                files = {"file": (file_path_obj.name, f, "application/x-ndjson")}
                data = {
                    "name": name,
                    "task_type": task_type,
                    "tenant_id": tenant_id,
                }

                response = httpx.post(
                    f"{api_url}/v0/datasets/",
                    files=files,
                    data=data,
                    timeout=300.0,  # 5 min timeout for large files
                )
                response.raise_for_status()

            progress.update(task, completed=True)

            result = response.json()
            console.print(f"\n✅ [green]Dataset uploaded successfully![/green]")
            console.print(f"Dataset ID: [cyan]{result['id']}[/cyan]")
            console.print(f"Total samples: {result['total_samples']}")
            console.print(f"Train: {result['train_samples']} | Val: {result['val_samples']} | Test: {result['test_samples']}")

        except httpx.HTTPStatusError as e:
            progress.stop()
            console.print(f"\n❌ [red]Error: {e.response.status_code}[/red]")
            try:
                error_detail = e.response.json().get("detail", str(e))
                console.print(f"[red]{error_detail}[/red]")
            except:
                console.print(f"[red]{e}[/red]")
            raise click.Abort()
        except Exception as e:
            progress.stop()
            console.print(f"\n❌ [red]Error: {e}[/red]")
            raise click.Abort()


@datasets.command("list")
@click.option("--limit", default=100, help="Maximum number of datasets to show")
def list_datasets(limit: int):
    """List all datasets"""
    api_url = get_api_base_url()
    tenant_id = get_tenant_id()

    try:
        response = httpx.get(
            f"{api_url}/v0/datasets/",
            params={"tenant_id": tenant_id, "limit": limit},
            timeout=30.0,
        )
        response.raise_for_status()
        datasets = response.json()

        if not datasets:
            console.print("[yellow]No datasets found[/yellow]")
            return

        table = Table(title="Datasets")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Task Type", style="magenta")
        table.add_column("Samples", justify="right")
        table.add_column("Train/Val/Test", justify="right")

        for ds in datasets:
            table.add_row(
                ds["id"][:8] + "...",
                ds["name"],
                ds["task_type"],
                str(ds["total_samples"]),
                f"{ds['train_samples']}/{ds['val_samples']}/{ds['test_samples']}",
            )

        console.print(table)

    except httpx.HTTPStatusError as e:
        console.print(f"❌ [red]Error: {e.response.status_code}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")
        raise click.Abort()


@datasets.command("get")
@click.argument("dataset_id")
def get_dataset(dataset_id: str):
    """Get detailed information about a dataset"""
    api_url = get_api_base_url()
    tenant_id = get_tenant_id()

    try:
        response = httpx.get(
            f"{api_url}/v0/datasets/{dataset_id}",
            params={"tenant_id": tenant_id},
            timeout=30.0,
        )
        response.raise_for_status()
        ds = response.json()

        console.print(f"\n[bold]Dataset: {ds['name']}[/bold]")
        console.print(f"ID: [cyan]{ds['id']}[/cyan]")
        console.print(f"Task Type: {ds['task_type']}")
        console.print(f"Schema Version: {ds['schema_version']}")
        console.print(f"\n[bold]Samples:[/bold]")
        console.print(f"  Total: {ds['total_samples']}")
        console.print(f"  Train: {ds['train_samples']}")
        console.print(f"  Val: {ds['val_samples']}")
        console.print(f"  Test: {ds['test_samples']}")
        console.print(f"\n[bold]Split Configuration:[/bold]")
        console.print(f"  Seed: {ds['split_seed']}")
        console.print(f"  Ratios: {ds['split_ratios']}")

    except httpx.HTTPStatusError as e:
        console.print(f"❌ [red]Error: {e.response.status_code}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")
        raise click.Abort()


@datasets.command("delete")
@click.argument("dataset_id")
@click.confirmation_option(prompt="Are you sure you want to delete this dataset?")
def delete_dataset(dataset_id: str):
    """Delete a dataset"""
    api_url = get_api_base_url()
    tenant_id = get_tenant_id()

    try:
        response = httpx.delete(
            f"{api_url}/v0/datasets/{dataset_id}",
            params={"tenant_id": tenant_id},
            timeout=30.0,
        )
        response.raise_for_status()
        console.print(f"✅ [green]Dataset {dataset_id} deleted successfully[/green]")

    except httpx.HTTPStatusError as e:
        console.print(f"❌ [red]Error: {e.response.status_code}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")
        raise click.Abort()
