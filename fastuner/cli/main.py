"""
Fastuner CLI - Main entry point

Commands:
- fastuner datasets upload
- fastuner datasets list
- fastuner finetune start
- fastuner finetune list
- fastuner inference run
- fastuner deployments list
- fastuner deployments delete
"""

import click
from rich.console import Console
from rich.table import Table

from fastuner import __version__

console = Console()


@click.group()
@click.version_option(version=__version__)
def cli():
    """Fastuner - One-Click Model Deployment & Fine-Tuning"""
    pass


# Import subcommands
from .datasets import datasets
from .finetune import finetune
from .inference import inference
from .deployments import deployments
from .cleanup import cleanup

cli.add_command(datasets)
cli.add_command(finetune)
cli.add_command(inference)
cli.add_command(deployments)
cli.add_command(cleanup)


if __name__ == "__main__":
    cli()
