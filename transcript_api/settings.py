"""
This script holds the settings used in this directory.
It keeps descriptive variable names to avoid verbose documentation.
"""

from os import environ

# Config Settings
DEBUG_FLAG = True

# YT-DLP Settings
MAX_VIDEO_LIMIT = 250
VALID_VIDEO_REGEX = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)(?![playlist|channel])([\w\-]+)(\S+)?$"
VALID_PLAYLIST_REGEX = r"^((?:https?:)?\/\/)?((?:www|m)\.)?(youtube\.com)\/(.*)[\&|\?](list=[\w\-]+)(\&index=[0-9]*)?(\&si=[\w\-]+)?$"
VALID_CHANNEL_REGEX = r"^((?:https?:)?\/\/)?((?:www|m)\.)?(youtube\.com)\/(((c\/)?[\w\-\.]+)|(\@[\w\-\.]{3,30})|(channel\/[\w\-]+))(\?si=[\w\-]+)?(\/videos|\/featured)?$"
YDL_OPS = {
    "quiet": True,
    "extract_flat": True,
    "playlist_items": f"1-{MAX_VIDEO_LIMIT}",
    "extractor_args": {'youtube': {'player_skip': ['webpage'], 'player_client': ['web', 'android']}},
    "source_address": "0.0.0.0", # we're getting ip blocked
}

# TYPESENSE Settings
MAX_QUERY_WORD_LIMIT = 5
TYPESENSE_API_KEY = environ.get("TYPESENSE_API_KEY")
TYPESENSE_HOST = environ.get("TYPESENSE_HOST")
TYPESENSE_SEARCH_PARAMS = {
    "drop_tokens_threshold": 0,
    "typo_tokens_threshold": 0,
    "page": 1,
    "per_page": 250,
    "prefix": False,
    "q": None,
    "query_by": "transcript",
    "sort_by": "upload_date:desc",
    "filter_by": "",
    "limit": 250,
    "highlight_start_tag": "",
    "highlight_end_tag": "",
}

# API Settings
API_RESPONSE_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PATCH,UPDATE,FETCH,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Origin, X-Requested-With, Content-Type, Accept, Authorization",
}

