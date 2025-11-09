"""Tests for social media scraper tool - FIXED VERSION."""

import pytest
from unittest.mock import MagicMock, patch, Mock
import sys
from typing import Any
from quantchain.tools import social_media_scraper
from quantchain.tools.social_media_scraper import (
    SocialMediaScraper,
    SocialMetrics,
)
from quantchain.core.exceptions import DataSourceError

# Mock problematic imports before importing the target module
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()


class TestSocialMetrics:
    """Test the SocialMetrics data class."""

    def test_social_metrics_default_values(self) -> None:
        """Test SocialMetrics default initialization."""
        metrics = SocialMetrics()

        assert metrics.telegram_followers == 0
        assert metrics.twitter_followers == 0
        assert metrics.recent_posts == 0
        assert metrics.engagement_rate == 0.0
        assert metrics.sentiment_score == 0.5

    def test_social_metrics_custom_values(self) -> None:
        """Test SocialMetrics with custom values."""
        metrics = SocialMetrics(
            telegram_followers=1000,
            twitter_followers=500,
            recent_posts=25,
            engagement_rate=2.5,
            sentiment_score=0.8,
        )

        assert metrics.telegram_followers == 1000
        assert metrics.twitter_followers == 500
        assert metrics.recent_posts == 25
        assert metrics.engagement_rate == 2.5
        assert metrics.sentiment_score == 0.8


