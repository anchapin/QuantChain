"""Social media scraper for QuantChain."""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import urllib.request
import urllib.parse
from urllib.error import URLError, HTTPError

from quantchain.core.config import QuantChainConfig
from quantchain.core.exceptions import QuantChainError


class SentimentScore(Enum):
    """Sentiment score enumeration."""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


@dataclass
class SocialMediaPost:
    """Represents a social media post."""
    id: str
    platform: str  # twitter, reddit, telegram, etc.
    author: str
    content: str
    timestamp: datetime
    likes: int = 0
    shares: int = 0
    comments: int = 0
    url: Optional[str] = None
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    sentiment_score: Optional[SentimentScore] = None
    confidence: float = 1.0  # 0.0 to 1.0


@dataclass
class SocialMediaMetrics:
    """Aggregated metrics for social media data."""
    platform: str
    symbol: str
    post_count: int
    total_likes: int
    total_shares: int
    total_comments: int
    unique_authors: int
    sentiment_distribution: Dict[SentimentScore, int] = field(default_factory=dict)
    top_hashtags: List[Tuple[str, int]] = field(default_factory=list)
    top_mentions: List[Tuple[str, int]] = field(default_factory=list)
    engagement_rate: Optional[float] = None
    time_period: str = "24h"
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class VibeAssessment:
    """Overall vibe assessment for a token/meme."""
    symbol: str
    platform: str
    vibe_score: float  # 0.0 to 100.0
    sentiment: SentimentScore
    confidence: float  # 0.0 to 1.0
    reasons: List[str] = field(default_factory=list)
    social_metrics: SocialMediaMetrics = None
    timestamp: datetime = field(default_factory=datetime.now)


