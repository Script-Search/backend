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

import re

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

def search_typesense(query_params: dict[str, object]) -> list[dict[str, str|list[dict[str, str|int]]]]:
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
        words = query_no_quotes.split()
        num_words = len(words)
        for index in find_indexes(hit["highlight"]["transcript"], query_no_quotes):
            transcript_casefoled = document["transcript"][index].casefold()

            if num_words != 1 and not (query_no_quotes in transcript_casefoled):
                document["transcript"][index] += f" {document['transcript'][index + 1]}"

            marked_snippet = document["transcript"][index]
            for word in words:
                marked_snippet = mark_word(marked_snippet, word)

            for i in range(2, MAX_QUERY_WORD_LIMIT):
                marked_snippet = marked_snippet.replace(r"<mark>" * i, "<mark>")
                marked_snippet = marked_snippet.replace(r"</mark>" * i, "</mark>")

            data["matches"].append(
                {"snippet": marked_snippet, "timestamp": document["timestamps"][index]})
        
        if data["matches"]:
            result.append(data)
            debug(f'{data["video_id"]} has {len(data["matches"])} matches.')

    return result

def single_word(transcript: list[dict[str, str|list[str]]], query: str) -> list[int]:
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

def multi_word(transcript: list[dict[str, str|list[str]]], words: list[str]) -> list[int]:
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
        casefolded = [word.casefold() for word in tokens["matched_tokens"]]
        if words[0] in casefolded:
            next_casefolded = [word.casefold() for word in transcript[i + 1]["matched_tokens"]] if i + 1 < len(transcript) else ""
            debug(f"Current Tokens: {casefolded}")
            debug(f"Next Tokens: {next_casefolded}")
            if next_casefolded:
                if all(word in casefolded or word in next_casefolded for word in words[1:]):
                    indexes.append(i)
            elif all(word in casefolded for word in words[1:]):
                    indexes.append(i)
    return indexes

def find_indexes(transcript: list[dict[str, str|list[str]]], query: str) -> list[int]:
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

