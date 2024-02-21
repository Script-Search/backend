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

  # response["hits"][i]["highlights"][j] gives specific highlight for the j-th match in the i-th document
  #     seems document ordering is reverse chronological based on insert time (or maybe its random lol)
  #     ...["indices"] will give list of indices of the match(es)

  transcript_matches = response["hits"][0]["highlights"][0]

  headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,PATCH,UPDATE,FETCH,DELETE',
  }
  return (transcript_matches, 200, headers)