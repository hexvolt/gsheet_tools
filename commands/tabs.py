import click

from models.receipt_book import ReceiptBook
from models.workbook import Workbook


@click.command()
@click.argument("filename")
@click.option("--one-by-one", is_flag=True)
@click.option("--reorder/--no-reorder", default=False)
@click.option("--validate/--no-validate", default=False)
@click.option("--find-duplicates/--no-find-duplicates", default=False)
def normalize(filename, one_by_one, reorder, validate, find_duplicates):
    """
    Normalize all tabs in the receipt book.

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
    receipt_book = ReceiptBook(filename)

    receipt_book.rename_tabs(one_by_one=one_by_one, dry=True)

    if click.confirm("Rename all tabs (tabs without proper date will be skipped)?"):
        receipt_book.rename_tabs(one_by_one=one_by_one)

    if reorder:
        click.echo("Sorting all tabs alphabetically...")
        receipt_book.reorder()

    if validate:
        click.echo("Validating prices in all tabs...")
        receipt_book.validate()

    if find_duplicates:
        click.echo("Looking for duplicate receipts...")
        receipt_book.find_duplicates()


@click.command()
@click.argument("filename")
def reorder(filename):
    """Reorder all tabs in the receipt book alphabetically."""
    receipt_book = ReceiptBook(filename)
    click.echo("Sorting all tabs alphabetically...")
    receipt_book.reorder()


@click.command()
@click.argument("filename")
def validate(filename):
    """
    Validate prices in all tabs.

    If numbers don't add up there - show the warning.
    """
    receipt_book = ReceiptBook(filename)
    click.echo("Validating prices in all tabs...")
    receipt_book.validate()


@click.command()
@click.argument("filename")
def find_duplicates(filename):
    """Analyze receipt book for duplicate tabs."""
    receipt_book = ReceiptBook(filename)
    if not click.confirm(
        "This may take a while, make sure that the titles of all tabs are normalized. Continue?",
        default=True,
    ):
        return
    click.echo("Looking for duplicate receipts...")
    receipt_book.find_duplicates()


@click.command()
@click.argument("filename")
@click.option("--one-by-one", is_flag=True)
@click.option("--unambiguous-only", is_flag=True)
def move_from_workbook(filename, one_by_one, unambiguous_only):
    """
    Move receipt tabs from workbook to appropriate monthly spreadsheets.

    The destination for each tab is determined by its title:
        "22.11.2017" will go to the spreadsheet with the name "2017-11"

    When --unambiguous-all option is specified, only unambiguous tabs
    will be processed.
    """
    workbook = Workbook(filename)
    click.echo("Reading tabs, preparing preview...")
    workbook.move_tabs(
        one_by_one=one_by_one, dry=True, unambiguous_only=unambiguous_only
    )

    if click.confirm("Continue?"):
        click.echo("Moving tabs to appropriate monthly spreadsheets...")
        workbook.move_tabs(one_by_one=one_by_one, unambiguous_only=unambiguous_only)
