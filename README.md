# CSCE 482 ScriptSearch 🔍

For transcript-api, all the packages and libraries required can be found in `transcript_api/requirements.txt`.
This code is meant to run on a google cloud function but can be emulated on a local machine via the following method.
First create a python virtual environment within the transcript api folder using the following command:
```bash
python3 -m venv venv
```

Then activate the virtual environment with the following command:
```bash
source ./venv/bin/activate
```

Then install all the dependencies within the virtual environment by running the following command:
```
./venv/bin/python3 -m pip install -r requirements.txt
```

Then start a local functions framework server by running the following command:
```bash
functions-framework --target=transcript_api --port 8080
```

Then to interact with the backend use several curl commands:
```bash
curl -X POST -H "Content-Type: application/json" -d "{"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"}" http://localhost:8080
curl -X POST -H "Content-Type: application/json" -d "{"query": "dynamic programming"}" http://localhost:8080
curl -X POST -H "Content-Type: application/json" -d "{"query": "dynamic programming", "channel_id": "UC_mYaQAE6-71rjSN6CeCA-g"}" http://localhost:8080
curl -X POST -H "Content-Type: application/json" -d "{"query": "dynamic programming", "video_ids": '["0baCL9wwJTA","RRP_GFSGrDA","gOFrQs_13mQ","dXBapNjnab4","StSGz5dx52s"]'}" http://localhost:8080
```

These curls emulate the four possible interaction states: populating the database, searching with no filter, searching with a channel filter, and searching with a playlist filter.
Feel free to change the various arguments to search a filter differently.


Within the functions folder there are 4 core functions integral to the scraping pipeline. This code is also meant to run in a cloud environment in a google cloud function, but should be able to be spun up rather simply. The end user needs to navigate to the function directory they're interested in and run cmd/main.go, which will spin up a server instance. Then, they'll be able to make a cURL request to the localhost:8080 url using some payload.

It's important to note that all of the functions are event-driven by pub/sub, which means that the user must base64 encode the data. This may be cumbersome to do within the command line, and may be easier to write a script for it such as below:
```python
import requests
import json
import base64

# The URL to send the POST request to
url = "http://localhost:8080"

# The headers for the POST request
headers = {
    "Content-Type": "application/cloudevents+json"
}

# The data you want to send, originally as an array of objects
data_array = [
    "KBZlN0izeiY"
]

# Convert the data array to a JSON string
json_string = json.dumps(data_array)

# Base64 encode the JSON string
encoded_data = base64.b64encode(json_string.encode()).decode()

# Create the payload with the encoded data
payload = {
    "specversion": "1.0",
    "type": "example.com.cloud.event",
    "source": "https://example.com/cloudevents/pull",
    "subject": "123",
    "id": "A234-1234-1234",
    "time": "2018-04-05T17:31:00Z",
    "data": {
        "Message": {
            "Data": encoded_data
        }
    }
}

# Sending the POST request
response = requests.post(url, headers=headers, data=json.dumps(payload))

# Printing the response from the server
print(response.status_code)
print(response.text)

```
