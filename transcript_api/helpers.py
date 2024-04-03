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
