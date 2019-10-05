import gspread

from utils.auth import get_credentials


def main():
    credentials = get_credentials()
    gc = gspread.authorize(credentials)
    spreadsheet = gc.open('2018-02')
    print(spreadsheet.title)


if __name__ == '__main__':
    main()
