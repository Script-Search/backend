"""
This script handles the searching function of the transcript-api.
It ___.
"""

import re
from typing import Any, Dict, List, Tuple

from typesense import Client

from helpers import debug
from settings import MAX_QUERY_WORD_LIMIT, TYPESENSE_HOST, TYPESENSE_API_KEY

TYPESENSE_CLIENT = None

def init_typesense():
    global TYPESENSE_CLIENT
    if TYPESENSE_CLIENT == None:
        TYPESENSE_CLIENT = Client({
            "nodes": [{
                "host": TYPESENSE_HOST,
                "port": 443,
                "protocol": "https"
            }],
            "api_key": TYPESENSE_API_KEY,
            "connection_timeout_seconds": 4
        })

def search_typesense(query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Searches for a query in the transcript data.

    Args:
        query (Dict[str, Any]): The query params to use when searching.

    Returns:
        Dict[str, List[Dict[str, Any]]]: The search results.
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

        query_no_quotes = query_params["q"][1:-1] # pylint: disable=E1136
        for index in find_indexes(hit["highlight"]["transcript"], query_no_quotes):
            marked_snippet = mark_word(
                document["transcript"][index], query_no_quotes)
            data["matches"].append(
                {"snippet": marked_snippet, "timestamp": document["timestamps"][index]})

        debug(f'{data["video_id"]} has {len(data["matches"])} matches.')

        result.append(data)
    return result

def single_word(transcript: List[Dict[str, Any]], query: str) -> List[int]:
    """
    Finds the indexes of the query in the transcript
        topic_path = publisher.topic_path("ScriptSearch", "YoutubeURLs")
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
    if len(words) > MAX_QUERY_WORD_LIMIT:
        raise ValueError(f"""Query is too long. Please limit to
                         {MAX_QUERY_WORD_LIMIT} words or less.""")

    words = [word.casefold() for word in words]

    return single_word(transcript, query.casefold()) \
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

    pattern = re.compile(re.escape(word), re.IGNORECASE)
    return pattern.sub(r"<mark>\g<0></mark>", sentence)
