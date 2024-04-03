import json

from google.cloud import pubsub_v1
from google.cloud.pubsub_v1.types import BatchSettings
from google.oauth2 import service_account

PUBLISHER = None
TOPIC_PATH = None

BATCH_SETTINGS = BatchSettings(
    max_messages=1,  # Publish after 1 message
    max_latency=0,   # Try to publish instantly
)

def initialize_pubsub() -> None:
    """Uses lazy-loading to initialize the pubsub client and topic"""
    global PUBLISHER, TOPIC_PATH
    if PUBLISHER is None:
        cred = service_account.Credentials.from_service_account_file(
            "credentials_pub_sub.json")
        PUBLISHER = pubsub_v1.PublisherClient(credentials=cred, batch_settings=BATCH_SETTINGS)
        TOPIC_PATH = PUBLISHER.topic_path("ScriptSearch", "SyncVideoBatch")

def publish(document):
    global PUBLISH, TOPIC_PATH
    byteString = json.dumps(document).encode("utf-8")
    PUBLISHER.publish(TOPIC_PATH, data=byteString) # We don't really need result from this I believe