"""
This script holds the settings used in this directory.
It keeps descriptive variable names to avoid verbose documentation.

Config Settings:
- DEBUG_FLAG: Flag indicating whether debug mode is enabled.

YT-DLP Settings:
- MAX_VIDEO_LIMIT: Maximum number of videos to retrieve.
- VALID_VIDEO_REGEX: Regular expression pattern for valid video URLs.
- VALID_PLAYLIST_REGEX: Regular expression pattern for valid playlist URLs.
- VALID_CHANNEL_REGEX: Regular expression pattern for valid channel URLs.
- YDL_OPS: Options for YT-DLP client.

TYPESENSE Settings:
- MAX_QUERY_WORD_LIMIT: Maximum number of words allowed in a query.
- TYPESENSE_API_KEY: API key for accessing Typesense (from environment variable).
- TYPESENSE_HOST: Hostname of the Typesense server (from environment variable).
- TYPESENSE_SEARCH_PARAMS: Parameters for Typesense search.

API Settings:
- API_RESPONSE_HEADERS: Headers for API responses.

Dependencies:
- os.environ: Environment variables.
- typing: Type hints support.

Note:
Ensure that the environment variables are properly configured before using this module.
"""
from __future__ import annotations

from os import environ
from typing import Literal

# Config Settings
DEBUG_FLAG: Literal[True] = True

# YT-DLP Settings
MAX_VIDEO_LIMIT: int = 250
VALID_VIDEO_REGEX: str      = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)(?![playlist|channel])([\w\-]+)(\S+)?$"
VALID_PLAYLIST_REGEX: str   = r"^((?:https?:)?\/\/)?((?:www|m)\.)?(youtube\.com)\/(.*)[\&|\?](list=[\w\-]+)(\&index=[0-9]*)?(\&si=[\w\-]+)?$"
VALID_CHANNEL_REGEX: str    = r"^((?:https?:)?\/\/)?((?:www|m)\.)?(youtube\.com)\/(((c\/)?[\w\-\.]+)|(\@[\w\-\.]{3,30})|(channel\/[\w\-]+))(\?si=[\w\-]+)?(\/videos|\/featured)?$"
YDL_OPS: dict[str, bool|str|dict[str, dict[str, list[str]]]] = {
    "quiet": True,
    "extract_flat": True,
    "playlist_items": f"1-{MAX_VIDEO_LIMIT}",
    "extractor_args": {
        "youtube": {
            "player_skip": ["webpage"],
            "player_client": ["web", "android"]
        }
    },
    "source_address": "0.0.0.0", # we're getting ip blocked
}

# TYPESENSE Settings
MAX_QUERY_WORD_LIMIT: int = 5
TYPESENSE_API_KEY: str|None = environ.get("TYPESENSE_API_KEY")
TYPESENSE_HOST: str|None    = environ.get("TYPESENSE_HOST")
TYPESENSE_SEARCH_PARAMS = {
    "drop_tokens_threshold": 0,
    "typo_tokens_threshold": 0,
    "page": 1,
    "per_page": 250,
    "prefix": False,
    "q": "",
    "query_by": "transcript",
    "sort_by": "upload_date:desc",
    "filter_by": "",
    "limit": 250,
    "highlight_start_tag": "",
    "highlight_end_tag": "",
}

# API Settings
API_RESPONSE_HEADERS: dict[str, str] = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PATCH,UPDATE,FETCH,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Origin, X-Requested-With, Content-Type, Accept, Authorization",
}

