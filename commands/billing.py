import click
from dateutil.parser import parse

from models.billing_book import BillingBook
from models.receipt_book import ReceiptBook
from utils.constants import RESULT_ERROR, RESULT_OK


@click.command()
@click.argument("source_filename")
@click.argument("billing_filename")
@click.option("--one-by-one", is_flag=True)
def import_to_billing(source_filename, billing_filename, one_by_one):
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
                month_billing.import_receipt(receipt)
            except Exception as e:
                result_msg = RESULT_ERROR.format(e)
            click.echo(result_msg)
