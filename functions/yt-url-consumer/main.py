import base64
import time
import functions_framework
import glob
import os
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
    "outtmpl": {
        "default": DELIMITER.join(["%(id)s", "%(channel_id)s", "%(uploader)s", "%(duration)s", "%(upload_date)s", "%(title)s"])
    },
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


def parse_ttml(ttml_file_name: str) -> Tuple[List[str], List[int]]:
    """Parse the ttml file into a list of subtitles and a list of timestamps

    Args:
        ttml_file_name (str): The name of the ttml file to parse

    Returns:
        Tuple[List[str], List[int]]: A tuple containing the list of subtitles and the list of timestamps
    """
    
    subtitles = []
    timestamps = []

    with open(ttml_file_name, "rb") as f:
        # Stream processing to not load entire XML tree at once
        for _, element in etree.iterparse(f, events=('end', )):
            if is_valid_subtitle(element):
                text = element.text.strip()
                begin = element.attrib['begin']
                subtitles.append(text)
                # TODO: convert begin to seconds
                timestamps.append(parse_timestamp(begin))

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


def insert_transcript(ttml_file_name: str) -> bool:
    """Inserts the transcript data into the firestore database

    Args:
        ttml_file_name (str): The name of the ttml file to insert

    Returns:
        bool: True if successful, False otherwise
    """

    try:
        initialize_firestore()

        # TODO: Handle potential error where there isn't exactly 1 ttml file
        video_id, channel_id, channel_name, duration, upload_date, title = ttml_file_name.split(
            DELIMITER)

        # Convert to the right data format (according to wiki)
        duration = int(duration)
        title = title.rstrip(".en.ttml")
        upload_date = int(upload_date)

        parsed_transcript, timestamps = parse_ttml(ttml_file_name)

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

    YDL.download(URL)

    # '''
    # TODO: Find a way to keep the info in memory instead of writing locally
    #         - Avoids unnecessary IO operation
    #         - In case of multiple function calls this avoids annoying edge cases
    # '''
    ttml_files = glob.glob("*.ttml")
    # There could be more if function called for multiple different URLs
    ttml_file_name = ttml_files[0] if len(ttml_files) == 1 else None

    if not ttml_file_name:
        print("No ttml files found")
        return 400

    insert_transcript(ttml_file_name)

    # Cleanup the ttml file to prepare the function for another URL; prevent memory increase
    os.remove(ttml_file_name)
    print(f"Elapsed Time: {time.time() - startTime}")
