import functions_framework
import os
import re
import typesense
import yt_dlp
from flask import jsonify, Request
from google.cloud import pubsub_v1, logging
from google.oauth2 import service_account
from firebase_admin import credentials, firestore, initialize_app
from typing import Dict, Any, List


test_collection = None
publisher = None
topic_path = None
logger = None

DEBUG = False

HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,PATCH,UPDATE,FETCH,DELETE',
}
"""
API headers to return with the data.
"""

SEARCH_PARAMS = {
    "drop_tokens_threshold": 0,
    "typo_tokens_threshold": 0,
    "page": 1,
    "per_page": 250,
    "prefix": False,
    "q": None,
    "query_by": "transcript",
    "sort_by": "upload_date:desc",
    "limit": 250,
    "limit_hits": 250,
    "highlight_start_tag": "",
    "highlight_end_tag": "",
}
"""
TypeSense search parameters.
"""

LIMIT = 10
"""
The maximum number of videos to process in a playlist or channel.
"""

TYPESENSE_API_KEY = os.environ.get("TYPESENSE_API_KEY")
"""
Typesense API key.
"""

TYPESENSE_HOST = os.environ.get("TYPESENSE_HOST")
"""
Typesense host.
"""

TYPESENSE = typesense.Client({
    "nodes": [{
        "host": TYPESENSE_HOST,
        "port": 443,
        "protocol": "https"
    }],
    "api_key": TYPESENSE_API_KEY,
    "connection_timeout_seconds": 2
})
"""
Typesense client.
"""

VALID_VIDEO = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)(?![playlist|channel])([\w\-]+)(\S+)?$"
VALID_PLAYLIST = r"^((?:https?:)?\/\/)?((?:www|m)\.)?(youtube\.com)\/(.*)[\&|\?](list=[\w\-]+)(\&index=[0-9]*)?(\&si=[\w\-]+)?$"
VALID_CHANNEL = r"^((?:https?:)?\/\/)?((?:www|m)\.)?(youtube\.com)\/((\@[\w\-\.]{3,30}(\?si=\w+)?)|(channel\/[\w\-]+))(\/videos)?$"

YDL_OPS = {
    "quiet": True,
    "extract_flat": True,
    "playlist_items": f"1-{LIMIT}",
}
YDL = yt_dlp.YoutubeDL(YDL_OPS)


def debug(message: str) -> None:
    """Print a debug message.

    Args:
        message (str): The message to print.

    Returns:
        None
    """

    global logger

    if not logger:
        cred = service_account.Credentials.from_service_account_file(
            "credentials_pub_sub.json")
        client = logging.Client(credentials=cred)
        logger = client.logger("scriptsearch")

    if DEBUG:
        logger.log_text(message, severity="DEBUG")
        print(message)
    return


def get_transcript(video_id: str) -> Dict[str, Any]:
    """Get the transcript for a video.

    Args:
        video_id (str): The video ID.


    Returns:
        Dict[str, Any]: The transcript data.
    """

    global test_collection
    if not test_collection:
        cred = credentials.Certificate("credentials.json")
        initialize_app(cred)
        db = firestore.client()
        test_collection = db.collection("test")

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

    is_video = re.search(VALID_VIDEO, url)
    is_playlist = re.search(VALID_PLAYLIST, url)
    is_channel = re.search(VALID_CHANNEL, url)

    if is_video:
        send_url(url)
        debug(f"Send this video to Pub/Sub: {url}")
    elif is_playlist:
        for video_url in get_playlist_videos(url):
            send_url(video_url)
            debug(f"Send this video to Pub/Sub: {video_url}")
        debug("=" * 100)
    elif is_channel:
        if url.endswith("/videos"):
            url = url[:-7]

        for video_url in get_channel_videos(url):
            send_url(video_url)
            debug(f"Send this video to Pub/Sub: {video_url}")
        debug("=" * 100)
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


