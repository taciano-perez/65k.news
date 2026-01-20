import unittest
import time
from unittest.mock import patch, MagicMock
import app as app_module

class TestNewsApp(unittest.TestCase):
    def setUp(self):
        self.app = app_module.app.test_client()
        self.app.testing = True

    @patch('app.RSS_FEEDS', [{"name": "TestFeed", "url": "http://test.com/rss"}])
    @patch('app.feedparser.parse')
    def test_home_page_success(self, mock_parse):
        # Mock RSS Feed
        mock_feed = MagicMock()
        mock_feed.entries = [
            MagicMock(title="Article 1", link="http://example.com/1", published="Mon, 01 Jan 2026", published_parsed=time.gmtime(1767225600)),
        ]
        mock_parse.return_value = mock_feed
        
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        # Check for [FeedName] prefix
        self.assertIn(b'[TestFeed] Article 1', response.data)
        # Check for ID based link (0-0 for first feed, first article)
        self.assertIn(b'/article?id=0-0', response.data)

    @patch('app.RSS_FEEDS', [{"name": "TestFeed", "url": "http://test.com/rss"}])
    @patch('app.feedparser.parse')
    def test_article_page_success(self, mock_parse):
        # Mock HTML Content in RSS Entry
        html_content = """<p>Real Content</p>"""
        
        # Mock Entry
        class MockEntry(object):
            def __init__(self, title, link, content_val):
                self.title = title
                self.link = link
                self.author = "Test Author"
                content_item = MagicMock()
                content_item.type = 'text/html'
                content_item.value = content_val
                self.content = [content_item]
                
            def __contains__(self, key):
                return hasattr(self, key)
                
            def get(self, key, default=None):
                return getattr(self, key, default)
                
        mock_entry = MockEntry("Real Page Title", "http://example.com/article", html_content)
        
        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry]
        mock_parse.return_value = mock_feed
        
        # Request with ID 0-0
        response = self.app.get('/article?id=0-0')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<title>Real Page Title</title>', response.data)
        self.assertIn(b'Real Content', response.data)

    def test_article_page_missing_id(self):
        response = self.app.get('/article')
        self.assertEqual(response.status_code, 400)

    def test_article_page_invalid_id_format(self):
        response = self.app.get('/article?id=invalid')
        self.assertEqual(response.status_code, 400)
        
    def test_article_page_invalid_id_values(self):
        response = self.app.get('/article?id=a-b')
        self.assertEqual(response.status_code, 400)

    @patch('app.RSS_FEEDS', [{"name": "TestFeed", "url": "http://test.com/rss"}])
    @patch('app.feedparser.parse')
    def test_article_not_found_feed(self, mock_parse):
        # Request feed ID 999
        response = self.app.get('/article?id=999-0')
        self.assertEqual(response.status_code, 404)

    @patch('app.RSS_FEEDS', [{"name": "TestFeed", "url": "http://test.com/rss"}])
    @patch('app.feedparser.parse')
    def test_article_not_found_entry(self, mock_parse):
        mock_feed = MagicMock()
        mock_feed.entries = [MagicMock()]
        mock_parse.return_value = mock_feed
        
        # Request entry ID 999
        response = self.app.get('/article?id=0-999')
        self.assertEqual(response.status_code, 404)

    @patch('app.RSS_FEEDS', [{"name": "TestFeed", "url": "http://test.com/rss"}])
    @patch('app.feedparser.parse')
    def test_home_page_sorting(self, mock_parse):
        # Mock RSS Feed with two articles in reverse chronological order
        mock_feed = MagicMock()
        mock_feed.entries = [
            MagicMock(title="Old Article", link="http://example.com/old", published="Mon, 01 Jan 2026", published_parsed=time.gmtime(1767225600)),
            MagicMock(title="New Article", link="http://example.com/new", published="Tue, 02 Jan 2026", published_parsed=time.gmtime(1767312000))
        ]
        mock_parse.return_value = mock_feed
        
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Verify that "New Article" appears before "Old Article"
        content = response.data.decode('utf-8')
        new_index = content.find("New Article")
        old_index = content.find("Old Article")
        
        self.assertNotEqual(new_index, -1)
        self.assertNotEqual(old_index, -1)
        self.assertTrue(new_index < old_index, "Newer article should appear before older article")

    @patch('app.RSS_FEEDS', [{"name": "FeedA", "url": "urlA"}, {"name": "FeedB", "url": "urlB"}])
    @patch('app.feedparser.parse')
    def test_feed_filtering(self, mock_parse):
        # Setup mocks - use recent timestamps (2026) to avoid mktime issues on Windows
        feed_a = MagicMock()
        feed_a.entries = [MagicMock(title="Article A", link="linkA", published="Mon, 01 Jan 2026", published_parsed=time.gmtime(1767225600))]
        
        feed_b = MagicMock()
        feed_b.entries = [MagicMock(title="Article B", link="linkB", published="Mon, 01 Jan 2026", published_parsed=time.gmtime(1767225600))]
        
        def side_effect(url):
            if url == "urlA": return feed_a
            if url == "urlB": return feed_b
            return MagicMock(entries=[])
            
        mock_parse.side_effect = side_effect
        
        # Test 1: All feeds enabled (default)
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'[FeedA] Article A', response.data)
        self.assertIn(b'[FeedB] Article B', response.data)
        self.assertIn(b'[x] FeedA', response.data)
        self.assertIn(b'[x] FeedB', response.data)
        
        # Test 2: Feed A disabled
        response = self.app.get('/?disabled=0')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'[FeedA] Article A', response.data)
        self.assertIn(b'[FeedB] Article B', response.data)
        # Check toggle status: FeedA should be [ ] and FeedB [x]
        self.assertIn(b'[ ] FeedA', response.data)
        self.assertIn(b'[x] FeedB', response.data)
        
        # Test 3: Feed B disabled
        response = self.app.get('/?disabled=1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'[FeedA] Article A', response.data)
        self.assertNotIn(b'[FeedB] Article B', response.data)

if __name__ == '__main__':
    unittest.main()