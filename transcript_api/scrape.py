"""
This script handles the scraping using yt-dlp.
It extracts metadata information from given URLs to send to another function.

Functions:
- init_ydl_client(): Initializes the YT-DLP client if not already initialized.
- process_url(url: str) -> Dict[str, Any]: Processes a Universal Reference Link to determine if it's a channel, playlist, or video and returns metadata.
- get_url_type(url: str) -> URLType: Determines the type of the URL.
- get_channel_videos(channel_url: str) -> Tuple[str, List[str], List[str]]: Gets video URLs from a channel.
- get_playlist_videos(playlist_url: str) -> Tuple[List[str], List[str]]: Gets video URLs from a playlist.
- get_video(url: str) -> str: Gets the video ID from a URL.

Global Variables:
- YDL_CLIENT: Initialized YT-DLP client.
- PUBLISHER: PublisherClient instance for publishing messages.
- TOPIC_PATH: Path to the Pub/Sub topic.

Dependencies:
- re: Regular expression operations.
- json: JSON encoder and decoder.
- enum: Support for enumerations.
- typing: Type hints support.
- io.StringIO: Implements an in-memory file-like object.
- yt_dlp.YoutubeDL: Download videos from YouTube-like sites.
- google.cloud.pubsub_v1.PublisherClient: Publisher client for Google Cloud Pub/Sub.
- google.cloud.pubsub_v1.types.BatchSettings: Batch settings for publishing messages.
- google.oauth2.service_account: Service account credentials.
- settings.YDL_OPS: Options for YT-DLP client.
- settings.VALID_CHANNEL_REGEX: Regular expression pattern for valid channel URLs.
- settings.VALID_PLAYLIST_REGEX: Regular expression pattern for valid playlist URLs.
- settings.VALID_VIDEO_REGEX: Regular expression pattern for valid video URLs.
- helpers.debug: Debugging utility.

Note:
Ensure that the settings module is properly configured before using this module.
"""
from __future__ import annotations

# Standard Library Imports
import re
import json
from enum import Enum
from io import StringIO
from typing import List

# Third-Party Imports
from yt_dlp import YoutubeDL
from google.cloud.pubsub_v1 import PublisherClient
from google.cloud.pubsub_v1.types import BatchSettings
from google.oauth2 import service_account

# File System Imports
from settings import YDL_OPS, VALID_CHANNEL_REGEX, VALID_PLAYLIST_REGEX, VALID_VIDEO_REGEX
from helpers import debug

BATCH_SETTINGS = BatchSettings(
    max_messages    = 1,    # Publish after 1 message
    max_latency     = 0,    # Try to publish instantly
)

YDL_CLIENT: YoutubeDL = None
PUBLISHER: PublisherClient = None
TOPIC_PATH = None

class URLType(Enum):
    """Enum for URL types."""
    VIDEO = 1
    PLAYLIST = 2
    CHANNEL = 3

def init_ydl_client():
    """
    Initialize the YT-DLP Client if not already initialized; Uses lazy loading
    """
    global YDL_CLIENT # pylint: disable=global-statement
    if not YDL_CLIENT:
        YDL_CLIENT = YoutubeDL(YDL_OPS)

def process_url(url: str) -> dict[str, list[str]|str|None]:
    """
    Takes a Universal Reference Link, 
    determines if the url is a channel or a playlist, 
    and returns 250 most recent videos.

    Args:
        url (str): Universsal Reference Link
    """
    debug(f"Processing URL: {url}")

    init_ydl_client()
    url_type = get_url_type(url)

    data: dict[str, str] = {
        "video_ids": None,
        "channel_id": None,
    }

    video_ids = []
    if url_type == URLType.VIDEO:
        video_id = get_video(url)
        video_ids.append(video_id)
        ss = StringIO()
        ss.write(f"[{video_id}]")
        data["video_ids"] = ss.getvalue()
    elif url_type == URLType.PLAYLIST:
        video_ids = get_playlist_videos(url)

        # Prepare video_ids for filtering
        ss = StringIO()
        ss.write("[")
        for video_id in video_ids:
            ss.write(f'`{video_id}`,')
        ss.write("]")
        data["video_ids"] = ss.getvalue()
        data["video_ids"] = str(data["video_ids"]).replace(",]", "]")

    elif url_type == URLType.CHANNEL:
        data["channel_id"], video_ids = get_channel_videos(url)
    else:
        raise ValueError(f"Invalid URL: {url}")
    
    global PUBLISHER, TOPIC_PATH # pylint: disable=global-statement
    if PUBLISHER is None:
        cred = service_account.Credentials.from_service_account_file(
            "credentials_pub_sub.json")
        PUBLISHER = PublisherClient(credentials=cred, batch_settings=BATCH_SETTINGS)
        TOPIC_PATH = PUBLISHER.topic_path("ScriptSearch", "Test-Go-Url-Check")
    
    byteString = json.dumps(video_ids).encode("utf-8")
    PUBLISHER.publish(TOPIC_PATH, data=byteString) # We don't really need result from this I believe

    return data

def get_url_type(url: str) -> URLType:
    """Determines the URL type.

    Args:
        url (str): The URL.

    Returns:
        URLType: The type of video.
    """

    if re.search(VALID_VIDEO_REGEX, url):
        return URLType.VIDEO
    if re.search(VALID_PLAYLIST_REGEX, url):
        return URLType.PLAYLIST
    if re.search(VALID_CHANNEL_REGEX, url):
        return URLType.CHANNEL
    raise ValueError(f"Invalid URL: {url}")

def get_channel_videos(channel_url: str) -> tuple[str, list[str]]:
    """Get the video urls from a channel.

    Args:
        channel_url (str): The channel URL.

    Returns:
        List[str]: The video URLs.
    """

    channel = YDL_CLIENT.extract_info(channel_url, download=False)

    if not channel["entries"]:
        raise ValueError(f"Channel {channel_url} has no videos.")

    # video_urls = []
    video_ids = []
    if "entries" in channel["entries"][0]:
        for entry in channel["entries"][0]["entries"]:
            # video_urls.append(entry["url"])
            video_ids.append(entry["id"])
    else:
        for entry in channel["entries"]:
            # video_urls.append(entry["url"])
            video_ids.append(entry["id"])

    return channel["channel_id"], video_ids

def get_playlist_videos(playlist_url: str) -> list[str]:
    """Get the video urls from a playlist.

    Args:
        playlist_url (str): The playlist URL.

    Returns:
        List[str]: The video URLs.
    """

    playlist = YDL_CLIENT.extract_info(playlist_url, download=False)
    # video_urls = []
    video_ids = []
    for entry in playlist["entries"]:
        # video_urls.append(entry["url"])
        video_ids.append(entry["id"])

    return video_ids

def get_video(url: str) -> str:
    """Get the video ID from a URL.

    Args:
        url (str): The URL

    Returns:
        str: The video ID
    """
    info = YDL_CLIENT.extract_info(url, download=False)
    return info["id"]

