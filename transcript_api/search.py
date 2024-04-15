"""
This module provides functions for searching and marking words in transcript data using Typesense.

It includes functions for initializing the Typesense client, searching for queries in transcript data,
finding indexes of words or phrases in the transcript, and marking specific words within a sentence.

Dependencies:
- typesense.Client: a Python client for the Typesense API
- helpers.debug: a function for debugging purposes
- settings.MAX_QUERY_WORD_LIMIT: the maximum number of words allowed in a query
- settings.TYPESENSE_HOST: the host URL for the Typesense server
- settings.TYPESENSE_API_KEY: the API key for accessing the Typesense server
"""

from __future__ import annotations

# Standard Library Imports
import re

# Third Party Imports
from typesense import Client

# File System Imports
from helpers import debug
from settings import MAX_QUERY_WORD_LIMIT, TYPESENSE_HOST, TYPESENSE_API_KEY 

TYPESENSE_CLIENT: Client = None

def init_typesense() -> None:
    """
    Initializes the typesense client.
    """

    global TYPESENSE_CLIENT  # pylint: disable=global-statement
    if not TYPESENSE_CLIENT:
        TYPESENSE_CLIENT = Client({
            "nodes": [{
                "host": TYPESENSE_HOST,
                "port": 443,
                "protocol": "https"
            }],
            "api_key": TYPESENSE_API_KEY,
            "connection_timeout_seconds": 4
        })


def process_hit(hit: dict[str, int|list[dict[str, str|list]]|dict[str, list]], query_no_quotes: str) -> list[dict[str, str|int]]:
    """
    Processes the hit data.

    Args:
        hit (dict[str, str|list[str]]): The hit data
        query_no_quotes (str): The query without quotes

    Returns:
        list[dict[str, str|int]]: The processed hit data
    """

    document = hit["document"]
    marked_snippets = []
    words = query_no_quotes.split()
    num_words = len(words)
    
    for index in find_indexes(document["transcript"], query_no_quotes):
        transcript_casefolded = document["transcript"][index].casefold()

        if num_words != 1 and index + 1 < len(document["transcript"]) and not (query_no_quotes in transcript_casefolded):
            document["transcript"][index] += f" {document['transcript'][index + 1]}"

        marked_snippet = document["transcript"][index]
        for word in words:
            marked_snippet = mark_word(marked_snippet, word)

        for i in range(MAX_QUERY_WORD_LIMIT, 1, -1):
            marked_snippet = marked_snippet.replace(r"<mark>" * i, "<mark>")
            marked_snippet = marked_snippet.replace(r"</mark>" * i, "</mark>")

        marked_snippets.append({"snippet": marked_snippet, "timestamp": document["timestamps"][index]})

    return marked_snippets

def search_playlist(search_requests: dict[str, list[dict[str, str]]], query_params: dict[str, object]) -> list[dict[str, str]]:
    """
    Searches for a query in the playlist data.

    Args:
        query_params (dict[str, str|int|bool]): The query params to use when searching.

    Returns:
        list[dict[str, str]]: The search results.
    """

    debug(f"Searching for {search_requests['searches'][0]['q']} in playlists.")

    init_typesense()
    responses = TYPESENSE_CLIENT.multi_search.perform(search_requests, query_params)
    result = []

    for response in responses["results"]:
        for hit in response["hits"]:
            data = {
                "video_id": hit["document"]["id"],
                "title": hit["document"]["title"],
                "channel_id": hit["document"]["channel_id"],
                "channel_name": hit["document"]["channel_name"],
                "duration": hit["document"]["duration"],
                "upload_date": hit["document"]["upload_date"],
                "matches": process_hit(hit, search_requests['searches'][0]['q'])
            }

            if data["matches"]:
                result.append(data)
                debug(f'{data["video_id"]} has {len(data["matches"])} matches.')
    return result


def search_typesense(query_params: dict[str, object]) -> list[dict[str, str | list[dict[str, str | int]]]]:
    """Searches for a query in the transcript data.

    Args:
        query_params (dict[str, str|int|bool]): The query params to use when searching.

    Returns:
        list[dict[str, str|list[dict[str, str|int]]]]: The search results.
    """

    debug(f"Searching for {query_params['q']} in transcripts.")

    init_typesense()
    response = TYPESENSE_CLIENT.collections["transcripts"].documents.search(query_params)

    result = []

    for hit in response["hits"]:
        data = {
            "video_id": hit["document"]["id"],
            "title": hit["document"]["title"],
            "channel_id": hit["document"]["channel_id"],
            "channel_name": hit["document"]["channel_name"],
            "duration": hit["document"]["duration"],
            "upload_date": hit["document"]["upload_date"],
            "matches": process_hit(hit, str(query_params["q"]))
        }

        if data["matches"]:
            result.append(data)
            debug(f'{data["video_id"]} has {len(data["matches"])} matches.')

    return result

def single_word(transcript: list[dict[str, str | list[str]]], query: str) -> list[int]:
    """
    Finds the indexes of the query in the transcript
        topic_path = publisher.topic_path("ScriptSearch", "YoutubeURLs")
    Args:
        transcript (list[dict[str, list[dict[str, list[str]|str]]]]): The transcript data
        query (str): The query

    Returns:
        List[int]: The indexes of the query
    """
    indexes = []
    for i, snippet in enumerate(transcript):
        if query in snippet.casefold():
            indexes.append(i)
    return indexes


def multi_word(transcript: list[dict[str, str | list[str]]], words: list[str]) -> list[int]:
    """
    Finds the indexes of the query in the transcript

    Args:
        transcript (list[dict[str, list[dict[str, list[str]|str]]]]): The transcript data
        words (list[str]): The query words

    Returns:
        list[int]: The indexes of the query
    """

    indexes = []
    for i, tokens in enumerate(transcript):
        casefolded = tokens.casefold()

        if not casefolded:
            continue

        index_not_found = 0
        for word in words:
            if word not in casefolded:
                break
            index_not_found += 1
        
        # All words are found in the current snippet
        if index_not_found == len(words):
            indexes.append(i)
            continue

        next_casefolded = [word.casefold() for word in transcript[i + 1]] if i + 1 < len(transcript) else None
        if next_casefolded:
            if all(word in casefolded or word in next_casefolded for word in words[index_not_found:]):
                indexes.append(i)
        elif all(word in casefolded for word in words[index_not_found:]):
            indexes.append(i)
    return indexes


def find_indexes(transcript: list[dict[str, str | list[str]]], query: str) -> list[int]:
    """
    Finds the indexes of the query in the transcript

    Args:
        transcript (list[dict[str, list[dict[str, list[str]|str]]]]): The transcript data
        query (str): The query

    Returns:
        list[int]: The indexes of the query
    """

    debug(f"Finding indexes of {query} in transcript.")
    query = query.casefold()
    words = query.split()

    if len(words) > MAX_QUERY_WORD_LIMIT:
        raise ValueError(f"""Query is too long. Please limit to
                         {MAX_QUERY_WORD_LIMIT} words or less.""")

    return single_word(transcript, query) \
        if len(words) == 1 \
        else multi_word(transcript, words)


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

    pattern = re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
    return pattern.sub(r"<mark>\g<0></mark>", sentence)
