"""Tutorial mode for human learning-focused trading simulation."""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import warnings

from .trading_execution import (
    TradingExecutionInterface,
    OrderRequest,
    OrderResult,
    OrderStatus,
    Position,
    AccountInfo,
)
from .paper_trading import PaperTradingExecutor
from ..core.reflection import ReflectionEngine, AgentAction
from ..core.config import QuantChainConfig


@dataclass
class TutorialSession:
    """Manages a single tutorial session."""

    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    symbols: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)
    duration_seconds: int = 3600  # 1 hour default
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        if self.end_time is not None:
            return False

        elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        return elapsed < self.duration_seconds

    @property
    def elapsed_time(self) -> int:
        """Get elapsed time in seconds."""
        return int((datetime.now(timezone.utc) - self.start_time).total_seconds())

    def add_objective(self, objective: str) -> None:
        """Add a learning objective."""
        if objective not in self.learning_objectives:
            self.learning_objectives.append(objective)

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "symbols": self.symbols,
            "learning_objectives": self.learning_objectives,
            "duration_seconds": self.duration_seconds,
            "is_active": self.is_active,
            "elapsed_time": self.elapsed_time,
            "metadata": self.metadata,
        }


@dataclass
class TradingMistake:
    """Represents a trading mistake for learning."""

    mistake_id: str
    timestamp: datetime
    order: OrderResult
    mistake_type: str  # timing, sizing, risk_management, market_misread
    severity: str  # minor, moderate, critical
    description: str
    learning_point: str
    market_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert mistake to dictionary."""
        return {
            "mistake_id": self.mistake_id,
            "timestamp": self.timestamp.isoformat(),
            "order_id": self.order.order_id,
            "symbol": self.order.symbol,
            "mistake_type": self.mistake_type,
            "severity": self.severity,
            "description": self.description,
            "learning_point": self.learning_point,
            "market_context": self.market_context,
        }


@dataclass
class DecisionAnalysis:
    """Analysis of a trading decision."""

    timestamp: datetime
    order: OrderResult
    market_drivers: List[str]
    decision_quality: float  # 0-1 scale
    risk_assessment: str
    educational_context: str
    alternatives: List[str]
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "order_id": self.order.order_id,
            "symbol": self.order.symbol,
            "market_drivers": self.market_drivers,
            "decision_quality": self.decision_quality,
            "risk_assessment": self.risk_assessment,
            "educational_context": self.educational_context,
            "alternatives": self.alternatives,
            "confidence": self.confidence,
        }


@dataclass
class TutorialFeedback:
    """Feedback from tutorial session."""

    session_id: str
    timestamp: datetime
    decision_analyses: List[DecisionAnalysis]
    mistakes: List[TradingMistake]
    confidence_score: float
    consistency_score: float
    risk_management_score: float
    learning_progress: Dict[str, Any]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert feedback to dictionary."""
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "decision_analyses": [da.to_dict() for da in self.decision_analyses],
            "mistakes": [m.to_dict() for m in self.mistakes],
            "confidence_score": self.confidence_score,
            "consistency_score": self.consistency_score,
            "risk_management_score": self.risk_management_score,
            "learning_progress": self.learning_progress,
            "recommendations": self.recommendations,
        }


