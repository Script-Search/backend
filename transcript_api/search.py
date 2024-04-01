"""
This script handles the searching function of the transcript-api.
It provides functions to search for specific queries within transcript data
stored in a Typesense database.

Functions:
- init_typesense(): Initializes the Typesense client.
- search_typesense(query_params: Dict[str, Any]) -> List[Dict[str, Any]]: Searches for a query in the transcript data.
- single_word(transcript: List[Dict[str, Any]], query: str) -> List[int]: Finds the indexes of a single-word query in the transcript.
- multi_word(transcript: List[Dict[str, Any]], words: List[str]) -> List[int]: Finds the indexes of a multi-word query in the transcript.
- find_indexes(transcript: List[Dict[str, Any]], query: str) -> List[int]: Finds the indexes of the query in the transcript.
- mark_word(sentence: str, word: str) -> str: Marks every instance of a word within a sentence with <mark> tags.

Dependencies:
- re: Regular expression operations.
- typing: Type hints support.
- typesense: Client for interacting with the Typesense API.
- helpers.debug: Debugging utility.
- settings.MAX_QUERY_WORD_LIMIT: Maximum word limit for a query.
- settings.TYPESENSE_HOST: Hostname of the Typesense server.
- settings.TYPESENSE_API_KEY: API key for accessing the Typesense server.

Global Variables:
- TYPESENSE_CLIENT: Initialized Typesense client instance.

Note:
Ensure that the settings and helpers modules are properly configured before using this module.
"""
from __future__ import annotations

import re

from typing import Any
from typesense import Client

from helpers import debug
from settings import MAX_QUERY_WORD_LIMIT, TYPESENSE_HOST, TYPESENSE_API_KEY

TYPESENSE_CLIENT: Client = None

def init_typesense() -> None:
    """
    Initializes the typesense client.
    """

    global TYPESENSE_CLIENT # pylint: disable=global-statement
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

def search_typesense(query_params: dict[str, str|int|bool]) -> list[dict[str, str|list[dict[str, str|int]]]]:
    """Searches for a query in the transcript data.

    Args:
        query_params (dict[str, str|int|bool]): The query params to use when searching.

    Returns:
        list[dict[str, str|list[dict[str, str|int]]]]: The search results.
    """

    debug(f"Searching for {query_params['q']} in transcripts.")

    init_typesense()
    response = TYPESENSE_CLIENT.collections["transcripts"].documents.search(
        query_params)

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

        query_no_quotes = str(query_params["q"])[1:-1]
        for index in find_indexes(hit["highlight"]["transcript"], query_no_quotes):
            if not (query_no_quotes in document["transcript"][index].casefold()):
                document["transcript"][index] += f" {document['transcript'][index + 1]}"

            marked_snippet = mark_word(
                document["transcript"][index], query_no_quotes)
            data["matches"].append(
                {"snippet": marked_snippet, "timestamp": document["timestamps"][index]})

        debug(f'{data["video_id"]} has {len(data["matches"])} matches.')

        result.append(data)
    return result

def single_word(transcript: list[dict[str, list[dict[str, list[str]|str]]]], query: str) -> list[int]:
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
        casefolded = [word.casefold() for word in snippet["matched_tokens"]]
        if query in casefolded:
            debug(f"Snippet: {snippet}")

            indexes.append(i)
    return indexes

def multi_word(transcript: list[dict[str, list[dict[str, list[str]|str]]]], words: list[str]) -> list[int]:
    """
    Finds the indexes of the query in the transcript

    Args:
        transcript (list[dict[str, list[dict[str, list[str]|str]]]]): The transcript data
        words (list[str]): The query words

    Returns:
        list[int]: The indexes of the query
    """

    indexes = []
    for i, snip in enumerate(transcript):
        snippet = [word.casefold() for word in snip["matched_tokens"]]
        if words[0] in snippet:
            next_snippet = [word.casefold() for word in transcript[i + 1]
                            ["matched_tokens"]] if i + 1 < len(transcript) else ""
            debug(f"Snippet: {snippet}")
            debug(f"Next Snippet: {next_snippet}")
            if next_snippet:
                if all(word in snippet or word in next_snippet for word in words[1:]):
                    indexes.append(i)
            elif all(word in snippet for word in words[1:]):
                    indexes.append(i)
    return indexes

def find_indexes(transcript: list[dict[str, list[dict[str, list[str]|str]]]], query: str) -> list[int]:
    """
    Finds the indexes of the query in the transcript

    Args:
        transcript (list[dict[str, list[dict[str, list[str]|str]]]]): The transcript data
        query (str): The query

    Returns:
        list[int]: The indexes of the query
    """

    debug(f"Finding indexes of {query} in transcript")
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

