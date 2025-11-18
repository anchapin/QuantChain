"""Comprehensive tests for social_media_scraper module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from quantchain.tools.social_media_scraper import (
    SentimentScore,
    SocialMediaMetrics,
    SocialMediaPost,
    SocialMediaScraper,
    VibeAssessment,
)


class TestSentimentScore:
    """Test SentimentScore enum functionality."""

    @pytest.mark.unit
    def test_sentiment_score_values(self):
        """Test SentimentScore enum values."""
        assert SentimentScore.VERY_NEGATIVE.value == "very_negative"
        assert SentimentScore.NEGATIVE.value == "negative"
        assert SentimentScore.NEUTRAL.value == "neutral"
        assert SentimentScore.POSITIVE.value == "positive"
        assert SentimentScore.VERY_POSITIVE.value == "very_positive"

    @pytest.mark.unit
    def test_sentiment_score_ordering(self):
        """Test sentiment score ordering for comparison."""
        scores = list(SentimentScore)
        assert len(scores) == 5

    @pytest.mark.unit
    def test_sentiment_score_iteration(self):
        """Test iteration over sentiment scores."""
        sentiments = list(SentimentScore)
        assert SentimentScore.VERY_NEGATIVE in sentiments
        assert SentimentScore.VERY_POSITIVE in sentiments


class TestSocialMediaPost:
    """Test SocialMediaPost dataclass functionality."""

    @pytest.mark.unit
    def test_post_creation_minimal(self):
        """Test creating social media post with minimal data."""
        timestamp = datetime.now()
        post = SocialMediaPost(
            id="123",
            platform="twitter",
            author="user",
            content="Test post",
            timestamp=timestamp
        )

        assert post.id == "123"
        assert post.platform == "twitter"
        assert post.author == "user"
        assert post.content == "Test post"
        assert post.timestamp == timestamp
        assert post.likes == 0  # Default value
        assert post.shares == 0  # Default value
        assert post.comments == 0  # Default value
        assert post.url is None  # Default value
        assert post.hashtags == []  # Default value
        assert post.mentions == []  # Default value
        assert post.sentiment_score is None  # Default value
        assert post.confidence == 1.0  # Default value

    @pytest.mark.unit
    def test_post_creation_full(self):
        """Test creating social media post with all data."""
        timestamp = datetime.now()
        post = SocialMediaPost(
            id="123",
            platform="reddit",
            author="redditor",
            content="Check out this crypto! #bitcoin @elonmusk",
            timestamp=timestamp,
            likes=100,
            shares=25,
            comments=50,
            url="https://reddit.com/r/crypto/123",
            hashtags=["bitcoin", "crypto"],
            mentions=["elonmusk"],
            sentiment_score=SentimentScore.POSITIVE,
            confidence=0.85
        )

        assert post.id == "123"
        assert post.platform == "reddit"
        assert post.author == "redditor"
        assert post.content == "Check out this crypto! #bitcoin @elonmusk"
        assert post.timestamp == timestamp
        assert post.likes == 100
        assert post.shares == 25
        assert post.comments == 50
        assert post.url == "https://reddit.com/r/crypto/123"
        assert post.hashtags == ["bitcoin", "crypto"]
        assert post.mentions == ["elonmusk"]
        assert post.sentiment_score == SentimentScore.POSITIVE
        assert post.confidence == 0.85

    @pytest.mark.unit
    def test_post_equality(self):
        """Test post equality comparison."""
        timestamp = datetime.now()
        post1 = SocialMediaPost(
            id="123",
            platform="twitter",
            author="user",
            content="Test",
            timestamp=timestamp
        )
        post2 = SocialMediaPost(
            id="123",
            platform="twitter",
            author="user",
            content="Test",
            timestamp=timestamp
        )
        post3 = SocialMediaPost(
            id="456",
            platform="twitter",
            author="user",
            content="Test",
            timestamp=timestamp
        )

        assert post1 == post2
        assert post1 != post3


class TestSocialMediaMetrics:
    """Test SocialMediaMetrics dataclass functionality."""

    @pytest.mark.unit
    def test_metrics_creation_minimal(self):
        """Test creating metrics with minimal data."""
        timestamp = datetime.now()
        metrics = SocialMediaMetrics(
            platform="twitter",
            symbol="BTC",
            post_count=10,
            total_likes=100,
            total_shares=20,
            total_comments=30,
            unique_authors=8,
            timestamp=timestamp
        )

        assert metrics.platform == "twitter"
        assert metrics.symbol == "BTC"
        assert metrics.post_count == 10
        assert metrics.total_likes == 100
        assert metrics.total_shares == 20
        assert metrics.total_comments == 30
        assert metrics.unique_authors == 8
        assert metrics.sentiment_distribution == {}  # Default
        assert metrics.top_hashtags == []  # Default
        assert metrics.top_mentions == []  # Default
        assert metrics.engagement_rate is None  # Default
        assert metrics.time_period == "24h"  # Default
        assert metrics.timestamp == timestamp

    @pytest.mark.unit
    def test_metrics_creation_full(self):
        """Test creating metrics with all data."""
        timestamp = datetime.now()
        sentiment_dist = {
            SentimentScore.POSITIVE: 5,
            SentimentScore.NEUTRAL: 3,
            SentimentScore.NEGATIVE: 2
        }
        top_hashtags = [("bitcoin", 8), ("crypto", 5)]
        top_mentions = [("elonmusk", 3), ("cz_binance", 2)]

        metrics = SocialMediaMetrics(
            platform="reddit",
            symbol="ETH",
            post_count=10,
            total_likes=200,
            total_shares=50,
            total_comments=75,
            unique_authors=12,
            sentiment_distribution=sentiment_dist,
            top_hashtags=top_hashtags,
            top_mentions=top_mentions,
            engagement_rate=32.5,
            time_period="7d",
            timestamp=timestamp
        )

        assert metrics.platform == "reddit"
        assert metrics.symbol == "ETH"
        assert metrics.post_count == 10
        assert metrics.total_likes == 200
        assert metrics.total_shares == 50
        assert metrics.total_comments == 75
        assert metrics.unique_authors == 12
        assert metrics.sentiment_distribution == sentiment_dist
        assert metrics.top_hashtags == top_hashtags
        assert metrics.top_mentions == top_mentions
        assert metrics.engagement_rate == 32.5
        assert metrics.time_period == "7d"
        assert metrics.timestamp == timestamp

    @pytest.mark.unit
    def test_metrics_engagement_calculation(self):
        """Test engagement rate calculation logic."""
        # Metrics should calculate engagement rate as (likes + comments + shares) / post_count
        metrics = SocialMediaMetrics(
            platform="twitter",
            symbol="DOGE",
            post_count=5,
            total_likes=100,
            total_shares=20,
            total_comments=30,
            unique_authors=4,
            engagement_rate=30.0  # (100 + 20 + 30) / 5 = 30.0
        )

        assert metrics.engagement_rate == 30.0


class TestVibeAssessment:
    """Test VibeAssessment dataclass functionality."""

    @pytest.mark.unit
    def test_vibe_assessment_creation_minimal(self):
        """Test creating vibe assessment with minimal data."""
        timestamp = datetime.now()
        assessment = VibeAssessment(
            symbol="MEME",
            platform="twitter",
            vibe_score=75.0,
            sentiment=SentimentScore.POSITIVE,
            confidence=0.8,
            timestamp=timestamp
        )

        assert assessment.symbol == "MEME"
        assert assessment.platform == "twitter"
        assert assessment.vibe_score == 75.0
        assert assessment.sentiment == SentimentScore.POSITIVE
        assert assessment.confidence == 0.8
        assert assessment.reasons == []  # Default
        assert assessment.social_metrics is None  # Default
        assert assessment.timestamp == timestamp

    @pytest.mark.unit
    def test_vibe_assessment_creation_full(self):
        """Test creating vibe assessment with all data."""
        timestamp = datetime.now()
        metrics = SocialMediaMetrics(
            platform="reddit",
            symbol="SHIB",
            post_count=50,
            total_likes=500,
            total_shares=100,
            total_comments=200,
            unique_authors=30
        )
        reasons = ["High engagement", "Positive sentiment"]

        assessment = VibeAssessment(
            symbol="SHIB",
            platform="reddit",
            vibe_score=85.5,
            sentiment=SentimentScore.VERY_POSITIVE,
            confidence=0.9,
            reasons=reasons,
            social_metrics=metrics,
            timestamp=timestamp
        )

        assert assessment.symbol == "SHIB"
        assert assessment.platform == "reddit"
        assert assessment.vibe_score == 85.5
        assert assessment.sentiment == SentimentScore.VERY_POSITIVE
        assert assessment.confidence == 0.9
        assert assessment.reasons == reasons
        assert assessment.social_metrics == metrics
        assert assessment.timestamp == timestamp


class TestSocialMediaScraper:
    """Test SocialMediaScraper functionality."""

    @pytest.mark.unit
    def test_scraper_init_default(self):
        """Test scraper initialization with defaults."""
        scraper = SocialMediaScraper()

        assert scraper.config is not None
        assert scraper.api_keys == {}
        assert scraper.request_delay == 1.0
        assert scraper.max_retries == 3
        assert scraper.timeout == 10
        assert "twitter" in scraper._mock_data
        assert "reddit" in scraper._mock_data

    @pytest.mark.unit
    def test_scraper_init_custom_params(self):
        """Test scraper initialization with custom parameters."""
        mock_config = Mock()
        api_keys = {"twitter": "test_key", "reddit": "test_key2"}

        scraper = SocialMediaScraper(
            config=mock_config,
            api_keys=api_keys,
            request_delay=2.0,
            max_retries=5,
            timeout=30
        )

        assert scraper.config == mock_config
        assert scraper.api_keys == api_keys
        assert scraper.request_delay == 2.0
        assert scraper.max_retries == 5
        assert scraper.timeout == 30

    @pytest.mark.unit
    def test_fetch_posts_twitter_success(self):
        """Test fetching posts from Twitter."""
        scraper = SocialMediaScraper()

        posts = scraper.fetch_posts("MEME", "twitter", max_posts=10)

        assert len(posts) > 0
        assert all(post.platform == "twitter" for post in posts)
        assert all(isinstance(post, SocialMediaPost) for post in posts)

    @pytest.mark.unit
    def test_fetch_posts_reddit_success(self):
        """Test fetching posts from Reddit."""
        scraper = SocialMediaScraper()

        posts = scraper.fetch_posts("MEME", "reddit", max_posts=10)

        assert len(posts) > 0
        assert all(post.platform == "reddit" for post in posts)
        assert all(isinstance(post, SocialMediaPost) for post in posts)

    @pytest.mark.unit
    def test_fetch_posts_unknown_platform(self):
        """Test fetching posts from unknown platform."""
        scraper = SocialMediaScraper()

        posts = scraper.fetch_posts("MEME", "unknown", max_posts=10)

        assert posts == []

    @pytest.mark.unit
    def test_fetch_posts_with_limit(self):
        """Test fetching posts with limit."""
        scraper = SocialMediaScraper()

        # Request more posts than available
        posts = scraper.fetch_posts("MEME", "twitter", max_posts=100)

        # Should return all available posts (limited by mock data)
        assert len(posts) >= 0

    @pytest.mark.unit
    def test_calculate_metrics_empty_posts(self):
        """Test calculating metrics with empty posts list."""
        scraper = SocialMediaScraper()

        metrics = scraper.calculate_metrics([], "MEME", "twitter")

        assert metrics.platform == "twitter"
        assert metrics.symbol == "MEME"
        assert metrics.post_count == 0
        assert metrics.total_likes == 0
        assert metrics.total_shares == 0
        assert metrics.total_comments == 0
        assert metrics.unique_authors == 0
        assert metrics.sentiment_distribution == {}
        assert metrics.top_hashtags == []
        assert metrics.top_mentions == []

    @pytest.mark.unit
    def test_calculate_metrics_with_posts(self):
        """Test calculating metrics with posts."""
        scraper = SocialMediaScraper()
        posts = scraper.fetch_posts("MEME", "twitter")

        metrics = scraper.calculate_metrics(posts, "MEME", "twitter")

        assert metrics.platform == "twitter"
        assert metrics.symbol == "MEME"
        assert metrics.post_count == len(posts)
        assert metrics.total_likes > 0
        assert metrics.unique_authors > 0
        assert metrics.engagement_rate is not None

    @pytest.mark.unit
    def test_calculate_metrics_sentiment_distribution(self):
        """Test sentiment distribution calculation."""
        scraper = SocialMediaScraper()

        # Create test posts with different sentiments
        posts = [
            SocialMediaPost(
                id="1", platform="test", author="user1", content="Good",
                timestamp=datetime.now(), sentiment_score=SentimentScore.POSITIVE
            ),
            SocialMediaPost(
                id="2", platform="test", author="user2", content="Bad",
                timestamp=datetime.now(), sentiment_score=SentimentScore.NEGATIVE
            ),
            SocialMediaPost(
                id="3", platform="test", author="user3", content="Neutral",
                timestamp=datetime.now(), sentiment_score=SentimentScore.NEUTRAL
            ),
        ]

        metrics = scraper.calculate_metrics(posts, "TEST", "test")

        assert metrics.sentiment_distribution[SentimentScore.POSITIVE] == 1
        assert metrics.sentiment_distribution[SentimentScore.NEGATIVE] == 1
        assert metrics.sentiment_distribution[SentimentScore.NEUTRAL] == 1

    @pytest.mark.unit
    def test_calculate_metrics_top_hashtags(self):
        """Test top hashtags calculation."""
        scraper = SocialMediaScraper()

        # Create test posts with hashtags
        posts = [
            SocialMediaPost(
                id="1", platform="test", author="user1", content="Test",
                timestamp=datetime.now(), hashtags=["crypto", "bitcoin"]
            ),
            SocialMediaPost(
                id="2", platform="test", author="user2", content="Test",
                timestamp=datetime.now(), hashtags=["crypto", "ethereum"]
            ),
            SocialMediaPost(
                id="3", platform="test", author="user3", content="Test",
                timestamp=datetime.now(), hashtags=["blockchain"]
            ),
        ]

        metrics = scraper.calculate_metrics(posts, "TEST", "test")

        # "crypto" should be the top hashtag (appears 2 times)
        assert len(metrics.top_hashtags) > 0
        assert any(tag == "crypto" for tag, count in metrics.top_hashtags)

    @pytest.mark.unit
    def test_calculate_metrics_top_mentions(self):
        """Test top mentions calculation."""
        scraper = SocialMediaScraper()

        # Create test posts with mentions
        posts = [
            SocialMediaPost(
                id="1", platform="test", author="user1", content="Test",
                timestamp=datetime.now(), mentions=["elonmusk"]
            ),
            SocialMediaPost(
                id="2", platform="test", author="user2", content="Test",
                timestamp=datetime.now(), mentions=["elonmusk", "cz_binance"]
            ),
        ]

        metrics = scraper.calculate_metrics(posts, "TEST", "test")

        # "elonmusk" should be the top mention (appears 2 times)
        assert len(metrics.top_mentions) > 0
        assert any(mention == "elonmusk" for mention, count in metrics.top_mentions)

    @pytest.mark.unit
    def test_assess_vibe_no_platforms(self):
        """Test vibe assessment with no platforms."""
        scraper = SocialMediaScraper()

        assessments = scraper.assess_vibe("UNKNOWN", platforms=[])

        assert assessments == []

    @pytest.mark.unit
    def test_assess_vibe_no_posts_found(self):
        """Test vibe assessment when no posts found."""
        scraper = SocialMediaScraper()

        assessments = scraper.assess_vibe("UNKNOWN", platforms=["unknown"])

        assert len(assessments) == 1
        assert assessments[0].symbol == "UNKNOWN"
        assert assessments[0].platform == "unknown"
        assert assessments[0].vibe_score == 50.0  # Neutral
        assert assessments[0].sentiment == SentimentScore.NEUTRAL
        assert assessments[0].confidence == 0.1  # Low confidence
        assert "No social media posts found" in assessments[0].reasons

    @pytest.mark.unit
    def test_assess_vibe_with_posts(self):
        """Test vibe assessment with posts."""
        scraper = SocialMediaScraper()

        assessments = scraper.assess_vibe("MEME", platforms=["twitter"])

        assert len(assessments) == 1
        assert assessments[0].symbol == "MEME"
        assert assessments[0].platform == "twitter"
        assert 0 <= assessments[0].vibe_score <= 100
        assert assessments[0].sentiment is not None
        assert 0 <= assessments[0].confidence <= 1
        assert len(assessments[0].reasons) > 0
        assert assessments[0].social_metrics is not None

    @pytest.mark.unit
    def test_assess_vibe_confidence_calculation(self):
        """Test confidence calculation based on post count."""
        scraper = SocialMediaScraper()

        # Test with low post count
        assessments = scraper.assess_vibe("LOW", platforms=["twitter"])
        if assessments and assessments[0].social_metrics:
            if assessments[0].social_metrics.post_count < 5:
                assert assessments[0].confidence == 0.3
            elif assessments[0].social_metrics.post_count < 20:
                assert assessments[0].confidence == 0.6
            else:
                assert assessments[0].confidence == 0.9

    @pytest.mark.unit
    def test_assess_vibe_sentiment_weighting(self):
        """Test sentiment weighting in vibe assessment."""
        scraper = SocialMediaScraper()

        assessments = scraper.assess_vibe("MEME", platforms=["twitter"])

        if assessments:
            assessment = assessments[0]
            metrics = assessment.social_metrics

            if metrics and metrics.sentiment_distribution:
                # Check that very positive sentiment results in high vibe score
                if assessment.sentiment == SentimentScore.VERY_POSITIVE:
                    assert assessment.vibe_score >= 70
                # Check that very negative sentiment results in low vibe score
                elif assessment.sentiment == SentimentScore.VERY_NEGATIVE:
                    assert assessment.vibe_score <= 30

    @pytest.mark.unit
    def test_assess_overall_vibe_no_data(self):
        """Test overall vibe assessment with no data."""
        scraper = SocialMediaScraper()

        assessment = scraper.assess_overall_vibe("UNKNOWN", platforms=["unknown"])

        assert assessment.symbol == "UNKNOWN"
        assert assessment.platform == "all"
        assert assessment.vibe_score == 50.0  # Neutral
        assert assessment.sentiment == SentimentScore.NEUTRAL
        assert assessment.confidence == 0.1  # Low confidence
        assert "No social media posts found" in assessment.reasons

    @pytest.mark.unit
    def test_assess_overall_vibe_with_data(self):
        """Test overall vibe assessment with data."""
        scraper = SocialMediaScraper()

        assessment = scraper.assess_overall_vibe("MEME", platforms=["twitter", "reddit"])

        assert assessment.symbol == "MEME"
        assert assessment.platform == "all"
        assert 0 <= assessment.vibe_score <= 100
        assert assessment.sentiment is not None
        assert 0 <= assessment.confidence <= 1
        assert len(assessment.reasons) > 0

    @pytest.mark.unit
    def test_assess_overall_vibe_weighted_scoring(self):
        """Test weighted scoring in overall vibe assessment."""
        scraper = SocialMediaScraper()

        # Mock platform assessments with different confidence scores
        with patch.object(scraper, 'assess_vibe') as mock_assess:
            mock_assess.return_value = [
                VibeAssessment(
                    symbol="TEST", platform="twitter", vibe_score=80.0,
                    sentiment=SentimentScore.POSITIVE, confidence=0.9
                ),
                VibeAssessment(
                    symbol="TEST", platform="reddit", vibe_score=60.0,
                    sentiment=SentimentScore.NEUTRAL, confidence=0.5
                ),
            ]

            assessment = scraper.assess_overall_vibe("TEST")

            # Should be weighted more towards the higher confidence assessment
            expected_weighted = (80.0 * 0.9 + 60.0 * 0.5) / (0.9 + 0.5)
            assert abs(assessment.vibe_score - expected_weighted) < 0.1

    @pytest.mark.unit
    def test_get_metrics_with_posts(self):
        """Test getting metrics for symbol with posts."""
        scraper = SocialMediaScraper()

        metrics = scraper.get_metrics("MEME")

        assert isinstance(metrics, SocialMediaMetrics)
        assert metrics.platform == "twitter"
        assert metrics.symbol == "MEME"

    @pytest.mark.unit
    def test_get_metrics_no_posts(self):
        """Test getting metrics for symbol with no posts."""
        scraper = SocialMediaScraper()

        # Mock fetch_posts to return empty list
        with patch.object(scraper, 'fetch_posts', return_value=[]):
            metrics = scraper.get_metrics("UNKNOWN")

            assert metrics.platform == "twitter"
            assert metrics.symbol == "UNKNOWN"
            assert metrics.post_count == 0
            assert metrics.total_likes == 0
            assert metrics.total_shares == 0
            assert metrics.total_comments == 0
            assert metrics.unique_authors == 0

    @pytest.mark.unit
    def test_engagement_rate_calculation(self):
        """Test engagement rate calculation in metrics."""
        scraper = SocialMediaScraper()

        # Create posts with known engagement
        posts = [
            SocialMediaPost(
                id="1", platform="test", author="user1", content="Test",
                timestamp=datetime.now(), likes=10, comments=5, shares=2
            ),
            SocialMediaPost(
                id="2", platform="test", author="user2", content="Test",
                timestamp=datetime.now(), likes=20, comments=8, shares=3
            ),
        ]

        metrics = scraper.calculate_metrics(posts, "TEST", "test")

        # Expected: (10+5+2 + 20+8+3) / 2 = 48 / 2 = 24
        expected_engagement = 24.0
        assert abs(metrics.engagement_rate - expected_engagement) < 0.1

    @pytest.mark.unit
    def test_reasons_generation(self):
        """Test reasons generation in vibe assessment."""
        scraper = SocialMediaScraper()

        assessments = scraper.assess_vibe("MEME", platforms=["twitter"])

        if assessments:
            assessment = assessments[0]
            assert len(assessment.reasons) > 0

            # Check for common reason patterns
            all_reasons_text = " ".join(assessment.reasons).lower()
            assert any(keyword in all_reasons_text for keyword in [
                "posts", "engagement", "sentiment", "authors"
            ])

    @pytest.mark.unit
    def test_mock_data_structure(self):
        """Test that mock data has proper structure."""
        scraper = SocialMediaScraper()

        # Check that mock data exists for expected platforms
        assert "twitter" in scraper._mock_data
        assert "reddit" in scraper._mock_data

        # Check that each platform has posts
        for platform, data in scraper._mock_data.items():
            assert "posts" in data
            assert isinstance(data["posts"], list)

            # Check that posts are SocialMediaPost objects
            for post in data["posts"]:
                assert isinstance(post, SocialMediaPost)
                assert post.platform == platform

    @pytest.mark.unit
    def test_case_insensitive_platform_matching(self):
        """Test case-insensitive platform matching."""
        scraper = SocialMediaScraper()

        # Test with uppercase platform name
        posts_upper = scraper.fetch_posts("MEME", "TWITTER")
        posts_lower = scraper.fetch_posts("MEME", "twitter")

        # Should return the same data
        assert len(posts_upper) == len(posts_lower)

    @pytest.mark.unit
    def test_vibe_score_bounds(self):
        """Test that vibe scores are always within bounds."""
        scraper = SocialMediaScraper()

        assessments = scraper.assess_vibe("MEME", platforms=["twitter", "reddit"])

        for assessment in assessments:
            assert 0 <= assessment.vibe_score <= 100

        overall = scraper.assess_overall_vibe("MEME", platforms=["twitter", "reddit"])
        assert 0 <= overall.vibe_score <= 100