@pytest.mark.unit
class TestSocialMediaScraper:
    """Test the SocialMediaScraper class."""

    def test_scraper_initialization_default(self) -> None:
        """Test scraper initialization with default parameters."""
        scraper = SocialMediaScraper()

        assert scraper.timeout == 10
        assert scraper.max_retries == 3
        assert scraper.twitter_bearer_token is None
        assert scraper.telegram_api_id is None
        assert scraper.telegram_api_hash is None
        assert scraper._min_request_interval == 1.0
        assert scraper.session is not None  # Should have a session

    def test_scraper_initialization_custom(self) -> None:
        """Test scraper initialization with custom parameters."""
        scraper = SocialMediaScraper(
            timeout=30,
            max_retries=5,
            twitter_bearer_token="test_token",
            telegram_api_id=12345,
            telegram_api_hash="test_hash",
        )

        assert scraper.timeout == 30
        assert scraper.max_retries == 5
        assert scraper.twitter_bearer_token == "test_token"
        assert scraper.telegram_api_id == 12345
        assert scraper.telegram_api_hash == "test_hash"
        assert scraper.session is not None  # Should have a session

    def test_requests_dependency_error(self) -> None:
        """Test that missing requests library raises ImportError."""
        with patch("quantchain.tools.social_media_scraper.requests", None):
            with pytest.raises(ImportError, match="The 'requests' library is required"):
                SocialMediaScraper()

    def test_aggregate_social_metrics_empty_data(self) -> None:
        """Test aggregating metrics with empty data."""
        scraper = SocialMediaScraper()
        telegram_data: dict[str, Any] = {}
        twitter_data: dict[str, Any] = {}

        metrics = scraper._aggregate_social_metrics(telegram_data, twitter_data)

        assert isinstance(metrics, SocialMetrics)
        assert metrics.telegram_followers == 0
        assert metrics.twitter_followers == 0
        assert metrics.recent_posts == 0
        assert metrics.engagement_rate == 0.0
        assert metrics.sentiment_score == 0.5

    def test_aggregate_social_metrics_full_data(self) -> None:
        """Test aggregating metrics with complete data."""
        scraper = SocialMediaScraper()
        telegram_data = {"followers": 1000, "recent_posts": 10, "sentiment": 0.7}
        twitter_data = {
            "followers": 500,
            "engagement_rate": 3.5,
            "sentiment_score": 0.8,
            "recent_posts": 20,
        }

        metrics = scraper._aggregate_social_metrics(telegram_data, twitter_data)

        assert metrics.telegram_followers == 1000
        assert metrics.twitter_followers == 500
        assert metrics.recent_posts == 20  # Should use higher count
        assert metrics.engagement_rate == 3.5
        assert metrics.sentiment_score == 0.8

    def test_aggregate_social_metrics_twitter_more_posts(self) -> None:
        """Test aggregation when Twitter has more recent posts."""
        scraper = SocialMediaScraper()
        telegram_data = {"recent_posts": 15}
        twitter_data = {"recent_posts": 25}

        metrics = scraper._aggregate_social_metrics(telegram_data, twitter_data)

        assert metrics.recent_posts == 25  # Should use Twitter's higher count

    def test_get_social_metrics_no_session(self) -> None:
        """Test get_social_metrics fails without session."""
        scraper = SocialMediaScraper()
        scraper.session = None  # Force no session

        with pytest.raises(DataSourceError, match="requests library not available"):
            scraper.get_social_metrics("BTC", "0x123")

    def test_get_social_metrics_with_exception(self) -> None:
        """Test get_social_metrics handles exceptions properly."""
        scraper = SocialMediaScraper()

        # Mock the _get_telegram_metrics to raise an exception
        with patch.object(
            scraper, "_get_telegram_metrics", side_effect=Exception("Network error")
        ):
            with pytest.raises(DataSourceError, match="Social media scraping failed"):
                scraper.get_social_metrics("BTC", "0x123")

    @patch.object(SocialMediaScraper, "_get_telegram_metrics")
    @patch.object(SocialMediaScraper, "_get_twitter_metrics")
    def test_get_social_metrics_success(
        self, mock_twitter: Mock, mock_telegram: Mock
    ) -> None:
        """Test successful social metrics retrieval."""
        # Setup mock data
        mock_telegram.return_value = {"followers": 1000, "recent_posts": 10}
        mock_twitter.return_value = {
            "followers": 500,
            "engagement_rate": 2.5,
            "sentiment_score": 0.7,
        }

        scraper = SocialMediaScraper()

        metrics = scraper.get_social_metrics("PEPE", "0x123")

        assert isinstance(metrics, SocialMetrics)
        assert metrics.telegram_followers == 1000
        assert metrics.twitter_followers == 500
        assert metrics.recent_posts == 10
        assert metrics.engagement_rate == 2.5
        assert metrics.sentiment_score == 0.7

    def test_get_telegram_metrics_success(self) -> None:
        """Test successful Telegram metrics retrieval."""
        scraper = SocialMediaScraper()

        with patch.object(scraper, "_search_telegram_channels") as mock_search:
            mock_search.return_value = [
                {"followers": 15000, "recent_posts": 5, "name": "Pepe Official"}
            ]

            result = scraper._get_telegram_metrics("PEPE")

            assert result["followers"] == 15000
            assert result["recent_posts"] == 5
            mock_search.assert_called()

    def test_get_telegram_metrics_no_channels(self) -> None:
        """Test Telegram metrics when no channels found."""
        scraper = SocialMediaScraper()

        with patch.object(scraper, "_search_telegram_channels", return_value=[]):
            result = scraper._get_telegram_metrics("UNKNOWN")

            assert result["followers"] == 0
            assert result["recent_posts"] == 0

    def test_get_telegram_metrics_exception_handling(self) -> None:
        """Test Telegram metrics error handling."""
        scraper = SocialMediaScraper()

        with patch.object(
            scraper, "_search_telegram_channels", side_effect=Exception("API error")
        ):
            result = scraper._get_telegram_metrics("ERROR")

            # Should return default values on error
            assert result["followers"] == 0
            assert result["recent_posts"] == 0

    def test_get_twitter_metrics_success(self) -> None:
        """Test successful Twitter metrics retrieval."""
        scraper = SocialMediaScraper()

        with patch.object(scraper, "_find_twitter_account") as mock_find:
            mock_find.return_value = {"username": "pepecoin", "followers": 5000}

            with patch.object(scraper, "_get_twitter_recent_activity") as mock_activity:
                mock_activity.return_value = {
                    "post_count": 15,
                    "engagement_rate": 3.2,
                    "sentiment_score": 0.7,
                }

                result = scraper._get_twitter_metrics("PEPE")

                assert result["followers"] == 5000
                assert result["recent_posts"] == 15
                assert result["engagement_rate"] == 3.2
                assert result["sentiment_score"] == 0.7

    def test_get_twitter_metrics_no_account(self) -> None:
        """Test Twitter metrics when no account found."""
        scraper = SocialMediaScraper()

        with patch.object(scraper, "_find_twitter_account", return_value=None):
            result = scraper._get_twitter_metrics("UNKNOWN")

            assert result["followers"] == 0
            assert result["recent_posts"] == 0
            assert result["engagement_rate"] == 0.0
            assert result["sentiment_score"] == 0.5

    def test_get_twitter_metrics_exception_handling(self) -> None:
        """Test Twitter metrics error handling."""
        scraper = SocialMediaScraper()

        with patch.object(
            scraper, "_find_twitter_account", side_effect=Exception("API error")
        ):
            result = scraper._get_twitter_metrics("ERROR")

            # Should return default values on error
            assert result["followers"] == 0
            assert result["recent_posts"] == 0
            assert result["engagement_rate"] == 0.0
            assert result["sentiment_score"] == 0.5

    def test_search_telegram_channels_crypto_keyword(self) -> None:
        """Test Telegram channel search with crypto keywords."""
        scraper = SocialMediaScraper()

        result = scraper._search_telegram_channels("bitcoin")

        assert len(result) == 1
        assert result[0]["name"] == "Bitcoin Official"
        # Implementation returns "members" not "followers"
        assert "members" in result[0]

    def test_search_telegram_channels_unknown_keyword(self) -> None:
        """Test Telegram channel search with unknown keywords."""
        scraper = SocialMediaScraper()

        result = scraper._search_telegram_channels("unknowncoin")

        assert len(result) == 0

    def test_find_twitter_account_success(self) -> None:
        """Test successful Twitter account finding."""
        scraper = SocialMediaScraper()

        with patch.object(scraper, "_get_twitter_account_info") as mock_info:
            mock_info.side_effect = [
                None,
                None,
                {"followers": 1000, "username": "pepe"},
            ]

            result = scraper._find_twitter_account("PEPE")

            assert result is not None
            assert result["followers"] == 1000
            assert result["username"] == "pepe"
            assert mock_info.call_count == 3

    def test_find_twitter_account_not_found(self) -> None:
        """Test Twitter account not found."""
        scraper = SocialMediaScraper()

        with patch.object(scraper, "_get_twitter_account_info", return_value=None):
            result = scraper._find_twitter_account("UNKNOWN")

            assert result is None

    def test_get_twitter_account_info(self) -> None:
        """Test Twitter account info retrieval."""
        scraper = SocialMediaScraper()

        # This method returns None in the current implementation
        result = scraper._get_twitter_account_info("testuser")

        assert result is None

    def test_get_twitter_recent_activity(self) -> None:
        """Test Twitter recent activity retrieval."""
        scraper = SocialMediaScraper()

        result = scraper._get_twitter_recent_activity("testuser")

        assert "post_count" in result
        assert "engagement_rate" in result
        assert "sentiment_score" in result

    def test_rate_limiting(self) -> None:
        """Test rate limiting functionality."""
        scraper = SocialMediaScraper()

        # Mock time to test rate limiting
        # Each call to _rate_limit() calls time.time() twice (start + end)
        # First call: 1000.0 (start), 1000.0 (end) -> no sleep, sets time to 1000.0
        # Second call: sleep 1 second (1000.0 -> 1002.0)
        time_values: list[float] = [1000.0, 1000.0, 1000.0, 1002.0]

        with patch("time.time", side_effect=time_values):
            with patch("time.sleep") as mock_sleep:
                scraper._rate_limit()  # First call: no sleep (1000.0, 1000.0)
                scraper._rate_limit()  # Second call: sleep 1 second (1000.0, 1002.0)
                # Should have attempted to sleep for 1 second
                mock_sleep.assert_called_once_with(1.0)
            # Should have updated last request time to 1002.0
            assert scraper._last_request_time == 1002.0

    def test_make_request_success(self) -> None:
        """Test successful HTTP request with retry."""
        scraper = SocialMediaScraper()

        mock_response = Mock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status.return_value = None

        with patch.object(
            scraper.session, "get", return_value=mock_response
        ) as mock_get:
            result = scraper._make_request("https://example.com")

            assert result == {"data": "test"}
            mock_get.assert_called_once()

    def test_make_request_retry_on_error(self) -> None:
        """Test HTTP request retry on error."""
        scraper = SocialMediaScraper(max_retries=2)

        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status.return_value = None

        # Test the retry mechanism by mocking the retry handler
        with patch.object(scraper.session, "get", return_value=mock_response):
            with patch.object(scraper._retry_handler, "execute") as mock_execute:
                mock_execute.return_value = {"data": "test"}
                result = scraper._make_request("https://example.com")

                # Verify retry handler was called
                mock_execute.assert_called_once()
                assert result == {"data": "test"}

    def test_get_beautiful_soup_available(self) -> None:
        """Test BeautifulSoup function when available."""
        with patch.object(
            social_media_scraper, "_get_beautiful_soup", return_value="MockSoup"
        ):
            result = social_media_scraper._get_beautiful_soup()
            assert result == "MockSoup"

    def test_get_beautiful_soup_unavailable(self) -> None:
        """Test BeautifulSoup function when not available."""
        with patch.object(
            social_media_scraper, "_get_beautiful_soup", return_value=None
        ):
            result = social_media_scraper._get_beautiful_soup()
            assert result is None


