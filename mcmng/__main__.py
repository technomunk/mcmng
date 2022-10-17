"""
Command line based [minecraft](https://www.minecraft.net/en-us)
server manager for individual admins.
"""
from datetime import datetime, timedelta
from os import makedirs
from time import sleep

import click
from mcstatus import JavaServer

from mcmng.backup import backup, delete_oldest_backups, newest_backup_time


@click.group()
def cli() -> None:
    """Manage Minecraft server(s)"""


@cli.command()
@click.argument("filepath", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.argument("address", type=str)
@click.option(
    "--backup-dir",
    "-d",
    type=click.Path(exists=False, dir_okay=True, file_okay=False),
    default="backups",
)
@click.option(
    "--world",
    "-w",
    type=str,
    multiple=True,
    default=["world", "world_nether", "world_the_end"],
    show_default=True,
    help="The world folders to backup",
)
@click.option(
    "--poll-rate",
    type=float,
    default=300,
    show_default=True,
    help="The period at which to check player presence in seconds",
)
@click.option(
    "--period",
    type=float,
    default=60,
    show_default=True,
    help="Amount of time between active backups in minutes",
)
@click.option(
    "--max-backups",
    type=int,
    default=0,
    help="Max number of backups to keep. 0 means keep any number",
)
def continuous_backup(
    filepath: str,
    address: str,
    *,
    backup_dir: str,
    world: tuple[str, ...],
    poll_rate: float,
    period: float,
    max_backups: int,
) -> None:
    """Create world backups for a provided server every so often."""
    address, port = _parse_address(address)  # pylint: disable=unpacking-non-sequence
    server = JavaServer(address, port)

    makedirs(backup_dir, exist_ok=True)
    activity_since_last_backup = False

    last_backup_time = newest_backup_time(backup_dir) or datetime.today()

    while True:
        if not activity_since_last_backup:
            activity_since_last_backup = server.status().players.online > 0

        if activity_since_last_backup:
            now = datetime.now()
            backup_time = last_backup_time + timedelta(minutes=period)
            if backup_time > now:
                backup(filepath, world, backup_dir)
                last_backup_time = now
                activity_since_last_backup = False
                if max_backups > 0:
                    delete_oldest_backups(backup_dir, keep=max_backups)
            else:
                sleep((backup_time - now).total_seconds())
                continue

        sleep(poll_rate)


def _parse_address(address: str) -> tuple[str, int | None]:
    """Parse provided address string with :port segment and return the address and port"""
    parts = address.split(":")
    match len(parts):
        case 1:
            return address, None
        case 2:
            return parts[0], int(parts[1])
        case _:
            raise ValueError("supplied address does not look like a valid network address")


if __name__ == "__main__":
    cli()
