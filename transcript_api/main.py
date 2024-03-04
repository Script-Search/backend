import functions_framework
import requests
import re
import yt_dlp
from flask import jsonify, Request
from google.cloud import pubsub_v1
from google.oauth2 import service_account
from firebase_admin import credentials, firestore, initialize_app
from typing import Dict, Any, List


test_collection = None
publisher = None
topic_path = None
HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,PATCH,UPDATE,FETCH,DELETE',
}

LIMIT = 250
YDL_OPS = {
    "quiet": True,
    "extract_flat": True,
    "playlist_items": f"1-{LIMIT}",
}

YDL = yt_dlp.YoutubeDL(YDL_OPS)
VALID_VIDEO = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)(?!.*playlist)([\w\-]+)(\S+)?$"


def get_transcript(video_id: str) -> Dict[str, Any]:
    """Get the transcript for a video.

    Args:
        video_id (str): The video ID.

    Returns:
        Dict[str, Any]: The transcript data.
    """

    global test_collection
    if test_collection == None:
        cred = credentials.Certificate("credentials.json")
        initialize_app(cred)
        db = firestore.client()
        test_collection = db.collection("test")
    print(video_id)
    document = test_collection.document(video_id).get()
    return document.to_dict()


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
        print(f"Send this video to Pub/Sub: {url}")
    elif is_playlist:
        for video_url in get_playlist_videos(url):
            print(f"Send this video to Pub/Sub: {video_url}")
    elif is_channel:
        for video_url in get_channel_videos(url):
            print(f"Send this video to Pub/Sub: {video_url}")
    else:
        raise ValueError(f"Invalid URL: {url}")
    return


def get_playlist_videos(playlist_url: str) -> List[str]:
    """Get the video urls from a playlist.

    Args:
        playlist_url (str): The playlist URL.

    Returns:
        List[str]: The video URLs.
    """

    playlist = YDL.extract_info(playlist_url, download=False)
    video_urls = [entry["url"] for entry in playlist["entries"]]

    return video_urls


def get_channel_videos(channel_url: str) -> List[str]:
    """Get the video urls from a channel.

    Args:
        channel_url (str): The channel URL.

    Returns:
        List[str]: The video URLs.
    """

    channel = YDL.extract_info(channel_url, download=False)
    video_urls = [entry["url"] for entry in channel["entries"][0]["entries"]]

    return video_urls


def send_url(url: str):
    """
    Sends a video url to Pub/Sub

    Args:
        url (str): Video URL

    Returns:
        None
    """

    global publisher, topic_path
    if (publisher == None):
        cred = service_account.Credentials.from_service_account_file(
            "credentials_pub_sub.json")
        publisher = pubsub_v1.PublisherClient(credentials=cred)
        topic_path = publisher.topic_path("ScriptSearch", "YoutubeURLs")
    data = url.encode("utf-8")

    future = publisher.publish(topic_path, data=data)
    future.result()

    print(f"Published message to {topic_path} with data {data}")

    return


@functions_framework.http
def transcript_api(request: Request) -> Request:
    """HTTP Cloud Function for handling transcript requests.

    This function handles incoming HTTP requests containing transcript data.

    Args:
        request (flask.Request): The request object.
            <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>

    Returns:
        Tuple containing:
        - The response text, or any set of values that can be turned into a
          Response object using `make_response`
          <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
        - HTTP status code.
        - Headers for the response.
    """

    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and "url" in request_json:
        url = request_json["url"]
    elif request_args and "url" in request_args:
        url = request_args["url"]
    else:
        url = None

    if url != None:
        try:
            process_url(url)
        except ValueError as e:
            return (jsonify({"error": str(e)}), 400, HEADERS)

    if request_json and "query" in request_json:
        query = request_json["query"]
    elif request_args and "query" in request_args:
        query = request_args["query"]
    else:
        query = None

    data = jsonify({"status": "success"})
    if (query != None):
        data = requests.get(
            f"https://us-central1-scriptsearch.cloudfunctions.net/typesense-searcher?query={query}").json()
    return (data, 200, HEADERS)