def send_url(url: str) -> None:
    """
    Sends a video url to Pub/Sub

    Args:
        url (str): Video URL

    Returns:
        None
    """

    global publisher, topic_path
    if not publisher:
        cred = service_account.Credentials.from_service_account_file(
            "credentials_pub_sub.json")
        publisher = pubsub_v1.PublisherClient(credentials=cred)
        topic_path = publisher.topic_path("ScriptSearch", "YoutubeURLs")
    data = url.encode("utf-8")

    future = publisher.publish(topic_path, data=data)
    future.result()

    debug(f"Published message to {topic_path} with data {data}")

    return


def single_word(transcript: List[Dict[str, Any]], query: str) -> List[int]:
    """
    Finds the indexes of the query in the transcript

    Args:
        transcript (List[Dict[str, Any]]): The transcript data
        query (str): The query

    Returns:
        List[int]: The indexes of the query
    """

    debug("Single word search")
    indexes = []
    for i, snippet in enumerate(transcript):
        if query in snippet["matched_tokens"]:
            debug(f"Snippet: {snippet}")

            indexes.append(i)
    debug("-" * 50)
    return indexes


def multi_word(transcript: List[Dict[str, Any]], words: List[str]) -> List[int]:
    """
    Finds the indexes of the query in the transcript

    Args:
        transcript (List[Dict[str, Any]]): The transcript data
        words (List[str]): The query words

    Returns:
        List[int]: The indexes of the query
    """

    debug("Multi word search")
    indexes = []
    for i, snippet in enumerate(transcript):
        if words[0] in snippet["matched_tokens"]:
            debug(f"Snippet: {snippet}")
            debug(f"Next Snippet: {transcript[i + 1]}")
            if all(word in snippet["matched_tokens"] or word in transcript[i + 1]["matched_tokens"] for word in words[1:]):
                indexes.append(i)
    debug("-" * 50)
    return indexes


def find_indexes(transcript: List[Dict[str, Any]], query: str) -> List[int]:
    """
    Finds the indexes of the query in the transcript

    Args:
        transcript (List[Dict[str, Any]]): The transcript data
        query (str): The query

    Returns:
        List[int]: The indexes of the query
    """

    debug(f"Finding indexes of {query} in transcript")
    words = query.split()

    return single_word(transcript, query) if len(words) == 1 else multi_word(transcript, words)


def mark_word(sentence: str, word: str) -> str:
    """
    Takes every instance of word within a sentence and wraps it in <mark> tags.
    This algorithm will also ignore cases.

    Args:
        sentence (str): The sentence
        word (str): The word

    Returns:
        str: The marked sentence
    """

    pattern = re.compile(re.escape(word), re.IGNORECASE)
    return pattern.sub(r"<mark>\g<0></mark>", sentence)


def search(query: str) -> Dict[str, List[Dict[str, Any]]]:
    SEARCH_PARAMS["q"] = f"\"{query}\""

    response = TYPESENSE.collections["transcripts"].documents.search(
        SEARCH_PARAMS)

    result = {"hits": []}

    for hit in response["hits"]:
        # get individual document featuring match
        document = hit["document"]

        # More or less metadata as required
        data = {
            "video_id": document["id"],
            "title": document["title"],
            "channel_id": document["channel_id"],
            "channel_name": document["channel_name"],
            "matches": []
        }

        # iterate through all matches within document
        for index in find_indexes(hit["highlight"]["transcript"], SEARCH_PARAMS["q"][1:-1]):
            data["matches"].append(
                {"snippet": mark_word(document["transcript"][index], SEARCH_PARAMS["q"][1:-1]), "timestamp": document["timestamps"][index]})

        debug(f"{data["video_id"]} has {len(data["matches"])} matches.")
        debug("-" * 50)

        result["hits"].append(data)
    debug("=" * 100)
    return result


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

    url = None
    if request_json and "url" in request_json:
        url = request_json["url"]
    elif request_args and "url" in request_args:
        url = request_args["url"]

    if url != None:
        try:
            process_url(url)
        except ValueError as e:
            return (jsonify({"error": str(e)}), 400, HEADERS)

    query = None
    if request_json and "query" in request_json:
        query = request_json["query"]
    elif request_args and "query" in request_args:
        query = request_args["query"]

    if (query != None):
        data = search(query)
        return (data, 200, HEADERS)

    return (jsonify({"status": "success", "query": False}), 200, HEADERS)
