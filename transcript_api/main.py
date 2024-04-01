"""
This script is the main entry point for the Cloud Function.
It processes incoming requests and sends them to the appropriate functions.
"""

# Standard Library Imports
import io
from time import perf_counter
import types
from typing import get_args, get_type_hints

# Third-Party Imports
import functions_framework
from flask import jsonify, Request, Response

# File-System Imports
from settings import API_RESPONSE_HEADERS, TYPESENSE_SEARCH_PARAMS, MAX_QUERY_WORD_LIMIT
from helpers import debug
from scrape import process_url
from search import search_typesense

@functions_framework.http
def transcript_api(request: Request) -> tuple[Response, int, dict[str, str]]:
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
        - API_RESPONSE_HEADERS for the response.
    """

    start = perf_counter()
    debug("Transcript API called")

    request_json = request.get_json(silent=True) or {"empty": True}
    request_args = request.args or {"empty": True}

    data: dict[str, str|int|float|list[str]|None] = {
        "status": "success",
        "MAX_QUERY_WORD_LIMIT": MAX_QUERY_WORD_LIMIT,
        "time": 0,
        "channel_id": None,
        "video_ids": None,
        "hits": None,
    }

    channel_id = request_json.get("channel_id")
    video_ids = request_json.get("video_ids")
    query = request_json.get("query")

    if query: # Case when only searching is happening
        copy_search_param = TYPESENSE_SEARCH_PARAMS.copy() # Normally copy is bad, but this should be fast
        copy_search_param["filter_by"] = f"channel_id:{channel_id}" if channel_id else ""
        if video_ids:
            ss = io.StringIO()
            ss.write("video_id:")
            ss.write(video_ids)

            copy_search_param["filter_by"] = ss.getvalue()
        copy_search_param["q"] = f"\"{query}\""
        try:
            data["hits"] = search_typesense(copy_search_param)
        except ValueError as e:
            return (jsonify({"error": str(e)}), 400, API_RESPONSE_HEADERS)
    else: # Case when we only scraping is happening
        if request_args and "url" in request_args:
            url = request_args["url"]
        if request_json and "url" in request_json:
            url = request_json.get("url")

        if url:
            data_temp = {}
            try:
                data_temp = process_url(url)
            except ValueError as e:
                return (jsonify({"error": str(e)}), 400, API_RESPONSE_HEADERS)
            data["video_ids"] = data_temp["video_ids"]
            data["channel_id"] = data_temp["channel_id"]

    if data["video_ids"] is None:
        data["video_ids"] = []

    end = perf_counter()
    data["time"] = end - start
    debug(f"Transcript API finished in {data['time']} seconds")

    for key, value in data.items():
        t = type(value)
        if t == types.UnionType:
            debug(f"{key} : {get_args(value)}")
        else:
            debug(f"{key} : {t}")

    return (jsonify(data), 200, API_RESPONSE_HEADERS)
