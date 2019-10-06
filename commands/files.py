import click
import gspread

from utils.auth import get_credentials


@click.command()
def ls():
    """List all available spreadsheets."""
    credentials = get_credentials()
    gc = gspread.authorize(credentials)
    for sheet_data in gc.list_spreadsheet_files():
        click.echo(sheet_data["name"])
