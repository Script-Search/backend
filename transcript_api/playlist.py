import re
import yt_dlp
from typing import List


LIMIT = 250
YDL_OPS = {
        "quiet": True,
        "extract_flat": True,
        "playlist_items": f"1-{LIMIT}",
        }

YDL = yt_dlp.YoutubeDL(YDL_OPS)
VALID_VIDEO = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu\.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
VALID_PLAYLIST = r"^.*(youtu.be\/|list=)([^#\&\?]*).*"

def process_url(url: str) -> List[str]:
    """
    Takes a Universal Reference Link, determines if the url is a channel or a playlist and returns NUMBER most recent videos.

    Args:
        url (str): Universsal Reference Link

    Returns:
        List[str]: list of video urls
    """
    is_short = "short" in url
    is_feed = "feed" in url

    if is_short or is_feed:
        raise ValueError(f"This type of url is not supported")

    is_video = re.search(VALID_VIDEO, url)
    is_playlist = "list=" in url
    is_channel = "channel" in url or "@" in url

    if is_video:
        print("Video")
    elif is_playlist:
        print("Playlist")
    elif is_channel:
        print("Channel")
    else:
        print("Invalid")
    return

def get_playlist_videos(playlist_url):
    playlist = YDL.extract_info(playlist_url, download=False)
    video_urls = [ entry["url"] for entry in playlist["entries"] ]

    return video_urls

def get_channel_videos(channel_url):
    channel = YDL.extract_info(channel_url, download=False)
    video_urls = [ entry["url"] for entry in channel["entries"][0]["entries"] ]

    return video_urls

def main():
    url = "https://youtube.com/playlist?list=PL94lfiY18_CgWGQzweD_aVjsFXiRi6kn5&si=UmiI8Ou09GHXwo6n"
    # url = "https://www.youtube.com/watch?v=xlQ0psr7Th4&list=PL94lfiY18_CgWGQzweD_aVjsFXiRi6kn5"
    # url = "https://www.youtube.com/@PewDiePie"
    process_url(url)

if __name__ == "__main__":
    main()

