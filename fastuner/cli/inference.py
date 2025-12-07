"""Inference CLI commands"""

import click
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import get_api_base_url, get_tenant_id

console = Console()


@click.group()
def inference():
    """Run inference with deployed adapters"""
    pass


@inference.command("run")
@click.option("--model-id", required=True, help="Base model ID")
@click.option("--adapter", required=True, help="Adapter name to use")
@click.option("--input", "input_text", required=True, help="Input text for inference")
@click.option("--max-tokens", default=100, type=int, help="Maximum tokens to generate")
@click.option("--temperature", default=0.7, type=float, help="Sampling temperature")
def run_inference(
    model_id: str,
    adapter: str,
    input_text: str,
    max_tokens: int,
    temperature: float,
):
    """
    Run inference using a deployed adapter.

    Example:
        fastuner inference run \\
          --model-id meta-llama/Llama-2-7b-chat-hf \\
          --adapter sentiment_v1 \\
          --input "I love this product!"
    """
    api_url = get_api_base_url()
    tenant_id = get_tenant_id()

    payload = {
        "model_id": model_id,
        "adapter_name": adapter,
        "inputs": [input_text],
        "parameters": {
            "max_new_tokens": max_tokens,
            "temperature": temperature,
        },
    }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running inference...", total=None)

        try:
            response = httpx.post(
                f"{api_url}/v0/inference/",
                json=payload,
                params={"tenant_id": tenant_id},
                timeout=120.0,  # 2 min for inference
            )
            response.raise_for_status()

            progress.update(task, completed=True)

            result = response.json()

            console.print(f"\n[bold]Input:[/bold]")
            console.print(Panel(input_text, border_style="cyan"))

            console.print(f"\n[bold]Output:[/bold]")
            if result["outputs"] and len(result["outputs"]) > 0:
                console.print(Panel(result["outputs"][0], border_style="green"))
            else:
                console.print(Panel(f"[yellow]No output returned. Raw result: {result}[/yellow]", border_style="yellow"))

            console.print(f"\n[dim]Latency: {result['latency_ms']:.2f}ms | Adapter: {result['adapter_name']}[/dim]")

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


@inference.command("batch")
@click.option("--model-id", required=True, help="Base model ID")
@click.option("--adapter", required=True, help="Adapter name to use")
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", type=click.Path(), help="Output file (default: stdout)")
def run_batch_inference(model_id: str, adapter: str, input_file: str, output: str):
    """
    Run batch inference from a file (one input per line).

    Example:
        fastuner inference batch \\
          --model-id meta-llama/Llama-2-7b-chat-hf \\
          --adapter sentiment_v1 \\
          inputs.txt --output results.txt
    """
    api_url = get_api_base_url()
    tenant_id = get_tenant_id()

    # Read inputs
    with open(input_file, "r", encoding="utf-8") as f:
        inputs = [line.strip() for line in f if line.strip()]

    console.print(f"Processing {len(inputs)} inputs...")

    payload = {
        "model_id": model_id,
        "adapter_name": adapter,
        "inputs": inputs,
    }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running batch inference...", total=None)

        try:
            response = httpx.post(
                f"{api_url}/v0/inference/",
                json=payload,
                params={"tenant_id": tenant_id},
                timeout=300.0,  # 5 min for batch
            )
            response.raise_for_status()

            progress.update(task, completed=True)

            result = response.json()
            outputs = result["outputs"]

            # Write outputs
            if output:
                with open(output, "w", encoding="utf-8") as f:
                    for out in outputs:
                        f.write(out + "\n")
                console.print(f"\n✅ [green]Results written to {output}[/green]")
            else:
                for i, out in enumerate(outputs):
                    console.print(f"\n[bold]Output {i+1}:[/bold]")
                    console.print(Panel(out, border_style="green"))

            console.print(f"\n[dim]Total latency: {result['latency_ms']:.2f}ms[/dim]")

        except httpx.HTTPStatusError as e:
            progress.stop()
            console.print(f"\n❌ [red]Error: {e.response.status_code}[/red]")
            raise click.Abort()
        except Exception as e:
            progress.stop()
            console.print(f"\n❌ [red]Error: {e}[/red]")
            raise click.Abort()
