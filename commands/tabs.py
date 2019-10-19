import click

from models.spreadsheet import Spreadsheet


@click.command()
@click.argument("filename")
@click.option("--one-by-one", is_flag=True)
@click.option("--reorder/--no-reorder", default=True)
@click.option("--validate/--no-validate", default=False)
def normalize(filename, one_by_one, reorder, validate):
    """
    Normalize all tabs in the spreadsheet.

    This includes:
    1. Renaming
        Copy of 2018/08/01 PM ==> 01
        Copy of 2018/08/01 ==> 01a (if tab "01" already exists)

        If the title of the tab does not correspond to the filename,
        then the warning shows up and full date remains in the title.

    2. Sorting tabs in ascending order
    3. Validation of prices.
        If a sum of prices does not correspond the total/subtotal
        price, a warning will be shown.
    4. Identification of potential duplicates.
    """
    click.echo(f"Analyzing tabs in {filename}...")
    spreadsheet = Spreadsheet(filename)

    spreadsheet.rename_tabs(one_by_one=one_by_one, dry=True)

    if click.confirm("Rename all tabs (tabs without proper date will be skipped)?"):
        spreadsheet.rename_tabs(one_by_one=one_by_one)

    if reorder:
        click.echo("Sorting all tabs alphabetically...")
        spreadsheet.reorder()

    if validate:
        click.echo("Validating prices in all tabs...")
        spreadsheet.validate()

    click.echo("Looking for duplicate receipts...")
    spreadsheet.find_duplicates()


@click.command()
@click.argument("filename")
def reorder(filename):
    """Reorder all tabs in the spreadsheet alphabetically."""
    spreadsheet = Spreadsheet(filename)
    click.echo("Sorting all tabs alphabetically...")
    spreadsheet.reorder()


@click.command()
@click.argument("filename")
def validate(filename):
    """Analyze spreadsheet for duplicate tabs."""
    spreadsheet = Spreadsheet(filename)
    click.echo("Validating prices in all tabs...")
    spreadsheet.validate()


@click.command()
@click.argument("filename")
def find_duplicates(filename):
    """Analyze spreadsheet for duplicate tabs."""
    spreadsheet = Spreadsheet(filename)
    click.echo("Looking for duplicate receipts...")
    spreadsheet.find_duplicates()
