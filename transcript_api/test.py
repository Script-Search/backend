from unittest import TestCase, main
from unittest.mock import patch

from helpers import distribute
from scrape import *
from search import * 
from settings import *

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

    @patch('scrape.get_url_type')
    def test_get_url_type_invalid(self, mock_type):
        invalid_url = r"https://www.google.com"
        with self.assertRaises(ValueError):
            get_url_type(invalid_url)

class TestExtractVideos(TestCase):
    @patch('scrape.get_video')
    def test_get_video(self, mock_type):
        video_url = r"https://www.youtube.com/watch?v=2rkAL9ehPq8"
        mock_type.return_value = str

        video_id = get_video(video_url)

        self.assertEqual(video_id, "2rkAL9ehPq8")

    @patch('scrape.get_playlist_videos')
    def test_get_playlist_videos(self, mock_type):
        playlist_url = r"https://www.youtube.com/playlist?list=PLBRObSmbZluRiGDWMKtOTJiLy3q0zIfd7"
        mock_type.return_value = tuple

        init_ydl_client()
        video_ids = get_playlist_videos(playlist_url)

        self.assertIsInstance(video_ids, list)
        self.assertIsInstance(video_ids[0], str)
        self.assertEqual(len(video_ids), 72)

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

    @patch('scrape.get_channel_videos')
    def test_get_channel_videos_no_shorts(self, mock_type):
        channel_url = r"https://www.youtube.com/@OverSimplified"
        expected_channel_id = r"UCNIuvl7V8zACPpTmmNIqP2A"
        mock_type.return_value = tuple

        init_ydl_client()
        channel_id, video_ids = get_channel_videos(channel_url)
        self.assertIsInstance(channel_id, str)
        self.assertEqual(channel_id, expected_channel_id)

        self.assertIsInstance(video_ids, list)
        self.assertIsInstance(video_ids[0], str)
        self.assertEqual(len(video_ids), 32)

    @patch('scrape.get_channel_videos')
    def test_get_empty_channel_videos(self, mock_type):
        channel_url = r"https://www.youtube.com/@huylai2024"
        self.assertRaises(ValueError, get_channel_videos, channel_url)

class TestProcessUrl(TestCase):
    @patch('scrape.process_url')
    def test_process_url_video(self, mock_type):
        video_url = r"https://www.youtube.com/watch?v=jNQXAC9IVRw"
        mock_type.return_value = dict

        result = process_url(video_url)

        self.assertTrue("video_ids" in result)
        self.assertEqual(len(result["video_ids"]), 1)

        self.assertTrue("channel_id" in result)
        self.assertIsNone(result["channel_id"])

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