class SocialMediaScraper:
    """Scrapes and analyzes social media data for meme coins."""

    def __init__(
        self,
        config: Optional[QuantChainConfig] = None,
        api_keys: Dict[str, str] = None,
        request_delay: float = 1.0,
        max_retries: int = 3,
        timeout: int = 10,
    ):
        """
        Initialize SocialMediaScraper.

        Args:
            config: QuantChain configuration
            api_keys: Dictionary of API keys for different platforms
            request_delay: Delay between requests in seconds
            max_retries: Maximum number of retries for failed requests
            timeout: Request timeout in seconds
        """
        self.config = config or QuantChainConfig()
        self.api_keys = api_keys or {}
        self.request_delay = request_delay
        self.max_retries = max_retries
        self.timeout = timeout

        # Mock data for testing
        self._mock_data = {
            "twitter": {
                "posts": [
                    SocialMediaPost(
                        id="1234567890",
                        platform="twitter",
                        author="crypto_enthusiast",
                        content="Just bought $MEME coin! 🚀 Going to the moon! #memecoin #crypto",
                        timestamp=datetime.now() - timedelta(hours=3),
                        likes=42,
                        shares=5,
                        comments=8,
                        url="https://twitter.com/crypto_enthusiast/status/1234567890",
                        hashtags=["memecoin", "crypto"],
                        sentiment_score=SentimentScore.POSITIVE
                    ),
                    SocialMediaPost(
                        id="1234567891",
                        platform="twitter",
                        author="skeptic_trader",
                        content="Beware of the pump and dump on $MEME. Looks like it's crashing soon. #cryptowarning",
                        timestamp=datetime.now() - timedelta(hours=5),
                        likes=18,
                        shares=2,
                        comments=12,
                        url="https://twitter.com/skeptic_trader/status/1234567891",
                        hashtags=["cryptowarning"],
                        sentiment_score=SentimentScore.NEGATIVE
                    ),
                ]
            },
            "reddit": {
                "posts": [
                    SocialMediaPost(
                        id="abc123",
                        platform="reddit",
                        author="diamond_hands",
                        content="HODL $MEME to the moon! 💎🙌 Not selling until it hits $1!",
                        timestamp=datetime.now() - timedelta(hours=2),
                        likes=156,
                        shares=0,  # Reddit doesn't have shares
                        comments=43,
                        url="https://reddit.com/r/cryptocurrency/comments/abc123",
                        sentiment_score=SentimentScore.VERY_POSITIVE
                    ),
                    SocialMediaPost(
                        id="def456",
                        platform="reddit",
                        author="rational_investor",
                        content="Can someone explain the fundamentals of $MEME? I don't see any utility here.",
                        timestamp=datetime.now() - timedelta(hours=8),
                        likes=23,
                        shares=0,
                        comments=67,
                        url="https://reddit.com/r/cryptocurrency/comments/def456",
                        sentiment_score=SentimentScore.NEUTRAL
                    ),
                ]
            }
        }

    def fetch_posts(
        self,
        symbol: str,
        platform: str,
        max_posts: int = 100,
        time_period: str = "24h"
    ) -> List[SocialMediaPost]:
        """
        Fetch posts mentioning a symbol from a specific platform.

        Args:
            symbol: Trading symbol (e.g., "DOGE", "SHIB")
            platform: Platform name (twitter, reddit, telegram)
            max_posts: Maximum number of posts to fetch
            time_period: Time period to search (e.g., "24h", "7d")

        Returns:
            List of SocialMediaPost objects
        """
        # In a real implementation, this would make API calls to the platform
        # For testing purposes, return mock data

        if platform.lower() in self._mock_data:
            return self._mock_data[platform.lower()]["posts"][:max_posts]

        return []

    def calculate_metrics(
        self,
        posts: List[SocialMediaPost],
        symbol: str,
        platform: str
    ) -> SocialMediaMetrics:
        """
        Calculate aggregated metrics from social media posts.

        Args:
            posts: List of social media posts
            symbol: Symbol being analyzed
            platform: Platform name

        Returns:
            SocialMediaMetrics object
        """
        if not posts:
            return SocialMediaMetrics(
                platform=platform,
                symbol=symbol,
                post_count=0,
                total_likes=0,
                total_shares=0,
                total_comments=0,
                unique_authors=0
            )

        # Calculate basic metrics
        post_count = len(posts)
        total_likes = sum(post.likes for post in posts)
        total_shares = sum(post.shares for post in posts)
        total_comments = sum(post.comments for post in posts)
        unique_authors = len(set(post.author for post in posts))

        # Calculate sentiment distribution
        sentiment_distribution = {}
        for sentiment in SentimentScore:
            sentiment_distribution[sentiment] = sum(
                1 for post in posts if post.sentiment_score == sentiment
            )

        # Calculate top hashtags
        hashtag_counts = {}
        for post in posts:
            for tag in post.hashtags:
                hashtag_counts[tag.lower()] = hashtag_counts.get(tag.lower(), 0) + 1

        top_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Calculate top mentions
        mention_counts = {}
        for post in posts:
            for mention in post.mentions:
                mention_counts[mention.lower()] = mention_counts.get(mention.lower(), 0) + 1

        top_mentions = sorted(mention_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Calculate engagement rate (likes + comments + shares) / post_count
        total_engagement = total_likes + total_comments + total_shares
        engagement_rate = total_engagement / post_count if post_count > 0 else 0

        return SocialMediaMetrics(
            platform=platform,
            symbol=symbol,
            post_count=post_count,
            total_likes=total_likes,
            total_shares=total_shares,
            total_comments=total_comments,
            unique_authors=unique_authors,
            sentiment_distribution=sentiment_distribution,
            top_hashtags=top_hashtags,
            top_mentions=top_mentions,
            engagement_rate=engagement_rate
        )

    def assess_vibe(
        self,
        symbol: str,
        platforms: List[str] = None,
        time_period: str = "24h"
    ) -> List[VibeAssessment]:
        """
        Assess the overall vibe for a symbol across platforms.

        Args:
            symbol: Symbol to assess
            platforms: List of platforms to check (default: all)
            time_period: Time period to analyze

        Returns:
            List of VibeAssessment objects, one per platform
        """
        if platforms is None:
            platforms = list(self._mock_data.keys())

        assessments = []

        for platform in platforms:
            # Fetch posts
            posts = self.fetch_posts(symbol, platform, time_period=time_period)

            if not posts:
                # Create a neutral assessment if no posts found
                assessments.append(VibeAssessment(
                    symbol=symbol,
                    platform=platform,
                    vibe_score=50.0,  # Neutral
                    sentiment=SentimentScore.NEUTRAL,
                    confidence=0.1,  # Low confidence due to no data
                    reasons=["No social media posts found"]
                ))
                continue

            # Calculate metrics
            metrics = self.calculate_metrics(posts, symbol, platform)

            # Determine overall sentiment
            total_posts = sum(metrics.sentiment_distribution.values())
            if total_posts == 0:
                overall_sentiment = SentimentScore.NEUTRAL
            else:
                # Weight sentiments: very_positive=2, positive=1, neutral=0, negative=-1, very_negative=-2
                sentiment_weights = {
                    SentimentScore.VERY_POSITIVE: 2,
                    SentimentScore.POSITIVE: 1,
                    SentimentScore.NEUTRAL: 0,
                    SentimentScore.NEGATIVE: -1,
                    SentimentScore.VERY_NEGATIVE: -2
                }

                weighted_score = sum(
                    metrics.sentiment_distribution[sentiment] * sentiment_weights[sentiment]
                    for sentiment in SentimentScore
                ) / total_posts

                # Convert weighted score back to sentiment
                if weighted_score >= 1:
                    overall_sentiment = SentimentScore.VERY_POSITIVE
                elif weighted_score >= 0.5:
                    overall_sentiment = SentimentScore.POSITIVE
                elif weighted_score > -0.5:
                    overall_sentiment = SentimentScore.NEUTRAL
                elif weighted_score > -1:
                    overall_sentiment = SentimentScore.NEGATIVE
                else:
                    overall_sentiment = SentimentScore.VERY_NEGATIVE

            # Calculate vibe score (0-100)
            # Base score from sentiment
            base_scores = {
                SentimentScore.VERY_POSITIVE: 85,
                SentimentScore.POSITIVE: 70,
                SentimentScore.NEUTRAL: 50,
                SentimentScore.NEGATIVE: 30,
                SentimentScore.VERY_NEGATIVE: 15
            }
            vibe_score = base_scores[overall_sentiment]

            # Adjust based on engagement
            if metrics.engagement_rate:
                # Higher engagement increases the score if sentiment is positive
                # or decreases it if sentiment is negative
                if overall_sentiment in [SentimentScore.POSITIVE, SentimentScore.VERY_POSITIVE]:
                    vibe_score += min(10, metrics.engagement_rate / 10)
                elif overall_sentiment in [SentimentScore.NEGATIVE, SentimentScore.VERY_NEGATIVE]:
                    vibe_score -= min(10, metrics.engagement_rate / 10)

            # Ensure score is within bounds
            vibe_score = max(0, min(100, vibe_score))

            # Determine confidence based on data volume
            if metrics.post_count < 5:
                confidence = 0.3
            elif metrics.post_count < 20:
                confidence = 0.6
            else:
                confidence = 0.9

            # Generate reasons for the assessment
            reasons = []
            if metrics.post_count:
                reasons.append(f"Found {metrics.post_count} posts mentioning ${symbol}")

            if metrics.engagement_rate and metrics.engagement_rate > 10:
                reasons.append("High engagement rate indicates strong interest")
            elif metrics.engagement_rate and metrics.engagement_rate < 2:
                reasons.append("Low engagement rate might indicate lack of interest")

            if overall_sentiment in [SentimentScore.POSITIVE, SentimentScore.VERY_POSITIVE]:
                reasons.append("Overall sentiment is positive")
            elif overall_sentiment in [SentimentScore.NEGATIVE, SentimentScore.VERY_NEGATIVE]:
                reasons.append("Overall sentiment is negative")

            if metrics.unique_authors > 50:
                reasons.append("Wide distribution of posters indicates broad appeal")
            elif metrics.unique_authors < 10:
                reasons.append("Few unique authors might indicate coordinated posting")

            # Create assessment
            assessment = VibeAssessment(
                symbol=symbol,
                platform=platform,
                vibe_score=vibe_score,
                sentiment=overall_sentiment,
                confidence=confidence,
                reasons=reasons,
                social_metrics=metrics
            )

            assessments.append(assessment)

        return assessments

    def assess_overall_vibe(
        self,
        symbol: str,
        platforms: List[str] = None,
        time_period: str = "24h"
    ) -> VibeAssessment:
        """
        Assess the overall vibe for a symbol across all platforms.

        Args:
            symbol: Symbol to assess
            platforms: List of platforms to check (default: all)
            time_period: Time period to analyze

        Returns:
            Single VibeAssessment object representing overall vibe
        """
        platform_assessments = self.assess_vibe(symbol, platforms, time_period)

        if not platform_assessments:
            return VibeAssessment(
                symbol=symbol,
                platform="all",
                vibe_score=50.0,  # Neutral
                sentiment=SentimentScore.NEUTRAL,
                confidence=0.1,  # Low confidence due to no data
                reasons=["No social media posts found on any platform"]
            )

        # Calculate weighted average vibe score based on confidence
        total_weight = sum(a.confidence for a in platform_assessments)
        if total_weight == 0:
            weighted_vibe_score = 50.0
            overall_confidence = 0.1
        else:
            weighted_vibe_score = sum(a.vibe_score * a.confidence for a in platform_assessments) / total_weight
            overall_confidence = min(0.9, sum(a.confidence for a in platform_assessments) / len(platform_assessments))

        # Determine overall sentiment (simple majority)
        sentiment_counts = {}
        for a in platform_assessments:
            sentiment_counts[a.sentiment] = sentiment_counts.get(a.sentiment, 0) + 1

        if sentiment_counts:
            overall_sentiment = max(sentiment_counts.keys(), key=lambda s: sentiment_counts[s])
        else:
            overall_sentiment = SentimentScore.NEUTRAL

        # Aggregate reasons from all platforms
        all_reasons = []
        for a in platform_assessments:
            all_reasons.extend(a.reasons)

        return VibeAssessment(
            symbol=symbol,
            platform="all",
            vibe_score=weighted_vibe_score,
            sentiment=overall_sentiment,
            confidence=overall_confidence,
            reasons=all_reasons
        )

    def get_metrics(self, symbol: str) -> SocialMediaMetrics:
        """
        Get social metrics for a symbol.

        Args:
            symbol: Symbol to get metrics for

        Returns:
            SocialMediaMetrics object
        """
        # In a real implementation, this would aggregate data from multiple platforms
        # For testing purposes, return mock data

        # Fetch posts from Twitter
        twitter_posts = self.fetch_posts(symbol, "twitter", max_posts=50)

        # Calculate metrics
        if twitter_posts:
            return self.calculate_metrics(twitter_posts, symbol, "twitter")
        else:
            # Return empty metrics if no posts found
            return SocialMediaMetrics(
                platform="twitter",
                symbol=symbol,
                post_count=0,
                total_likes=0,
                total_shares=0,
                total_comments=0,
                unique_authors=0
            )
