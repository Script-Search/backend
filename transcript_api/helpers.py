"""
This script holds helper functions for our cloud function.
These functions are meant to be imported into other files.

Functions:
- debug(message: str) -> None: Print a debug message.

Global Variables:
- LOGGER_CONSOLE: Logger instance for console logging.

Dependencies:
- logging: Provides logging functionality.
- settings.DEBUG_FLAG: Flag indicating whether debug messages should be printed.

Note:
Ensure that the settings module is properly configured before using this module.
"""

# Standard Library Imports
from logging import DEBUG, getLogger, StreamHandler, Formatter

# File System Imports
from settings import DEBUG_FLAG

LOGGER_CONSOLE = None

def distribute(items: list, n: int) -> list[list]:
    """Distribute items into n groups.

    Args:
        items (list): The items to distribute.
        n (int): The number of groups to distribute the items into.

    Returns:
        list[list]: A list of lists containing the distributed items.
    """
    sublist_length = len(items) // n
    remainder = len(items) % n

    sublists: list[list] = [[] for _ in range(n)]
    start = 0

    for i in range(n):
        sublist_size = (sublist_length + 1) if i < remainder else sublist_length
        sublists[i] = items[start:start+sublist_size]
        start += sublist_size

    return sublists

def debug(message: str) -> None:
    """Print a debug message.

    Args:
        message (str): The message to print.
    """

    global LOGGER_CONSOLE # pylint: disable=global-statement
    if not LOGGER_CONSOLE:
        LOGGER_CONSOLE = getLogger("scriptsearch")
        LOGGER_CONSOLE.setLevel(DEBUG)
        handler = StreamHandler()
        handler.setFormatter(Formatter("%(asctime)s %(message)s"))
        LOGGER_CONSOLE.addHandler(handler)

    if DEBUG_FLAG:
        LOGGER_CONSOLE.log(DEBUG, message)
