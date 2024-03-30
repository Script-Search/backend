from firebase_admin import credentials, firestore, initialize_app

test_collection = None

def initialize_firestore() -> None:
    """Uses lazy-loading to initialize the firestore client and collection
    """
    global test_collection
    if test_collection == None:
        cred = credentials.Certificate("credentials.json")
        initialize_app(cred)
        db = firestore.client()
        test_collection = db.collection("test")

def upsert(document):
    doc_ref = test_collection.document(document["video_id"])
    doc_ref.set(document)