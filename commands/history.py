import click

from models.receipt_book import ReceiptBook
from models.transaction import TransactionHistory
from utils.constants import RESULT_OK


@click.command()
@click.argument("source_filenames", nargs=-1)
@click.argument("transactions_filename")
def mark_transactions(source_filenames, transactions_filename):
    """
    Read the receipts from source_filenames and mark an appropriate
    transaction in transactions_filename with a check-mark that it
    has a corresponding receipt.

    :param source_filenames: names of month Receipt book files (2017-11 ...)
    :param transactions_filename: a name of the file with transactions
    """
    click.echo(f"Reading the transactions history from '{transactions_filename}'")
    history = TransactionHistory(filename=transactions_filename)
    if history.transactions:
        click.echo(RESULT_OK)

    for source_filename in source_filenames:
        click.echo(f"Processing '{source_filename}'")
        receipt_book = ReceiptBook(filename=source_filename)

        for receipt in receipt_book.receipts:
            click.echo(f"{receipt.worksheet.title} ==> ", nl=False)
            transaction = history.find_transaction(
                created=receipt.date,
                price=receipt.actually_paid or receipt.total or receipt.subtotal,
                has_receipt=False,
            )
            if transaction:
                click.echo(RESULT_OK + "Found.")
                transaction.has_receipt = True
            else:
                click.echo("Not found.")

        click.echo("Updating the history spreadsheet...")
        history.post_to_spreadsheet()
        click.echo(RESULT_OK)
