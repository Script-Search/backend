from urllib3 import PoolManager

req_pool = None

def initialize_req_pool() -> None:
    """Uses lazy-loading to initialize the requests pool
    """

    global req_pool
    if req_pool == None:
        req_pool = PoolManager()

def get_ttml_response(ttml_url):
    return req_pool.request("GET", ttml_url)