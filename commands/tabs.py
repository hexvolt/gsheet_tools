import click

from models.receipts_sheet import ReceiptsSheet


@click.command()
@click.argument("filename")
@click.option("--one-by-one", is_flag=True)
@click.option("--reorder/--no-reorder", default=True)
@click.option("--validate/--no-validate", default=False)
def normalize(filename, one_by_one, reorder, validate):
    """
    Normalize all tabs in the receipts spreadsheet.

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
    receipts_sheet = ReceiptsSheet(filename)

    receipts_sheet.rename_tabs(one_by_one=one_by_one, dry=True)

    if click.confirm("Rename all tabs (tabs without proper date will be skipped)?"):
        receipts_sheet.rename_tabs(one_by_one=one_by_one)

    if reorder:
        click.echo("Sorting all tabs alphabetically...")
        receipts_sheet.reorder()

    if validate:
        click.echo("Validating prices in all tabs...")
        receipts_sheet.validate()

    click.echo("Looking for duplicate receipts...")
    receipts_sheet.find_duplicates()


@click.command()
@click.argument("filename")
def reorder(filename):
    """Reorder all tabs in the receipts sheet alphabetically."""
    receipts_sheet = ReceiptsSheet(filename)
    click.echo("Sorting all tabs alphabetically...")
    receipts_sheet.reorder()


@click.command()
@click.argument("filename")
def validate(filename):
    """Analyze receipts sheet for duplicate tabs."""
    receipts_sheet = ReceiptsSheet(filename)
    click.echo("Validating prices in all tabs...")
    receipts_sheet.validate()


@click.command()
@click.argument("filename")
def find_duplicates(filename):
    """Analyze receipts sheet for duplicate tabs."""
    receipts_sheet = ReceiptsSheet(filename)
    click.echo("Looking for duplicate receipts...")
    receipts_sheet.find_duplicates()
