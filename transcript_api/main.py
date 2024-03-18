import functions_framework
import io
import os
import re
import typesense
import yt_dlp
from flask import jsonify, Request
from google.cloud import pubsub_v1, logging
from google.oauth2 import service_account
from firebase_admin import credentials, firestore, initialize_app
from logging import DEBUG, getLogger, StreamHandler, Formatter
from typing import Any, Dict, List, Tuple


test_collection = None
publisher = None
topic_path = None
logger_cloud = None
logger_console = None

DEBUG = True

LOG_FORMAT = Formatter("%(asctime)s %(message)s")

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
    "filter_by": "",
    "limit": 250,
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
VALID_CHANNEL = r"^((?:https?:)?\/\/)?((?:www|m)\.)?(youtube\.com)\/((\@[\w\-\.]{3,30}(\?si=\w+)?)|(channel\/[\w\-]+))(\/videos)?$"

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


def debug(message: str) -> None:
    """Print a debug message.

    Args:
        message (str): The message to print.

    Retu_cloudrns:
        None
    """

    global logger_cloud, logger_console

    if not logger_cloud:
        cred = service_account.Credentials.from_service_account_file(
            "credentials_pub_sub.json")
        client = logging.Client(credentials=cred)
        logger_cloud = client.logger("scriptsearch")

    if not logger_console:
        logger_console = getLogger("scriptsearch")
        logger_console.setLevel(DEBUG)
        handler = StreamHandler()
        handler.setFormatter(LOG_FORMAT)
        logger_console.addHandler(handler)

    if DEBUG:
        # logger_cloud.log_text(message, severity="DEBUG")
        logger_console.log(DEBUG, message)
    return


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
        # send_url(url)
        debug(f"Send this video to Pub/Sub: {url}")
    elif is_playlist:
        ss = io.StringIO()
        ss.write("video_id:=[")
        for video_url in get_playlist_videos(url):
            # send_url(video_url)
            ss.write(f"`{getID(video_url)}`,")
            debug(f"Send this video to Pub/Sub: {video_url}")
        ss.write("]")
        string = ss.getvalue()
        string = string[:-2] + string[-1]
        SEARCH_PARAMS["filter_by"] = string
        debug(SEARCH_PARAMS["filter_by"])
    elif is_channel:
        if url.endswith("/videos"):
            url = url[:-7]

        channel_id, videos = get_channel_videos(url)
        SEARCH_PARAMS["filter_by"] = f"channel_id:={channel_id}"
        debug(SEARCH_PARAMS["filter_by"])

        for video_url in videos:
            # send_url(video_url)
            debug(f"Send this video to Pub/Sub: {video_url}")
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


def get_channel_videos(channel_url: str) -> Tuple[str, List[str]]:
    """Get the video urls from a channel.

    Args:
        channel_url (str): The channel URL.

    Returns:
        List[str]: The video URLs.
    """

    channel = YDL.extract_info(channel_url, download=False)
    video_urls = [entry["url"] for entry in channel["entries"][0]["entries"]]

    return channel["channel_id"], video_urls


def getID(url: str) -> str:
    match = re.match(VALID_VIDEO, url)
    return match.group(5) if match else None


def video_exists(video_id) -> bool:
    global test_collection
    if not test_collection:
        cred = credentials.Certificate("credentials_firebase.json")
        initialize_app(cred)
        db = firestore.client()
        test_collection = db.collection("test")

    document = test_collection.document(video_id)
    return bool(document)

def send_url(url: str) -> None:
    """
    Sends a video url to Pub/Sub

    Args:
        url (str): Video URL

    Returns:
        None
    """
    id = getID(url)

    if video_exists(id):
        debug(f"Video {id} already exists in Firestore")
        return
    
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
        if query.casefold() in map(str.casefold, snippet["matched_tokens"]):
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
        snippet = map(str.casefold, snip["matched_tokens"])
        if words[0].casefold() in snippet:
            next_snippet = map(str.casefold, transcript[i + 1]) if i + 1 < len(transcript) else None
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
        raise ValueError(f"Query is too long. Please limit to {WORD_LIMIT} words or less.")

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
    """Searches for a query in the transcript data.

    Args:
        query (str): The query to search for.

    Returns:
        Dict[str, List[Dict[str, Any]]]: The search results.
    """
    SEARCH_PARAMS["q"] = f"\"{query}\""
    # SEARCH_PARAMS["filter_by"] = ""

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

        debug(f'{data["video_id"]} has {len(data["matches"])} matches.')

        result["hits"].append(data)
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
    debug(f"Transcript API called")

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

    data = {
        "status": "success",
        "query": bool(query),
        "url": bool(url),
        "word_limit": WORD_LIMIT,
    }

    return (jsonify(data), 200, HEADERS)
