import click
from gspread import SpreadsheetNotFound

from models.receipt_book import ReceiptBook
from models.workbook import Workbook
from utils.constants import RESULT_WARNING, RESULT_ERROR, RESULT_OK


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
@click.argument("filenames", nargs=-1)
def validate(filenames):
    """
    Validate prices in all tabs of specified files.

    If numbers don't add up there - shows the warning.
    Shows the summary with issues across all files at the end.
    """
    suspicious_receipts = []
    total = 0
    for filename in filenames:
        try:
            receipt_book = ReceiptBook(filename)
        except SpreadsheetNotFound:
            click.echo(
                RESULT_ERROR.format(
                    f"'{filename}' not found. Check the name or permissions."
                )
            )
            continue

        click.echo(f"Validating prices in '{filename}'...")
        suspicious_receipts.extend(
            receipt
            for receipt in receipt_book.receipts
            if not receipt.prices_are_valid(raise_exception=False) or receipt.discount
        )
        total += len(receipt_book.receipts)

    click.echo(
        "\n"
        + RESULT_OK
        + f"{total} receipts analyzed. {len(suspicious_receipts)} suspicious found:\n"
    )

    for receipt in suspicious_receipts:
        click.echo(
            f"{receipt.worksheet.spreadsheet.title} : {receipt.worksheet.title} ==> ",
            nl=False,
        )
        try:
            receipt.prices_are_valid(raise_exception=True)
            if receipt.discount:
                click.echo(
                    RESULT_OK + f"Receipt has a discount/loyalty of {receipt.discount}."
                )
        except ValueError as e:
            click.echo(RESULT_WARNING.format(e))
        except Exception as e:
            click.echo(RESULT_ERROR.format(e))


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
    click.echo("Gathering data...")
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
