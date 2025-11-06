"""Tests for social media scraper tool."""

import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock problematic imports before importing the target module
sys.modules["torch"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()

from quantchain.tools.social_media_scraper import (
    SocialMediaScraper,
    SocialMetrics,
    _get_beautiful_soup,
)
from quantchain.core.exceptions import DataSourceError


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

    def test_aggregate_social_metrics_empty_data(self) -> None:
        """Test aggregating metrics with empty data."""
        scraper = SocialMediaScraper()
        telegram_data = {}
        twitter_data = {}

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
        scraper.session = None

        with pytest.raises(DataSourceError, match="requests library not available"):
            scraper.get_social_metrics("BTC", "0x123")

    @patch.object(SocialMediaScraper, "_get_telegram_metrics")
    @patch.object(SocialMediaScraper, "_get_twitter_metrics")
    def test_get_social_metrics_success(self, mock_twitter, mock_telegram) -> None:
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

    def test_get_beautiful_soup_available(self) -> None:
        """Test BeautifulSoup function when available."""
        with patch(
            "quantchain.tools.social_media_scraper.bs4.BeautifulSoup", "MockSoup"
        ):
            result = _get_beautiful_soup()
            assert result == "MockSoup"

    def test_get_beautiful_soup_unavailable(self) -> None:
        """Test BeautifulSoup function when not available."""
        with patch("quantchain.tools.social_media_scraper.bs4", None):
            result = _get_beautiful_soup()
            assert result is None

    def test_rate_limiting_logic(self) -> None:
        """Test rate limiting parameters are set correctly."""
        scraper = SocialMediaScraper()

        # Test that rate limiting is configured
        assert scraper._min_request_interval == 1.0
        assert hasattr(scraper, "_last_request_time")

    def test_retry_handler_initialization(self) -> None:
        """Test retry handler is properly initialized."""
        scraper = SocialMediaScraper(max_retries=2, timeout=5)

        # Check that retry handler has correct settings
        assert scraper._retry_handler.max_retries == 2
        assert scraper._retry_handler.base_delay == 1.0
        assert scraper._retry_handler.backoff_factor == 2.0


@pytest.mark.unit
class TestSocialMediaScraperIntegration:
    """Integration tests for SocialMediaScraper."""

    def test_scraper_with_mock_session_flow(self) -> None:
        """Test complete data flow with mocked session."""
        with patch(
            "quantchain.tools.social_media_scraper.requests.Session"
        ) as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value = mock_session

            scraper = SocialMediaScraper()

            # Test that session is properly created
            assert scraper.session == mock_session

    def test_error_handling_resilience(self) -> None:
        """Test error handling maintains data integrity."""
        scraper = SocialMediaScraper()

        # Test with invalid input should still return SocialMetrics
        telegram_data = {}
        twitter_data = {}

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
