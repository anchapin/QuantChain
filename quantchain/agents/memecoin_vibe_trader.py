"""Memecoin Vibe Trader Agent - Autonomous trading agent for memecoins."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol

from langgraph.graph import END, StateGraph

from ..connectors.dexscreener_connector import DexscreenerDataConnector
from ..core.exceptions import QuantChainError
from ..tools.execution import AlpacaExecutionTool
from ..tools.social_media_scraper import SocialMediaScraper, SocialMetrics


class LLMProtocol(Protocol):
    """Protocol for LLM interface."""

    def invoke(self, prompt: str) -> Any:
        """Invoke the LLM with a prompt."""
        ...


class MockLLM:
    """Simple mock LLM for testing."""

    def __init__(self, response_text: str = ""):
        self.response_text = response_text

    def invoke(self, prompt: str) -> Any:
        """Return mock response."""

        class MockResponse:
            def __init__(self, content: str):
                self.content = content

        return MockResponse(self.response_text)


@dataclass
class TokenPair:
    """Token pair data structure."""

    address: str
    symbol: str
    name: str
    liquidity: float
    volume_24h: float
    created_at: datetime
    dex: str
    base_token_address: Optional[str] = None
    quote_token_address: Optional[str] = None


@dataclass
class VibeAssessment:
    """LLM assessment of token vibe."""

    token: TokenPair
    social_metrics: SocialMetrics
    vibe_score: float  # 0-100 scale
    recommendation: str  # "BUY", "HOLD", "SKIP"
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    reasoning: str


@dataclass
class AgentState:
    """State for the LangGraph agent."""

    tokens: Optional[List[TokenPair]] = None
    social_data: Optional[Dict[str, SocialMetrics]] = None
    assessments: Optional[List[VibeAssessment]] = None
    trades_executed: Optional[List[Dict[str, Any]]] = None
    current_step: str = "scan"
    error_message: Optional[str] = None

    def __post_init__(self) -> None:
        if self.tokens is None:
            self.tokens = []
        if self.social_data is None:
            self.social_data = {}
        if self.assessments is None:
            self.assessments = []
        if self.trades_executed is None:
            self.trades_executed = []


@dataclass
class MemecoinVibeTraderConfig:
    """Configuration for the Memecoin Vibe Trader."""

    scan_interval: int = 3600  # seconds
    max_positions: int = 5
    max_allocation_per_trade: float = 0.02  # 2% of portfolio
    min_liquidity_threshold: float = 10000  # USD
    min_vibe_score_threshold: float = 70
    risk_tolerance: str = "MEDIUM"
    time_window: str = "1h"  # Time window for new token detection


class MemecoinVibeTraderError(QuantChainError):
    """Custom exception for Memecoin Vibe Trader."""

    pass


class MemecoinVibeTrader:
    """Autonomous trading agent for memecoin opportunities.

    This agent uses LangGraph to orchestrate the trading workflow:
    1. Scan for new token pairs on DEXs
    2. Gather social media metrics
    3. Use LLM to assess "vibe" and make trading decisions
    4. Execute trades via Alpaca
    """

    def __init__(
        self,
        config: MemecoinVibeTraderConfig,
        dex_connector: DexscreenerDataConnector,
        social_scraper: SocialMediaScraper,
        execution_tool: AlpacaExecutionTool,
        llm: Optional[LLMProtocol] = None,
    ):
        """Initialize the Memecoin Vibe Trader.

        Args:
            config: Agent configuration
            dex_connector: Dexscreener data connector
            social_scraper: Social media scraper tool
            execution_tool: Alpaca execution tool
            llm: Language model for vibe assessment (defaults to GPT-4)
        """
        self.config = config
        self.dex_connector = dex_connector
        self.social_scraper = social_scraper
        self.execution_tool = execution_tool
        self.llm = llm or MockLLM()

        self.logger = logging.getLogger(__name__)

        # Build the LangGraph workflow
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for the trading agent."""

        # Define the workflow
        workflow = StateGraph(AgentState)

        # Add nodes (steps in the process)
        workflow.add_node("scan_tokens", self._scan_tokens)
        workflow.add_node("gather_social_data", self._gather_social_data)
        workflow.add_node("assess_vibes", self._assess_vibes)
        workflow.add_node("execute_trades", self._execute_trades)
        workflow.add_node("handle_error", self._handle_error)

        # Define the flow
        workflow.set_entry_point("scan_tokens")

        # Add conditional edges
        workflow.add_conditional_edges(
            "scan_tokens",
            self._should_continue_after_scan,
            {
                "continue": "gather_social_data",
                "error": "handle_error",
                "end": END,
            },
        )

        workflow.add_conditional_edges(
            "gather_social_data",
            self._should_continue_after_social,
            {
                "continue": "assess_vibes",
                "error": "handle_error",
                "end": END,
            },
        )

        workflow.add_conditional_edges(
            "assess_vibes",
            self._should_continue_after_assessment,
            {
                "continue": "execute_trades",
                "error": "handle_error",
                "end": END,
            },
        )

        workflow.add_conditional_edges(
            "execute_trades",
            self._should_continue_after_execution,
            {
                "continue": END,
                "error": "handle_error",
                "end": END,
            },
        )

        workflow.add_edge("handle_error", END)

        return workflow.compile()

    def run_cycle(self) -> Dict[str, Any]:
        """Run one complete trading cycle.

        Returns:
            Summary of the trading cycle results
        """
        try:
            # Initialize state
            initial_state = AgentState()

            # Run the workflow
            final_state = self.workflow.invoke(initial_state)

            # Normalize final_state to dict for consistent access
            if not isinstance(final_state, dict):
                # Convert AgentState or other object to dict
                final_state = {
                    "error_message": getattr(final_state, "error_message", None),
                    "tokens": getattr(final_state, "tokens", []),
                    "assessments": getattr(final_state, "assessments", []),
                    "trades_executed": getattr(final_state, "trades_executed", []),
                    "current_step": getattr(final_state, "current_step", "unknown"),
                }

            # Extract values from normalized dict
            error_msg = final_state.get("error_message")
            tokens = final_state.get("tokens", [])
            assessments = final_state.get("assessments", [])
            trades = final_state.get("trades_executed", [])

            return {
                "success": error_msg is None,
                "tokens_scanned": len(tokens),
                "assessments_made": len(assessments),
                "trades_executed": len(trades),
                "error_message": error_msg,
                "trades": trades,
            }

        except Exception as e:
            self.logger.error(f"Error running trading cycle: {str(e)}")
            return {
                "success": False,
                "error_message": str(e),
                "tokens_scanned": 0,
                "assessments_made": 0,
                "trades_executed": 0,
                "trades": [],
            }

    def _filter_and_convert_tokens(
        self, raw_pairs: List[Dict[str, Any]]
    ) -> List[TokenPair]:
        """Filter and convert raw token pair data to TokenPair objects.

        Args:
                raw_pairs: Raw token pair data from Dexscreener

        Returns:
        List of TokenPair objects that meet liquidity requirements
        """
        tokens = []
        for pair_data in raw_pairs:
            if pair_data["liquidity"] >= self.config.min_liquidity_threshold:
                token = TokenPair(
                    address=pair_data["address"],
                    symbol=pair_data["symbol"],
                    name=pair_data["name"],
                    liquidity=pair_data["liquidity"],
                    volume_24h=pair_data["volume_24h"],
                    created_at=pair_data["created_at"],
                    dex=pair_data["dex"],
                    base_token_address=pair_data.get("base_token_address"),
                    quote_token_address=pair_data.get("quote_token_address"),
                )
                tokens.append(token)
        return tokens

    def _scan_tokens(self, state: AgentState) -> AgentState:
        """Scan for new token pairs."""
        try:
            self.logger.info("Scanning for new token pairs...")

            # Get new token pairs from Dexscreener
            raw_pairs = self.dex_connector.get_new_token_pairs(
                time_window=self.config.time_window
            )

            # Filter and convert to TokenPair objects
            tokens = self._filter_and_convert_tokens(raw_pairs)

            state.tokens = tokens
            state.current_step = "scan"
            self.logger.info(f"Found {len(tokens)} qualifying new tokens")

        except Exception as e:
            state.error_message = f"Failed to scan tokens: {str(e)}"
            self.logger.error(state.error_message)

        return state

    def _gather_social_data(self, state: AgentState) -> AgentState:
        """Gather social media metrics for tokens."""
        try:
            self.logger.info("Gathering social media data...")

            social_data = {}
            if state.tokens:
                for token in state.tokens:
                    try:
                        metrics = self.social_scraper.get_social_metrics(
                            token.symbol, token.address
                        )
                        social_data[token.symbol] = metrics
                        self.logger.debug(f"Got social data for {token.symbol}")

                    except Exception as e:
                        self.logger.warning(
                            f"Failed to get social data for {token.symbol}: {str(e)}"
                        )
                        # Use default empty metrics
                        social_data[token.symbol] = SocialMetrics()

            state.social_data = social_data
            state.current_step = "social"

        except Exception as e:
            state.error_message = f"Failed to gather social data: {str(e)}"
            self.logger.error(state.error_message)

        return state

    def _assess_vibes(self, state: AgentState) -> AgentState:
        """Use LLM to assess token vibes and make recommendations."""
        try:
            self.logger.info("Assessing token vibes...")

            assessments = []
            if state.tokens:
                for token in state.tokens:
                    try:
                        social_metrics = (state.social_data or {}).get(
                            token.symbol, SocialMetrics()
                        )

                        # Create assessment prompt
                        prompt = self._create_assessment_prompt(token, social_metrics)

                        # Get LLM response
                        response = self.llm.invoke(prompt)

                        # Parse response
                        assessment = self._parse_llm_response(
                            getattr(response, "content", ""), token, social_metrics
                        )
                        assessments.append(assessment)

                        self.logger.debug(
                            f"Assessed {token.symbol}: {assessment.recommendation}"
                        )

                    except Exception as e:
                        self.logger.warning(
                            f"Failed to assess {token.symbol}: {str(e)}"
                        )
                        # Create default SKIP assessment
                        assessments.append(
                            VibeAssessment(
                                token=token,
                                social_metrics=social_metrics,
                                vibe_score=0.0,
                                recommendation="SKIP",
                                risk_level="HIGH",
                                reasoning=f"Assessment failed: {str(e)}",
                            )
                        )

            state.assessments = assessments
            state.current_step = "assessment"

        except Exception as e:
            state.error_message = f"Failed to assess vibes: {str(e)}"
            self.logger.error(state.error_message)

        return state

    def _execute_trades(self, state: AgentState) -> AgentState:
        """Execute trades for qualifying tokens."""
        try:
            self.logger.info("Executing trades...")

            trades_executed = []

            # Get current account balance
            account_balance = self.execution_tool.get_account_balance()
            portfolio_value = account_balance["portfolio_value"]

            # Get current positions
            current_positions = self.execution_tool.get_positions()
            current_position_symbols = {pos["symbol"] for pos in current_positions}

            # Filter assessments for BUY recommendations above threshold
            buy_candidates = [
                assessment
                for assessment in (state.assessments or [])
                if (
                    assessment.recommendation == "BUY"
                    and assessment.vibe_score >= self.config.min_vibe_score_threshold
                    and assessment.token.symbol not in current_position_symbols
                )
            ]

            # Sort by vibe score (highest first)
            buy_candidates.sort(key=lambda x: x.vibe_score, reverse=True)

            # Execute trades within limits
            for assessment in buy_candidates[: self.config.max_positions]:
                try:
                    # Calculate position size
                    position_value = (
                        portfolio_value * self.config.max_allocation_per_trade
                    )

                    # Skip trade if portfolio value is zero or position value is
                    # too small
                    if portfolio_value <= 0 or position_value <= 0:
                        self.logger.info(
                            f"Skipping trade for {assessment.token.symbol}: "
                            f"portfolio_value={portfolio_value}, "
                            f"position_value={position_value}"
                        )
                        continue

                    # TODO: Get actual token price from price oracle or DEX data
                    # For now, estimate token price based on liquidity/volume ratio
                    # This is a simplified approach for backtesting
                    estimated_price = self._estimate_token_price(assessment.token)
                    quantity = (
                        position_value / estimated_price if estimated_price > 0 else 0
                    )

                    # Skip trade if quantity is zero or too small
                    if quantity <= 0:
                        self.logger.info(
                            f"Skipping trade for {assessment.token.symbol}: "
                            f"quantity={quantity}, estimated_price={estimated_price}"
                        )
                        continue

                    # Execute buy order (Alpaca format)
                    order_result = self.execution_tool.execute_market_order(
                        symbol=f"{assessment.token.symbol}/USD",
                        side="buy",
                        quantity=quantity,
                    )

                    trade_info = {
                        "token": assessment.token.symbol,
                        "order_id": order_result.order_id,
                        "quantity": quantity,
                        "vibe_score": assessment.vibe_score,
                        "timestamp": datetime.now().isoformat(),
                    }
                    trades_executed.append(trade_info)

                    self.logger.info(f"Executed trade for {assessment.token.symbol}")

                except Exception as e:
                    self.logger.error(
                        f"Failed to execute trade for {assessment.token.symbol}: "
                        f"{str(e)}"
                    )

            state.trades_executed = trades_executed
            state.current_step = "execution"

        except Exception as e:
            state.error_message = f"Failed to execute trades: {str(e)}"
            self.logger.error(state.error_message)

        return state

    def _handle_error(self, state: AgentState) -> AgentState:
        """Handle errors in the workflow."""
        self.logger.error(f"Workflow error: {state.error_message}")
        return state

    def _should_continue_after_scan(self, state: AgentState) -> str:
        """Determine next step after scanning."""
        if state.error_message:
            return "error"
        if not state.tokens:
            self.logger.info("No tokens found, ending cycle")
            return "end"
        return "continue"

    def _should_continue_after_social(self, state: AgentState) -> str:
        """Determine next step after gathering social data."""
        if state.error_message:
            return "error"
        if not state.social_data:
            self.logger.info("No social data gathered, ending cycle")
            return "end"
        return "continue"

    def _should_continue_after_assessment(self, state: AgentState) -> str:
        """Determine next step after vibe assessment."""
        if state.error_message:
            return "error"
        if not state.assessments:
            self.logger.info("No assessments made, ending cycle")
            return "end"
        return "continue"

    def _should_continue_after_execution(self, state: AgentState) -> str:
        """Determine next step after trade execution."""
        # Always continue to end, even if no trades were executed
        return "continue"

    def _create_assessment_prompt(
        self, token: TokenPair, social_metrics: SocialMetrics
    ) -> str:
        """Create the LLM prompt for vibe assessment."""
        return f"""Analyze this cryptocurrency token and determine if it's worth trading
        based on its "vibe" - the combination of cultural relevance, social momentum,
        and market potential.

Token Information:
- Symbol: {token.symbol}
- Name: {token.name}
- Liquidity: ${token.liquidity:,.0f}
- 24h Volume: ${token.volume_24h:,.0f}
- DEX: {token.dex}

Social Metrics:
- Telegram Followers: {social_metrics.telegram_followers:,}
- Twitter Followers: {social_metrics.twitter_followers:,}
- Recent Posts: {social_metrics.recent_posts}
- Engagement Rate: {social_metrics.engagement_rate:.3f}
- Sentiment Score: {social_metrics.sentiment_score:.3f}

Please assess the token's "vibe" on a scale of 0-100, considering:
1. Name creativity and memetic potential
2. Social media momentum and community size
3. Trading volume relative to liquidity
4. Overall market sentiment

Provide your response in this exact format:
VIBE_SCORE: [0-100]
RECOMMENDATION: [BUY/HOLD/SKIP]
RISK_LEVEL: [LOW/MEDIUM/HIGH]
REASONING: [Your detailed analysis in 2-3 sentences]
"""

    def _parse_llm_response(
        self, response: str, token: TokenPair, social_metrics: SocialMetrics
    ) -> VibeAssessment:
        """Parse the LLM response into a VibeAssessment."""
        lines = response.strip().split("\n")

        vibe_score = 50.0
        recommendation = "HOLD"
        risk_level = "MEDIUM"
        reasoning = "LLM assessment parsing failed"

        import re

        # Regex patterns for robust parsing
        vibe_score_pattern = re.compile(
            r"^VIBE_SCORE:\s*(-?\d+(?:\.\d+)?)", re.IGNORECASE
        )
        recommendation_pattern = re.compile(
            r"^RECOMMENDATION:\s*(BUY|SELL|HOLD|SKIP)", re.IGNORECASE
        )
        risk_level_pattern = re.compile(
            r"^RISK_LEVEL:\s*(LOW|MEDIUM|HIGH|VERY_HIGH)", re.IGNORECASE
        )
        reasoning_pattern = re.compile(r"^REASONING:\s*(.+)", re.IGNORECASE | re.DOTALL)

        for line in lines:
            line = line.strip()

            if vibe_match := vibe_score_pattern.match(line):
                try:
                    score = float(vibe_match.group(1))
                    vibe_score = max(0, min(100, score))  # Clamp to 0-100
                except ValueError:
                    pass

            if rec_match := recommendation_pattern.match(line):
                recommendation = rec_match.group(1).upper()

            if risk_match := risk_level_pattern.match(line):
                risk_level = risk_match.group(1).upper()

            if reason_match := reasoning_pattern.match(line):
                reasoning = reason_match.group(1).strip()

        return VibeAssessment(
            token=token,
            social_metrics=social_metrics,
            vibe_score=vibe_score,
            recommendation=recommendation,
            risk_level=risk_level,
            reasoning=reasoning,
        )

    def _estimate_token_price(self, token: TokenPair) -> float:
        """Estimate token price based on liquidity and volume data.

        This is a simplified approach for backtesting purposes.
        In production, you would use a price oracle or DEX data.

        Args:
            token: The token pair to estimate price for

        Returns:
            Estimated price in USD (defaults to 1.0 if calculation fails)
        """
        try:
            # Simple heuristic: price = volume / (liquidity * 10)
            # This assumes most tokens have reasonable volume relative to liquidity
            # The factor of 10 is arbitrary to keep prices in a reasonable range
            if token.volume_24h > 0 and token.liquidity > 0:
                return min(
                    token.volume_24h / (token.liquidity * 10), 100.0
                )  # Cap at $100
            return 1.0  # Default to $1 if no data
        except Exception:
            return 1.0  # Default to $1 on error
