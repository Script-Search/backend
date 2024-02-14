from firebase_admin import credentials, firestore, initialize_app
from typing import Dict, Any


def get_transcript(video_id: str) -> Dict[str, Any]:
    cred = credentials.Certificate("credentials.json")
    initialize_app(cred)
    db = firestore.client()
    test = db.collection("test")
    document = test.document(video_id).get()
    return document.to_dict()


def main():
    print(get_transcript("jNQXAC9IVRw"))


if __name__ == "__main__":
    main()
