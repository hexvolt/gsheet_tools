import click

RESULT_OK = click.style("Done.", fg="green")
RESULT_WARNING = click.style("WARNING: {}", fg="yellow")
RESULT_SKIPPED = click.style("Skipped.", fg="yellow")
RESULT_ERROR = click.style("ERROR: {}", fg="red")
