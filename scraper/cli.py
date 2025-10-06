"""
Command line interface for the PySmash scraper.
"""

import logging
import sys
from typing import Optional

import click

from .database.repository import SmashUpRepository
from .scrapers.card_scraper import CardScraper
from .scrapers.faction_scraper import FactionScraper
from .scrapers.set_scraper import SetScraper
from .utils.web_client import SmashUpWebClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--database-url", default="sqlite:///smashup.db", help="Database URL")
@click.pass_context
def cli(ctx, verbose, database_url):
    """PySmash Scraper - Extract Smash Up! data from the wiki."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Store context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["database_url"] = database_url
    ctx.obj["verbose"] = verbose


@cli.command()
@click.pass_context
def scrape_all(ctx):
    """Scrape all available data (sets, factions, cards, bases)."""
    click.echo("🎯 Starting complete data scraping...")

    database_url = ctx.obj["database_url"]
    repository = SmashUpRepository(database_url)

    success_count = 0
    error_count = 0

    with SmashUpWebClient() as web_client:
        # Scrape sets and factions
        set_scraper = SetScraper(web_client)
        faction_scraper = FactionScraper(web_client)

        sets = set_scraper.get_available_sets()
        click.echo(f"📦 Found {len(sets)} sets to process")

        for set_name in sets:
            try:
                click.echo(f"Processing set: {set_name}")

                # Scrape set data
                set_data = set_scraper.scrape_set_data(set_name)
                if repository.insert_set(set_data):
                    success_count += 1
                    click.echo(f"  ✅ Set inserted: {set_name}")
                else:
                    error_count += 1
                    click.echo(f"  ❌ Failed to insert set: {set_name}")
                    continue

                # Scrape factions for this set
                factions = set_scraper.scrape_set_factions(set_name)
                click.echo(f"  🏛️ Found {len(factions)} factions")

                for faction_name in factions:
                    if not faction_name.strip():
                        continue

                    try:
                        faction_data = faction_scraper.scrape_faction_data(
                            faction_name, set_data.set_id
                        )

                        if repository.insert_faction(faction_data):
                            click.echo(f"    ✅ Faction inserted: {faction_name}")

                            # Scrape cards for this faction
                            card_result = faction_scraper.scrape_faction_cards(
                                faction_name, faction_data.faction_id
                            )

                            if card_result:
                                click.echo(f"    🃏 Processed cards for {faction_name}")

                        else:
                            click.echo(
                                f"    ❌ Failed to insert faction: {faction_name}"
                            )
                            error_count += 1

                    except Exception as e:
                        click.echo(
                            f"    ❌ Error processing faction {faction_name}: {e}"
                        )
                        error_count += 1

            except Exception as e:
                click.echo(f"❌ Error processing set {set_name}: {e}")
                error_count += 1

    click.echo(f"\n🎯 Scraping complete!")
    click.echo(f"✅ Successes: {success_count}")
    click.echo(f"❌ Errors: {error_count}")


@cli.command()
@click.argument("faction_name")
@click.option("--set-name", help="Name of the set this faction belongs to")
@click.pass_context
def scrape_faction(ctx, faction_name, set_name):
    """Scrape a specific faction and its cards."""
    click.echo(f"🏛️ Scraping faction: {faction_name}")

    database_url = ctx.obj["database_url"]
    repository = SmashUpRepository(database_url)

    with SmashUpWebClient() as web_client:
        faction_scraper = FactionScraper(web_client)

        # Generate or get set_id
        set_id = None
        if set_name:
            set_scraper = SetScraper(web_client)
            set_data = set_scraper.scrape_set_data(set_name)
            set_id = set_data.set_id
            repository.insert_set(set_data)

        result = faction_scraper.scrape(faction_name, set_id)

        if result.success:
            click.echo(f"✅ {result.message}")
        else:
            click.echo(f"❌ {result.message}")
            for error in result.errors:
                click.echo(f"   • {error}")


@cli.command()
@click.argument("set_name")
@click.pass_context
def scrape_set(ctx, set_name):
    """Scrape a specific set and its factions."""
    click.echo(f"📦 Scraping set: {set_name}")

    database_url = ctx.obj["database_url"]
    repository = SmashUpRepository(database_url)

    with SmashUpWebClient() as web_client:
        set_scraper = SetScraper(web_client)
        result = set_scraper.scrape(set_name)

        if result.success:
            click.echo(f"✅ {result.message}")
        else:
            click.echo(f"❌ {result.message}")
            for error in result.errors:
                click.echo(f"   • {error}")


@cli.command()
@click.pass_context
def list_sets(ctx):
    """List all sets in the database."""
    database_url = ctx.obj["database_url"]
    repository = SmashUpRepository(database_url)

    sets = repository.get_all_sets()

    if sets:
        click.echo("📦 Sets in database:")
        for set_data in sets:
            click.echo(f"  • {set_data['set_name']} (ID: {set_data['set_id']})")
    else:
        click.echo("No sets found in database. Run 'scrape-all' first.")


@cli.command()
@click.argument("set_id")
@click.pass_context
def list_factions(ctx, set_id):
    """List all factions for a specific set."""
    database_url = ctx.obj["database_url"]
    repository = SmashUpRepository(database_url)

    factions = repository.get_factions_by_set(set_id)

    if factions:
        click.echo(f"🏛️ Factions in set {set_id}:")
        for faction in factions:
            click.echo(f"  • {faction['faction_name']} (ID: {faction['faction_id']})")
    else:
        click.echo(f"No factions found for set {set_id}")


@cli.command()
@click.confirmation_option(prompt="Are you sure you want to clear all data?")
@click.pass_context
def clear_database(ctx):
    """Clear all data from the database."""
    database_url = ctx.obj["database_url"]
    repository = SmashUpRepository(database_url)

    if repository.clear_all_data():
        click.echo("✅ Database cleared successfully")
    else:
        click.echo("❌ Failed to clear database")


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n🛑 Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
