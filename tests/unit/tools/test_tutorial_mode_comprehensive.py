"""
Tests for tutorial_mode module to improve coverage.
Targets increasing coverage from 0% to 90%+.
"""

import pytest

try:
    from quantchain.tools.tutorial_mode import (
        AdvancedStrategiesStep,
        IntroductionStep,
        OrderPlacementStep,
        PortfolioAnalysisStep,
        RiskManagementStep,
        TutorialFeedback,
        TutorialMode,
        TutorialStep,
    )

    TUTORIAL_MODE_AVAILABLE = True
except ImportError as e:
    TUTORIAL_MODE_AVAILABLE = False
    print(f"Tutorial mode module not available: {e}")


@pytest.mark.skipif(not TUTORIAL_MODE_AVAILABLE, reason="Tutorial mode not available")
class TestTutorialFeedback:
    """Test TutorialFeedback class for comprehensive coverage."""

    def test_tutorial_feedback_creation(self):
        """Test creating tutorial feedback."""
        feedback = TutorialFeedback(
            message="Great job!",
            feedback_type="success",
            suggestions=["Keep up the good work"],
            next_steps="Move to the next lesson",
        )
        assert feedback.message == "Great job!"
        assert feedback.feedback_type == "success"
        assert len(feedback.suggestions) == 1
        assert feedback.next_steps == "Move to the next lesson"

    def test_tutorial_feedback_warning_type(self):
        """Test warning feedback type."""
        feedback = TutorialFeedback(
            message="Be careful with position sizing",
            feedback_type="warning",
            suggestions=["Consider risk management"],
        )
        assert feedback.feedback_type == "warning"

    def test_tutorial_feedback_error_type(self):
        """Test error feedback type."""
        feedback = TutorialFeedback(
            message="Invalid order parameters",
            feedback_type="error",
            suggestions=["Check your order size and price"],
        )
        assert feedback.feedback_type == "error"

    def test_tutorial_feedback_to_dict(self):
        """Test converting feedback to dictionary."""
        feedback = TutorialFeedback(
            message="Test feedback",
            feedback_type="info",
            suggestions=["Tip 1", "Tip 2"],
        )
        feedback_dict = feedback.to_dict()

        assert feedback_dict["message"] == "Test feedback"
        assert feedback_dict["feedback_type"] == "info"
        assert len(feedback_dict["suggestions"]) == 2


@pytest.mark.skipif(not TUTORIAL_MODE_AVAILABLE, reason="Tutorial mode not available")
class TestTutorialStep:
    """Test TutorialStep base class for comprehensive coverage."""

    def test_tutorial_step_abstract(self):
        """Test that TutorialStep cannot be instantiated directly."""
        with pytest.raises(TypeError):
            TutorialStep("Test Step")

    def test_concrete_tutorial_step(self):
        """Test creating concrete tutorial step."""

        class ConcreteStep(TutorialStep):
            def execute(self, user_action):
                return TutorialFeedback("Step completed", "success")

            def get_instructions(self):
                return "Follow these instructions"

        step = ConcreteStep("Test Step")
        assert step.name == "Test Step"
        assert hasattr(step, "execute")
        assert hasattr(step, "get_instructions")


@pytest.mark.skipif(not TUTORIAL_MODE_AVAILABLE, reason="Tutorial mode not available")
class TestIntroductionStep:
    """Test IntroductionStep for comprehensive coverage."""

    def test_introduction_step_creation(self):
        """Test creating introduction step."""
        step = IntroductionStep()
        assert step.name == "Introduction"

    def test_introduction_step_instructions(self):
        """Test getting introduction instructions."""
        step = IntroductionStep()
        instructions = step.get_instructions()
        assert isinstance(instructions, str)
        assert len(instructions) > 0

    def test_introduction_step_execute(self):
        """Test executing introduction step."""
        step = IntroductionStep()
        feedback = step.execute({"action": "start"})

        assert isinstance(feedback, TutorialFeedback)
        assert feedback.feedback_type in ["success", "info"]


