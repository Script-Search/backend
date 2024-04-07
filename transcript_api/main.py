"""
This module contains an HTTP Cloud Function for handling transcript requests.
It includes functionality to process incoming HTTP requests containing transcript data, 
either for searching or scraping.

The function `transcript_api` handles these requests, 
extracting necessary data from the request payload or query parameters, 
and performs either searching or scraping operations based on the provided data.

The function returns a JSON response containing information about the operation status, 
maximum query word limit, execution time, channel ID, video IDs, and search hits (if applicable).

Dependencies:
- functions_framework
- flask
- settings
- helpers
- scrape
- search

Usage:
The function can be deployed as an HTTP Cloud Function and accessed via HTTP requests. 
It accepts JSON payloads with optional parameters such as 
`channel_id`, `video_ids`, and `query` for searching, or `url` for scraping.
"""

from __future__ import annotations

# Standard Library Imports
import io
from time import perf_counter

# Third-Party Imports
import functions_framework
from flask import jsonify, Request, Response

# File-System Imports
from settings import API_RESPONSE_HEADERS, TYPESENSE_SEARCH_PARAMS, TYPESENSE_SEARCH_REQUESTS, MAX_QUERY_WORD_LIMIT
from helpers import debug, distribute
from scrape import process_url
from search import search_typesense, search_playlist

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

    try:
        start = perf_counter()
        debug("======================== TRANSCRIPT API ========================")

        request_json = request.get_json(silent=True) or {"empty": True}
        request_args = request.args or {"empty": True}

        data = {
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
            copy_search_param["q"] = f"\"{query}\""
            if channel_id:
                copy_search_param["filter_by"] = f"channel_id:{channel_id}"

                try:
                    data["hits"] = search_typesense(copy_search_param)
                except ValueError as e:
                    return (jsonify({"error": str(e)}), 400, API_RESPONSE_HEADERS)

            elif video_ids:
                copy_search_param = TYPESENSE_SEARCH_PARAMS.copy()

                del copy_search_param["drop_tokens_threshold"]
                del copy_search_param["typo_tokens_threshold"]
                del copy_search_param["page"]
                del copy_search_param["filter_by"]
                del copy_search_param["q"]

                copy_search_requests = TYPESENSE_SEARCH_REQUESTS.copy() 
                split_video_ids = distribute(video_ids, 5)

                string_ids = [",".join(ids) for ids in split_video_ids]

                for i, sub_search in enumerate(copy_search_requests["searches"]):
                    sub_search["q"] = f"{query}"
                    sub_search["filter_by"] = f"video_id:[{string_ids[i]}]"

                data["hits"] = search_playlist(copy_search_requests, copy_search_param)

        else: # Case when we only scraping is happening
            url = ""
            if request_args and "url" in request_args:
                url = str(request_args["url"])
            if request_json and "url" in request_json:
                url = request_json.get("url", "")

            if url:
                data_temp = {}
                try:
                    data_temp = process_url(url)
                except ValueError as e:
                    return (jsonify({"error": str(e)}), 400, API_RESPONSE_HEADERS)
                data["video_ids"] = data_temp["video_ids"]
                data["channel_id"] = data_temp["channel_id"]

        end = perf_counter()
        data["time"] = end - start
        debug(f"Transcript API finished in {data['time']} seconds")

        return (jsonify(data), 200, API_RESPONSE_HEADERS)

    except Exception as e:      # catch all other exceptions
        return (jsonify({"error": str(e)}), 500, API_RESPONSE_HEADERS)