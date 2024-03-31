from unittest import TestCase, main
from unittest.mock import patch

from scrape import URLType, get_url_type

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


if __name__ == '__main__':
    main()
