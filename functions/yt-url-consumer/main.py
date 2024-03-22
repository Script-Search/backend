import base64
import time
import functions_framework
import requests
import io
import yt_dlp

from firebase_admin import credentials, firestore, initialize_app
from lxml import etree
from typing import Tuple, List

test_collection = None

DELIMITER = "$#$"
"""
Delimiter used to separate the different fields in the output file name
"""

YDL_OPTS = {
    "skip_download": True,
    "writesubtitles": True,
    "writeautomaticsub": True,
    "subtitleslangs": ["en"],  # TODO: Handle other languages (en-.*)
    "subtitlesformat": "ttml",
    "extractor_args": {'youtube': {'player_skip': ['webpage'], 'player_client': ['web']}},
    "quiet": True, 
}
"""
Options for yt-dlp to download the subtitles in the right format
"""

YDL = yt_dlp.YoutubeDL(YDL_OPTS)
"""
yt-dlp object to download the subtitles
"""


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


def parse_ttml(ttml_url: str) -> Tuple[List[str], List[int]]:
    """Make a request to the ttml_url to download the subtitles and parse it

    Args:
        ttml_url (str): The url of the ttml file

    Returns:
        Tuple[List[str], List[int]]: A tuple containing the list of subtitles and the list of timestamps
    """

    subtitles = []
    timestamps = []
    
    r = requests.get(ttml_url)
    xml_like_obj = io.BytesIO(r.content)

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


def initialize_firestore() -> None:
    """Uses lazy-loading to initialize the firestore client and collection
    """

    global test_collection
    if test_collection == None:
        cred = credentials.Certificate("credentials.json")
        initialize_app(cred)
        db = firestore.client()
        test_collection = db.collection("test")


def insert_transcript(info_json: dict) -> bool:
    """Inserts the transcript data into the firestore database

    Args:
        info_json (dict): Json converted to dictionary about video's information

    Returns:
        bool: True if successful, False otherwise
    """

    try:
        initialize_firestore()

        video_id = info_json["id"]
        channel_id = info_json["channel_id"]
        channel_name = info_json["channel"]
        duration = info_json["duration"]
        upload_date = int(info_json["upload_date"])
        title = info_json["title"]

        upload_date = int(upload_date)

        ttml_url = info_json.get("subtitle_url")

        if not ttml_url:
            raise Exception("No ttml_url from given video.")

        parsed_transcript, timestamps = parse_ttml(ttml_url)

        doc_ref = test_collection.document(video_id)
        doc_ref.set({
            "video_id": video_id,
            "channel_id": channel_id,
            "channel_name": channel_name,
            "duration": int(duration),
            "upload_date": upload_date,  # Maybe defer this to a later function
            "title": title,
            "transcript": parsed_transcript,
            "timestamps": timestamps
        })
        return True
    except Exception as e:
        print(f"Error inserting transcript data: {e}")
        return False

# Triggered from a message on a Cloud Pub/Sub topic.


@functions_framework.cloud_event
def transcript_downloader(cloud_event: functions_framework.CloudEvent) -> None:
    """Downloads the transcript from the given URL and inserts it into the firestore database

    Args:
        cloud_event (CloudEvent): The cloud event containing the URL to download the transcript from

    Returns:
        None
    """
    
    startTime = time.time()
    URL = base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")

    if "watch" not in URL:  # TODO: Ensure inputted URL is a singular video
        print("watch not in URL")
        return 400

    info = YDL.extract_info(URL, download=False)
    print(info)
    insert_transcript(info)

    print(f"Elapsed Time: {time.time() - startTime}")
