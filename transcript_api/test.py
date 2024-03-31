from unittest import TestCase, main
from unittest.mock import patch

from scrape import URLType, init_ydl_client, get_url_type, get_channel_videos, get_playlist_videos

class TestGetURLType(TestCase):
    @patch('scrape.get_url_type')
    def test_get_url_type_video(self, mock_type):
        video_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        mock_type.return_value = URLType.VIDEO
        self.assertEqual(get_url_type(video_url), URLType.VIDEO)

    @patch('scrape.get_url_type')
    def test_get_url_type_playlist(self, mock_type):
        playlist_url = "https://www.youtube.com/playlist?list=PLBRObSmbZluRiGDWMKtOTJiLy3q0zIfd7"
        mock_type.return_value = URLType.PLAYLIST
        self.assertEqual(get_url_type(playlist_url), URLType.PLAYLIST)

    @patch('scrape.get_url_type')
    def test_get_url_type_channel(self, mock_type):
        channel_url = "https://www.youtube.com/@jawed"
        mock_type.return_value = URLType.CHANNEL
        self.assertEqual(get_url_type(channel_url), URLType.CHANNEL)

class TestExtractVideos(TestCase):
    @patch('scrape.get_channel_videos')
    def test_get_channel_videos(self, mock_type):
        channel_url = "https://www.youtube.com/@jacksepticeye"
        expected_channel_id = "UCYzPXprvl5Y-Sf0g4vX-m6g"
        mock_type.return_value = tuple
    
        init_ydl_client()
        channel_id, video_urls, video_ids = get_channel_videos(channel_url)

        self.assertIsInstance(channel_id, str)
        self.assertEqual(channel_id, expected_channel_id)

        self.assertIsInstance(video_urls, list)
        self.assertIsInstance(video_urls[0], str)
        self.assertEqual(len(video_urls), 250)

        self.assertIsInstance(video_ids, list)
        self.assertIsInstance(video_ids[0], str)
        self.assertEqual(len(video_ids), 250)

        self.assertEqual(len(video_urls), len(video_ids))

    @patch('scrape.get_playlist_videos')
    def test_get_playlist_videos(self, mock_type):
        playlist_url = "https://www.youtube.com/playlist?list=PLBRObSmbZluRiGDWMKtOTJiLy3q0zIfd7"
        mock_type.return_value = tuple

        init_ydl_client()
        video_urls, video_ids = get_playlist_videos(playlist_url)

        self.assertIsInstance(video_urls, list)
        self.assertIsInstance(video_urls[0], str)
        self.assertEqual(len(video_urls), 72)

        self.assertIsInstance(video_ids, list)
        self.assertIsInstance(video_ids[0], str)
        self.assertEqual(len(video_ids), 72)

        self.assertEqual(len(video_urls), len(video_ids))

if __name__ == '__main__':
    main()

