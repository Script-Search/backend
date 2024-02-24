import functions_framework
import os
import typesense

TYPESENSE_API_KEY = os.environ.get("TYPESENSE_API_KEY")
TYPESENSE_HOST = os.environ.get("TYPESENSE_HOST")

@functions_framework.http

def search_typesense(request):
  request_json = request.get_json(silent=True)
  request_args = request.args
  query = None
  if request_json and "request" in request_json:
    query = request_json["request"]
  elif request_args and "request" in request_args:
    query = request_args["request"]
  
  client = typesense.Client({
    'nodes': [{
      'host': TYPESENSE_HOST,
      'port': '443',
      'protocol': 'https'
    }],
    'api_key': TYPESENSE_API_KEY,
    'connection_timeout_seconds': 2
  })

  search_parameters = {
    'q': query,
    'query_by': 'transcript',
  }

  response = client.collections['transcripts'].documents.search(search_parameters)

  # TODO: address edge case where query is at either beginning or end of list element (and thus snippet)

  result = {
    "hits": []
  }
  for doc_hits in response["hits"]:
      # get individual document featuring match
      doc_info = doc_hits["document"]
      # get info from document
      video_id = doc_info["id"]
      channel_id = doc_info["channel_id"]
      title = doc_info["title"]
      channel_name = doc_info["channel_name"]
      # more or less metadata as required ...
      # main concern is list of all timestamps
      all_timestamps = doc_info["timestamps"]

      # iterate through all matches within document
      all_doc_matches = doc_hits["highlights"]
      matches = []
      for doc_match in all_doc_matches:
          match_indices = doc_match["indices"]
          match_snippets = doc_match["snippets"]

          # create list of "mappings" between each match and its timestamp
          # matches = [{"snippet": match_snippets[i], "timestamp": all_timestamps[i]} for i in match_indices]
          for i in range(len(match_indices)):
              index = match_indices[i]
              matches = matches + [{"snippet": match_snippets[i], "timestamp": all_timestamps[index]}]
      

      result["hits"].append({
          "video_id": video_id,
          "title": title,
          "channel_id": channel_id,
          "channel_name": channel_name,
          "matches": matches
      })

  headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,PATCH,UPDATE,FETCH,DELETE',
  }

  return (result, 200, headers)