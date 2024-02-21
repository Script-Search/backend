from google.cloud import pubsub_v1
from google.oauth2 import service_account

def send_url(url: str):
    """
    Sends a video url to Pub/Sub

    Args:
        url (str): Video URL

    Returns:
        None
    """
    cred = service_account.Credentials.from_service_account_file("credentials_pub_sub.json")
    publisher = pubsub_v1.PublisherClient(credentials=cred)
    topic_path = publisher.topic_path("ScriptSearch", "YoutubeURLs")
    data = url.encode("utf-8")

    future = publisher.publish(topic_path, data=data)
    print(future.result())

    return

def main():
    url = "https://www.youtube.com/watch?v=LToM9bAnsyM"
    send_url(url)

if __name__ == "__main__":
    main()

