import unittest
import time
from unittest.mock import patch, MagicMock
from app import app

class TestNewsApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.feedparser.parse')
    def test_home_page_success(self, mock_parse):
        # Mock RSS Feed
        mock_feed = MagicMock()
        mock_feed.entries = [
            MagicMock(title="Test Article 1", link="http://example.com/1", published="Mon, 01 Jan 2026", published_parsed=time.gmtime(1767225600)),
            MagicMock(title="Test Article 2", link="http://example.com/2", published="Mon, 02 Jan 2026", published_parsed=time.gmtime(1767312000))
        ]
        mock_parse.return_value = mock_feed
        
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Article 1', response.data)
        self.assertIn(b'Test Article 2', response.data)
        self.assertIn(b'/article?url=http%3A//example.com/1', response.data)

    @patch('app.feedparser.parse')
    def test_article_page_success(self, mock_parse):
        # Mock HTML Content in RSS Entry
        html_content = """
            <p>This is the <span>real</span> content.&nbsp;With a non-breaking space and "quotes".</p>
            <a href="http://other.com">Link Text</a>
            <form><input type="text"></form>
            <figure>
                <img src="pic.jpg">
                <figcaption>A picture</figcaption>
            </figure>
            <div class="extra">More text</div>
        """
        
        # Mock Entry - use a class that supports 'in' operator and attribute access
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
        
        response = self.app.get('/article?url=http://example.com/article')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<title>Real Page Title</title>', response.data)
        self.assertIn(b'By Test Author', response.data)
        self.assertIn(b'real', response.data)
        
        # Check for non-breaking space replacement
        self.assertNotIn(b'&nbsp;', response.data)
        self.assertNotIn(b'\xa0', response.data)

        # Check for quote escaping (Expected to fail until implemented)
        self.assertIn(b'&quot;quotes&quot;', response.data)
        
        # Verify cleaning
        self.assertNotIn(b'<script>', response.data)
        self.assertNotIn(b'<img', response.data)
        self.assertNotIn(b'<div', response.data)
        self.assertNotIn(b'<span', response.data)

    def test_article_page_missing_url(self):
        response = self.app.get('/article')
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'No URL provided', response.data)

    @patch('app.feedparser.parse')
    def test_article_not_found(self, mock_parse):
        mock_feed = MagicMock()
        mock_feed.entries = []
        mock_parse.return_value = mock_feed
        
        response = self.app.get('/article?url=http://unknown.com')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'Article not found', response.data)

if __name__ == '__main__':
    unittest.main()
