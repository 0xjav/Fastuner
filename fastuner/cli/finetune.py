"""Fine-tuning CLI commands"""

import click
import httpx
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import get_api_base_url, get_tenant_id

console = Console()


@click.group()
def finetune():
    """Manage fine-tuning jobs"""
    pass


@finetune.command("start")
@click.option("--model-id", required=True, help="Base model ID (e.g., meta-llama/Llama-2-7b-chat-hf)")
@click.option("--dataset-id", required=True, help="Dataset ID to use for training")
@click.option("--adapter-name", required=True, help="Name for the fine-tuned adapter")
@click.option("--method", type=click.Choice(["lora", "qlora"]), default="qlora", help="Fine-tuning method")
@click.option("--learning-rate", default=0.0002, type=float, help="Learning rate")
@click.option("--num-epochs", default=3, type=int, help="Number of training epochs")
@click.option("--batch-size", default=4, type=int, help="Batch size")
@click.option("--lora-rank", default=16, type=int, help="LoRA rank")
@click.option("--lora-alpha", default=32, type=int, help="LoRA alpha")
@click.option("--auto-deploy", is_flag=True, help="Automatically deploy after training")
def start_finetune(
    model_id: str,
    dataset_id: str,
    adapter_name: str,
    method: str,
    learning_rate: float,
    num_epochs: int,
    batch_size: int,
    lora_rank: int,
    lora_alpha: int,
    auto_deploy: bool,
):
    """
    Start a fine-tuning job.

    Example:
        fastuner finetune start \\
          --model-id meta-llama/Llama-2-7b-chat-hf \\
          --dataset-id ds_xxx \\
          --adapter-name sentiment_v1 \\
          --method qlora \\
          --auto-deploy
    """
    api_url = get_api_base_url()
    tenant_id = get_tenant_id()

    payload = {
        "base_model_id": model_id,
        "dataset_id": dataset_id,
        "adapter_name": adapter_name,
        "method": method,
        "learning_rate": learning_rate,
        "num_epochs": num_epochs,
        "batch_size": batch_size,
        "lora_rank": lora_rank,
        "lora_alpha": lora_alpha,
        "auto_deploy": auto_deploy,
    }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating fine-tune job...", total=None)

        try:
            response = httpx.post(
                f"{api_url}/v0/fine-tune-jobs/",
                json=payload,
                params={"tenant_id": tenant_id},
                timeout=60.0,
            )
            response.raise_for_status()

            progress.update(task, completed=True)

            result = response.json()
            console.print(f"\n✅ [green]Fine-tune job created successfully![/green]")
            console.print(f"Job ID: [cyan]{result['id']}[/cyan]")
            console.print(f"Status: {result['status']}")
            console.print(f"Adapter: {result['adapter_name']}")

            if result.get('sagemaker_job_name'):
                console.print(f"SageMaker Job: {result['sagemaker_job_name']}")

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


@finetune.command("list")
@click.option("--limit", default=100, help="Maximum number of jobs to show")
def list_finetune_jobs(limit: int):
    """List all fine-tune jobs"""
    api_url = get_api_base_url()
    tenant_id = get_tenant_id()

    try:
        response = httpx.get(
            f"{api_url}/v0/fine-tune-jobs/",
            params={"tenant_id": tenant_id, "limit": limit},
            timeout=30.0,
        )
        response.raise_for_status()
        jobs = response.json()

        if not jobs:
            console.print("[yellow]No fine-tune jobs found[/yellow]")
            return

        table = Table(title="Fine-Tune Jobs", show_lines=True)
        table.add_column("Job ID", style="cyan", no_wrap=False)
        table.add_column("Adapter ID", style="bright_cyan", no_wrap=False)
        table.add_column("Model", style="magenta", no_wrap=False)
        table.add_column("Status", style="yellow")
        table.add_column("Method")

        for job in jobs:
            status_color = {
                "pending": "yellow",
                "running": "blue",
                "completed": "green",
                "failed": "red",
            }.get(job["status"], "white")

            adapter_id = job.get("adapter_id") or "-"

            table.add_row(
                job["id"],
                adapter_id,
                job["base_model_id"],
                f"[{status_color}]{job['status']}[/{status_color}]",
                job["method"].upper(),
            )

        console.print(table)

    except httpx.HTTPStatusError as e:
        console.print(f"❌ [red]Error: {e.response.status_code}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")
        raise click.Abort()


@finetune.command("get")
@click.argument("job_id")
def get_finetune_job(job_id: str):
    """Get detailed information about a fine-tune job"""
    api_url = get_api_base_url()
    tenant_id = get_tenant_id()

    try:
        response = httpx.get(
            f"{api_url}/v0/fine-tune-jobs/{job_id}",
            params={"tenant_id": tenant_id},
            timeout=30.0,
        )
        response.raise_for_status()
        job = response.json()

        console.print(f"\n[bold]Fine-Tune Job: {job['adapter_name']}[/bold]")
        console.print(f"ID: [cyan]{job['id']}[/cyan]")
        console.print(f"Status: {job['status']}")
        console.print(f"Base Model: {job['base_model_id']}")
        console.print(f"Dataset ID: {job['dataset_id']}")
        console.print(f"\n[bold]Configuration:[/bold]")
        console.print(f"  Method: {job['method'].upper()}")
        console.print(f"  Learning Rate: {job['learning_rate']}")
        console.print(f"  Epochs: {job['num_epochs']}")
        console.print(f"  Batch Size: {job['batch_size']}")
        console.print(f"  LoRA Rank: {job['lora_rank']}")
        console.print(f"  LoRA Alpha: {job['lora_alpha']}")

        if job.get('sagemaker_job_name'):
            console.print(f"\n[bold]SageMaker:[/bold]")
            console.print(f"  Job Name: {job['sagemaker_job_name']}")

        if job.get('final_train_loss'):
            console.print(f"\n[bold]Metrics:[/bold]")
            console.print(f"  Final Train Loss: {job['final_train_loss']:.4f}")
            if job.get('final_val_loss'):
                console.print(f"  Final Val Loss: {job['final_val_loss']:.4f}")

    except httpx.HTTPStatusError as e:
        console.print(f"❌ [red]Error: {e.response.status_code}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")
        raise click.Abort()


@finetune.command("cancel")
@click.argument("job_id")
@click.confirmation_option(prompt="Are you sure you want to cancel this job?")
def cancel_finetune_job(job_id: str):
    """Cancel a running fine-tune job"""
    api_url = get_api_base_url()
    tenant_id = get_tenant_id()

    try:
        response = httpx.delete(
            f"{api_url}/v0/fine-tune-jobs/{job_id}",
            params={"tenant_id": tenant_id},
            timeout=30.0,
        )
        response.raise_for_status()
        console.print(f"✅ [green]Fine-tune job {job_id} cancelled[/green]")

    except httpx.HTTPStatusError as e:
        console.print(f"❌ [red]Error: {e.response.status_code}[/red]")
        raise click.Abort()
    except Exception as e:
        console.print(f"❌ [red]Error: {e}[/red]")
        raise click.Abort()
