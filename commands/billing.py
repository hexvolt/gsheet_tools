import click
from dateutil.parser import parse

from models.billing_book import BillingBook
from models.receipt_book import ReceiptBook
from models.transaction import TransactionHistory
from utils.constants import RESULT_ERROR, RESULT_OK, RESULT_WARNING, CellType


@click.command()
@click.argument("source_filename")
@click.argument("billing_filename")
@click.argument("note_threshold", default=50)
@click.option("--one-by-one", is_flag=True)
def receipts_to_billing(source_filename, billing_filename, note_threshold, one_by_one):
    """
    Import receipts from the Receipt book into Billing book.

    Since Receipt book contains all receipts from one month, this
    command basically populates month tab in the billing.

    if source_filename contains a specific receipt names, e.g. `2017-11:10:21d`
    then only 2 receipts 10 and 21d from 2017-11 will be imported.
    """
    receipt_book_name, *receipt_titles = source_filename.split(":")

    receipt_book = ReceiptBook(receipt_book_name)
    month = parse(receipt_book_name).month

    billing_book = BillingBook(billing_filename)
    month_billing = billing_book.get_month_billing(month=month)

    if not click.confirm("Continue?", default=True):
        return

    if receipt_titles:
        receipts_to_import = [
            receipt_book.get_receipt(title) for title in receipt_titles
        ]
    else:
        receipts_to_import = receipt_book.receipts

    for receipt in receipts_to_import:
        click.echo(f"Importing {receipt.worksheet.title}...")

        if not one_by_one or one_by_one and click.confirm(f"Continue?", default=True):
            result_msg = RESULT_OK
            try:
                month_billing.import_receipt(receipt, note_threshold=note_threshold)
            except Exception as e:
                result_msg = RESULT_ERROR.format(e)
            click.echo(result_msg)


@click.command()
@click.argument("source_filename")
@click.argument("billing_filename")
@click.argument("note_threshold", default=50)
@click.option("--one-by-one", is_flag=True)
def transactions_to_billing(
    transactions_filename, billing_filename, note_threshold, one_by_one
):
    """
    Import from the Transaction history into Billing book.

    This command takes year from the billing filename and imports only those transactions
    which correspond to that year.
    """
    click.echo(f"Reading the transactions history from '{transactions_filename}'")
    history = TransactionHistory(filename=transactions_filename)
    if history.transactions:
        click.echo(RESULT_OK)

    click.echo(f"Reading the destination billing file '{billing_filename}'")
    billing_book = BillingBook(billing_filename)
    if billing_book.month_billings:
        click.echo(RESULT_OK)

    try:
        for transaction in history.transactions:
            if transaction.has_receipt or transaction.created.year != billing_book.year:
                continue

            click.echo(f"Importing {transaction}...")

            if not one_by_one or one_by_one and click.confirm(f"Continue?", default=True):
                result_msg = RESULT_OK
                month_billing = billing_book.get_month_billing(
                    month=transaction.created.month
                )

                if len(transaction.matching_types) > 1:
                    choices = "\n".join(
                        f"{i} - {cell_type.name}"
                        for i, cell_type in enumerate(transaction.matching_types)
                    )
                    msg = f"Transaction {transaction} can be one of: {choices}"
                    selected_index = click.prompt(text=msg, show_choices=True)
                    preferred_type = choices[selected_index]

                elif len(transaction.matching_types) < 1:
                    available_types = {i: cell_type for i, cell_type in enumerate(CellType)}
                    choices = "\n".join(
                        f"{i} - {cell_type.name}"
                        for i, cell_type in available_types.items()
                    )
                    msg = f"Can't determine good type for {transaction}. Choose one of: {choices}"
                    selected_index = click.prompt(text=msg, show_choices=True)
                    preferred_type = available_types[selected_index]

                else:
                    preferred_type = transaction.good_type

                try:
                    month_billing.import_transaction(
                        transaction,
                        note_threshold=note_threshold,
                        preferred_type=preferred_type,
                    )
                except ValueError as e:
                    result_msg = RESULT_WARNING.format(e)

                except Exception as e:
                    result_msg = RESULT_ERROR.format(e)

                click.echo(result_msg)
                transaction.has_receipt = True
    finally:
        click.echo("Updating the history spreadsheet...")
        history.post_to_spreadsheet()
        click.echo(RESULT_OK)


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
