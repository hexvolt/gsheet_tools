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
    Import all receipts from the Receipt book into Billing book.

    Since Receipt book contains all receipts from one month, this
    command basically populates month tab in the billing.
    """
    receipt_book = ReceiptBook(source_filename)
    month = parse(source_filename).month

    billing_book = BillingBook(billing_filename)
    month_billing = billing_book.get_month_billing(month=month)

    if not click.confirm("Continue?"):
        return

    for receipt in receipt_book.receipts:
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
    month_billing = billing_book.get_month_billing(month=month)
    if click.confirm(
        f"This will delete all expenses from `{billing_filename}` month number {month}. Continue?",
        default=False,
    ):
        month_billing.clear_expenses()