class MarketDriverAnalysis:
    """Analyzes market drivers for educational feedback."""

    def __init__(self, rag_system=None):
        """Initialize market driver analysis."""
        self.rag_system = rag_system
        self.drivers_cache = {}

    def analyze_market_drivers(self, symbol: str, order: OrderResult) -> List[str]:
        """Analyze market drivers for a trade decision."""
        # Check cache first
        cache_key = f"{symbol}_{order.timestamp.isoformat()}"
        if cache_key in self.drivers_cache:
            return self.drivers_cache[cache_key]

        drivers = self._identify_basic_drivers(symbol, order)

        # Add RAG context if available
        if self.rag_system:
            try:
                query = f"Market analysis for {symbol} trading decision"
                relevant_data = self.rag_system.retrieve_relevant_data(query, limit=3)

                for data in relevant_data:
                    if data.data_type == "technical" and symbol == data.symbol:
                        drivers.extend(self._extract_technical_drivers(data.content))
                    elif data.data_type == "news" and symbol in data.content.get(
                        "symbols", []
                    ):
                        drivers.extend(self._extract_news_drivers(data.content))
            except Exception:
                # Fallback if RAG fails
                warnings.warn("RAG system unavailable for market driver analysis")

        # Cache results
        self.drivers_cache[cache_key] = drivers
        return drivers

    def _identify_basic_drivers(self, symbol: str, order: OrderResult) -> List[str]:
        """Identify basic market drivers from order information."""
        drivers = []

        # Price action driver
        if order.avg_fill_price:
            drivers.append(f"Price action at ${order.avg_fill_price:.2f}")

        # Order type driver
        if order.order_type.value == "market":
            drivers.append("Immediate execution requirement")
        elif order.order_type.value == "limit":
            drivers.append(f"Price discipline at ${order.price:.2f}")

        # Position sizing driver
        if order.quantity > 1000:
            drivers.append("Large position sizing strategy")
        elif order.quantity < 100:
            drivers.append("Conservative position sizing")

        return drivers

    def _extract_technical_drivers(self, content: Dict[str, Any]) -> List[str]:
        """Extract technical drivers from content."""
        drivers = []
        indicators = content.get("indicators", {})

        if indicators.get("rsi", 50) < 30:
            drivers.append("Oversold RSI condition")
        elif indicators.get("rsi", 50) > 70:
            drivers.append("Overbought RSI condition")

        if indicators.get("macd_signal", False):
            drivers.append("MACD signal confirmation")

        volume = indicators.get("volume_change", 0)
        if abs(volume) > 0.2:  # 20% volume change
            direction = "above" if volume > 0 else "below"
            drivers.append(f"Volume {direction} average by {abs(volume):.1%}")

        return drivers

    def _extract_news_drivers(self, content: Dict[str, Any]) -> List[str]:
        """Extract news drivers from content."""
        drivers = []
        sentiment = content.get("sentiment", "neutral")

        if sentiment != "neutral":
            drivers.append(f"News sentiment: {sentiment}")

        topics = content.get("topics", [])
        if topics:
            drivers.append(f"Relevant news topics: {', '.join(topics[:2])}")

        return drivers

    def generate_educational_context(self, symbol: str, drivers: List[str]) -> str:
        """Generate educational context for the market drivers."""
        if not drivers:
            return f"No specific market drivers identified for {symbol} trade."

        context = f"Market drivers for {symbol}:\n"
        for i, driver in enumerate(drivers, 1):
            context += f"{i}. {driver}\n"

        context += "\nEducational Notes:\n"
        context += "- Consider how these drivers interact with each other\n"
        context += "- Market drivers often have time-dependent effects\n"
        context += "- Multiple drivers suggest stronger conviction in trade\n"

        return context