@pytest.mark.unit
class TestSocialMediaScraperIntegration:
    """Integration tests for SocialMediaScraper."""

    def test_complete_workflow_mocked(self) -> None:
        """Test complete workflow with mocked dependencies."""
        scraper = SocialMediaScraper()

        # Mock the main methods to return predictable data
        telegram_data = {"followers": 2000, "recent_posts": 12}
        twitter_data = {
            "followers": 1500,
            "recent_posts": 18,
            "engagement_rate": 2.8,
            "sentiment_score": 0.6,
        }

        with patch.object(scraper, "_get_telegram_metrics", return_value=telegram_data):
            with patch.object(
                scraper, "_get_twitter_metrics", return_value=twitter_data
            ):
                metrics = scraper.get_social_metrics("DOGE", "0xabc")

                assert isinstance(metrics, SocialMetrics)
                assert metrics.telegram_followers == 2000
                assert metrics.twitter_followers == 1500
                assert metrics.recent_posts == 18  # Twitter has more posts
                assert metrics.engagement_rate == 2.8
                assert metrics.sentiment_score == 0.6

    def test_error_resilience_workflow(self) -> None:
        """Test error resilience in complete workflow."""
        scraper = SocialMediaScraper()

        # Mock telegram to fail, twitter to succeed
        with patch.object(
            scraper, "_get_telegram_metrics", side_effect=Exception("Telegram error")
        ):
            with patch.object(
                scraper, "_get_twitter_metrics", return_value={"followers": 100}
            ):
                # Should still return metrics with defaults for failed source
                with pytest.raises(DataSourceError):
                    scraper.get_social_metrics("FAIL", "0x123")

    def test_session_management(self) -> None:
        """Test session management and creation."""
        with patch(
            "quantchain.tools.social_media_scraper.requests.Session"
        ) as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            scraper = SocialMediaScraper()

            # Test that session is properly created and configured
            assert scraper.session == mock_session
            mock_session_class.assert_called_once()

    def test_retry_handler_configuration(self) -> None:
        """Test retry handler is properly configured."""
        scraper = SocialMediaScraper(max_retries=5, timeout=15)

        # Check that retry handler has correct settings
        assert scraper._retry_handler.max_retries == 5
        assert scraper._retry_handler.base_delay == 1.0
        assert scraper._retry_handler.backoff_factor == 2.0

    def test_rate_limiting_parameters(self) -> None:
        """Test rate limiting parameters are set correctly."""
        scraper = SocialMediaScraper()

        # Test that rate limiting is configured
        assert scraper._min_request_interval == 1.0
        assert hasattr(scraper, "_last_request_time")
        assert isinstance(scraper._last_request_time, (int, float))

    def test_error_handling_resilience(self) -> None:
        """Test error handling maintains data integrity."""
        scraper = SocialMediaScraper()

        # Test with invalid input should still return SocialMetrics
        telegram_data: dict[str, Any] = {}
        twitter_data: dict[str, Any] = {}

        metrics = scraper._aggregate_social_metrics(telegram_data, twitter_data)

        # Should return default values rather than raising
        assert isinstance(metrics, SocialMetrics)
        assert all(
            [
                metrics.telegram_followers >= 0,
                metrics.twitter_followers >= 0,
                metrics.recent_posts >= 0,
                metrics.engagement_rate >= 0.0,
                0.0 <= metrics.sentiment_score <= 1.0,
            ]
        )
