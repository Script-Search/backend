"""
Module for configuring various settings related to YouTube downloading, Typesense search, and API responses.

Future imports:
    - `annotations` from `__future__`

Imports:
    - `environ` from `os`

Constants:
    - `DEBUG_FLAG`: A literal indicating debugging status.
    - `MAX_VIDEO_LIMIT`: Maximum limit for video downloads.
    - `VALID_VIDEO_REGEX`: Regular expression pattern for validating video URLs.
    - `VALID_PLAYLIST_REGEX`: Regular expression pattern for validating playlist URLs.
    - `VALID_CHANNEL_REGEX`: Regular expression pattern for validating channel URLs.
    - `YDL_OPS`: Dictionary containing options for YT-DLP.
    - `MAX_QUERY_WORD_LIMIT`: Maximum limit for query words.
    - `TYPESENSE_API_KEY`: Typesense API key.
    - `TYPESENSE_HOST`: Typesense host URL.
    - `TYPESENSE_SEARCH_PARAMS`: Parameters for Typesense search.
    - `API_RESPONSE_HEADERS`: Headers for API responses.
"""
from __future__ import annotations

from os import environ

# Config Settings
DEBUG_FLAG = True

BANNED_CHARS: list[str] = ["!", "@", "#", "$", "%", "^", "&", "*",
                           "(", ")", "-", "_", "=", "+", "[", "]", "{", "}", "\\", "|", ":", ";", "<", ">", ",", ".", "?", "/", "\""]

# YT-DLP Settings
MAX_VIDEO_LIMIT: int = 250
VALID_VIDEO_REGEX: str = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)(?![playlist|channel])([\w\-]+)(\S+)?$"
VALID_PLAYLIST_REGEX: str = r"^((?:https?:)?\/\/)?((?:www|m)\.)?(youtube\.com)\/(.*)[\&|\?](list=[\w\-]+)(\&index=[0-9]*)?(\&si=[\w\-]+)?$"
VALID_CHANNEL_REGEX: str = r"^((?:https?:)?\/\/)?((?:www|m)\.)?(youtube\.com)\/(((c\/)?[\w\-\.]+)|(\@[\w\-\.]{3,30})|(channel\/[\w\-]+))(\?si=[\w\-]+)?(\/videos|\/featured)?$"
YDL_OPS: dict[str, bool | str | dict[str, dict[str, list[str]]]] = {
    "quiet": True,
    "extract_flat": True,
    "playlist_items": f"1-{MAX_VIDEO_LIMIT}",
    "extractor_args": {
        "youtube": {
            "player_skip": ["webpage"],
            "player_client": ["web"]
        }
    },
    "source_address": "0.0.0.0",  # we're getting ip blocked
}

# TYPESENSE Settings
MAX_QUERY_WORD_LIMIT: int = 5
TYPESENSE_API_KEY: str | None = environ.get("TYPESENSE_API_KEY")
TYPESENSE_HOST: str | None = environ.get("TYPESENSE_HOST")
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
    "enable_highlight_v1": False,
}
TYPESENSE_SEARCH_REQUESTS = {
    "searches": [
        {
            "collection": "transcripts",
            "q": "",
            "filter_by": "",
        },
        {
            "collection": "transcripts",
            "q": "",
            "filter_by": "",
        },
        {
            "collection": "transcripts",
            "q": "",
            "filter_by": "",
        },
        {
            "collection": "transcripts",
            "q": "",
            "filter_by": "",
        },
        {
            "collection": "transcripts",
            "q": "",
            "filter_by": "",
        },
    ]
}

# API Settings
API_RESPONSE_HEADERS: dict[str, str] = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PATCH,UPDATE,FETCH,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Origin, X-Requested-With, Content-Type, Accept, Authorization",
}
