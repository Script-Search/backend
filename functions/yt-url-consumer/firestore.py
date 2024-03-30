import firebase_admin
from firebase_admin import credentials, firestore, initialize_app, get_app

test_collection = None

def initialize_firestore() -> None:
    """Uses lazy-loading to initialize the firestore client and collection
    """
    global test_collection
    if test_collection is None:
        if not firebase_admin._apps:
            cred = credentials.Certificate("credentials.json")
            app = initialize_app(cred)
        else:
            app = get_app()
        
        db = firestore.client(app=app)  # Use the retrieved or initialized app
        test_collection = db.collection("test")

def upsert(document):
    doc_ref = test_collection.document(document["video_id"])
    doc_ref.set(document)