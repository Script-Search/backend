import functions_framework
import io
import os
import re
import typesense
import yt_dlp
from enum import Enum
from flask import jsonify, Request
from google.cloud import pubsub_v1
from google.oauth2 import service_account
from firebase_admin import credentials, firestore, initialize_app
from logging import DEBUG, getLogger, StreamHandler, Formatter
from time import perf_counter
from typing import Any, Dict, List, Tuple


test_collection = None
publisher = None
topic_path = None
logger_console = None

DEBUG_FLAG = True

HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PATCH,UPDATE,FETCH,DELETE,OPTIONS",
    "Access-Control-Allow-Headers": "Origin, X-Requested-With, Content-Type, Accept, Authorization",
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
    "filter_by": "",
    "limit": 250,
    "highlight_start_tag": "",
    "highlight_end_tag": "",
}
"""
TypeSense search parameters.
"""

LIMIT = 50
"""
The maximum number of videos to process in a playlist or channel.
"""

WORD_LIMIT = 5
"""
The maximum number of words allowed in a query.
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
VALID_CHANNEL = r"^((?:https?:)?\/\/)?((?:www|m)\.)?(youtube\.com)\/(((c\/)?[\w\-\.]+)|(\@[\w\-\.]{3,30})|(channel\/[\w\-]+))(\?si=[\w\-]+)?(\/videos|\/featured)?$"

YDL_OPS = {
    "quiet": True,
    "extract_flat": True,
    "playlist_items": f"1-{LIMIT}",
}
"""
Youtube-dl options.
"""

YDL = yt_dlp.YoutubeDL(YDL_OPS)
"""
Youtube-dl client.
"""


class URLType(Enum):
    """Enum for URL types."""

    VIDEO = 1
    PLAYLIST = 2
    CHANNEL = 3


def debug(message: str) -> None:
    """Print a debug message.

    Args:
        message (str): The message to print.

    Retu_cloudrns:
        None
    """

    global logger_console

    if not logger_console:
        logger_console = getLogger("scriptsearch")
        logger_console.setLevel(DEBUG)
        handler = StreamHandler()
        handler.setFormatter(Formatter("%(asctime)s %(message)s"))
        logger_console.addHandler(handler)

    if DEBUG_FLAG:
        logger_console.log(DEBUG, message)
    return


def get_video_type(url: str) -> URLType:
    """Determines the type of video from the URL.

    Args:
        url (str): The URL.

    Returns:
        URLType: The type of video.
    """

    if re.search(VALID_VIDEO, url):
        return URLType.VIDEO
    elif re.search(VALID_PLAYLIST, url):
        return URLType.PLAYLIST
    elif re.search(VALID_CHANNEL, url):
        return URLType.CHANNEL
    else:
        raise ValueError(f"Invalid URL: {url}")


def process_url(url: str, url_type: URLType) -> Dict[str, Any]:
    """
    Takes a Universal Reference Link, determines if the url is a channel or a playlist and returns NUMBER most recent videos.

    Args:
        url (str): Universsal Reference Link
    """
    debug(f"Processing URL: {url}")

    data = {
        "video_ids": [],
        "channel_id": None,
    }

    if url_type == URLType.VIDEO:
        send_url(url)
    elif url_type == URLType.PLAYLIST:
        ss = io.StringIO()
        ss.write("[")
        for video_url, video_id in get_playlist_videos(url):
            send_url(video_url)
            ss.write(f'`{video_id}`,')
        ss.write("]")
        data["video_ids"] = ss.getvalue()
        data["video_ids"] = data["video_ids"].replace(",]", "]")
    elif url_type == URLType.CHANNEL:
        data["channel_id"], videos = get_channel_videos(url)
        for video_url in videos:
            send_url(video_url)
    else:
        raise ValueError(f"Invalid URL: {url}")

    return data


def get_playlist_videos(playlist_url: str) -> List[str]:
    """Get the video urls from a playlist.

    Args:
        playlist_url (str): The playlist URL.

    Returns:
        List[str]: The video URLs.
    """

    playlist = YDL.extract_info(playlist_url, download=False)
    video_urls = [(entry["url"], entry["id"]) for entry in playlist["entries"]]

    return video_urls


def get_channel_videos(channel_url: str) -> Tuple[str, List[str]]:
    """Get the video urls from a channel.

    Args:
        channel_url (str): The channel URL.

    Returns:
        List[str]: The video URLs.
    """

    channel = YDL.extract_info(channel_url, download=False)

    if not channel["entries"]:
        raise ValueError(f"Channel {channel_url} has no videos.")

    if "entries" in channel["entries"][0]:
        video_urls = [entry["url"]
                      for entry in channel["entries"][0]["entries"]]
    else:
        video_urls = [entry["url"] for entry in channel["entries"]]

    return channel["channel_id"], video_urls


def getID(url: str) -> str:
    """Get the video ID from a URL.

    Args:
        url (str): The URL

    Returns:
        str: The video ID
    """
    info = YDL.extract_info(url, download=False)
    return info["id"]


def video_exists(video_id: str) -> bool:
    """Checks to see if a video exists in Firestore

    Args:
        video_id (str): The video ID

    Returns:
        bool: True if the video exists, False otherwise
    """

    debug("Checking if video exists in Firestore")

    global test_collection
    if not test_collection:
        cred = credentials.Certificate("credentials_firebase.json")
        initialize_app(cred)
        db = firestore.client()
        test_collection = db.collection("test")

    document = test_collection.document(video_id).get()
    return document.exists


def send_url(url: str) -> None:
    """
    Sends a video url to Pub/Sub

    Args:
        url (str): Video URL

    Returns:
        None
    """
    # id = getID(url)

    # if video_exists(id):
    #     debug(f"Video {id} already exists in Firestore")
    #     return

    debug(f"Sending URL: {url}")

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

    indexes = []
    for i, snippet in enumerate(transcript):
        casefolded = [word.casefold() for word in snippet["matched_tokens"]]
        if query in casefolded:
            debug(f"Snippet: {snippet}")

            indexes.append(i)
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

    indexes = []
    for i, snip in enumerate(transcript):
        snippet = [word.casefold() for word in snip["matched_tokens"]]
        if words[0] in snippet:
            next_snippet = [word.casefold() for word in transcript[i + 1]
                            ["matched_tokens"]] if i + 1 < len(transcript) else None
            debug(f"Snippet: {snippet}")
            debug(f"Next Snippet: {next_snippet}")
            if next_snippet:
                if all(word in snippet or word in next_snippet for word in words[1:]):
                    indexes.append(i)
            else:
                if all(word in snippet for word in words[1:]):
                    indexes.append(i)
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
    if len(words) > WORD_LIMIT:
        raise ValueError(f"""Query is too long. Please limit to
                         {WORD_LIMIT} words or less.""")

    words = [word.casefold() for word in words]

    return single_word(transcript, query.casefold()) if len(words) == 1 else multi_word(transcript, words)


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


def search(query: str) -> List[Dict[str, Any]]:
    """Searches for a query in the transcript data.

    Args:
        query (str): The query to search for.

    Returns:
        Dict[str, List[Dict[str, Any]]]: The search results.
    """
    SEARCH_PARAMS["q"] = f"\"{query}\""

    debug(f"Searching for {SEARCH_PARAMS['q']} in transcripts.")

    response = TYPESENSE.collections["transcripts"].documents.search(
        SEARCH_PARAMS)

    result = []

    for hit in response["hits"]:
        document = hit["document"]

        data = {
            "video_id": document["id"],
            "title": document["title"],
            "channel_id": document["channel_id"],
            "channel_name": document["channel_name"],
            "matches": []
        }

        query_no_quotes = SEARCH_PARAMS["q"][1:-1]
        for index in find_indexes(hit["highlight"]["transcript"], query_no_quotes):
            marked_snippet = mark_word(
                document["transcript"][index], query_no_quotes)
            data["matches"].append(
                {"snippet": marked_snippet, "timestamp": document["timestamps"][index]})

        debug(f'{data["video_id"]} has {len(data["matches"])} matches.')

        result.append(data)
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

    start = perf_counter()
    debug(f"Transcript API called")

    request_json = request.get_json(silent=True)
    request_args = request.args

    data = {
        "status": "success",
        "word_limit": WORD_LIMIT,
        "time": None,
        "channel_id": None,
        "video_ids": None,
        "hits": None,
    }

    SEARCH_PARAMS["filter_by"] = ""

    channel_id = None
    if request_json and "channel_id" in request_json:
        channel_id = request_json["channel_id"]
    elif request_args and "channel_id" in request_args:
        channel_id = request_args["channel_id"]

    if channel_id:
        SEARCH_PARAMS["filter_by"] = f"channel_id:={channel_id}"

    video_ids = None
    if request_json and "video_ids" in request_json:
        video_ids = request_json["video_ids"]
    elif request_args and "video_ids" in request_args:
        video_ids = request_args["video_ids"]

    if video_ids:
        ss = io.StringIO()
        ss.write("video_id:=")
        ss.write(video_ids)
        SEARCH_PARAMS["filter_by"] = ss.getvalue()

    url = None
    if request_json and "url" in request_json:
        url = request_json["url"]
    elif request_args and "url" in request_args:
        url = request_args["url"]

    if url:
        data_temp = None
        url_type = get_video_type(url)
        try:
            data_temp = process_url(url, url_type)
        except ValueError as e:
            return (jsonify({"error": str(e)}), 400, HEADERS)
        data["video_ids"] = data_temp["video_ids"]
        data["channel_id"] = data_temp["channel_id"]

    query = None
    if request_json and "query" in request_json:
        query = request_json["query"]
    elif request_args and "query" in request_args:
        query = request_args["query"]

    if (query != None):
        try:
            data["hits"] = search(query)
        except ValueError as e:
            return (jsonify({"error": str(e)}), 400, HEADERS)
    end = perf_counter()
    data["time"] = end - start
    debug(f"Transcript API finished in {data['time']} seconds")

    return (jsonify(data), 200, HEADERS)
