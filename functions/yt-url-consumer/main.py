import base64
import functions_framework
import io
import json
import yt_dlp

from lxml import etree
from typing import Tuple, List

# File-System Imports; Use modules like singletons to ensure only one instance created
from pubsub import initialize_pubsub, publish
from poolmanager import initialize_req_pool, get_ttml_response

YDL_OPTS = {
    "skip_download": True,
    "writesubtitles": True,
    "writeautomaticsub": True,
    "subtitleslangs": ["en"],  # TODO: Handle other languages (en-.*)
    "subtitlesformat": "ttml",
    "extractor_args": {'youtube': {'player_skip': ['webpage'], 'player_client': ['web']}},
    "source_address": "0.0.0.0",
    "quiet": True, 
}
"""
Options for yt-dlp to download the subtitles in the right format
"""

YDL = yt_dlp.YoutubeDL(YDL_OPTS)

def is_valid_subtitle(element: etree._Element) -> bool:
    """Checks if the element is a valid subtitle element

    Args:
        element (idk): The element to check
    """

    return element.tag.endswith('p') and 'begin' in element.attrib and 'end' in element.attrib and element.text


def parse_timestamp(timestamp: str) -> int:
    """Parse the timestamp into seconds

    Args:
        timestamp (str): The timestamp in the format HH:MM:SS.sss

    Returns:
        int: The timestamp in seconds
    """
    
    hours, minutes, seconds = timestamp.split(":")
    seconds = seconds.split(".")[0]
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)


def parse_ttml(response_data: str) -> Tuple[List[str], List[int]]:
    """Make a request to the ttml_url to download the subtitles and parse it

    Args:
        response_data (str): Byte string of the url content (ttml)

    Returns:
        Tuple[List[str], List[int]]: A tuple containing the list of subtitles and the list of timestamps
    """

    subtitles = []
    timestamps = []
    
    xml_like_obj = io.BytesIO(response_data)

    # Stream processing to not load entire XML tree at once
    for _, element in etree.iterparse(xml_like_obj, events=('end', )):
        if is_valid_subtitle(element):
            text = element.text.strip()
            begin = element.attrib['begin']
            subtitles.append(text)
            timestamps.append(parse_timestamp(begin)) # TODO: convert begin to seconds

        # Clear element to release memory, can help w/ mem usage
        element.clear()

        # # Clear parent element to release memory, can help w/ mem usage
        # while element.getprevious() is not None:
        #     del element.getparent()[0]

    return subtitles, timestamps

def insert_transcript(info_json: dict) -> bool:
    """Inserts the transcript data into the firestore database

    Args:
        info_json (dict): Json converted to dictionary about video's information

    Returns:
        bool: True if successful, False otherwise
    """

    try:
        initialize_req_pool()
        initialize_pubsub() # TODO: Make this asynchronous somehow...

        video_id = info_json["id"]
        channel_id = info_json["channel_id"]
        channel_name = info_json["channel"]
        duration = info_json["duration"]
        upload_date = int(info_json["upload_date"])
        title = info_json["title"]

        upload_date = int(upload_date)

        ttml_url = info_json.get("subtitle_url")

        if not ttml_url:
            raise Exception(f"No ttml_url from given video: https://www.youtube.com/watch?v={video_id}")
        
        response = get_ttml_response(ttml_url)

        if response.status != 200:
            raise Exception(f"Unable to fetch ttml_url, {response.status} code.")

        parsed_transcript, timestamps = parse_ttml(response.data)
        publish([{
            "video_id": video_id,
            "channel_id": channel_id,
            "channel_name": channel_name,
            "duration": int(duration),
            "upload_date": upload_date,  # Maybe defer this to a later function
            "title": title,
            "transcript": parsed_transcript,
            "timestamps": timestamps
        }])
        return True
    except Exception as e:
        print(f"Error inserting transcript data: {e}")
        return False

@functions_framework.cloud_event
def transcript_downloader(cloud_event: functions_framework.CloudEvent) -> None:
    """Downloads the transcript from the given URL and inserts it into the firestore database

    Args:
        cloud_event (CloudEvent): Pub/Sub msg containing the URL to download the transcript from

    Returns:
        None
    """
    try:
        URLs = json.loads(base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8"))
        URL = URLs[0] # TODO: Add client-side batching to handle parallel URLs in the future

        if "watch" not in URL:  # TODO: Ensure inputted URL is a singular video
            print("watch not in URL")
            return 500
        info = YDL.extract_info(URL, download=False)
        insert_transcript(info)
    except Exception as e:
        return {"error": str(e)}, 500