import click

RESULT_OK = click.style("OK.", fg="green")
RESULT_WARNING = click.style("WARNING: {}", fg="yellow")
RESULT_SKIPPED = click.style("Skipped.", fg="yellow")
RESULT_ERROR = click.style("ERROR: {}", fg="red")
