import click
from dateutil.parser import parse

from models.billing_book import BillingBook
from models.receipt_book import ReceiptBook
from utils.constants import RESULT_ERROR, RESULT_OK


@click.command()
@click.argument("source_filename")
@click.argument("billing_filename")
@click.argument("note_threshold", default=50)
@click.option("--one-by-one", is_flag=True)
def import_to_billing(source_filename, billing_filename, note_threshold, one_by_one):
    """
    Import receipts from the Receipt book into Billing book.

    Since Receipt book contains all receipts from one month, this
    command basically populates month tab in the billing.

    if source_filename contains a specific receipt names, e.g. `2017-11:10:21d`
    then only 2 receipts 10 and 21d from 2017-11 will be imported.
    """
    receipt_book_name, *receipt_titles = source_filename.split(':')

    receipt_book = ReceiptBook(receipt_book_name)
    month = parse(receipt_book_name).month

    billing_book = BillingBook(billing_filename)
    month_billing = billing_book.get_month_billing(month=month)

    if not click.confirm("Continue?"):
        return

    if receipt_titles:
        receipts_to_import = [receipt_book.get_receipt(title) for title in receipt_titles]
    else:
        receipts_to_import = receipt_book.receipts

    for receipt in receipts_to_import:
        click.echo(f"Importing {receipt.worksheet.title}...")

        if not one_by_one or one_by_one and click.confirm(f"Rename?", default=True):
            result_msg = RESULT_OK
            try:
                month_billing.import_receipt(receipt, note_threshold=note_threshold)
            except Exception as e:
                result_msg = RESULT_ERROR.format(e)
            click.echo(result_msg)


@click.command()
@click.argument("billing_filename")
@click.argument("month")
def clear_expenses(billing_filename, month):
    """Clear all expenses in the month billing spreadsheet."""
    billing_book = BillingBook(billing_filename)
    month_billing = billing_book.get_month_billing(month=int(month))
    if click.confirm(
        f"This will delete all expenses from `{billing_filename}` month number {month}. Continue?",
        default=False,
    ):
        month_billing.clear_expenses()