class MistakeTracker:
    """Tracks and categorizes trading mistakes."""

    def __init__(self):
        """Initialize mistake tracker."""
        self.mistakes: List[TradingMistake] = []
        self.mistake_patterns: Dict[str, int] = {}

    def analyze_mistake(
        self, order: OrderResult, market_context: Dict[str, Any]
    ) -> Optional[TradingMistake]:
        """Analyze an order for potential mistakes."""
        mistake = None

        # Check for timing mistakes
        if self._is_timing_mistake(order, market_context):
            mistake = self._create_mistake(order, "timing", "moderate", market_context)

        # Check for sizing mistakes
        elif self._is_sizing_mistake(order, market_context):
            mistake = self._create_mistake(order, "sizing", "moderate", market_context)

        # Check for risk management mistakes
        elif self._is_risk_mistake(order, market_context):
            mistake = self._create_mistake(
                order, "risk_management", "critical", market_context
            )

        # Check for market misread mistakes
        elif self._is_market_misread(order, market_context):
            mistake = self._create_mistake(
                order, "market_misread", "minor", market_context
            )

        if mistake:
            self.mistakes.append(mistake)
            self.mistake_patterns[mistake.mistake_type] = (
                self.mistake_patterns.get(mistake.mistake_type, 0) + 1
            )

        return mistake

    def _is_timing_mistake(self, order: OrderResult, context: Dict[str, Any]) -> bool:
        """Check if this is a timing mistake."""
        # Simple heuristic - check if order was filled quickly in volatile market
        volatility = context.get("volatility", 0.15)  # Default 15% volatility
        if volatility > 0.25 and order.status == OrderStatus.FILLED:
            # High volatility with immediate fill might be poor timing
            return True
        return False

    def _is_sizing_mistake(self, order: OrderResult, context: Dict[str, Any]) -> bool:
        """Check if this is a sizing mistake."""
        portfolio_value = context.get("portfolio_value", 100000)
        order_value = (order.avg_fill_price or 0) * order.quantity
        position_size = order_value / portfolio_value

        # Position size > 20% might be too large
        if position_size > 0.2:
            return True
        # Position size < 1% might be too small for meaningful learning
        elif position_size < 0.01:
            return True
        return False

    def _is_risk_mistake(self, order: OrderResult, context: Dict[str, Any]) -> bool:
        """Check if this is a risk management mistake."""
        # Check if order violates basic risk principles
        portfolio_value = context.get("portfolio_value", 100000)
        order_value = (order.avg_fill_price or 0) * order.quantity

        # Using > 50% of portfolio in single position
        if order_value / portfolio_value > 0.5:
            return True

        # No stop loss on volatile position (simplified check)
        volatility = context.get("volatility", 0.15)
        if volatility > 0.3 and order.order_type.value == "market":
            return True

        return False

    def _is_market_misread(self, order: OrderResult, context: Dict[str, Any]) -> bool:
        """Check if this is a market misread mistake."""
        # Simple heuristic - if order is immediately filled but market moves against
        # position
        immediate_move = context.get("immediate_price_move", 0)
        if abs(immediate_move) > 0.01:  # 1% immediate move
            # If market moved against the position immediately
            if (order.side.value == "buy" and immediate_move < 0) or (
                order.side.value == "sell" and immediate_move > 0
            ):
                return True
        return False

    def _create_mistake(
        self,
        order: OrderResult,
        mistake_type: str,
        severity: str,
        context: Dict[str, Any],
    ) -> TradingMistake:
        """Create a mistake object with appropriate details."""
        descriptions = {
            "timing": "Order placed at suboptimal time considering market conditions",
            "sizing": "Position size not aligned with risk management principles",
            "risk_management": "Insufficient risk controls for market conditions",
            "market_misread": "Market direction misinterpreted in trading decision",
        }

        learning_points = {
            "timing": "Wait for clearer signals in volatile markets or use limit "
            "orders",
            "sizing": "Consider position sizing rules (1-5% risk per trade)",
            "risk_management": "Always use stop-losses and respect position size "
            "limits",
            "market_misread": "Confirm market direction with multiple indicators "
            "before trading",
        }

        return TradingMistake(
            mistake_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            order=order,
            mistake_type=mistake_type,
            severity=severity,
            description=descriptions.get(mistake_type, "Identified trading mistake"),
            learning_point=learning_points.get(mistake_type, "Review trading strategy"),
            market_context=context,
        )

    def get_mistake_history(self) -> List[TradingMistake]:
        """Get complete mistake history."""
        return self.mistakes.copy()

    def get_mistake_patterns(self) -> Dict[str, int]:
        """Get patterns in mistake types."""
        return self.mistake_patterns.copy()

    def get_learning_recommendations(self) -> List[str]:
        """Get learning recommendations based on mistake patterns."""
        recommendations = []

        for mistake_type, count in self.mistake_patterns.items():
            if count >= 3:  # Pattern detected after 3 similar mistakes
                if mistake_type == "timing":
                    recommendations.append(
                        "Focus on market timing - study volume and volatility patterns"
                    )
                elif mistake_type == "sizing":
                    recommendations.append(
                        "Review position sizing strategy - implement fixed percentage "
                        "rules"
                    )
                elif mistake_type == "risk_management":
                    recommendations.append(
                        "Strengthen risk management - add stop-losses and position "
                        "limits"
                    )
                elif mistake_type == "market_misread":
                    recommendations.append(
                        "Improve market analysis - use multiple confirmation signals"
                    )

        return recommendations