class TestHelpers(TestCase):
    @patch('helpers.distribute')
    def test_distribute(self, mock_type):
        num_blocks = 5 
        video_ids = ['c0yuuZO8m2k', 'xqwOyV5smbk', 'YRshnXmNE98', '18WbGcZlwAk', 'kO5GGQYO55E', '7ijG6G-CSu8', 'cCQ2qeQTuOc', 'n18y3FDNuGQ', 'QUXqJrtJKt8', 'GvD0oX5Tzjo', 'eiZ5pGxjzcI', 'h8-9LdW26y0', 'AvIXVkK1qpg', 'V0ew5B7FR4s', '13Ul-P8n4fo', '36edJh-Ui8w', 'TkNlrKcWzm4', 'ZEhguiVoqpc', 'T4g3C1kDETI', 'n5VOcqSt_7A', 'lL_CEWRcvnU', 'M4Tw8GP4jUs', 'Lv0rBno4qL8', '7Cfak2_meq0', '5FGvoo95mAg', 'lmCt4W8UMLE', '1PvVHOtMvYY', '76uUho_mNeM', '0eEv9sEMJNw', 'rcHcVjnO1gY', 'IypNr1AD3WA', 'Cr7mI7TAVwM', 'T5nV2DSAJtY', '0MUyykKYd_A', 'K2MZINKrr6w', '7K7HeFbd4t8', 'SrX-RPpAYkk', 'eve8V0MhdB8', 'wHSHsSmpoIY', '7kqZEdjLYpM', 'S9O1UGbtwNk', 'HXx2ToETj28', 'lM2IH9OVO8U', 'VWZZYFxPoy0', 'XUIqmEDNG5U', 'YN6wVzJAXD4', 'VF6uJ-sG5Vs', 'EYoRF-3PieE', 'k_yDYjBUWzg', '4SvYSugBMjc', 'vPgNPA1cJrY', 'jWT8C0AtBSY', '5MVbKNV19vQ', 'pE3N517N_-Q', '1dGjzM1asOg', 'mM-L_rmjRxM', 'RzlzmV4KzEY', 'ljKynkWKLew', 'v2YX4RcM9KA', 'RaIChmx0L4Y', 'hRCyLMq4pEg', '55wVYLmf6vs', 'I1uKIizYrtw', 'dN07kwJmTBw', 'txgd6WFs4z8', 'd6-mtiYrVn8', '5gr3y1Z6FbI', 'KGTIsei_lNY', 'gCkM-CbstJg', 'VxKM6rzDsyc', 'IvO2tdjvcvA', 'dJqEfvzVscM', 'n1fC0B1QrmU', 'Bwrx2u_R3fo', 't2xHU8QtI0U', 'fxHujNz2-Ps', 'nICptERl0rI', 'RNZ6JecZ2aM', 'CEnFNkT86iA', 'AtAH44bXbc8', 'Sm2uvwnfewo', 'EmrKgUgpgJg', 'dgB3PxkH9-A', 'n65MjKibbGA', '9-5jwyx9PX0', '-cDaJhiA_14', 'kGp_vJq-2aw', 'vx4CBuOMi_I', 'Eog2o7k3rDE', 'AiTFPXYMjxA', 'rUEPItWpkjw', 'rcjJS3I-vMM', '2VawZHybZaE', 'JTGXckgaSFQ', 'q27sfrkVecU', 'uh-6xdtDwwk', 'fgS1blcp51A', 'f3GRVa_NTMQ', 'LlglgtHBS6k', 'dFERcR5363k', 'QM5m2Uu5RZI', 'Jiz6o1htkX8', 'dUQcCa_-hCE', 'tsp4wb2wPgU', 'lgP8Sa4Ddhc', '82bXVPC_kQ0', 'Ff74UHL0nRE', 'oscLnpX1hwY', '23wEjwu_fGQ', 'GTy7EDP1hdE', 'BGEuwsLFjrk', 'nz187mPALAo', 'Ux77MfHnXpc', 'NrwxVEq625o', 'aI7UOfq1HlI', 'g95SUXXmulc', 'QjOTHPr7jlg', 'lQyN9jdVO0Q', '2qWH_ZoIIMM', 'qNYwHjbVgpM', 'nFLPIC701tk', 'sWtWZsS4-OE', 'UKsGQmkZvGU', 'zbSiaIz23jk', 'BN19jPOI6gc', 'rUwEQHJVKQ8', '9gh3jMBZM-E', 'p9VnrOP61H4', 'T98wkC6mIrs', 'i-f1cLc-0EU', 'KhO7jKBYgkw', 'V__njos2-go', 'zqlKFg6jAZY', 'UBXfxEV6Yc8', '4Gsqceni_as', '33j-y4RYShM', 'XZc8xtAPb4A', 'Wop52Wn6DTM', 'IeytGOkr-6A', 'fz6VenBEJDY', 'yWWf34P0Dxc', 'FU2NZIjG41s', 'ynwHBUCcVBM', 'I_BUebzsVBQ', 'ALQNwOhFJcU', 'eV40Mgqi2M4', 'eHeKVLC46UU', 'oQPy91IsNbw', 'clIfgvFqpTg', '79nR17JDErA', 'mfDOUyCAQPw', 'QHFQjruqV2s', 'k9BCo5lLvE0', 'rPUDq3ad8lI', 'ccJpBXXQ384', 'wnO0H8sBgRY', '2h674E1ei3U', 'VM9ZHb4uJ5g', '9TCtOMKTaMU', 'dSxxsnOc3w0', 'wCGhkB1wGmk', '8vdRsO-Ad_A', 'ayTvInZjIqs', 'NLgzdRNVKWA', '0BUilXBCvDE', '_hSaxgom__M', 'Z5zq5wPG2dg', 'KBjo5A3rN-c', 'JaF84VzEt54', 'lzw4eDvwgrs', 'J6E0AuWUAwU', 'SLzlOznq8Qo', 'jocTiBV923U', 'nQjrM9Sl6Gg', '4cIGUpedGOw', 'ldMtM6hOm3E', 'Ud-5L9h5nrc', 'FIUxXmcZlnI', 'SMatb23ASzY', 'noVqSnU_I0Q', 'uM7RfeRcPz4', '0YGT60oO3FQ', '7Oc67Bos9_s', 'TyaHveKt6TM', 'CYyIV66yiFs', 'h0XhJUSE6X8', 'JzKtwQzTFQ4', 'bE3NjeAfVlk', 'ACRLdLQQ-FQ', 'ScCyy_Cux-w', 'rJsF9h0m8T4', 'Jazi8Z4sFcw', '963E0dTaXAE', 'liACqm2Y5tM']

        result = distribute(video_ids, num_blocks)
        self.assertEqual(len(result), num_blocks)
        self.assertEqual(len(result[0]), 194//num_blocks + 1)
        self.assertEqual(len(result[1]), 194//num_blocks + 1)
        self.assertEqual(len(result[2]), 194//num_blocks + 1)
        self.assertEqual(len(result[3]), 194//num_blocks + 1)
        self.assertEqual(len(result[4]), 194//num_blocks)

class TestMarkWord(TestCase):
    @patch('search.mark_word')
    def test_mark_word(self, mocktype):
        word = re.compile(r"\b" + re.escape("game") + r"\b", re.IGNORECASE)
        text = "This is a game"
        result = mark_word(text, word)
        self.assertEqual(result, "This is a <mark>game</mark>")

class TestSearch(TestCase):
    @patch('search.search_typesense')
    def test_search_single_no_filter(self, mocktype):
        mocktype.return_value = dict
        copy_search_params = TYPESENSE_SEARCH_PARAMS.copy()
        copy_search_params["q"] = "game"

        result = search_typesense(copy_search_params)
        self.assertIsNotNone(result)
        self.assertTrue("video_id" in result[0])
        self.assertTrue("channel_id" in result[0])
        self.assertTrue("title" in result[0])
        self.assertTrue("channel_name" in result[0])
        self.assertTrue("matches" in result[0])

        self.assertIsNotNone(result[0]["matches"])

    @patch('search.search_typesense')
    def test_search_phrase_no_filter(self, mocktype):
        mocktype.return_value = dict
        copy_search_params = TYPESENSE_SEARCH_PARAMS.copy()
        copy_search_params["q"] = "dynamic programming"

        result = search_typesense(copy_search_params)
        self.assertIsNotNone(result)
        self.assertTrue("video_id" in result[0])
        self.assertTrue("channel_id" in result[0])
        self.assertTrue("title" in result[0])
        self.assertTrue("channel_name" in result[0])
        self.assertTrue("matches" in result[0])
        
        self.assertIsNotNone(result[0]["matches"])

    @patch('search.search_typesense')
    def test_search_single_filter_channel(self, mocktype):
        mocktype.return_value = dict
        copy_search_params = TYPESENSE_SEARCH_PARAMS.copy()
        copy_search_params["q"] = "game"
        copy_search_params["filter_by"] = "channel_id:UCYzPXprvl5Y-Sf0g4vX-m6g"

        result = search_typesense(copy_search_params)
        self.assertIsNotNone(result)
        self.assertTrue("video_id" in result[0])
        self.assertTrue("channel_id" in result[0])
        self.assertTrue("title" in result[0])
        self.assertTrue("channel_name" in result[0])
        self.assertTrue("matches" in result[0])

        self.assertIsNotNone(result[0]["matches"])

    @patch('search.search_typesense')
    def test_search_phrase_filter_channel(self, mocktype):
        mocktype.return_value = dict
        copy_search_params = TYPESENSE_SEARCH_PARAMS.copy()
        copy_search_params["q"] = "dynamic programming"
        copy_search_params["filter_by"] = "channel_id:UC_mYaQAE6-71rjSN6CeCA-g"

        result = search_typesense(copy_search_params)
        self.assertIsNotNone(result)
        self.assertTrue("video_id" in result[0])
        self.assertTrue("channel_id" in result[0])
        self.assertTrue("title" in result[0])
        self.assertTrue("channel_name" in result[0])
        self.assertTrue("matches" in result[0])
        
        self.assertIsNotNone(result[0]["matches"])

    @patch('search.search_typesense')
    def test_search_single_filter_playlist(self, mocktype):
        mocktype.return_value = dict
        copy_search_params = TYPESENSE_SEARCH_PARAMS.copy()
        copy_search_params["q"] = "game"
        copy_search_params["video_ids"] = '["0baCL9wwJTA","RRP_GFSGrDA","gOFrQs_13mQ","dXBapNjnab4","StSGz5dx52s","kAT_xX-Xk6c","YlQ53oOQPRo","-pb7MrRnPv0","-pVg8ZnSARo","mVTbjsQbG1w","e5e1z3A3cfo","3-LJtJKYXrA","B_NscD2IECQ","DzioXvXd5fE","VUQs9prUia0","T0LYsNXkUX0","cz9ATZecggQ","2WKfYPAP5DQ","EYiil5yOHjQ","D1jTOSrwpOQ","9xgtuRqBS5A","mjfpixY7WdE","ecf7vPw8A2o","m9-mg4m6IW4","7vEXqbPCgao","RTSMxUsh3-g","HKx_VfcPJlU","Y1xzL8I9sAE","X0J2Lq2z2Vk","i__ZXVjCl_I","0JhTJRl4uew","X0xRJRF-g5w","ZaA7CqEK5Cc","QP3zjbr_U28","4u9KktKMLUg","1gfCG4bYVYM","npxaoLRfeXA","Y2_CN0StX5U","-UyZeZAeXPw","j1-D08FV780","AVFlqoQjh1M","2w_NQXb2KX4","3UC9qVNtCag","hQX0_MoBe9s","HP_BwlBgLb4","HYGIfWNe4NE","sZ6hp3keToo","R6rf2RPAe7s","aynVOIjCXvU","a5XKyiaw97c","Bb4dhojfB0o","RO0yTly_fqo","ivxXd__504o","bTbmOAbmrUk","kyW1Mo_uCDg","KhHIBFgaMCc","vlhsz5flDs4","4y_c2aCQ9hY","eACSzFJpetI","8_8BSdyEwoM","ZYSu2xg5c5w","qK1oN9dBs5A","89ZycCcH7sc","JU4qoXp3Sec","qjrwwV-bMTI","ujO3XtcPZ_4","LJBsRgSaVLU","i61Wcnjq-0Q","Lshh01K5JyI","zHACgmQkw3Q","qbJhi5Y0pLE","Z47RnEMnniQ"]'
    
        result = search_typesense(copy_search_params)
        self.assertIsNotNone(result)
        self.assertTrue("video_id" in result[0])
        self.assertTrue("channel_id" in result[0])
        self.assertTrue("title" in result[0])
        self.assertTrue("channel_name" in result[0])
        self.assertTrue("matches" in result[0])

        self.assertIsNotNone(result[0]["matches"])

    @patch('search.search_playlist')
    def test_search_phrase_filter_playlist(self, mocktype):
        mocktype.return_value = dict
        copy_search_params = TYPESENSE_SEARCH_PARAMS.copy()
        copy_search_params["q"] = "dynamic programming"
        copy_search_params["video_ids"] = '["KLlXCFG5TnA", "1pkOgXD63yU", "3OamzN90kPg", "bNvIQI2wAjk", "5WZl3MMT0Eg", "lXVy6YWFcRM", "nIVW4P8b1VA", "U8XENwh8Oy8", "jzZsG8n2R9A", "UuiTKBwPgAo", "5Km3utixwZs", "RyBM56RIWrM", "WnPLSRLSANE", "UcoN6UjAI64", "Y0lT9Fck7qI", "H9bfqozjoqs", "cjWnW0hdF1Y", "Ua0GhsJSlWM", "Sx9NNgInc3A", "GBKI9VSKdGg", "73r3KWiEvyk", "rWAJCfYYOvM", "6aEyTjOwlJU", "IlEsdxuD4lY", "Yan0cv2cLy8", "mQeF6bN8hMk", "EgI5nU9etnU", "s-VkcjHqkGI", "pV2kpPD66nE", "P6RZZMu_maU", "6kTZYvNNyps", "bXsUuownnoQ", "8f1XPm4WOUc", "A8NUOmlwOlM", "44H3cEC2fFM", "nONCGxWoUfM", "PaJxqZVPhbg", "FdzJmTCVyJU", "G0_I-ZF0S38", "gBTe7lFR3vc", "XIdigk956u0", "q5a5OiGbT6Q", "XVuQxVej6y8", "S5bfdUTrKLM", "T41rL0L3Pnw", "BJnMZNwUk1M", "fMSJSS7eO1w", "pfiQ_PS1g8E", "wiGpQwVHdE0", "gqXU1UyA8pk", "jSto0O4AJbM", "vzdNOK2oB2E", "WTzjTskDFMg", "jJXJ16kPFWg", "XYQecbcd6_c", "4RACzI5-du8", "B1k_sxOSgv8", "hTM3phVI6YQ", "vRbbcKXCxOw", "OnSn2XEQ4MY", "Hr5cWUld4vU", "6ZnyEApgFYg", "u4JAi2JJhI8", "E36O5SWp-LE", "ihj4IQGZ2zc", "s6ATEkipzow", "5LUXSvjmGCw", "gs2LMfuOR9k", "oobqoCJlHA0", "BTf05gs_8iU", "asbcE9mZz_U", "YPTqKIgVk-k", "itmhHWaHupI", "9UtInBqnCgA", "gVUrDV4tZfY"]'

        result = search_typesense(copy_search_params)
        self.assertIsNotNone(result)
        self.assertTrue("video_id" in result[0])
        self.assertTrue("channel_id" in result[0])
        self.assertTrue("title" in result[0])
        self.assertTrue("channel_name" in result[0])
        self.assertTrue("matches" in result[0])

        self.assertIsNotNone(result[0]["matches"])

    @patch('search.search_playlist')
    def test_search_phrase_multi_line(self, mocktype):
        copy_search_params = TYPESENSE_SEARCH_PARAMS.copy()
        copy_search_params["q"] = "mega knight"

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

        result = search_playlist(copy_search_requests, copy_search_param)
        self.assertIsNotNone(result)

if __name__ == '__main__':
    main()
