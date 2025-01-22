import click
from app.database.management import truncate_tables, reset_database, get_table_counts, init_db


@click.group()
def cli():
    """Database management commands"""
    pass


@cli.command()
def init():
    """Initialize the database"""
    if click.confirm("Are you sure you want to initialize the database?"):
        if init_db():
            click.echo("Successfully initialized the database")
        else:
            click.echo("Failed to initialize database")


@cli.command()
def truncate():
    """Truncate all tables in the database"""
    if click.confirm(
        "Are you sure you want to truncate all tables? This cannot be undone."
    ):
        if truncate_tables():
            click.echo("Successfully truncated all tables")
        else:
            click.echo("Failed to truncate tables")


@cli.command()
def reset():
    """Reset the entire database (drop and recreate all tables)"""
    if click.confirm(
        "Are you sure you want to reset the database? This cannot be undone."
    ):
        if reset_database():
            click.echo("Successfully reset the database")
        else:
            click.echo("Failed to reset database")


@cli.command()
def status():
    """Show current record counts in all tables"""
    counts = get_table_counts()
    if counts:
        click.echo("\nCurrent table record counts:")
        for table, count in counts.items():
            click.echo(f"{table}: {count}")
    else:
        click.echo("Failed to get table counts")


if __name__ == "__main__":
    cli()
