"""Functions for finding various information about files."""
import pandas

from datetime import datetime
from os import path


def is_file_stale(file_path: str, stale_by_date: datetime.date) -> bool:
    """A file is considered 'stale' if it was created on or before a given date"""
    if path.exists(file_path):
        if datetime.fromtimestamp(path.getctime(file_path)).date() > stale_by_date:
            return False

    return True


def csv_row_count_check(file_path: str, row_count: int) -> bool:
    """
    Return true if the file exists and its number of rows equals row_count

    Parameters:
        file_path (str): The fully qualified path to the csv file.
        row_count (int): The expected number of rows to find in the file.

    Returns:
        bool: True if the file exists and its number of rows equals row_count. Otherwise False.
    """
    if path.exists(file_path):
        df = pandas.read_csv(file_path)
        return len(df) == row_count

    return False


def add_date_to_file_name(file_name: str, date: datetime.date, fmt: str = "%Y%m%d") -> str:
    """
    Takes a file name and inserts a formatted date string in front of the file extension.

    Parameters:
        file_name (str): The file name.
        date (datetime.date): The date to format and add to the file name.
        fmt (str): Optional. The string format to apply to the date.
    Returns:
        str: The revised file name.
    """
    split = file_name.rsplit(".", 1)
    split.insert(1, date.strftime(fmt))
    return ".".join(split)