@pytest.mark.skipif(not TUTORIAL_MODE_AVAILABLE, reason="Tutorial mode not available")
class TestOrderPlacementStep:
    """Test OrderPlacementStep for comprehensive coverage."""

    def test_order_placement_step_creation(self):
        """Test creating order placement step."""
        step = OrderPlacementStep()
        assert step.name == "Order Placement"

    def test_order_placement_step_instructions(self):
        """Test getting order placement instructions."""
        step = OrderPlacementStep()
        instructions = step.get_instructions()
        assert isinstance(instructions, str)
        assert "order" in instructions.lower()

    def test_order_placement_step_execute_valid_order(self):
        """Test executing order placement step with valid order."""
        step = OrderPlacementStep()
        user_action = {
            "symbol": "AAPL",
            "side": "buy",
            "quantity": 100,
            "order_type": "market",
            "price": None,
        }

        feedback = step.execute(user_action)
        assert isinstance(feedback, TutorialFeedback)

    def test_order_placement_step_execute_invalid_order(self):
        """Test executing order placement step with invalid order."""
        step = OrderPlacementStep()
        user_action = {
            "symbol": "",  # Invalid empty symbol
            "side": "invalid",
            "quantity": -10,  # Invalid negative quantity
        }

        feedback = step.execute(user_action)
        assert isinstance(feedback, TutorialFeedback)
        assert feedback.feedback_type in ["error", "warning"]


@pytest.mark.skipif(not TUTORIAL_MODE_AVAILABLE, reason="Tutorial mode not available")
class TestRiskManagementStep:
    """Test RiskManagementStep for comprehensive coverage."""

    def test_risk_management_step_creation(self):
        """Test creating risk management step."""
        step = RiskManagementStep()
        assert step.name == "Risk Management"

    def test_risk_management_step_instructions(self):
        """Test getting risk management instructions."""
        step = RiskManagementStep()
        instructions = step.get_instructions()
        assert isinstance(instructions, str)
        assert "risk" in instructions.lower()

    def test_risk_management_step_execute_good_risk(self):
        """Test executing risk management step with good risk practices."""
        step = RiskManagementStep()
        user_action = {
            "position_size": 0.02,  # 2% risk - good
            "stop_loss": 0.95,  # 5% stop loss
            "portfolio_risk": 0.01,  # 1% portfolio risk
        }

        feedback = step.execute(user_action)
        assert isinstance(feedback, TutorialFeedback)
        assert feedback.feedback_type in ["success", "info"]

    def test_risk_management_step_execute_poor_risk(self):
        """Test executing risk management step with poor risk practices."""
        step = RiskManagementStep()
        user_action = {
            "position_size": 0.20,  # 20% risk - too high
            "stop_loss": None,  # No stop loss
            "portfolio_risk": 0.15,  # 15% portfolio risk
        }

        feedback = step.execute(user_action)
        assert isinstance(feedback, TutorialFeedback)
        assert feedback.feedback_type in ["warning", "error"]


@pytest.mark.skipif(not TUTORIAL_MODE_AVAILABLE, reason="Tutorial mode not available")
class TestPortfolioAnalysisStep:
    """Test PortfolioAnalysisStep for comprehensive coverage."""

    def test_portfolio_analysis_step_creation(self):
        """Test creating portfolio analysis step."""
        step = PortfolioAnalysisStep()
        assert step.name == "Portfolio Analysis"

    def test_portfolio_analysis_step_instructions(self):
        """Test getting portfolio analysis instructions."""
        step = PortfolioAnalysisStep()
        instructions = step.get_instructions()
        assert isinstance(instructions, str)
        assert "portfolio" in instructions.lower()

    def test_portfolio_analysis_step_execute_with_data(self):
        """Test executing portfolio analysis step with portfolio data."""
        step = PortfolioAnalysisStep()
        user_action = {
            "portfolio_data": {
                "positions": [
                    {"symbol": "AAPL", "value": 15000, "weight": 0.6},
                    {"symbol": "GOOGL", "value": 10000, "weight": 0.4},
                ],
                "total_value": 25000,
                "cash": 5000,
            }
        }

        feedback = step.execute(user_action)
        assert isinstance(feedback, TutorialFeedback)

    def test_portfolio_analysis_step_execute_empty_portfolio(self):
        """Test executing portfolio analysis step with empty portfolio."""
        step = PortfolioAnalysisStep()
        user_action = {
            "portfolio_data": {"positions": [], "total_value": 0, "cash": 10000}
        }

        feedback = step.execute(user_action)
        assert isinstance(feedback, TutorialFeedback)


