"""
This script handles the scraping using yt-dlp.
It extracts metadata information from given urls to send to another function.
"""

# Standard Library Imports
import re
import json
from enum import Enum
from typing import Any, Dict, List, Tuple
from io import StringIO

# Third-Party Imports
from yt_dlp import YoutubeDL
from google.cloud import pubsub_v1
from google.oauth2 import service_account

# File-System Imports
from settings import YDL_OPS, VALID_CHANNEL_REGEX, VALID_PLAYLIST_REGEX, VALID_VIDEO_REGEX
from helpers import debug

YDL_CLIENT = None
PUBLISHER = None
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
    global YDL_CLIENT
    if YDL_CLIENT == None:
        YDL_CLIENT = YoutubeDL(YDL_OPS)

def process_url(url: str) -> Dict[str, Any]:
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

    data = {
        "video_ids": [],
        "channel_id": None,
    }

    video_ids = []
    if url_type == URLType.VIDEO:
        video_id = get_video(url)
        ss = StringIO()
        ss.write(f"[{video_id}]")
        data["video_ids"] = ss.getvalue()
    elif url_type == URLType.PLAYLIST:
        video_urls, video_ids = get_playlist_videos(url)

        # Prepare video_ids for filtering
        ss = StringIO()
        ss.write("[")
        for video_id in video_ids:
            ss.write(f'`{video_id}`,')
        ss.write("]")
        data["video_ids"] = ss.getvalue()
        data["video_ids"] = data["video_ids"].replace(",]", "]") # pylint: disable=E1101

    elif url_type == URLType.CHANNEL:
        data["channel_id"], video_urls, video_ids = get_channel_videos(url)
    else:
        raise ValueError(f"Invalid URL: {url}")
    
    global PUBLISHER, TOPIC_PATH # pylint: disable=W0603
    if PUBLISHER is None:
        cred = service_account.Credentials.from_service_account_file(
            "credentials_pub_sub.json")
        PUBLISHER = pubsub_v1.PublisherClient(credentials=cred)
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

def get_channel_videos(channel_url: str) -> Tuple[str, List[str]]:
    """Get the video urls from a channel.

    Args:
        channel_url (str): The channel URL.

    Returns:
        List[str]: The video URLs.
    """

    channel = YDL_CLIENT.extract_info(channel_url, download=False)

    if not channel["entries"]:
        raise ValueError(f"Channel {channel_url} has no videos.")

    video_urls = []
    video_ids = []
    if "entries" in channel["entries"][0]:
        for entry in channel["entries"][0]["entries"]:
            video_urls.append(entry["url"])
            video_ids.append(entry["id"])
    else:
        for entry in channel["entries"]:
            video_urls.append(entry["url"])
            video_ids.append(entry["id"])

    return channel["channel_id"], video_urls, video_ids

def get_playlist_videos(playlist_url: str) -> List[str]:
    """Get the video urls from a playlist.

    Args:
        playlist_url (str): The playlist URL.

    Returns:
        List[str]: The video URLs.
    """

    playlist = YDL_CLIENT.extract_info(playlist_url, download=False)
    video_urls = []
    video_ids = []
    for entry in playlist["entries"]:
        video_urls.append(entry["url"])
        video_ids.append(entry["id"])

    return video_urls, video_ids

def get_video(url: str) -> str:
    """Get the video ID from a URL.

    Args:
        url (str): The URL

    Returns:
        str: The video ID
    """
    info = YDL_CLIENT.extract_info(url, download=False)
    return info["id"]
