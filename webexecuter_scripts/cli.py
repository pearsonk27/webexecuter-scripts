"""CLI interface for webexecuter_scripts project."""
import click
from .task import refresh


@click.command()
@click.option(
    "--task", prompt="Task to run?", help='Job to execute (ex. "refresh").'
)
def main(task):  # pragma: no cover
    """
    The main function executes on commands:
    `python -m webexecuter_scripts` and `$ webexecuter_scripts `.
    """
    if task == "refresh":
        refresh()
    else:
        print("Unrecognized task")