@pytest.mark.skipif(not TUTORIAL_MODE_AVAILABLE, reason="Tutorial mode not available")
class TestAdvancedStrategiesStep:
    """Test AdvancedStrategiesStep for comprehensive coverage."""

    def test_advanced_strategies_step_creation(self):
        """Test creating advanced strategies step."""
        step = AdvancedStrategiesStep()
        assert step.name == "Advanced Strategies"

    def test_advanced_strategies_step_instructions(self):
        """Test getting advanced strategies instructions."""
        step = AdvancedStrategiesStep()
        instructions = step.get_instructions()
        assert isinstance(instructions, str)
        assert "strategy" in instructions.lower()

    def test_advanced_strategies_step_execute_basic_strategy(self):
        """Test executing advanced strategies step with basic strategy."""
        step = AdvancedStrategiesStep()
        user_action = {
            "strategy_type": "momentum",
            "parameters": {"lookback_period": 20, "signal_threshold": 0.02},
        }

        feedback = step.execute(user_action)
        assert isinstance(feedback, TutorialFeedback)

    def test_advanced_strategies_step_execute_complex_strategy(self):
        """Test executing advanced strategies step with complex strategy."""
        step = AdvancedStrategiesStep()
        user_action = {
            "strategy_type": "mean_reversion",
            "parameters": {
                "lookback_period": 50,
                "entry_threshold": 2.0,
                "exit_threshold": 0.5,
                "position_sizing": "kelly",
            },
        }

        feedback = step.execute(user_action)
        assert isinstance(feedback, TutorialFeedback)


@pytest.mark.skipif(not TUTORIAL_MODE_AVAILABLE, reason="Tutorial mode not available")
class TestTutorialMode:
    """Test TutorialMode class for comprehensive coverage."""

    def test_tutorial_mode_init(self):
        """Test tutorial mode initialization."""
        tutorial = TutorialMode()
        assert hasattr(tutorial, "current_step")
        assert hasattr(tutorial, "completed_steps")
        assert hasattr(tutorial, "feedback_history")

    def test_tutorial_mode_start_tutorial(self):
        """Test starting tutorial."""
        tutorial = TutorialMode()
        tutorial.start_tutorial()

        assert tutorial.current_step is not None
        assert isinstance(tutorial.current_step, TutorialStep)

    def test_tutorial_mode_get_current_instructions(self):
        """Test getting current step instructions."""
        tutorial = TutorialMode()
        tutorial.start_tutorial()

        instructions = tutorial.get_current_instructions()
        assert isinstance(instructions, str)
        assert len(instructions) > 0

    def test_tutorial_mode_execute_step(self):
        """Test executing current tutorial step."""
        tutorial = TutorialMode()
        tutorial.start_tutorial()

        user_action = {"action": "test_action"}
        feedback = tutorial.execute_step(user_action)

        assert isinstance(feedback, TutorialFeedback)

    def test_tutorial_mode_next_step(self):
        """Test moving to next tutorial step."""
        tutorial = TutorialMode()
        tutorial.start_tutorial()

        initial_step = tutorial.current_step
        tutorial.next_step()

        assert tutorial.current_step != initial_step

    def test_tutorial_mode_previous_step(self):
        """Test moving to previous tutorial step."""
        tutorial = TutorialMode()
        tutorial.start_tutorial()

        # Move forward a few steps
        tutorial.next_step()
        tutorial.next_step()

        current_step = tutorial.current_step
        tutorial.previous_step()

        assert tutorial.current_step != current_step

    def test_tutorial_mode_get_progress(self):
        """Test getting tutorial progress."""
        tutorial = TutorialMode()
        tutorial.start_tutorial()

        progress = tutorial.get_progress()
        assert isinstance(progress, dict)
        assert "current_step" in progress
        assert "completed_steps" in progress
        assert "total_steps" in progress
        assert "progress_percentage" in progress

    def test_tutorial_mode_complete_tutorial(self):
        """Test completing tutorial."""
        tutorial = TutorialMode()
        tutorial.start_tutorial()

        # Complete all steps
        while tutorial.current_step is not None:
            tutorial.execute_step({"action": "complete"})
            tutorial.next_step()

        assert tutorial.current_step is None
        assert tutorial.is_completed()


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
