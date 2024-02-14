import functions_framework
from flask import jsonify, Request
from firebase_admin import credentials, firestore, initialize_app
from typing import Dict, Any


def get_transcript(video_id: str) -> Dict[str, Any]:
    cred = credentials.Certificate("credentials.json")
    initialize_app(cred)
    db = firestore.client()
    test = db.collection("test")
    document = test.document(video_id).get()
    return document.to_dict()


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

    if request_json and "request" in request_json:
        request = request_json["request"]
    elif request_args and "request" in request_args:
        request = request_args["request"]
    else:
        request = None

    data = {
        "request": request
    }

    return (jsonify(data), 200, headers)
