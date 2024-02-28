import yt_dlp

limit = 250
ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'extractor_args': {
            'youtube': {
                'playlistend': limit
                }
            }
        }

ydl = yt_dlp.YoutubeDL(ydl_opts)

def get_playlist_videos(playlist_url):
    playlist = ydl.extract_info(playlist_url, download=False)
    video_urls = [ entry["url"] for entry in playlist["entries"] ]

    return video_urls

def get_channel_videos(channel_url):
    channel = ydl.extract_info(channel_url, download=False)
    video_urls = [ entry["url"] for entry in channel["entries"][0]["entries"] ]

    return video_urls

def main():
    # playlist_url = "https://youtube.com/playlist?list=PL94lfiY18_CgWGQzweD_aVjsFXiRi6kn5&si=UmiI8Ou09GHXwo6n"
    channel_url = "https://www.youtube.com/@PewDiePie"
    # video_urls = get_playlist_videos(playlist_url)
    video_urls = get_channel_videos(channel_url)

    for url in video_urls:
        print(url)
    print(len(video_urls))

if __name__ == "__main__":
    main()