class ConfidenceMetrics:
    """Tracks confidence building metrics for tutorial mode."""

    def __init__(self):
        """Initialize confidence metrics."""
        self.decisions: List[Dict[str, Any]] = []
        self.performance_history: List[float] = []

    def record_decision(
        self,
        decision_quality: float,
        risk_assessment: str,
        consistency_score: float = None,
    ) -> None:
        """Record a trading decision with quality metrics."""
        self.decisions.append(
            {
                "timestamp": datetime.now(timezone.utc),
                "decision_quality": decision_quality,
                "risk_assessment": risk_assessment,
                "consistency_score": consistency_score,
            }
        )

    def calculate_confidence_score(self) -> float:
        """Calculate overall confidence score (0-1)."""
        if not self.decisions:
            return 0.0

        # Weight recent decisions more heavily
        weights = [
            0.7 + (0.3 * i / len(self.decisions)) for i in range(len(self.decisions))
        ]
        weights = weights[::-1]  # Reverse to give more weight to recent

        quality_scores = [d["decision_quality"] for d in self.decisions]

        if len(quality_scores) != len(weights):
            weights = [1.0] * len(quality_scores)

        weighted_score = sum(q * w for q, w in zip(quality_scores, weights)) / sum(
            weights
        )
        return weighted_score

    def calculate_consistency_score(self) -> float:
        """Calculate decision consistency score (0-1)."""
        if len(self.decisions) < 2:
            return 0.5  # Neutral score with insufficient data

        quality_scores = [d["decision_quality"] for d in self.decisions]

        # Calculate standard deviation
        import statistics

        std_dev = statistics.stdev(quality_scores)

        # Convert to consistency score (lower std_dev = higher consistency)
        consistency = max(
            0.0, 1.0 - (std_dev / 0.5)
        )  # Normalize assuming 0.5 as max std_dev
        return consistency

    def calculate_risk_management_score(self) -> float:
        """Calculate risk management adherence score (0-1)."""
        if not self.decisions:
            return 0.0

        # Score based on risk assessments
        risk_scores = []
        for decision in self.decisions:
            risk = decision["risk_assessment"].lower()
            if "low" in risk:
                risk_scores.append(0.9)
            elif "medium" in risk:
                risk_scores.append(0.7)
            elif "high" in risk:
                risk_scores.append(0.3)
            else:
                risk_scores.append(0.5)

        return sum(risk_scores) / len(risk_scores)

    def get_learning_progress(self) -> Dict[str, Any]:
        """Get detailed learning progress metrics."""
        if not self.decisions:
            return {"message": "Insufficient data for learning progress"}

        # Split decisions into halves to compare progression
        mid_point = len(self.decisions) // 2
        early_decisions = self.decisions[:mid_point] if mid_point > 0 else []
        recent_decisions = (
            self.decisions[mid_point:] if mid_point > 0 else self.decisions
        )

        early_avg = (
            sum(d["decision_quality"] for d in early_decisions) / len(early_decisions)
            if early_decisions
            else 0
        )
        recent_avg = (
            sum(d["decision_quality"] for d in recent_decisions) / len(recent_decisions)
            if recent_decisions
            else 0
        )

        improvement = recent_avg - early_avg

        return {
            "total_decisions": len(self.decisions),
            "early_average_quality": early_avg,
            "recent_average_quality": recent_avg,
            "improvement": improvement,
            "trend": (
                "improving"
                if improvement > 0.05
                else "declining" if improvement < -0.05 else "stable"
            ),
            "current_confidence": self.calculate_confidence_score(),
            "consistency": self.calculate_consistency_score(),
            "risk_management": self.calculate_risk_management_score(),
        }

    def is_ready_for_live_trading(self, threshold: float = 0.75) -> bool:
        """Check if ready for live trading based on confidence threshold."""
        confidence = self.calculate_confidence_score()
        consistency = self.calculate_consistency_score()
        risk_mgmt = self.calculate_risk_management_score()

        # Need at least 10 decisions and meet all thresholds
        return (
            len(self.decisions) >= 10
            and confidence >= threshold
            and consistency >= 0.6
            and risk_mgmt >= 0.7
        )


