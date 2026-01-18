import unittest
from unittest.mock import patch, MagicMock
from app import app

class TestNewsApp(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch('app.requests.get')
    def test_home_page_success(self, mock_get):
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "title": "Test Article",
                    "url": "http://example.com",
                    "source": "Test Source",
                    "published_at": "2023-10-27T10:00:00Z",
                    "description": "Test description"
                }
            ]
        }
        mock_get.return_value = mock_response

        with patch('app.API_TOKEN', 'fake_token'):
            response = self.app.get('/')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Test Article', response.data)
            
            # Verify that headers include our additions
            args, kwargs = mock_get.call_args
            self.assertIn('User-Agent', kwargs['headers'])

    def test_missing_api_token(self):
        with patch('app.API_TOKEN', None):
            response = self.app.get('/')
            self.assertEqual(response.status_code, 500)
            self.assertIn(b'API_TOKEN is missing', response.data)

    @patch('app.requests.get')
    def test_api_error(self, mock_get):
        with patch('app.API_TOKEN', 'fake_token'):
            # Mock connection error
            import requests
            mock_get.side_effect = requests.exceptions.RequestException("Connection refused")
            
            response = self.app.get('/')
            self.assertEqual(response.status_code, 502)
            self.assertIn(b'Error fetching news', response.data)

if __name__ == '__main__':
    unittest.main()
