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

