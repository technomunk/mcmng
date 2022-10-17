"""Save backups"""


import re
from datetime import datetime
from functools import partial
from os import listdir, path, remove
from typing import Collection, Iterable
from zipfile import ZIP_DEFLATED, ZipFile

BACKUP_NAME_PATTERN = (
    r"[1-9][0-9]{3}-"  # year
    r"(0[1-9]|1[0-2])-"  # month
    r"([0-2][0-9]|3[01]) "  # day
    r"[0-5][0-9]:"  # hour
    r"[0-5][0-9]:"  # minute
    ".zip"
)


def backup(filepath: str, worlds: Collection[str], backup_dir: str) -> str:
    """
    Backup the worlds of the server at the provided path.
    Returns the newly created backup filename.
    """

    backup_name = datetime.now().isoformat(timespec="minutes") + ".zip"
    backup_path = path.join(backup_dir, backup_name)
    with ZipFile(backup_path, "x", compression=ZIP_DEFLATED) as zip_file:
        for filename in filter(lambda name: name in worlds, listdir(filepath)):
            zip_file.write(path.join(filepath, filename))

    return backup_path


def delete_oldest_backups(backup_dir: str, keep: int = 1) -> list[str]:
    """
    Remove oldest backups until "keep" backups remain in provided directory.
    """

    backups: Iterable[str] = filter(partial(_is_backup, backup_dir), listdir(backup_dir))
    backups = sorted(backups, key=partial(_backup_age, backup_dir))

    for filename in backups[:-keep]:
        remove(path.join(backup_dir, filename))

    return backups[:-keep]


def newest_backup_time(backup_dir: str) -> datetime | None:
    """Get the newest backup age in provided folder"""
    backups = filter(partial(_is_backup, backup_dir), listdir(backup_dir))
    if not backups:
        return None
    age = min(path.getmtime(path.join(backup_dir, filename)) for filename in backups)
    return datetime.fromtimestamp(age)


def _is_backup(backup_dir: str, filename: str) -> bool:
    return all(
        [
            re.fullmatch(BACKUP_NAME_PATTERN, filename),
            path.isfile(path.join(backup_dir, filename)),
        ]
    )


def _backup_age(backup_dir: str, filename: str) -> float:
    return path.getmtime(path.join(backup_dir, filename))
