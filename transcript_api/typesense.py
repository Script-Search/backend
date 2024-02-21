import functions_framework
import typesense
import os

TYPESENSE_HOST = os.environ.get("TYPESENSE_HOST")
TYPESENSE_API_KEY = os.environ.get("TYPESENSE_API_KEY")
# just a quick demo on how to do typesense searching
@functions_framework.http
def typesense_test(request):
    # want request string lol
    request_json = request.get_json(silent=True)
    request_args = request.args
    if request_json and "request" in request_json:
        request = request_json["request"]
    elif request_args and "request" in request_args:
        request = request_args["request"]
    else:
        request = None

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
        "q": request,               # whatever you want to search for
        "query_by": "transcript"    # column(s) you want to search in
        # optional filter_by and sort_by also
    }

    results = client.collections['transcripts'].documents.search(search_parameters)
    return results["hits"]

