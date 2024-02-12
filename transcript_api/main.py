import functions_framework
from flask import jsonify

@functions_framework.http
def transcript_api(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    request_json = request.get_json(silent=True)
    request_args = request.args

    if request_json and "request" in request_json:
        request = request_json["request"]
    elif request_args and "request" in request_args:
        request = request_args["request"]
    else:
        request = None
    
    data = {
        "request": request
    }

    return jsonify(data)
