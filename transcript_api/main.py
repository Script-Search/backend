import functions_framework
import requests
from flask import jsonify, Request
from google.cloud import pubsub_v1
from google.oauth2 import service_account
from firebase_admin import credentials, firestore, initialize_app
from typing import Dict, Any, List


test_collection = None
publisher = None
topic_path = None

#
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
    return


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
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,POST,PATCH,UPDATE,FETCH,DELETE',
    }

    if request_json and "url" in request_json:
        url = request_json["url"]
    elif request_args and "url" in request_args:
        url = request_args["url"]
    else:
        url = None

    if url != None:
        send_url(url)
        return (jsonify({"status": "success"}), 200, headers)

    if request_json and "query" in request_json:
        query = request_json["query"]
    elif request_args and "query" in request_args:
        query = request_args["query"]
    else:
        query = None

    if (query != None):
        data = requests.get(
            f"https://us-central1-scriptsearch.cloudfunctions.net/typesense-searcher?query={query}").json()
        return (data, 200, headers)

    return (jsonify({"status": "failure"}), 200, headers)
