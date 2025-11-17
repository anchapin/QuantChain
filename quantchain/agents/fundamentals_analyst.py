"""Fundamentals Analyst Agent - Analyzes financial statements and earnings reports."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base import (
    AgentAnalysis,
    AgentArgument,
    AgentRole,
    BaseSpecializedAgent,
    RecommendationType,
)


@dataclass
class FinancialMetrics:
    """Financial metrics for fundamentals analysis."""

    revenue: Optional[float] = None
    revenue_growth: Optional[float] = None
    net_income: Optional[float] = None
    earnings_per_share: Optional[float] = None
    price_to_earnings: Optional[float] = None
    price_to_sales: Optional[float] = None
    debt_to_equity: Optional[float] = None
    return_on_equity: Optional[float] = None
    free_cash_flow: Optional[float] = None
    profit_margin: Optional[float] = None
    book_value_per_share: Optional[float] = None
    market_cap: Optional[float] = None


@dataclass
class EarningsData:
    """Earnings report data."""

    quarter: str
    year: int
    eps_actual: Optional[float] = None
    eps_estimated: Optional[float] = None
    revenue_actual: Optional[float] = None
    revenue_estimated: Optional[float] = None
    beat_eps: Optional[bool] = None
    beat_revenue: Optional[bool] = None
    guidance: Optional[str] = None


class FundamentalsAnalystAgent(BaseSpecializedAgent):
    """Agent specializing in fundamental analysis of companies."""

    def __init__(
        self,
        config: Any,
        llm_provider: Any,
        data_connector: Optional[Any] = None,
    ):
        """Initialize the fundamentals analyst agent.

        Args:
            config: QuantChain configuration
            llm_provider: LLM provider for analysis
            data_connector: Financial data connector (e.g., Alpha Vantage)
        """
        super().__init__(config, llm_provider, AgentRole.FUNDAMENTALS)
        self.data_connector = data_connector
        self.logger = logging.getLogger(__name__)

        # Configuration
        self.min_data_quality_score = self.agent_config.get(
            "min_data_quality_score", 70.0
        )
        self.pe_ratio_thresholds = self.agent_config.get(
            "pe_ratio_thresholds", {"overvalued": 30, "undervalued": 10}
        )
        self.debt_to_equity_limit = self.agent_config.get("debt_to_equity_limit", 2.0)
        self.roe_threshold = self.agent_config.get("roe_threshold", 15.0)

    def analyze(self, symbol: str, **kwargs) -> AgentAnalysis:
        """Perform fundamental analysis for a given symbol.

        Args:
            symbol: Trading symbol to analyze
            **kwargs: Additional analysis parameters

        Returns:
            AgentAnalysis with fundamental analysis recommendation
        """
        try:
            self.logger.info(f"Performing fundamental analysis for {symbol}")

            # Gather financial data
            financial_metrics = self._get_financial_metrics(symbol)
            earnings_data = self._get_earnings_data(symbol)

            # Validate data quality
            data_quality_score = self._calculate_data_quality(
                financial_metrics, earnings_data
            )

            if data_quality_score < self.min_data_quality_score:
                return self._create_base_analysis(
                    symbol=symbol,
                    recommendation=RecommendationType.HOLD,
                    confidence_score=data_quality_score,
                    reasoning=f"Insufficient fundamental data quality (score: {data_quality_score:.1f})",
                    data_sources=["financial_statements", "earnings_reports"],
                    metadata={"data_quality_score": data_quality_score},
                )

            # Perform fundamental analysis
            fundamental_score, reasoning = self._analyze_fundamentals(
                financial_metrics, earnings_data
            )

            # Generate recommendation based on fundamental score
            recommendation = self._score_to_recommendation(fundamental_score)

            return self._create_base_analysis(
                symbol=symbol,
                recommendation=recommendation,
                confidence_score=fundamental_score,
                reasoning=reasoning,
                data_sources=[
                    "financial_statements",
                    "earnings_reports",
                    "market_data",
                ],
                metadata={
                    "financial_metrics": financial_metrics.__dict__,
                    "earnings_data": [ed.__dict__ for ed in earnings_data],
                    "fundamental_score": fundamental_score,
                    "data_quality_score": data_quality_score,
                },
            )

        except Exception as e:
            self.logger.error(f"Error in fundamental analysis for {symbol}: {str(e)}")
            return self._create_base_analysis(
                symbol=symbol,
                recommendation=RecommendationType.HOLD,
                confidence_score=0.0,
                reasoning=f"Fundamental analysis failed: {str(e)}",
                data_sources=["error"],
            )

    def create_argument(self, context: Dict[str, Any]) -> AgentArgument:
        """Create an argument for the debate phase based on fundamental analysis.

        Args:
            context: Context including other agents' analyses

        Returns:
            AgentArgument for portfolio committee debate
        """
        symbol = context.get("symbol", "")
        fundamental_analysis = context.get("fundamentals_analysis")
        other_analyses = context.get("other_analyses", {})

        if not fundamental_analysis:
            return AgentArgument(
                agent_role=self.role,
                argument_type="neutral",
                target_agent=None,
                reasoning="No fundamental analysis available",
                evidence=[],
                confidence_impact=0.0,
            )

        # Create argument supporting or opposing based on fundamental strength
        fundamental_score = fundamental_analysis.metadata.get("fundamental_score", 50)

        if fundamental_score >= 75:
            return AgentArgument(
                agent_role=self.role,
                argument_type="support",
                target_agent=None,
                reasoning=f"Strong fundamentals support BUY recommendation. Score: {fundamental_score}/100",
                evidence=self._extract_fundamental_evidence(fundamental_analysis),
                confidence_impact=20.0,
            )
        elif fundamental_score <= 25:
            return AgentArgument(
                agent_role=self.role,
                argument_type="oppose",
                target_agent=None,
                reasoning=f"Weak fundamentals justify SELL recommendation. Score: {fundamental_score}/100",
                evidence=self._extract_fundamental_evidence(fundamental_analysis),
                confidence_impact=-20.0,
            )
        else:
            return AgentArgument(
                agent_role=self.role,
                argument_type="neutral",
                target_agent=None,
                reasoning=f"Mixed fundamental indicators suggest HOLD. Score: {fundamental_score}/100",
                evidence=self._extract_fundamental_evidence(fundamental_analysis),
                confidence_impact=0.0,
            )

    def _get_financial_metrics(self, symbol: str) -> FinancialMetrics:
        """Get financial metrics for the symbol.

        Args:
            symbol: Trading symbol

        Returns:
            FinancialMetrics object
        """
        if not self.data_connector:
            # Return empty metrics if no connector
            return FinancialMetrics()

        try:
            # In a real implementation, this would fetch from financial data provider
            # For now, return mock data
            return FinancialMetrics(
                revenue=1000000.0,
                revenue_growth=15.0,
                net_income=100000.0,
                earnings_per_share=2.5,
                price_to_earnings=20.0,
                price_to_sales=2.0,
                debt_to_equity=0.5,
                return_on_equity=18.0,
                free_cash_flow=150000.0,
                profit_margin=10.0,
                book_value_per_share=25.0,
                market_cap=50000000.0,
            )
        except Exception as e:
            self.logger.error(f"Error getting financial metrics for {symbol}: {str(e)}")
            return FinancialMetrics()

    def _get_earnings_data(self, symbol: str) -> List[EarningsData]:
        """Get earnings data for the symbol.

        Args:
            symbol: Trading symbol

        Returns:
            List of EarningsData objects
        """
        if not self.data_connector:
            return []

        try:
            # In a real implementation, this would fetch from earnings data provider
            # For now, return mock data
            current_quarter = (datetime.now().month - 1) // 3 + 1
            return [
                EarningsData(
                    quarter=f"Q{current_quarter}",
                    year=datetime.now().year,
                    eps_actual=2.5,
                    eps_estimated=2.3,
                    revenue_actual=1000000.0,
                    revenue_estimated=950000.0,
                    beat_eps=True,
                    beat_revenue=True,
                    guidance="Positive outlook for next quarter",
                )
            ]
        except Exception as e:
            self.logger.error(f"Error getting earnings data for {symbol}: {str(e)}")
            return []

    def _calculate_data_quality(
        self, financial_metrics: FinancialMetrics, earnings_data: List[EarningsData]
    ) -> float:
        """Calculate data quality score.

        Args:
            financial_metrics: Financial metrics
            earnings_data: Earnings data

        Returns:
            Data quality score (0-100)
        """
        score = 0.0
        max_score = 100.0

        # Check financial metrics completeness
        financial_fields = [
            financial_metrics.revenue,
            financial_metrics.net_income,
            financial_metrics.earnings_per_share,
            financial_metrics.price_to_earnings,
            financial_metrics.return_on_equity,
        ]
        financial_completeness = sum(
            1 for field in financial_fields if field is not None
        ) / len(financial_fields)
        score += financial_completeness * 40

        # Check earnings data completeness
        if earnings_data:
            latest_earnings = earnings_data[0]
            earnings_fields = [
                latest_earnings.eps_actual,
                latest_earnings.eps_estimated,
                latest_earnings.revenue_actual,
                latest_earnings.revenue_estimated,
            ]
            earnings_completeness = sum(
                1 for field in earnings_fields if field is not None
            ) / len(earnings_fields)
            score += earnings_completeness * 40

        # Check data recency (earnings should be within last 6 months)
        if earnings_data:
            latest_date = datetime(
                earnings_data[0].year,
                ((int(earnings_data[0].quarter[1]) - 1) * 3 + 1),
                1,
            )
            days_since_earnings = (datetime.now() - latest_date).days
            if days_since_earnings <= 180:
                score += 20
            elif days_since_earnings <= 365:
                score += 10

        return min(score, max_score)

    def _analyze_fundamentals(
        self, financial_metrics: FinancialMetrics, earnings_data: List[EarningsData]
    ) -> tuple[float, str]:
        """Analyze fundamentals and return score with reasoning.

        Args:
            financial_metrics: Financial metrics
            earnings_data: Earnings data

        Returns:
            Tuple of (score, reasoning)
        """
        score = 50.0  # Neutral starting point
        reasoning_parts = []

        # P/E ratio analysis
        if financial_metrics.price_to_earnings:
            if (
                financial_metrics.price_to_earnings
                < self.pe_ratio_thresholds["undervalued"]
            ):
                score += 15
                reasoning_parts.append(
                    f"Low P/E ratio ({financial_metrics.price_to_earnings:.1f}) suggests undervaluation"
                )
            elif (
                financial_metrics.price_to_earnings
                > self.pe_ratio_thresholds["overvalued"]
            ):
                score -= 15
                reasoning_parts.append(
                    f"High P/E ratio ({financial_metrics.price_to_earnings:.1f}) suggests overvaluation"
                )

        # Debt-to-equity analysis
        if financial_metrics.debt_to_equity:
            if financial_metrics.debt_to_equity < self.debt_to_equity_limit:
                score += 10
                reasoning_parts.append(
                    f"Healthy debt-to-equity ratio ({financial_metrics.debt_to_equity:.2f})"
                )
            else:
                score -= 10
                reasoning_parts.append(
                    f"High debt-to-equity ratio ({financial_metrics.debt_to_equity:.2f})"
                )

        # Return on equity analysis
        if financial_metrics.return_on_equity:
            if financial_metrics.return_on_equity > self.roe_threshold:
                score += 10
                reasoning_parts.append(
                    f"Strong ROE ({financial_metrics.return_on_equity:.1f}%)"
                )
            else:
                score -= 5
                reasoning_parts.append(
                    f"Weak ROE ({financial_metrics.return_on_equity:.1f}%)"
                )

        # Earnings analysis
        if earnings_data:
            latest_earnings = earnings_data[0]
            if latest_earnings.beat_eps:
                score += 10
                reasoning_parts.append("Beat EPS estimates")
            if latest_earnings.beat_revenue:
                score += 10
                reasoning_parts.append("Beat revenue estimates")

        # Revenue growth analysis
        if financial_metrics.revenue_growth:
            if financial_metrics.revenue_growth > 10:
                score += 10
                reasoning_parts.append(
                    f"Strong revenue growth ({financial_metrics.revenue_growth:.1f}%)"
                )
            elif financial_metrics.revenue_growth < 0:
                score -= 10
                reasoning_parts.append(
                    f"Negative revenue growth ({financial_metrics.revenue_growth:.1f}%)"
                )

        # Combine reasoning
        reasoning = (
            "; ".join(reasoning_parts)
            if reasoning_parts
            else "Mixed fundamental indicators"
        )

        return max(0, min(100, score)), reasoning

    def _score_to_recommendation(self, score: float) -> RecommendationType:
        """Convert fundamental score to recommendation.

        Args:
            score: Fundamental score (0-100)

        Returns:
            RecommendationType
        """
        if score >= 75:
            return RecommendationType.BUY
        elif score <= 25:
            return RecommendationType.SELL
        else:
            return RecommendationType.HOLD

    def _extract_fundamental_evidence(self, analysis: AgentAnalysis) -> List[str]:
        """Extract key fundamental evidence from analysis.

        Args:
            analysis: AgentAnalysis with fundamental data

        Returns:
            List of evidence points
        """
        evidence = []
        financial_metrics = analysis.metadata.get("financial_metrics", {})

        # Key fundamental indicators
        if financial_metrics.get("price_to_earnings"):
            evidence.append(f"P/E Ratio: {financial_metrics['price_to_earnings']:.1f}")
        if financial_metrics.get("return_on_equity"):
            evidence.append(f"ROE: {financial_metrics['return_on_equity']:.1f}%")
        if financial_metrics.get("debt_to_equity"):
            evidence.append(f"Debt/Equity: {financial_metrics['debt_to_equity']:.2f}")
        if financial_metrics.get("revenue_growth"):
            evidence.append(
                f"Revenue Growth: {financial_metrics['revenue_growth']:.1f}%"
            )

        return evidence
