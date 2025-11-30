"""Risk Manager Agent - Portfolio risk assessment and position sizing."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .base import (
    AgentAnalysis,
    AgentArgument,
    AgentRole,
    BaseSpecializedAgent,
    RecommendationType,
)


@dataclass
class RiskMetrics:
    """Risk assessment metrics."""

    value_at_risk_1d: float  # 1-day VaR (95% confidence)
    value_at_risk_5d: float  # 5-day VaR (95% confidence)
    max_drawdown: float
    current_drawdown: float
    sharpe_ratio: float
    volatility: float  # Annualized volatility
    beta: float  # Market beta
    correlation_to_market: float
    position_concentration: float  # Largest position as % of portfolio
    sector_exposure: Dict[str, float]  # Sector exposure percentages
    liquidity_score: float  # 0-100, higher = more liquid


@dataclass
class PositionRisk:
    """Risk assessment for a specific position."""

    symbol: str
    position_size: float  # Dollar value
    position_weight: float  # % of portfolio
    stop_loss: Optional[float]  # Suggested stop loss price
    take_profit: Optional[float]  # Suggested take profit price
    position_risk: float  # Risk amount (position_size * risk_percent)
    risk_reward_ratio: float  # Potential reward / potential risk
    volatility: float  # Position volatility
    beta: float  # Position beta
    liquidity_risk: float  # 0-100, higher = riskier
    sector: Optional[str]


@dataclass
class PortfolioRisk:
    """Overall portfolio risk assessment."""

    total_value: float
    cash_position: float
    total_risk: float  # Total portfolio risk
    risk_budget_used: float  # % of risk budget used
    diversification_score: float  # 0-100, higher = more diversified
    leverage_ratio: float  # Total exposure / portfolio value
    positions: List[PositionRisk]
    portfolio_metrics: RiskMetrics


@dataclass
class RiskParameters:
    """Risk management parameters."""

    max_portfolio_risk: float  # Max risk as % of portfolio
    max_position_size: float  # Max single position as % of portfolio
    max_sector_exposure: float  # Max sector exposure as % of portfolio
    min_liquidity_score: float  # Minimum acceptable liquidity score
    max_leverage: float  # Maximum leverage ratio
    stop_loss_atr_multiplier: float  # ATR multiplier for stop losses
    position_sizing_method: str  # "fixed", "kelly", "volatility"


class RiskManagerAgent(BaseSpecializedAgent):
    """Agent specializing in risk management and position sizing."""

    def __init__(
        self,
        config: Any,
        llm_provider: Any,
        portfolio_connector: Optional[Any] = None,
        market_data_connector: Optional[Any] = None,
    ):
        """Initialize the risk manager agent.

        Args:
            config: QuantChain configuration
            llm_provider: LLM provider for risk analysis
            portfolio_connector: Portfolio data connector
            market_data_connector: Market data connector
        """
        super().__init__(config, llm_provider, AgentRole.RISK_MANAGER)
        self.portfolio_connector = portfolio_connector
        self.market_data_connector = market_data_connector
        self.logger = logging.getLogger(__name__)

        # Risk parameters
        self.risk_params = RiskParameters(
            max_portfolio_risk=self.agent_config.get("max_portfolio_risk", 0.02),  # 2%
            max_position_size=self.agent_config.get("max_position_size", 0.05),  # 5%
            max_sector_exposure=self.agent_config.get(
                "max_sector_exposure", 0.25
            ),  # 25%
            min_liquidity_score=self.agent_config.get("min_liquidity_score", 30.0),
            max_leverage=self.agent_config.get("max_leverage", 1.0),
            stop_loss_atr_multiplier=self.agent_config.get(
                "stop_loss_atr_multiplier", 2.0
            ),
            position_sizing_method=self.agent_config.get(
                "position_sizing_method", "volatility"
            ),
        )

    def analyze(self, symbol: str, **kwargs: Any) -> AgentAnalysis:
        """Perform risk analysis for a given symbol.

        Args:
            symbol: Trading symbol to analyze
            **kwargs: Additional analysis parameters including:
                - proposed_position_size: Proposed position size in dollars
                - action: "BUY", "SELL", or "HOLD"

        Returns:
            AgentAnalysis with risk analysis recommendation
        """
        try:
            self.logger.info(f"Performing risk analysis for {symbol}")

            # Get current portfolio state
            portfolio_risk = self._get_portfolio_risk()
            if not portfolio_risk:
                return self._create_base_analysis(
                    symbol=symbol,
                    recommendation=RecommendationType.HOLD,
                    confidence_score=50.0,
                    reasoning="Portfolio data unavailable for risk assessment",
                    data_sources=["portfolio_data"],
                    metadata={"risk_available": False},
                )

            # Get proposed action details
            action = kwargs.get("action", "HOLD")
            proposed_size = kwargs.get("proposed_position_size", 0)

            if action not in ["BUY", "SELL"]:
                return self._create_base_analysis(
                    symbol=symbol,
                    recommendation=RecommendationType.HOLD,
                    confidence_score=75.0,
                    reasoning="No action required for risk analysis",
                    data_sources=["portfolio_data"],
                    metadata={
                        "risk_available": True,
                        "portfolio_risk": portfolio_risk.__dict__,
                    },
                )

            # Analyze position-specific risk
            position_risk = self._analyze_position_risk(symbol, proposed_size, action)

            # Assess if action fits within risk parameters
            risk_assessment, reasoning = self._assess_risk_action(
                portfolio_risk, position_risk, action
            )

            # Generate risk-based recommendation
            recommendation = self._risk_to_recommendation(risk_assessment, action)

            return self._create_base_analysis(
                symbol=symbol,
                recommendation=recommendation,
                confidence_score=risk_assessment["confidence"],
                reasoning=reasoning,
                data_sources=["portfolio_data", "market_data", "risk_metrics"],
                metadata={
                    "risk_available": True,
                    "portfolio_risk": portfolio_risk.__dict__,
                    "position_risk": position_risk.__dict__,
                    "risk_assessment": risk_assessment,
                    "recommended_position_size": risk_assessment.get(
                        "recommended_size", proposed_size
                    ),
                },
            )

        except Exception as e:
            self.logger.error(f"Error in risk analysis for {symbol}: {str(e)}")
            return self._create_base_analysis(
                symbol=symbol,
                recommendation=RecommendationType.HOLD,
                confidence_score=0.0,
                reasoning=f"Risk analysis failed: {str(e)}",
                data_sources=["error"],
            )

    def create_argument(self, context: Dict[str, Any]) -> AgentArgument:
        """Create an argument for the debate phase based on risk analysis.

        Args:
            context: Context including other agents' analyses

        Returns:
            AgentArgument for portfolio committee debate
        """
        symbol = context.get("symbol", "")
        risk_analysis = context.get("risk_analysis")
        action = context.get("proposed_action", "HOLD")

        if not risk_analysis or not risk_analysis.metadata.get("risk_available"):
            return AgentArgument(
                agent_role=self.role,
                argument_type="neutral",
                target_agent=None,
                reasoning="Risk analysis unavailable",
                evidence=[],
                confidence_impact=0.0,
            )

        risk_assessment = risk_analysis.metadata.get("risk_assessment", {})
        confidence = risk_assessment.get("confidence", 50)

        # Determine risk argument based on assessment
        if risk_assessment.get("risk_level") == "LOW" and confidence > 70:
            return AgentArgument(
                agent_role=self.role,
                argument_type="support" if action == "BUY" else "neutral",
                target_agent=None,
                reasoning=f"Low risk level ({confidence}% confidence) supports {action} action",
                evidence=self._extract_risk_evidence(risk_analysis, "low_risk"),
                confidence_impact=10.0,
            )
        elif risk_assessment.get("risk_level") == "HIGH":
            return AgentArgument(
                agent_role=self.role,
                argument_type="oppose" if action == "BUY" else "support",
                target_agent=None,
                reasoning=f"High risk level ({confidence}% confidence) opposes {action} action",
                evidence=self._extract_risk_evidence(risk_analysis, "high_risk"),
                confidence_impact=-15.0,
            )
        else:
            return AgentArgument(
                agent_role=self.role,
                argument_type="neutral",
                target_agent=None,
                reasoning=f"Moderate risk level ({confidence}% confidence) - proceed with caution",
                evidence=self._extract_risk_evidence(risk_analysis, "moderate_risk"),
                confidence_impact=0.0,
            )

    def _get_portfolio_risk(self) -> Optional[PortfolioRisk]:
        """Get current portfolio risk assessment.

        Returns:
            PortfolioRisk object or None if unavailable
        """
        if not self.portfolio_connector:
            # Return mock portfolio for testing
            return self._generate_mock_portfolio_risk()

        try:
            # In a real implementation, this would fetch from portfolio data source
            return self._generate_mock_portfolio_risk()
        except Exception as e:
            self.logger.error(f"Error getting portfolio risk: {str(e)}")
            return None

    def _generate_mock_portfolio_risk(self) -> PortfolioRisk:
        """Generate mock portfolio risk data for testing.

        Returns:
            Mock PortfolioRisk
        """
        # Mock positions
        positions = [
            PositionRisk(
                symbol="AAPL",
                position_size=10000.0,
                position_weight=0.10,
                stop_loss=145.0,
                take_profit=165.0,
                position_risk=500.0,
                risk_reward_ratio=2.0,
                volatility=0.25,
                beta=1.2,
                liquidity_risk=20.0,
                sector="Technology",
            ),
            PositionRisk(
                symbol="MSFT",
                position_size=8000.0,
                position_weight=0.08,
                stop_loss=280.0,
                take_profit=320.0,
                position_risk=400.0,
                risk_reward_ratio=1.8,
                volatility=0.22,
                beta=0.9,
                liquidity_risk=15.0,
                sector="Technology",
            ),
        ]

        # Mock portfolio metrics
        portfolio_metrics = RiskMetrics(
            value_at_risk_1d=1500.0,
            value_at_risk_5d=3500.0,
            max_drawdown=0.15,
            current_drawdown=0.05,
            sharpe_ratio=1.2,
            volatility=0.18,
            beta=1.05,
            correlation_to_market=0.85,
            position_concentration=0.10,
            sector_exposure={"Technology": 0.18, "Healthcare": 0.12, "Finance": 0.10},
            liquidity_score=85.0,
        )

        total_value = 100000.0
        total_risk = sum(pos.position_risk for pos in positions)

        return PortfolioRisk(
            total_value=total_value,
            cash_position=20000.0,
            total_risk=total_risk,
            risk_budget_used=total_risk
            / (total_value * self.risk_params.max_portfolio_risk),
            diversification_score=75.0,
            leverage_ratio=1.0,
            positions=positions,
            portfolio_metrics=portfolio_metrics,
        )

    def _analyze_position_risk(
        self, symbol: str, proposed_size: float, action: str
    ) -> PositionRisk:
        """Analyze risk for a specific position.

        Args:
            symbol: Trading symbol
            proposed_size: Proposed position size in dollars
            action: Action type

        Returns:
            PositionRisk object
        """
        # Get market data for the symbol
        if not self.market_data_connector:
            # Return mock data for testing
            return PositionRisk(
                symbol=symbol,
                position_size=proposed_size,
                position_weight=proposed_size / 100000.0,  # Assuming $100k portfolio
                stop_loss=None,
                take_profit=None,
                position_risk=proposed_size * 0.02,  # 2% risk
                risk_reward_ratio=2.0,
                volatility=0.25,
                beta=1.0,
                liquidity_risk=30.0,
                sector="Unknown",
            )

        # In a real implementation, calculate actual metrics from market data
        # For now, return reasonable defaults
        return PositionRisk(
            symbol=symbol,
            position_size=proposed_size,
            position_weight=proposed_size / 100000.0,
            stop_loss=None,  # Would calculate based on ATR
            take_profit=None,  # Would calculate based on risk/reward
            position_risk=proposed_size * 0.02,
            risk_reward_ratio=2.0,
            volatility=0.25,
            beta=1.0,
            liquidity_risk=30.0,
            sector="Unknown",
        )

    def _assess_risk_action(
        self, portfolio_risk: PortfolioRisk, position_risk: PositionRisk, action: str
    ) -> Tuple[Dict[str, Any], str]:
        """Assess if a risk action fits within risk parameters.

        Args:
            portfolio_risk: Current portfolio risk
            position_risk: Position-specific risk
            action: Action type

        Returns:
            Tuple of (risk_assessment_dict, reasoning_str)
        """
        risk_factors = []
        confidence_score = 100.0
        risk_level = "LOW"

        # Check position size limit
        if position_risk.position_weight > self.risk_params.max_position_size:
            risk_factors.append(
                f"Position size {position_risk.position_weight:.1%} exceeds limit {self.risk_params.max_position_size:.1%}"
            )
            confidence_score -= 30
            risk_level = "HIGH"

        # Check portfolio risk budget
        if action == "BUY":
            new_total_risk = portfolio_risk.total_risk + position_risk.position_risk
            new_risk_budget_used = new_total_risk / (
                portfolio_risk.total_value * self.risk_params.max_portfolio_risk
            )
            if new_risk_budget_used > 1.0:
                risk_factors.append(
                    f"Portfolio risk budget would be exceeded ({new_risk_budget_used:.1%})"
                )
                confidence_score -= 40
                risk_level = "HIGH"

        # Check liquidity risk
        if position_risk.liquidity_risk > (100 - self.risk_params.min_liquidity_score):
            risk_factors.append(
                f"High liquidity risk score: {position_risk.liquidity_risk:.1f}"
            )
            confidence_score -= 20

        # Check sector concentration
        current_sector_exposure = portfolio_risk.portfolio_metrics.sector_exposure.get(
            position_risk.sector or "Unknown", 0
        )
        new_sector_exposure = current_sector_exposure + position_risk.position_weight
        if new_sector_exposure > self.risk_params.max_sector_exposure:
            risk_factors.append(
                f"Sector exposure would exceed limit: {new_sector_exposure:.1%}"
            )
            confidence_score -= 25
            if risk_level != "HIGH":
                risk_level = "MODERATE"

        # Calculate recommended position size
        recommended_size = self._calculate_recommended_position_size(
            portfolio_risk, position_risk
        )

        # Build reasoning
        if risk_factors:
            reasoning = f"Risk concerns: {'; '.join(risk_factors)}"
        else:
            reasoning = "Action fits within risk parameters"

        if action == "BUY":
            reasoning += f". Recommended position size: ${recommended_size:,.0f}"

        risk_assessment = {
            "risk_level": risk_level,
            "confidence": max(0, confidence_score),
            "recommended_size": recommended_size,
            "risk_factors": risk_factors,
            "position_weight": position_risk.position_weight,
            "position_risk": position_risk.position_risk,
            "risk_reward_ratio": position_risk.risk_reward_ratio,
        }

        return risk_assessment, reasoning

    def _calculate_recommended_position_size(
        self, portfolio_risk: PortfolioRisk, position_risk: PositionRisk
    ) -> float:
        """Calculate recommended position size based on risk parameters.

        Args:
            portfolio_risk: Current portfolio risk
            position_risk: Position risk data

        Returns:
            Recommended position size in dollars
        """
        if self.risk_params.position_sizing_method == "fixed":
            # Fixed percentage method
            return portfolio_risk.total_value * self.risk_params.max_position_size

        elif self.risk_params.position_sizing_method == "volatility":
            # Volatility-based sizing (simplified Kelly criterion)
            # Size = (ExpectedReturn * WinRate) / (Volatility^2)
            # Using assumed values for demo
            expected_return = 0.15  # 15% annual return
            win_rate = 0.55  # 55% win rate
            volatility = position_risk.volatility

            if volatility > 0:
                kelly_fraction = (expected_return * win_rate) / (volatility**2)
                # Apply fractional Kelly (25% of full Kelly for safety)
                kelly_fraction *= 0.25
                # Cap at maximum position size
                kelly_fraction = min(kelly_fraction, self.risk_params.max_position_size)
                return portfolio_risk.total_value * kelly_fraction
            else:
                return portfolio_risk.total_value * 0.01  # Default 1%

        else:  # Default to fixed
            return portfolio_risk.total_value * self.risk_params.max_position_size

    def _risk_to_recommendation(
        self, risk_assessment: Dict[str, Any], action: str
    ) -> RecommendationType:
        """Convert risk assessment to recommendation.

        Args:
            risk_assessment: Risk assessment dictionary
            action: Proposed action

        Returns:
            RecommendationType
        """
        risk_level = risk_assessment.get("risk_level", "MODERATE")
        confidence = risk_assessment.get("confidence", 50)

        if risk_level == "HIGH" or confidence < 30:
            return RecommendationType.HOLD
        elif risk_level == "LOW" and confidence > 70:
            return (
                RecommendationType.BUY if action == "BUY" else RecommendationType.SELL
            )
        else:
            return RecommendationType.HOLD

    def _extract_risk_evidence(
        self, risk_analysis: AgentAnalysis, risk_type: str
    ) -> List[str]:
        """Extract key risk evidence from analysis.

        Args:
            risk_analysis: Risk analysis
            risk_type: Type of risk ("low_risk", "high_risk", "moderate_risk")

        Returns:
            List of evidence points
        """
        evidence = []
        risk_assessment = risk_analysis.metadata.get("risk_assessment", {})
        position_risk = risk_analysis.metadata.get("position_risk", {})
        portfolio_risk = risk_analysis.metadata.get("portfolio_risk", {})

        evidence.append(f"Risk Level: {risk_assessment.get('risk_level', 'UNKNOWN')}")
        evidence.append(f"Confidence: {risk_assessment.get('confidence', 0):.1f}%")
        evidence.append(
            f"Position Weight: {position_risk.get('position_weight', 0):.1%}"
        )
        evidence.append(
            f"Risk/Reward Ratio: {position_risk.get('risk_reward_ratio', 0):.1f}"
        )

        if portfolio_risk:
            evidence.append(
                f"Current Portfolio Risk: {portfolio_risk.get('risk_budget_used', 0):.1%}"
            )
            evidence.append(
                f"Diversification Score: {portfolio_risk.get('diversification_score', 0):.1f}"
            )

        risk_factors = risk_assessment.get("risk_factors", [])
        if risk_factors:
            evidence.append(f"Risk Factors: {len(risk_factors)} identified")

        return evidence