class TutorialExecutor(TradingExecutionInterface):
    """Tutorial executor for human learning-focused trading simulation."""

    def __init__(
        self,
        initial_cash: float = 100000.0,
        config: Optional[QuantChainConfig] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize tutorial executor.

        Args:
            initial_cash: Starting cash balance
            config: QuantChain configuration
            **kwargs: Additional configuration including:
                - learning_objectives: List of learning objectives
                - session_duration: Session duration in seconds
                - feedback_level: Feedback verbosity (basic, detailed, comprehensive)
                - track_mistakes: Enable mistake tracking
                - analyze_market_drivers: Enable market driver analysis
        """
        # Initialize paper trading executor as the base
        self.paper_executor = PaperTradingExecutor(initial_cash=initial_cash, **kwargs)

        # Configuration
        self.config = config or QuantChainConfig()
        self.learning_objectives = kwargs.get("learning_objectives", [])
        self.session_duration = kwargs.get("session_duration", 3600)
        self.feedback_level = kwargs.get("feedback_level", "detailed")
        self.track_mistakes = kwargs.get("track_mistakes", True)
        self.analyze_market_drivers = kwargs.get("analyze_market_drivers", True)

        # Tutorial components
        self.reflection_engine = ReflectionEngine()
        self.market_driver_analysis = MarketDriverAnalysis()
        self.mistake_tracker = MistakeTracker()
        self.confidence_metrics = ConfidenceMetrics()

        # Session management
        self.current_session: Optional[TutorialSession] = None
        self.decision_history: List[DecisionAnalysis] = []
        self.feedback_history: List[TutorialFeedback] = []

        # Try to initialize RAG if available
        self.rag_system = None
        try:
            from ..core.rag_system import (
                MarketDataRAG,
                ChromaVectorStore,
                SentenceTransformerProvider,
            )

            if self.config.get("rag.enabled", False):
                vector_store = ChromaVectorStore(
                    persist_directory=self.config.get(
                        "rag.persist_directory", "./data/chroma_db"
                    )
                )
                embedding_provider = SentenceTransformerProvider(
                    model_name=self.config.get(
                        "rag.embedding_model", "all-MiniLM-L6-v2"
                    )
                )
                self.rag_system = MarketDataRAG(vector_store, embedding_provider)
                self.market_driver_analysis.rag_system = self.rag_system
        except Exception as e:
            warnings.warn(f"RAG system not available for tutorial mode: {str(e)}")

    def start_tutorial_session(
        self,
        symbols: List[str],
        objectives: Optional[List[str]] = None,
        duration_seconds: Optional[int] = None,
    ) -> TutorialSession:
        """Start a new tutorial session."""
        # End current session if active
        if self.current_session and self.current_session.is_active:
            self.end_tutorial_session()

        # Create new session
        session_id = str(uuid.uuid4())
        session = TutorialSession(
            session_id=session_id,
            start_time=datetime.now(timezone.utc),
            symbols=symbols,
            learning_objectives=objectives or self.learning_objectives,
            duration_seconds=duration_seconds or self.session_duration,
        )

        self.current_session = session

        # Add learning objectives to session
        for obj in self.learning_objectives:
            session.add_objective(obj)

        return session

    def end_tutorial_session(self) -> Dict[str, Any]:
        """End current tutorial session and generate report."""
        if not self.current_session:
            raise ValueError("No active tutorial session")

        self.current_session.end_time = datetime.now(timezone.utc)

        # Generate final feedback
        feedback = self.get_tutorial_feedback()

        # Create session report
        report = {
            "session": self.current_session.to_dict(),
            "final_feedback": feedback.to_dict(),
            "paper_trading_metrics": self.paper_executor.get_performance_metrics(),
            "trade_history": self.paper_executor.export_trade_history().to_dict(
                "records"
            ),
            "ready_for_live": self.confidence_metrics.is_ready_for_live_trading(
                threshold=self.config.get("tutorial.confidence_threshold", 0.75)
            ),
        }

        return report

    def place_order(self, order: OrderRequest) -> OrderResult:
        """Place order with enhanced learning feedback."""
        # Execute order through paper trading
        result = self.paper_executor.place_order(order)

        # Only analyze if session is active and order was filled
        if (
            self.current_session
            and self.current_session.is_active
            and result.status == OrderStatus.FILLED
        ):
            # Analyze decision
            analysis = self.analyze_decision(order, result)
            self.decision_history.append(analysis)

            # Record action for reflection
            action = AgentAction(
                timestamp=result.timestamp,
                action_type=f"trade_{order.side.value}",
                parameters={
                    "symbol": order.symbol,
                    "quantity": order.quantity,
                    "type": order.order_type.value,
                },
                result=result,
                confidence_score=analysis.confidence,
                success=True,
                reward=0.0,  # Will be calculated on position close
            )
            self.reflection_engine.record_action(action)

        return result

    def analyze_decision(
        self, order: OrderRequest, result: OrderResult
    ) -> DecisionAnalysis:
        """Analyze a trading decision for learning purposes."""
        # Get market drivers
        market_drivers = []
        if self.analyze_market_drivers:
            market_drivers = self.market_driver_analysis.analyze_market_drivers(
                result.symbol, result
            )

        # Calculate decision quality
        decision_quality = self._calculate_decision_quality(order, result)

        # Risk assessment
        risk_assessment = self._assess_risk(order, result)

        # Educational context
        educational_context = ""
        if self.analyze_market_drivers:
            educational_context = (
                self.market_driver_analysis.generate_educational_context(
                    result.symbol, market_drivers
                )
            )

        # Generate alternatives
        alternatives = self._generate_alternatives(order, result)

        # Calculate confidence
        confidence = self._calculate_confidence(decision_quality, risk_assessment)

        analysis = DecisionAnalysis(
            timestamp=datetime.now(timezone.utc),
            order=result,
            market_drivers=market_drivers,
            decision_quality=decision_quality,
            risk_assessment=risk_assessment,
            educational_context=educational_context,
            alternatives=alternatives,
            confidence=confidence,
        )

        # Track mistakes if enabled
        if self.track_mistakes:
            market_context = {
                "symbol": result.symbol,
                "portfolio_value": self.get_account().portfolio_value,
                "volatility": 0.15,  # Default - would be calculated from market data
            }

            mistake = self.mistake_tracker.analyze_mistake(result, market_context)
            if mistake and self.feedback_level in ["detailed", "comprehensive"]:
                analysis.educational_context += (
                    f"\n\nMISTAKE IDENTIFIED:\n{mistake.description}\n\n"
                    f"LEARNING POINT:\n{mistake.learning_point}"
                )

        # Record for confidence metrics
        self.confidence_metrics.record_decision(
            decision_quality=decision_quality,
            risk_assessment=risk_assessment,
            consistency_score=self.confidence_metrics.calculate_consistency_score(),
        )

        return analysis

    def _calculate_decision_quality(
        self, order: OrderRequest, result: OrderResult
    ) -> float:
        """Calculate decision quality score (0-1)."""
        quality = 0.5  # Base score

        # Order type consideration
        if order.order_type.value == "market":
            quality += 0.1  # Simplicity
        elif order.order_type.value == "limit":
            quality += 0.2  # Price discipline

        # Position sizing (simplified check)
        portfolio_value = self.get_account().portfolio_value
        order_value = (result.avg_fill_price or 0) * order.quantity
        position_size = order_value / portfolio_value

        if 0.05 <= position_size <= 0.15:  # 5-15% position size
            quality += 0.2
        elif position_size < 0.05:  # Very small
            quality += 0.1
        elif position_size > 0.25:  # Too large
            quality -= 0.2

        # Add randomness for simulation
        import random

        quality += random.uniform(-0.1, 0.1)

        return max(0.0, min(1.0, quality))

    def _assess_risk(self, order: OrderRequest, result: OrderResult) -> str:
        """Assess risk level of the decision."""
        portfolio_value = self.get_account().portfolio_value
        order_value = (result.avg_fill_price or 0) * order.quantity
        position_size = order_value / portfolio_value

        if position_size > 0.2:
            return "High risk - large position size"
        elif position_size > 0.1:
            return "Medium risk - moderate position size"
        else:
            return "Low risk - conservative position size"

    def _generate_alternatives(
        self, order: OrderRequest, result: OrderResult
    ) -> List[str]:
        """Generate alternative strategies for learning."""
        alternatives = []

        if order.order_type.value == "market":
            alternatives.append("Use limit order for better price control")
            alternatives.append("Scale into position over time")
        elif order.order_type.value == "limit":
            alternatives.append("Use market order for immediate execution")
            alternatives.append("Set wider limit for higher fill probability")

        # Position sizing alternatives
        portfolio_value = self.get_account().portfolio_value
        order_value = (result.avg_fill_price or 0) * order.quantity
        position_size = order_value / portfolio_value

        if position_size > 0.15:
            alternatives.append("Reduce position size to manage risk")
        elif position_size < 0.05:
            alternatives.append("Increase position size for meaningful exposure")

        return alternatives

    def _calculate_confidence(
        self, decision_quality: float, risk_assessment: str
    ) -> float:
        """Calculate overall confidence in the decision."""
        base_confidence = decision_quality * 0.7

        # Adjust based on risk
        if "low risk" in risk_assessment.lower():
            base_confidence += 0.1
        elif "high risk" in risk_assessment.lower():
            base_confidence -= 0.1

        return max(0.0, min(1.0, base_confidence))

    def get_tutorial_feedback(self) -> TutorialFeedback:
        """Get comprehensive tutorial feedback."""
        if not self.current_session:
            raise ValueError("No active tutorial session")

        # Get recent decision analyses
        recent_analyses = (
            self.decision_history[-10:]
            if len(self.decision_history) > 10
            else self.decision_history
        )

        # Get recent mistakes
        recent_mistakes = (
            self.mistake_tracker.get_mistake_history()[-5:]
            if len(self.mistake_tracker.mistakes) > 5
            else self.mistake_tracker.get_mistake_history()
        )

        # Calculate scores
        confidence_score = self.confidence_metrics.calculate_confidence_score()
        consistency_score = self.confidence_metrics.calculate_consistency_score()
        risk_management_score = (
            self.confidence_metrics.calculate_risk_management_score()
        )

        # Get learning progress
        learning_progress = self.confidence_metrics.get_learning_progress()

        # Generate recommendations
        recommendations = self.mistake_tracker.get_learning_recommendations()
        if confidence_score < 0.5:
            recommendations.append(
                "Practice more to build confidence in trading decisions"
            )
        if consistency_score < 0.6:
            recommendations.append("Focus on developing consistent trading approach")
        if risk_management_score < 0.7:
            recommendations.append("Strengthen risk management practices")

        return TutorialFeedback(
            session_id=self.current_session.session_id,
            timestamp=datetime.now(timezone.utc),
            decision_analyses=recent_analyses,
            mistakes=recent_mistakes,
            confidence_score=confidence_score,
            consistency_score=consistency_score,
            risk_management_score=risk_management_score,
            learning_progress=learning_progress,
            recommendations=recommendations,
        )

    def get_current_session(self) -> Optional[TutorialSession]:
        """Get current tutorial session."""
        return self.current_session

    def get_decision_history(self) -> List[DecisionAnalysis]:
        """Get decision analysis history."""
        return self.decision_history.copy()

    def get_mistake_history(self) -> List[TradingMistake]:
        """Get mistake history."""
        return self.mistake_tracker.get_mistake_history()

    def get_confidence_score(self) -> float:
        """Get current confidence score."""
        return self.confidence_metrics.calculate_confidence_score()

    def is_ready_for_live_trading(self, threshold: float = 0.75) -> bool:
        """Check if ready for live trading."""
        return self.confidence_metrics.is_ready_for_live_trading(threshold)

    def export_tutorial_report(self) -> Dict[str, Any]:
        """Export comprehensive tutorial report."""
        if not self.current_session:
            raise ValueError("No tutorial session to export")

        return self.end_tutorial_session()

    # Delegate methods to paper trading executor
    def cancel_order(self, order_id: str) -> OrderResult:
        """Cancel an order."""
        return self.paper_executor.cancel_order(order_id)

    def get_order(self, order_id: str) -> OrderResult:
        """Get order details."""
        return self.paper_executor.get_order(order_id)

    def get_account(self) -> AccountInfo:
        """Get account information."""
        return self.paper_executor.get_account()

    def get_positions(self) -> List[Position]:
        """Get current positions."""
        return self.paper_executor.get_positions()

    def get_order_history(
        self,
        symbol: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[OrderResult]:
        """Get order history."""
        return self.paper_executor.get_order_history(
            symbol, status, start_date, end_date, limit
        )

    def is_market_open(self, symbol: Optional[str] = None) -> bool:
        """Check if market is open."""
        return self.paper_executor.is_market_open(symbol)

    def set_market_price(self, symbol: str, price: float) -> None:
        """Set market price for testing."""
        self.paper_executor.set_market_price(symbol, price)

    def update_market_data(self, symbols: List[str]) -> None:
        """Update market data."""
        self.paper_executor.update_market_data(symbols)

    def get_performance_metrics(self):
        """Get paper trading performance metrics."""
        return self.paper_executor.get_performance_metrics()

    def reset(self) -> None:
        """Reset tutorial state."""
        self.paper_executor.reset()
        self.current_session = None
        self.decision_history.clear()
        self.feedback_history.clear()
        self.reflection_engine = ReflectionEngine()
        self.mistake_tracker = MistakeTracker()
        self.confidence_metrics = ConfidenceMetrics()
