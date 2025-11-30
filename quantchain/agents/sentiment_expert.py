"""Sentiment Expert Agent - Processes news sentiment and social media analysis."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .base import (
    AgentAnalysis,
    AgentArgument,
    AgentRole,
    BaseSpecializedAgent,
    RecommendationType,
)


@dataclass
class NewsArticle:
    """News article data for sentiment analysis."""

    title: str
    content: str
    source: str
    published_at: datetime
    url: Optional[str] = None
    relevance_score: Optional[float] = None
    sentiment_score: Optional[float] = None


@dataclass
class SocialMediaPost:
    """Social media post data for sentiment analysis."""

    platform: str  # Twitter, Reddit, etc.
    content: str
    author: str
    published_at: datetime
    likes: int = 0
    shares: int = 0
    comments: int = 0
    relevance_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    followers_count: Optional[int] = None


@dataclass
class SentimentMetrics:
    """Aggregated sentiment metrics."""

    overall_sentiment: float  # -100 to 100
    news_sentiment: float  # -100 to 100
    social_sentiment: float  # -100 to 100
    sentiment_trend: str  # "improving", "declining", "stable"
    sentiment_volatility: float  # 0 to 100
    volume_score: float  # 0 to 100 (mention volume)
    influencer_sentiment: float  # Weighted by follower count
    news_count: int
    social_count: int
    timeframe_hours: int


class SentimentExpertAgent(BaseSpecializedAgent):
    """Agent specializing in sentiment analysis from news and social media."""

    def __init__(
        self,
        config: Any,
        llm_provider: Any,
        news_connector: Optional[Any] = None,
        social_connector: Optional[Any] = None,
    ):
        """Initialize the sentiment expert agent.

        Args:
            config: QuantChain configuration
            llm_provider: LLM provider for analysis
            news_connector: News data connector
            social_connector: Social media data connector
        """
        super().__init__(config, llm_provider, AgentRole.SENTIMENT)
        self.news_connector = news_connector
        self.social_connector = social_connector
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.analysis_timeframe_hours = self.agent_config.get(
            "analysis_timeframe_hours", 24
        )
        self.min_mentions_threshold = self.agent_config.get(
            "min_mentions_threshold", 10
        )
        self.sentiment_thresholds = self.agent_config.get(
            "sentiment_thresholds", {"bullish": 30, "bearish": -30}
        )
        self.influencer_min_followers = self.agent_config.get(
            "influencer_min_followers", 10000
        )

    def analyze(self, symbol: str, **kwargs: Any) -> AgentAnalysis:
        """Perform sentiment analysis for a given symbol.

        Args:
            symbol: Trading symbol to analyze
            **kwargs: Additional analysis parameters

        Returns:
            AgentAnalysis with sentiment analysis recommendation
        """
        try:
            self.logger.info(f"Performing sentiment analysis for {symbol}")

            # Gather sentiment data
            news_articles = self._get_news_articles(symbol)
            social_posts = self._get_social_posts(symbol)

            # Validate data quality
            if len(news_articles) == 0 and len(social_posts) == 0:
                return self._create_base_analysis(
                    symbol=symbol,
                    recommendation=RecommendationType.HOLD,
                    confidence_score=30.0,
                    reasoning="No sentiment data available for analysis",
                    data_sources=["news", "social_media"],
                    metadata={
                        "sentiment_available": False,
                        "sentiment_score": 0.0,
                    },
                )

            # Calculate sentiment metrics
            sentiment_metrics = self._calculate_sentiment_metrics(
                news_articles, social_posts
            )

            # Analyze sentiment and generate recommendation
            sentiment_score, reasoning = self._analyze_sentiment(
                sentiment_metrics, symbol
            )
            recommendation = self._sentiment_to_recommendation(sentiment_score)

            return self._create_base_analysis(
                symbol=symbol,
                recommendation=recommendation,
                confidence_score=abs(sentiment_score),
                reasoning=reasoning,
                data_sources=["news", "social_media"],
                metadata={
                    "sentiment_metrics": sentiment_metrics.__dict__,
                    "sentiment_score": sentiment_score,
                    "news_articles_count": len(news_articles),
                    "social_posts_count": len(social_posts),
                },
            )

        except Exception as e:
            self.logger.error(f"Error in sentiment analysis for {symbol}: {str(e)}")
            return self._create_base_analysis(
                symbol=symbol,
                recommendation=RecommendationType.HOLD,
                confidence_score=0.0,
                reasoning=f"Sentiment analysis failed: {str(e)}",
                data_sources=["error"],
            )

    def create_argument(self, context: Dict[str, Any]) -> AgentArgument:
        """Create an argument for the debate phase based on sentiment analysis.

        Args:
            context: Context including other agents' analyses

        Returns:
            AgentArgument for portfolio committee debate
        """
        symbol = context.get("symbol", "")
        sentiment_analysis = context.get("sentiment_analysis")

        if not sentiment_analysis or not sentiment_analysis.metadata.get(
            "sentiment_available"
        ):
            return AgentArgument(
                agent_role=self.role,
                argument_type="neutral",
                target_agent=None,
                reasoning="No sentiment data available",
                evidence=[],
                confidence_impact=0.0,
            )

        sentiment_score = sentiment_analysis.metadata.get("sentiment_score", 0)
        sentiment_metrics = sentiment_analysis.metadata.get("sentiment_metrics", {})

        if sentiment_score > self.sentiment_thresholds["bullish"]:
            return AgentArgument(
                agent_role=self.role,
                argument_type="support",
                target_agent=None,
                reasoning=f"Strong positive sentiment supports BUY recommendation. Score: {sentiment_score}",
                evidence=self._extract_sentiment_evidence(sentiment_metrics, "bullish"),
                confidence_impact=min(15.0, sentiment_score / 10),
            )
        elif sentiment_score < self.sentiment_thresholds["bearish"]:
            return AgentArgument(
                agent_role=self.role,
                argument_type="oppose",
                target_agent=None,
                reasoning=f"Strong negative sentiment supports SELL recommendation. Score: {sentiment_score}",
                evidence=self._extract_sentiment_evidence(sentiment_metrics, "bearish"),
                confidence_impact=max(-15.0, sentiment_score / 10),
            )
        else:
            return AgentArgument(
                agent_role=self.role,
                argument_type="neutral",
                target_agent=None,
                reasoning=f"Neutral sentiment suggests HOLD. Score: {sentiment_score}",
                evidence=self._extract_sentiment_evidence(sentiment_metrics, "neutral"),
                confidence_impact=0.0,
            )

    def _get_news_articles(self, symbol: str) -> List[NewsArticle]:
        """Get news articles for the symbol.

        Args:
            symbol: Trading symbol

        Returns:
            List of NewsArticle objects
        """
        if not self.news_connector:
            return []

        try:
            # In a real implementation, this would fetch from news API
            # For now, return mock data
            cutoff_time = datetime.now() - timedelta(
                hours=self.analysis_timeframe_hours
            )
            return [
                NewsArticle(
                    title=f"{symbol} Reports Strong Quarterly Earnings",
                    content=f"{symbol} announced better than expected quarterly results with revenue growth of 15% year over year.",
                    source="Financial News",
                    published_at=datetime.now() - timedelta(hours=2),
                    relevance_score=0.9,
                    sentiment_score=0.7,
                ),
                NewsArticle(
                    title=f"Analysts Upgrade {symbol} to Buy",
                    content=f"Major investment banks have upgraded {symbol} citing strong fundamentals and positive outlook.",
                    source="Market Watch",
                    published_at=datetime.now() - timedelta(hours=5),
                    relevance_score=0.8,
                    sentiment_score=0.6,
                ),
            ]
        except Exception as e:
            self.logger.error(f"Error getting news articles for {symbol}: {str(e)}")
            return []

    def _get_social_posts(self, symbol: str) -> List[SocialMediaPost]:
        """Get social media posts for the symbol.

        Args:
            symbol: Trading symbol

        Returns:
            List of SocialMediaPost objects
        """
        if not self.social_connector:
            return []

        try:
            # In a real implementation, this would fetch from social media APIs
            # For now, return mock data
            cutoff_time = datetime.now() - timedelta(
                hours=self.analysis_timeframe_hours
            )
            return [
                SocialMediaPost(
                    platform="Twitter",
                    content=f"Just bought more {symbol}! Great technical setup and fundamentals look strong. 🚀",
                    author="TraderJoe",
                    published_at=datetime.now() - timedelta(hours=1),
                    likes=150,
                    shares=45,
                    comments=23,
                    relevance_score=0.8,
                    sentiment_score=0.8,
                    followers_count=50000,
                ),
                SocialMediaPost(
                    platform="Reddit",
                    content=f"{symbol} has been consolidating nicely. Looking for breakout above resistance.",
                    author="Investor123",
                    published_at=datetime.now() - timedelta(hours=3),
                    likes=75,
                    shares=12,
                    comments=8,
                    relevance_score=0.7,
                    sentiment_score=0.4,
                    followers_count=15000,
                ),
            ]
        except Exception as e:
            self.logger.error(f"Error getting social posts for {symbol}: {str(e)}")
            return []

    def _calculate_sentiment_metrics(
        self, news_articles: List[NewsArticle], social_posts: List[SocialMediaPost]
    ) -> SentimentMetrics:
        """Calculate aggregated sentiment metrics.

        Args:
            news_articles: List of news articles
            social_posts: List of social media posts

        Returns:
            SentimentMetrics object
        """
        # Calculate news sentiment
        news_sentiments = [
            article.sentiment_score
            for article in news_articles
            if article.sentiment_score is not None
        ]
        news_sentiment = (
            sum(news_sentiments) / len(news_sentiments) * 100 if news_sentiments else 0
        )

        # Calculate social sentiment
        social_sentiments = [
            post.sentiment_score
            for post in social_posts
            if post.sentiment_score is not None
        ]
        social_sentiment = (
            sum(social_sentiments) / len(social_sentiments) * 100
            if social_sentiments
            else 0
        )

        # Calculate influencer sentiment (weighted by follower count)
        influencer_posts = [
            post
            for post in social_posts
            if post.followers_count
            and post.followers_count >= self.influencer_min_followers
        ]
        if influencer_posts:
            # Filter posts with valid data and cast to proper types
            valid_posts = [
                post
                for post in influencer_posts
                if post.followers_count is not None and post.sentiment_score is not None
            ]
            total_weight = sum(
                int(post.followers_count)
                for post in valid_posts
                if post.followers_count is not None
            )
            influencer_sentiment = float(
                sum(
                    (float(post.sentiment_score) * int(post.followers_count))
                    / total_weight
                    for post in valid_posts
                    if post.sentiment_score is not None
                    and post.followers_count is not None
                )
                * 100
                if total_weight > 0 and valid_posts
                else 0
            )
        else:
            influencer_sentiment = float(social_sentiment)

        # Calculate overall sentiment (weighted: news 60%, social 40%)
        if news_sentiments and social_sentiments:
            overall_sentiment = (news_sentiment * 0.6) + (social_sentiment * 0.4)
        elif news_sentiments:
            overall_sentiment = news_sentiment
        elif social_sentiments:
            overall_sentiment = social_sentiment
        else:
            overall_sentiment = 0

        # Calculate volume score based on mention count
        total_mentions = len(news_articles) + len(social_posts)
        volume_score = min(100, (total_mentions / self.min_mentions_threshold) * 50)

        # Calculate sentiment volatility (simplified - based on sentiment spread)
        all_sentiments = news_sentiments + social_sentiments
        if len(all_sentiments) > 1:
            avg_sentiment = sum(all_sentiments) / len(all_sentiments)
            variance = sum((s - avg_sentiment) ** 2 for s in all_sentiments) / len(
                all_sentiments
            )
            sentiment_volatility = min(100, variance * 100)
        else:
            sentiment_volatility = 0

        # Determine sentiment trend (simplified - just based on recent vs older posts)
        sentiment_trend = (
            "stable"  # Would require more historical data for real trend analysis
        )

        return SentimentMetrics(
            overall_sentiment=overall_sentiment,
            news_sentiment=news_sentiment,
            social_sentiment=social_sentiment,
            sentiment_trend=sentiment_trend,
            sentiment_volatility=sentiment_volatility,
            volume_score=volume_score,
            influencer_sentiment=influencer_sentiment,
            news_count=len(news_articles),
            social_count=len(social_posts),
            timeframe_hours=self.analysis_timeframe_hours,
        )

    def _analyze_sentiment(
        self, sentiment_metrics: SentimentMetrics, symbol: str
    ) -> tuple[float, str]:
        """Analyze sentiment metrics and return score with reasoning.

        Args:
            sentiment_metrics: Sentiment metrics
            symbol: Trading symbol

        Returns:
            Tuple of (score, reasoning)
        """
        score = sentiment_metrics.overall_sentiment
        reasoning_parts = []

        # Overall sentiment
        if sentiment_metrics.overall_sentiment > 30:
            reasoning_parts.append(
                f"Strong positive sentiment ({sentiment_metrics.overall_sentiment:.1f})"
            )
        elif sentiment_metrics.overall_sentiment < -30:
            reasoning_parts.append(
                f"Strong negative sentiment ({sentiment_metrics.overall_sentiment:.1f})"
            )
        else:
            reasoning_parts.append(
                f"Neutral sentiment ({sentiment_metrics.overall_sentiment:.1f})"
            )

        # Volume analysis
        if sentiment_metrics.volume_score > 75:
            reasoning_parts.append(
                f"High mention volume ({sentiment_metrics.volume_score:.1f})"
            )
            score += 10  # Boost confidence for high volume
        elif sentiment_metrics.volume_score < 25:
            reasoning_parts.append(
                f"Low mention volume ({sentiment_metrics.volume_score:.1f})"
            )
            score *= 0.8  # Reduce confidence for low volume

        # Influencer sentiment
        if abs(sentiment_metrics.influencer_sentiment) > 50:
            reasoning_parts.append(
                f"Strong influencer sentiment ({sentiment_metrics.influencer_sentiment:.1f})"
            )

        # Sentiment consistency (low volatility)
        if sentiment_metrics.sentiment_volatility < 30:
            reasoning_parts.append("Consistent sentiment across sources")
        else:
            reasoning_parts.append("High sentiment volatility")

        # News vs social alignment
        if (
            sentiment_metrics.news_sentiment > 20
            and sentiment_metrics.social_sentiment > 20
        ) or (
            sentiment_metrics.news_sentiment < -20
            and sentiment_metrics.social_sentiment < -20
        ):
            reasoning_parts.append("Aligned sentiment across news and social media")
        else:
            reasoning_parts.append("Divergent sentiment between news and social media")

        reasoning = "; ".join(reasoning_parts)

        return max(-100, min(100, score)), reasoning

    def _sentiment_to_recommendation(
        self, sentiment_score: float
    ) -> RecommendationType:
        """Convert sentiment score to recommendation.

        Args:
            sentiment_score: Sentiment score (-100 to 100)

        Returns:
            RecommendationType
        """
        if sentiment_score > 30:
            return RecommendationType.BUY
        elif sentiment_score < -30:
            return RecommendationType.SELL
        else:
            return RecommendationType.HOLD

    def _extract_sentiment_evidence(
        self, sentiment_metrics: Dict[str, Any], sentiment_type: str
    ) -> List[str]:
        """Extract key sentiment evidence from metrics.

        Args:
            sentiment_metrics: Sentiment metrics dictionary
            sentiment_type: Type of sentiment ("bullish", "bearish", "neutral")

        Returns:
            List of evidence points
        """
        evidence = []

        evidence.append(
            f"Overall Sentiment: {sentiment_metrics.get('overall_sentiment', 0):.1f}"
        )
        evidence.append(
            f"News Sentiment: {sentiment_metrics.get('news_sentiment', 0):.1f}"
        )
        evidence.append(
            f"Social Sentiment: {sentiment_metrics.get('social_sentiment', 0):.1f}"
        )

        if sentiment_metrics.get("volume_score", 0) > 75:
            evidence.append("High mention volume")
        if sentiment_metrics.get("influencer_sentiment", 0) > 50:
            evidence.append("Positive influencer sentiment")

        evidence.append(f"News Articles: {sentiment_metrics.get('news_count', 0)}")
        evidence.append(f"Social Posts: {sentiment_metrics.get('social_count', 0)}")

        return evidence
