import os
import sys
import json
from io import BytesIO
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from fetch_tool_info import fetch_github_latest_release


def test_fetch_github_latest_release_success():
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        'tag_name': 'v1.0.0',
        'html_url': 'https://example.com/release',
        'published_at': '2026-01-01T00:00:00Z'
    }).encode('utf-8')
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)

    with patch('urllib.request.urlopen', return_value=mock_response):
        result = fetch_github_latest_release('owner/repo')

    assert result['latest_version'] == 'v1.0.0'
    assert result['release_url'] == 'https://example.com/release'
    assert result['published_at'] == '2026-01-01T00:00:00Z'


def test_fetch_github_latest_release_error():
    from urllib.error import HTTPError
    with patch('urllib.request.urlopen', side_effect=HTTPError(
        'url', 404, 'Not Found', {}, BytesIO(b'not found')
    )):
        result = fetch_github_latest_release('owner/repo')
    assert 'error' in result
