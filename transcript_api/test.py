from unittest import TestCase, main
from unittest.mock import patch

from helpers import distribute
from scrape import URLType, init_ydl_client, get_url_type, get_channel_videos, get_playlist_videos, get_video, process_url
from search import search_typesense, search_playlist, mark_word
from settings import MAX_VIDEO_LIMIT, TYPESENSE_SEARCH_PARAMS, TYPESENSE_SEARCH_REQUESTS

class TestGetURLType(TestCase):
    @patch('scrape.get_url_type')
    def test_get_url_type_video(self, mock_type):
        video_url = r"https://www.youtube.com/watch?v=jNQXAC9IVRw"
        mock_type.return_value = URLType.VIDEO
        self.assertEqual(get_url_type(video_url), URLType.VIDEO)

    @patch('scrape.get_url_type')
    def test_get_url_type_playlist(self, mock_type):
        playlist_url = r"https://www.youtube.com/playlist?list=PLBRObSmbZluRiGDWMKtOTJiLy3q0zIfd7"
        mock_type.return_value = URLType.PLAYLIST
        self.assertEqual(get_url_type(playlist_url), URLType.PLAYLIST)

    @patch('scrape.get_url_type')
    def test_get_url_type_channel(self, mock_type):
        channel_url = r"https://www.youtube.com/@jawed"
        mock_type.return_value = URLType.CHANNEL
        self.assertEqual(get_url_type(channel_url), URLType.CHANNEL)

class TestExtractVideos(TestCase):
    @patch('scrape.get_channel_videos')
    def test_get_channel_videos(self, mock_type):
        channel_url = r"https://www.youtube.com/@jacksepticeye"
        expected_channel_id = r"UCYzPXprvl5Y-Sf0g4vX-m6g"
        mock_type.return_value = tuple
    
        init_ydl_client()
        channel_id, video_ids = get_channel_videos(channel_url)

        self.assertIsInstance(channel_id, str)
        self.assertEqual(channel_id, expected_channel_id)

        self.assertIsInstance(video_ids, list)
        self.assertIsInstance(video_ids[0], str)
        self.assertEqual(len(video_ids), MAX_VIDEO_LIMIT)

    @patch('scrape.get_playlist_videos')
    def test_get_playlist_videos(self, mock_type):
        playlist_url = r"https://www.youtube.com/playlist?list=PLBRObSmbZluRiGDWMKtOTJiLy3q0zIfd7"
        mock_type.return_value = tuple

        init_ydl_client()
        video_ids = get_playlist_videos(playlist_url)

        self.assertIsInstance(video_ids, list)
        self.assertIsInstance(video_ids[0], str)
        self.assertEqual(len(video_ids), 72)

    @patch('scrape.get_video')
    def test_get_video(self, mock_type):
        video_url = r"https://www.youtube.com/watch?v=qaKbCsV53sg"
        mock_type.return_value = str

        video_id = get_video(video_url)
        print(video_id)

        self.assertEqual(video_id, "qaKbCsV53sg")

class TestProcessUrl(TestCase):
    @patch('scrape.process_url')
    def test_process_url_playlist(self, mock_type):
        playlist_url = r"https://www.youtube.com/playlist?list=PLBRObSmbZluRiGDWMKtOTJiLy3q0zIfd7"
        mock_type.return_value = dict

        result = process_url(playlist_url)

        self.assertTrue("video_ids" in result)
        self.assertIsNotNone(result["video_ids"])
        self.assertEqual(len(result["video_ids"]), 72)

        self.assertTrue("channel_id" in result)
        self.assertIsNone(result["channel_id"])

    @patch('scrape.process_url')
    def test_process_url_channel(self, mock_type):
        channel_url = r"https://www.youtube.com/@jacksepticeye"
        mock_type.return_value = dict

        result = process_url(channel_url)

        self.assertTrue("video_ids" in result)
        self.assertIsNone(result["video_ids"])

        self.assertTrue("channel_id" in result)
        self.assertEqual(result["channel_id"], "UCYzPXprvl5Y-Sf0g4vX-m6g")

    @patch('scrape.process_url')
    def test_process_url_video(self, mock_type):
        video_url = r"https://www.youtube.com/watch?v=jNQXAC9IVRw"
        mock_type.return_value = dict

        result = process_url(video_url)

        self.assertTrue("video_ids" in result)
        self.assertEqual(len(result["video_ids"]), 1)

        self.assertTrue("channel_id" in result)
        self.assertIsNone(result["channel_id"])

class TestHelpers(TestCase):
    @patch('helpers.distribute')
    def test_distribute(self, mock_type):
        playlist_url = r"https://www.youtube.com/playlist?list=PLmYjNW5fJqQyW4dEwB_-f7LKKNr8pCE95"
        
        init_ydl_client()
        video_ids = get_playlist_videos(playlist_url)
        self.assertEqual(len(video_ids), 194)

        result = distribute(video_ids, 5)
        self.assertEqual(len(result), 5)
        self.assertEqual(len(result[0]), 194//5 + 1)
        self.assertEqual(len(result[1]), 194//5 + 1)
        self.assertEqual(len(result[2]), 194//5 + 1)
        self.assertEqual(len(result[3]), 194//5 + 1)
        self.assertEqual(len(result[4]), 194//5)

class TestSearch(TestCase):
    @patch('search.search_typesense')
    def test_search_typesense(self, mocktype):
        mocktype.return_value = dict
        copy_search_params = TYPESENSE_SEARCH_PARAMS.copy()
        copy_search_params["q"] = "\"game\""

        result = search_typesense(copy_search_params)
        self.assertIsNotNone(result)
        self.assertTrue("video_id" in result[0])
        self.assertTrue("channel_id" in result[0])
        self.assertTrue("title" in result[0])
        self.assertTrue("channel_name" in result[0])
        self.assertTrue("matches" in result[0])

        self.assertIsNotNone(result[0]["matches"])
    
    @patch('search.search_playlist')
    def test_search_playlist(self, mocktype):
        playlist_url = r"https://www.youtube.com/playlist?list=PLBRObSmbZluRiGDWMKtOTJiLy3q0zIfd7"
        mocktype.return_value = dict
        video_ids = get_playlist_videos(playlist_url)
        
        query = "chess"
        copy_search_param = TYPESENSE_SEARCH_PARAMS.copy()
        
        del copy_search_param["drop_tokens_threshold"]
        del copy_search_param["typo_tokens_threshold"]
        del copy_search_param["page"]
        del copy_search_param["filter_by"]
        del copy_search_param["q"]
            
        copy_search_requests = TYPESENSE_SEARCH_REQUESTS.copy() 
        split_video_ids = distribute(video_ids, 5)
        
        
        string_ids = [",".join(ids) for ids in split_video_ids]

        for i, sub_search in enumerate(copy_search_requests["searches"]):
            sub_search["q"] = f"{query}"
            sub_search["filter_by"] = f"video_id:[{string_ids[i]}]"

        print(copy_search_requests)
        result = search_playlist(copy_search_requests, copy_search_param)


if __name__ == '__main__':
    main()

