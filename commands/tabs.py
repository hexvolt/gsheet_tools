import click
import gspread

from utils.auth import get_credentials
from utils.constants import RESULT_SKIPPED, RESULT_OK, RESULT_ERROR, RESULT_WARNING
from utils.names import get_normalized_title


def _rename(spreadsheet, one_by_one, dry=False):
    names_registry = set()
    for worksheet in spreadsheet.worksheets():
        title_before = worksheet.title
        try:
            normalized_title = get_normalized_title(
                tab_title=title_before,
                filename=spreadsheet.title,
                names_registry=names_registry
            )
        except ValueError as e:
            conversion_error = RESULT_WARNING.format(e) if dry else RESULT_SKIPPED
            normalized_title = None
        else:
            conversion_error = None

        names_registry.add(normalized_title or title_before)

        click.echo(f"{title_before} ==> " + f"{normalized_title or conversion_error}")
        if dry or conversion_error:
            continue

        if not one_by_one or one_by_one and click.confirm(f"Rename?", default=True):
            result_msg = RESULT_SKIPPED if conversion_error else RESULT_OK
            try:
                worksheet.update_title(normalized_title)
            except Exception as e:
                result_msg = RESULT_ERROR.format(e)
            click.echo(result_msg)


@click.command()
@click.argument('filename')
@click.option('--one-by-one', is_flag=True)
def normalize(filename, one_by_one):
    """
    Normalize the titles of all tabs in the spreadsheet.

    Copy of 2018/08/01 PM ==> 01
    Copy of 2018/08/01 ==> 01a (if tab "01" already exists)

    If the title of the tab does not correspond to the filename,
    then the warning shows up and full date remains in the title.
    """
    click.echo(f"Analyzing tabs in {filename}...")

    credentials = get_credentials()
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open(filename)

    _rename(spreadsheet=spreadsheet, one_by_one=one_by_one, dry=True)

    if not one_by_one and not click.confirm("Rename all tabs (tabs without proper date will be skipped)?"):
        return None

    _rename(spreadsheet=spreadsheet, one_by_one=one_by_one)
