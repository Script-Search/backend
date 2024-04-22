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
from time import perf_counter
from collections.abc import Generator
from typing import Pattern

# Third Party Imports
from typesense import Client

# File System Imports
from helpers import debug
from settings import TYPESENSE_HOST, TYPESENSE_API_KEY 

TYPESENSE_CLIENT: Client = None
cleantext = re.compile(r'[^a-z0-9 ]+')

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

    cleaned_query = cleantext.sub('', search_requests['searches'][0]['q']).lower()
    query_pattern = re.compile(r"\b" + re.escape(search_requests['searches'][0]['q']) + r"\b", re.IGNORECASE)
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
                "matches": process_hit(hit, cleaned_query, query_pattern)
            }

            if data["matches"]:
                result.append(data)
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
    
    start = perf_counter()
    response = TYPESENSE_CLIENT.collections["transcripts"].documents.search(query_params)
    end = perf_counter()
    debug(f"Search took {end - start} seconds.")

    cleaned_query = cleantext.sub('', query_params["q"]).lower()
    query_pattern = re.compile(r"\b" + re.escape(query_params["q"]) + r"\b", re.IGNORECASE)
    result = []
    for hit in response["hits"]:
        data = {
            "video_id": hit["document"]["id"],
            "title": hit["document"]["title"],
            "channel_id": hit["document"]["channel_id"],
            "channel_name": hit["document"]["channel_name"],
            "duration": hit["document"]["duration"],
            "upload_date": hit["document"]["upload_date"],
            "matches": process_hit(hit, cleaned_query, query_pattern)
        }

        if data["matches"]:
            result.append(data)

    return result

def process_hit(hit: dict[str, int|list[dict[str, str|list]]|dict[str, list]], query_no_quotes: str, query_pattern: Pattern) -> list[dict[str, str|int]]:
    """
    Processes the hit data.

    Args:
        hit (dict[str, str|list[str]]): The hit data
        query_no_quotes (str): The query without quotes
        query_pattern (Pattern): The query as a regex pattern

    Returns:
        list[dict[str, str|int]]: The processed hit data
    """

    document = hit["document"]
    marked_snippets = []

    # Preprocess the transcript
    new_transcript = [cleantext.sub('', sentence.lower()) for sentence in document["transcript"]]
    for index, sentence in enumerate(sentence_search(document["transcript"], new_transcript, query_no_quotes, query_pattern)):
        if not sentence: continue

        marked_snippets.append({"snippet": mark_word(sentence, query_pattern), "timestamp": document["timestamps"][index]})

    return marked_snippets

def sentence_search(transcript: list[dict[str, str | list[str]]], new_transcript: list[dict[str, str | list[str]]], query: str, query_pattern: Pattern) -> Generator[str]:
    """
    Returns a sentence if query found (handles multi-word as well)

    Args:
        transcript (list[dict[str, list[dict[str, list[str]|str]]]]): The transcript data
        transcript (list[dict[str, list[dict[str, list[str]|str]]]]): The transcript data, cleaned and preprocessed
        query (str): The query

    Returns:
        Generator[str]: sentence yielded to create a generator (saving memory)
    """
    words = query.split()
    skip_next = False # If this is set to true then we know that previous snippet current sentence
    for i, sentence in enumerate(new_transcript):
        if skip_next:
            skip_next = False
            yield None
            continue
        if len(words) == 1:
            yield transcript[i] if single_word(sentence, query_pattern) else None
        else:
            num_sentences = multi_word(sentence, new_transcript[i+1] if i != len(transcript)-1 else None, query)
            if num_sentences == 1:
                yield transcript[i]
            elif num_sentences == 2:
                skip_next = True
                yield transcript[i] + " " + transcript[i+1]
            else:
                yield None
        
def single_word(sentence: str, query_pattern: Pattern) -> str|None:
    """
    Finds the query within the sentence if it exists
    Args:
        sentence (str): The sentence within the transcript
        query_pattern (Pattern): The query as a regex pattern

    Returns:
        str|None: The sentence if it exists else None
    """
    return re.search(query_pattern, sentence)

def multi_word(sentence: str, next_sentence: str|None, query: str) -> str|None:
    """
    Finds the indexes of the query in the sentences

    Args:
        sentence (str): The current sentence to search for string in
        next_sentence str|None: The next sentence to append to current for searching
        query (str): The query or the phrase to do sorta-exact matching on

    Returns:
        str|None: The sentence if the query exists else None
    """
    if query in sentence:
        return 1
    elif next_sentence and query in (new_sentence := sentence + " " + next_sentence): # walrus operator
        return 2
    return 0

def mark_word(sentence: str, query_pattern: Pattern) -> str:
    """
    Takes every instance of word or phrase within a sentence and wraps it in <mark> tags.
    This algorithm will also ignore cases.

    Args:
        sentence (str): The sentence
        query_pattern (Pattern): The query precompiled

    Returns:
        str: The marked sentence
    """
    return query_pattern.sub(r"<mark>\g<0></mark>", sentence)
