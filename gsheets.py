import click

from commands import tabs, files


@click.group()
def cli():
    pass


cli.add_command(tabs.normalize)
cli.add_command(files.ls)


if __name__ == "__main__":
    cli()
