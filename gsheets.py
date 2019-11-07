import click

from commands import tabs, files, billing, history


@click.group()
def cli():
    pass


cli.add_command(tabs.normalize)
cli.add_command(tabs.reorder)
cli.add_command(tabs.validate)
cli.add_command(tabs.find_duplicates)
cli.add_command(tabs.move_from_workbook)
cli.add_command(files.ls)
cli.add_command(billing.import_to_billing)
cli.add_command(billing.clear_expenses)
cli.add_command(history.mark_transactions)
cli.add_command(history.reset_transactions)


if __name__ == "__main__":
    cli()
