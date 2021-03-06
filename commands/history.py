import click

from models.receipt_book import ReceiptBook
from models.transaction import TransactionHistory
from utils.constants import RESULT_OK


@click.command()
@click.argument("source_filenames", nargs=-1)
@click.argument("transactions_filename")
@click.option("--overwrite", is_flag=True)
def mark_transactions(source_filenames, transactions_filename, overwrite):
    """
    Read the receipts from source_filenames and mark an appropriate
    transaction in transactions_filename with a check-mark that it
    has a corresponding receipt.

    :param source_filenames: names of month Receipt book files (2017-11 ...)
    :param transactions_filename: a name of the file with transactions
    """
    not_found_receipts = []

    click.echo(f"Reading the transactions history from '{transactions_filename}'")
    history = TransactionHistory(filename=transactions_filename)
    if history.transactions:
        click.echo(RESULT_OK)

    for source_filename in source_filenames:
        click.echo(f"Processing '{source_filename}'")
        receipt_book = ReceiptBook(filename=source_filename)

        try:
            for receipt in receipt_book.receipts:
                click.echo(f"{receipt.worksheet.title} ==> ", nl=False)
                transactions = history.find_transactions(
                    created=receipt.date,
                    price=receipt.actually_paid or receipt.total or receipt.subtotal,
                    has_receipt=None if overwrite else False,
                )
                if transactions:
                    click.echo(RESULT_OK + "Found.")
                    transactions[0].has_receipt = True
                else:
                    click.echo("Not found.")
                    not_found_receipts.append(receipt)
        finally:
            click.echo("Updating the history spreadsheet...")
            history.post_to_spreadsheet()
            click.echo(RESULT_OK)

        click.echo("Receipts not found in transactions history:")
        for receipt in not_found_receipts:
            click.echo(
                f"{receipt.worksheet.spreadsheet.title}:{receipt.worksheet.title}"
            )


@click.command()
@click.argument("transactions_filename")
def reset_transactions(transactions_filename):
    """Reset the has_receipt flag of all transactions in spreadsheet."""
    history = TransactionHistory(filename=transactions_filename)
    if click.confirm(
        f"This will reset the has_receipt flag of all transactions in the file `{transactions_filename}`. Continue?",
        default=False,
    ):
        history.reset_flags()
        history.post_to_spreadsheet()
