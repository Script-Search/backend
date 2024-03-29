"""
This script holds helper functions for our cloud function.
These functions are meant to be imported into other files.
"""

from logging import DEBUG, getLogger, StreamHandler, Formatter

from settings import DEBUG_FLAG

LOGGER_CONSOLE = None

def debug(message: str) -> None:
    """Print a debug message.

    Args:
        message (str): The message to print.

    Returns:
        None
    """

    global LOGGER_CONSOLE # pylint: disable=W0603
    if not LOGGER_CONSOLE:
        LOGGER_CONSOLE = getLogger("scriptsearch")
        LOGGER_CONSOLE.setLevel(DEBUG)
        handler = StreamHandler()
        handler.setFormatter(Formatter("%(asctime)s %(message)s"))
        LOGGER_CONSOLE.addHandler(handler)

    if DEBUG_FLAG:
        LOGGER_CONSOLE.log(DEBUG, message)