import base64
import time
import functions_framework
import glob
import os
import yt_dlp

from firebase_admin import credentials, firestore, initialize_app
from lxml import etree

ydl_opts = {
    "skip_download": True,
    "writesubtitles": True,
    "writeautomaticsub": True,
    "subtitleslangs": ["en"],
    "subtitlesformat": "ttml",
    'outtmpl': {'default': '%(id)s.%(channel_id)s.%(upload_date)s.%(duration)s'}, # Change output file name
    "quiet": True, # Don't display stuff to the console
}

test_collection = None
ydl = yt_dlp.YoutubeDL(ydl_opts)

def is_valid_subtitle(element):
    return element.tag.endswith('p') and 'begin' in element.attrib and 'end' in element.attrib and element.text

def parse_ttml(ttml_file_name):
    subtitles = []

    with open(ttml_file_name, "rb") as f:
        # Stream processing to not load entire XML tree at once
        for _, element in etree.iterparse(f, events=('end', )):
            if is_valid_subtitle(element):
                text = element.text.strip()
                begin = element.attrib['begin']
                end = element.attrib['end']
                subtitles.append(f"{text} [{begin} - {end}]")

            # Clear element to release memory, can help w/ mem usage
            # element.clear()

            # # Clear parent element to release memory, can help w/ mem usage
            # while element.getprevious() is not None:
            #     del element.getparent()[0]

    return '\n'.join(subtitles)

def insert_transcript(ttml_file_name):
    # global test_collection
    # if test_collection == None:
    #     cred = credentials.Certificate("credentials.json")
    #     initialize_app(cred)
    #     db = firestore.client()
    #     test_collection = db.collection("test")

    # Insert into the database
    try:
        # TODO: Handle potential error where there isn't exactly 1 ttml file
        video_id, channel_id, upload_date, duration, lang, transcript_format = ttml_file_name.split(".")

        parsed_transcript = parse_ttml(ttml_file_name)

        # doc_ref = test_collection.document(video_id)
        # doc_ref.set({
        #     "channel_id": channel_id,
        #     "upload_date": upload_date,
        #     "duration": duration,
        #     "transcript": parsed_transcript
        # })
        return True
    except Exception as e:
        print(f"Error inserting transcript data: {e}")
        return False

# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def transcript_downloader(cloud_event):
    startTime = time.time()
    # URL = base64.b64decode(cloud_event.data["message"]["data"])
    URL = cloud_event.data
    ydl.download(URL)

    # '''
    # TODO: Find a way to keep the info in memory instead of writing locally
    #         - Avoids unnecessary IO operation
    #         - In case of multiple function calls this avoids annoying edge cases
    # '''
    ttml_files = glob.glob("*.ttml")
    ttml_file_name = ttml_files[0] if len(ttml_files) == 1 else None # There could be more if function called for multiple different URLs

    insert_transcript(ttml_file_name)

    os.remove(ttml_file_name) # Cleanup the ttml file to prepare the function for another URL; prevent memory ^^^
    print(f"Elapsed Time: {time.time() - startTime}")