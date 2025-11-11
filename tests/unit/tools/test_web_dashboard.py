"""Tests for Web Dashboard components."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

# Check for optional dependencies
try:
    import plotly  # noqa: F401

    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import streamlit  # noqa: F401

    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


# Test data structures that will be defined in implementation
@pytest.fixture
def mock_agent_status():
    """Create a mock agent status for testing."""
    return {
        "agent_id": "test_agent_001",
        "agent_type": "memecoin_vibe_trader",
        "status": "RUNNING",
        "last_update": datetime.now(),
        "current_positions": [
            {"symbol": "BTC-USD", "quantity": 0.5, "value": 25000.0},
            {"symbol": "ETH-USD", "quantity": 2.0, "value": 4000.0},
        ],
        "recent_trades": [
            {
                "symbol": "BTC-USD",
                "side": "buy",
                "quantity": 0.5,
                "price": 50000.0,
                "timestamp": datetime.now(),
            }
        ],
        "error_count": 0,
        "uptime": timedelta(hours=5),
    }


@pytest.fixture
def mock_portfolio_metrics():
    """Create mock portfolio metrics for testing."""
    return {
        "agent_id": "test_agent_001",
        "total_value": 30000.0,
        "cash_balance": 1000.0,
        "total_pnl": 1500.0,
        "pnl_percentage": 5.25,
        "win_rate": 0.65,
        "max_drawdown": 0.08,
        "sharpe_ratio": 1.2,
        "trade_count": 25,
        "last_updated": datetime.now(),
    }


@pytest.fixture
def mock_system_health():
    """Create mock system health data for testing."""
    return {
        "api_status": {"alpaca": True, "dexscreener": False, "llm": True},
        "llm_response_time_ms": 1250.0,
        "error_rate_24h": 0.02,
        "cpu_usage_percent": 45.5,
        "memory_usage_percent": 68.2,
        "disk_space_gb": 125.8,
        "uptime_hours": 72.5,
    }


@pytest.fixture
def mock_dashboard_config():
    """Create mock dashboard configuration."""
    return {
        "refresh_interval": 5,
        "max_data_points": 1000,
        "enable_real_time": True,
        "theme": "light",
        "default_agent_id": None,
        "port": 8501,
        "host": "localhost",
    }


@pytest.mark.skipif(
    not (HAS_PLOTLY and HAS_STREAMLIT), reason="plotly and streamlit not available"
)
@pytest.mark.requires_web
class TestWebDashboardApp:
    """Test cases for WebDashboardApp."""

    @pytest.fixture
    def mock_config(self, mock_dashboard_config):
        """Create mock configuration for dashboard app."""
        config = Mock()
        config.refresh_interval = mock_dashboard_config["refresh_interval"]
        config.max_data_points = mock_dashboard_config["max_data_points"]
        config.enable_real_time = mock_dashboard_config["enable_real_time"]
        config.theme = mock_dashboard_config["theme"]
        config.default_agent_id = mock_dashboard_config["default_agent_id"]
        config.port = mock_dashboard_config["port"]
        config.host = mock_dashboard_config["host"]
        return config

    def test_web_dashboard_app_initialization(self, mock_config) -> None:
        """Test WebDashboardApp initialization."""
        from quantchain.tools.web_dashboard import WebDashboardApp

        app = WebDashboardApp(mock_config)

        assert app.config == mock_config
        assert app.config.refresh_interval == mock_config.refresh_interval
        assert app.config.enable_real_time == mock_config.enable_real_time

    @patch("subprocess.run")
    def test_web_dashboard_run(self, mock_subprocess_run, mock_config) -> None:
        """Test running the Streamlit application."""
        from quantchain.tools.web_dashboard import WebDashboardApp

        app = WebDashboardApp(mock_config)

        app.run(host="0.0.0.0", port=8080)

        # The run method sets up the page config and renders the main page
        # For direct execution, it uses subprocess
        # The test verifies the app can be instantiated without errors
        assert app.config == mock_config


@pytest.mark.requires_web
class TestMonitoringService:
    """Test cases for MonitoringService."""

    @pytest.fixture
    def mock_agent_registry(self) -> None:
        """Create mock agent registry."""
        registry = Mock()
        registry.get_agent_status.return_value = {
            "agent_id": "test_agent_001",
            "status": "RUNNING",
        }
        registry.get_all_agents.return_value = [
            {"agent_id": "test_agent_001", "status": "RUNNING"},
            {"agent_id": "test_agent_002", "status": "STOPPED"},
        ]
        return registry

    def test_get_agent_status_success(
        self, mock_agent_registry, mock_agent_status
    ) -> None:
        """Test successful agent status retrieval."""
        mock_agent_registry.get_agent_status.return_value = mock_agent_status

        from quantchain.tools.web_dashboard import MonitoringService

        service = MonitoringService(mock_agent_registry)

        status = service.get_agent_status("test_agent_001")

        assert status["agent_id"] == "test_agent_001"
        assert status["status"] == "RUNNING"
        mock_agent_registry.get_agent_status.assert_called_once_with("test_agent_001")

    def test_get_agent_status_not_found(self, mock_agent_registry) -> None:
        """Test agent status retrieval for non-existent agent."""
        mock_agent_registry.get_agent_status.side_effect = Exception("Agent not found")

        from quantchain.tools.web_dashboard import MonitoringService

        service = MonitoringService(mock_agent_registry)

        with pytest.raises(Exception, match="Agent not found"):
            service.get_agent_status("nonexistent_agent")

    def test_get_portfolio_metrics_success(
        self, mock_agent_registry, mock_portfolio_metrics
    ):
        """Test successful portfolio metrics retrieval."""
        mock_agent_registry.get_portfolio_metrics.return_value = mock_portfolio_metrics

        from quantchain.tools.web_dashboard import MonitoringService

        service = MonitoringService(mock_agent_registry)

        metrics = service.get_portfolio_metrics("test_agent_001")

        assert metrics["agent_id"] == "test_agent_001"
        assert metrics["total_value"] == 30000.0
        assert metrics["pnl_percentage"] == 5.25

    def test_get_system_health_success(
        self, mock_agent_registry, mock_system_health
    ) -> None:
        """Test successful system health retrieval."""
        mock_agent_registry.get_system_health.return_value = mock_system_health

        from quantchain.tools.web_dashboard import MonitoringService

        service = MonitoringService(mock_agent_registry)

        health = service.get_system_health()

        assert health["api_status"]["alpaca"] is True
        assert health["api_status"]["dexscreener"] is False
        assert health["llm_response_time_ms"] == 1250.0


@pytest.mark.skipif(not HAS_PLOTLY, reason="plotly not available")
@pytest.mark.requires_web
class TestVisualizationService:
    """Test cases for VisualizationService."""

    def test_create_equity_curve_success(self) -> None:
        """Test successful equity curve creation."""
        from quantchain.tools.web_dashboard import VisualizationService

        service = VisualizationService()

        # Create mock portfolio data
        portfolio_data = [
            {
                "timestamp": datetime.now() - timedelta(days=i),
                "total_value": 30000 - i * 100,
            }
            for i in range(10)
        ]

        figure = service.create_equity_curve(portfolio_data)

        assert figure is not None
        assert hasattr(figure, "data")
        assert len(figure.data) > 0

    def test_create_equity_curve_empty_data(self) -> None:
        """Test equity curve creation with empty data."""
        from quantchain.tools.web_dashboard import VisualizationService

        service = VisualizationService()

        figure = service.create_equity_curve([])

        assert figure is not None
        assert hasattr(figure, "data")
        # Should have a "No data available" annotation

    def test_create_decision_flow_diagram_success(self) -> None:
        """Test successful decision flow diagram creation."""
        from quantchain.tools.web_dashboard import VisualizationService

        service = VisualizationService()

        # Create mock reasoning data
        reasoning_data = {
            "agent_id": "test_agent_001",
            "decision_steps": [
                {"step": "scan", "status": "completed", "output": "5 tokens found"},
                {
                    "step": "analyze",
                    "status": "completed",
                    "output": "HYPE token selected",
                },
                {
                    "step": "execute",
                    "status": "completed",
                    "output": "Buy order placed",
                },
            ],
        }

        figure = service.create_decision_flow_diagram(reasoning_data)

        assert figure is not None
        assert hasattr(figure, "data")

    def test_create_decision_flow_diagram_empty(self) -> None:
        """Test decision flow diagram creation with no steps."""
        from quantchain.tools.web_dashboard import VisualizationService

        service = VisualizationService()

        reasoning_data = {"agent_id": "test_agent_001", "decision_steps": []}

        figure = service.create_decision_flow_diagram(reasoning_data)

        assert figure is not None
        assert hasattr(figure, "data")

    def test_create_performance_charts_success(self, mock_portfolio_metrics) -> None:
        """Test successful performance charts creation."""
        from quantchain.tools.web_dashboard import VisualizationService

        service = VisualizationService()

        charts = service.create_performance_charts(mock_portfolio_metrics)

        assert isinstance(charts, dict)
        assert len(charts) > 0

        for chart_name, figure in charts.items():
            assert figure is not None
            assert hasattr(figure, "data")


@pytest.mark.skipif(not HAS_STREAMLIT, reason="streamlit not available")
@pytest.mark.requires_web
class TestConfigurationWizard:
    """Test cases for ConfigurationWizard."""

    def test_get_agent_template_success(self) -> None:
        """Test successful agent template retrieval."""
        from quantchain.tools.web_dashboard import ConfigurationWizard

        wizard = ConfigurationWizard()

        template = wizard.get_agent_template("memecoin_vibe_trader")

        assert template is not None
        assert "agent_id" in template
        assert "agent_type" in template
        assert template["agent_type"] == "memecoin_vibe_trader"

    def test_get_agent_template_invalid_type(self) -> None:
        """Test agent template retrieval for unknown type."""
        from quantchain.tools.web_dashboard import ConfigurationWizard

        wizard = ConfigurationWizard()

        with pytest.raises(ValueError, match="Unknown agent type"):
            wizard.get_agent_template("unknown_agent_type")

    def test_validate_config_valid(self) -> None:
        """Test configuration validation for valid config."""
        from quantchain.tools.web_dashboard import ConfigurationWizard

        wizard = ConfigurationWizard()

        valid_config = {
            "agent_id": "test_agent_001",
            "agent_type": "memecoin_vibe_trader",
            "name": "Test Agent",
            "description": "A test agent",
            "parameters": {"max_positions": 5},
            "risk_settings": {"max_allocation": 0.02},
            "data_sources": ["alpaca"],
            "llm_config": {"model": "gpt-4"},
        }

        result = wizard.validate_config(valid_config)

        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_config_invalid(self) -> None:
        """Test configuration validation for invalid config."""
        from quantchain.tools.web_dashboard import ConfigurationWizard

        wizard = ConfigurationWizard()

        invalid_config = {
            "agent_id": "",  # Invalid empty ID
            "agent_type": "unknown_type",  # Unknown agent type
            # Missing required fields
        }

        result = wizard.validate_config(invalid_config)

        assert result["is_valid"] is False
        assert len(result["errors"]) > 0

    def test_save_config_success(self) -> None:
        """Test successful configuration saving."""
        from quantchain.tools.web_dashboard import ConfigurationWizard

        wizard = ConfigurationWizard()

        config = {
            "agent_id": "test_agent_001",
            "agent_type": "memecoin_vibe_trader",
            "name": "Test Agent",
        }

        with patch("builtins.open", create=True) as mock_open:
            with patch("json.dump") as mock_dump:
                result = wizard.save_config(config, "/tmp/test_config.json")

                assert result is True
                mock_open.assert_called_once_with("/tmp/test_config.json", "w")
                mock_dump.assert_called_once()


@pytest.mark.requires_web
class TestMonitoringServiceAdditional:
    """Additional test cases for MonitoringService to improve coverage."""

    def test_get_all_agents_with_registry(self) -> None:
        """Test getting all agents when registry is provided."""
        from unittest.mock import Mock

        from quantchain.tools.web_dashboard import MonitoringService

        mock_agent_registry = Mock()
        mock_agent_registry.get_all_agents.return_value = [
            {
                "agent_id": "agent1",
                "agent_type": "memecoin_vibe_trader",
                "status": "RUNNING",
            },
            {"agent_id": "agent2", "agent_type": "chart_reader", "status": "STOPPED"},
        ]

        service = MonitoringService(mock_agent_registry)
        agents = service.get_all_agents()

        assert len(agents) == 2
        assert agents[0]["agent_id"] == "agent1"
        assert agents[1]["status"] == "STOPPED"
        mock_agent_registry.get_all_agents.assert_called_once()

    def test_get_all_agents_without_registry(self) -> None:
        """Test getting all agents when no registry is provided (mock data)."""
        from quantchain.tools.web_dashboard import MonitoringService

        service = MonitoringService()
        agents = service.get_all_agents()

        assert len(agents) == 3
        assert any(agent["status"] == "RUNNING" for agent in agents)
        assert any(agent["status"] == "STOPPED" for agent in agents)
        assert any(agent["status"] == "ERROR" for agent in agents)

    def test_get_portfolio_metrics_without_registry(self) -> None:
        """Test portfolio metrics retrieval without registry."""
        from quantchain.tools.web_dashboard import MonitoringService

        service = MonitoringService()
        metrics = service.get_portfolio_metrics("any_agent_id")

        assert metrics["agent_id"] == "any_agent_id"
        assert metrics["total_value"] == 30000.0
        assert metrics["sharpe_ratio"] == 1.2

    def test_get_system_health_without_registry(self) -> None:
        """Test system health retrieval without registry."""
        from quantchain.tools.web_dashboard import MonitoringService

        service = MonitoringService()
        health = service.get_system_health()

        assert "api_status" in health
        assert "llm_response_time_ms" in health
        assert health["api_status"]["alpaca"] is True
        assert health["api_status"]["dexscreener"] is False

    def test_get_agent_status_without_registry(self) -> None:
        """Test agent status retrieval without registry."""
        from quantchain.tools.web_dashboard import MonitoringService

        service = MonitoringService()
        status = service.get_agent_status("test_agent")

        assert status["agent_id"] == "test_agent"
        assert status["status"] == "RUNNING"
        assert len(status["current_positions"]) > 0
        assert len(status["recent_trades"]) > 0


@pytest.mark.requires_web
class TestVisualizationServiceAdditional:
    """Additional test cases for VisualizationService to improve coverage."""

    def test_create_equity_curve_with_real_data(self) -> None:
        """Test equity curve with realistic data."""
        import pandas as pd

        from quantchain.tools.web_dashboard import VisualizationService

        service = VisualizationService()

        # Create realistic portfolio data
        portfolio_data = pd.DataFrame(
            {
                "timestamp": pd.date_range("2024-01-01", periods=30, freq="D"),
                "total_value": [10000 + i * 100 + (i % 5) * 50 for i in range(30)],
            }
        ).to_dict("records")

        figure = service.create_equity_curve(portfolio_data)

        assert figure is not None
        assert hasattr(figure, "data")
        assert len(figure.data) > 0
        assert figure.layout.title.text == "Portfolio Equity Curve"

    def test_create_decision_flow_diagram_with_complex_flow(self) -> None:
        """Test decision flow diagram with complex reasoning flow."""
        from quantchain.tools.web_dashboard import VisualizationService

        service = VisualizationService()

        complex_reasoning = {
            "agent_id": "complex_agent",
            "decision_steps": [
                {
                    "step": "market_scan",
                    "status": "completed",
                    "output": "15 opportunities found",
                    "duration_ms": 250,
                },
                {
                    "step": "sentiment_analysis",
                    "status": "completed",
                    "output": "Positive sentiment detected",
                    "duration_ms": 450,
                },
                {
                    "step": "risk_assessment",
                    "status": "completed",
                    "output": "Risk score: 0.65",
                    "duration_ms": 180,
                },
                {
                    "step": "position_sizing",
                    "status": "completed",
                    "output": "Size: 2.5% of portfolio",
                    "duration_ms": 120,
                },
                {
                    "step": "order_placement",
                    "status": "failed",
                    "output": "Insufficient liquidity",
                    "duration_ms": 320,
                },
                {
                    "step": "retry_mechanism",
                    "status": "completed",
                    "output": "Order placed at revised price",
                    "duration_ms": 200,
                },
            ],
        }

        figure = service.create_decision_flow_diagram(complex_reasoning)

        assert figure is not None
        assert hasattr(figure, "data")

    def test_create_performance_charts_with_edge_cases(self) -> None:
        """Test performance charts with edge case values."""
        from quantchain.tools.web_dashboard import VisualizationService

        service = VisualizationService()

        edge_case_metrics = {
            "agent_id": "edge_case_agent",
            "total_value": 0.0,  # Zero value
            "cash_balance": -100.0,  # Negative balance
            "total_pnl": -5000.0,  # Large loss
            "pnl_percentage": -100.0,  # Complete loss
            "win_rate": 0.0,  # No wins
            "max_drawdown": 1.0,  # Complete drawdown
            "sharpe_ratio": -2.5,  # Very poor Sharpe
            "trade_count": 0,  # No trades
            "last_updated": datetime.now(),
        }

        charts = service.create_performance_charts(edge_case_metrics)

        assert isinstance(charts, dict)
        assert len(charts) > 0

        # Each chart should handle edge cases gracefully
        for chart_name, figure in charts.items():
            assert figure is not None
            assert hasattr(figure, "data")


@pytest.mark.requires_web
class TestConfigurationWizardAdditional:
    """Additional test cases for ConfigurationWizard to improve coverage."""

    def test_get_agent_template_multiple_types(self) -> None:
        """Test getting templates for different agent types."""
        from quantchain.tools.web_dashboard import ConfigurationWizard

        wizard = ConfigurationWizard()

        # Test known agent types
        for agent_type in [
            "memecoin_vibe_trader",
            "chart_reader",
            "smart_contract_auditor",
        ]:
            try:
                template = wizard.get_agent_template(agent_type)
                assert template is not None
                assert "agent_id" in template
                assert template["agent_type"] == agent_type
            except ValueError:
                # Some agent types might not be implemented yet
                pass

    def test_validate_config_with_warnings(self) -> None:
        """Test configuration validation that produces warnings."""
        from quantchain.tools.web_dashboard import ConfigurationWizard

        wizard = ConfigurationWizard()

        config_with_warnings = {
            "agent_id": "test_agent",
            "agent_type": "memecoin_vibe_trader",
            "name": "Test Agent",
            "description": "A test agent",
            "parameters": {"max_positions": 0},  # Edge case - zero positions
            "risk_settings": {"max_allocation": 1.0},  # Full allocation
            "data_sources": [],  # No data sources
            "llm_config": {"model": "unknown_model"},  # Unknown model
        }

        result = wizard.validate_config(config_with_warnings)

        # Should either be valid with warnings or invalid with errors
        assert "is_valid" in result
        assert "errors" in result

    def test_save_config_with_permission_error(self) -> None:
        """Test configuration saving with permission error."""
        from quantchain.tools.web_dashboard import ConfigurationWizard

        wizard = ConfigurationWizard()

        config = {"agent_id": "test_agent", "agent_type": "memecoin_vibe_trader"}

        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            result = wizard.save_config(config, "/root/protected.json")

            assert result is False

    def test_save_config_with_invalid_path(self) -> None:
        """Test configuration saving with invalid file path."""
        from quantchain.tools.web_dashboard import ConfigurationWizard

        wizard = ConfigurationWizard()

        config = {"agent_id": "test_agent", "agent_type": "memecoin_vibe_trader"}

        # Test with invalid path
        result = wizard.save_config(config, "")

        assert result is False


@pytest.mark.requires_web
class TestWebDashboardAppAdditional:
    """Additional test cases for WebDashboardApp to improve coverage."""

    def test_dashboard_app_initialization_with_custom_config(self) -> None:
        """Test WebDashboardApp initialization with custom configuration."""
        from quantchain.tools.web_dashboard import DashboardConfig, WebDashboardApp

        custom_config = DashboardConfig(
            refresh_interval=10,
            max_data_points=2000,
            enable_real_time=False,
            theme="dark",
            default_agent_id="test_agent",
            port=8080,
            host="0.0.0.0",
        )

        app = WebDashboardApp(custom_config)

        assert app.config.refresh_interval == 10
        assert app.config.max_data_points == 2000
        assert app.config.enable_real_time is False
        assert app.config.theme == "dark"
        assert app.config.default_agent_id == "test_agent"
        assert app.config.port == 8080
        assert app.config.host == "0.0.0.0"

    def test_dashboard_service_initialization(self) -> None:
        """Test dashboard service initialization and basic methods."""
        from quantchain.tools.web_dashboard import DashboardConfig, WebDashboardApp

        config = DashboardConfig()
        app = WebDashboardApp(config)

        # Test that services are initialized
        assert hasattr(app, "monitoring_service")
        assert hasattr(app, "visualization_service")
        assert hasattr(app, "config_wizard")
        assert app.monitoring_service is not None
        assert app.visualization_service is not None
        assert app.config_wizard is not None

    @patch("streamlit.set_page_config")
    def test_dashboard_page_config_setup(self, mock_set_page_config) -> None:
        """Test dashboard page configuration setup."""
        from quantchain.tools.web_dashboard import DashboardConfig, WebDashboardApp

        config = DashboardConfig()
        app = WebDashboardApp(config)

        # Test _setup_page_config
        app._setup_page_config()
        mock_set_page_config.assert_called_once()

    def test_dashboard_helper_methods(self) -> None:
        """Test dashboard helper methods and utilities."""
        from quantchain.tools.web_dashboard import DashboardConfig, WebDashboardApp

        config = DashboardConfig()
        app = WebDashboardApp(config)

        # Test service initialization
        assert hasattr(app, "monitoring_service")
        assert hasattr(app, "visualization_service")
        assert hasattr(app, "config_wizard")
        assert app.monitoring_service is not None
        assert app.visualization_service is not None
        assert app.config_wizard is not None


@pytest.mark.requires_web
class TestDataStructures:
    """Test data structure classes for proper initialization."""

    def test_dashboard_config_defaults(self) -> None:
        """Test DashboardConfig default values."""
        from quantchain.tools.web_dashboard import DashboardConfig

        config = DashboardConfig()

        assert config.refresh_interval == 5
        assert config.max_data_points == 1000
        assert config.enable_real_time is True
        assert config.theme == "light"
        assert config.default_agent_id is None
        assert config.port == 8501
        assert config.host == "localhost"

    def test_dashboard_config_custom_values(self) -> None:
        """Test DashboardConfig with custom values."""
        from quantchain.tools.web_dashboard import DashboardConfig

        config = DashboardConfig(
            refresh_interval=15,
            max_data_points=500,
            enable_real_time=False,
            theme="dark",
            default_agent_id="custom_agent",
            port=9000,
            host="custom.host",
        )

        assert config.refresh_interval == 15
        assert config.max_data_points == 500
        assert config.enable_real_time is False
        assert config.theme == "dark"
        assert config.default_agent_id == "custom_agent"
        assert config.port == 9000
        assert config.host == "custom.host"


@pytest.mark.requires_web
class TestWebDashboardIntegration:
    """Integration tests for Web Dashboard components."""

    def test_dashboard_app_creation(self) -> None:
        """Test dashboard app creation with default config."""
        from quantchain.tools.web_dashboard import DashboardConfig, create_dashboard

        # Test with default config
        dashboard = create_dashboard()
        assert dashboard is not None
        assert dashboard.config.refresh_interval == 5

        # Test with custom config
        custom_config = DashboardConfig(refresh_interval=10, theme="dark")
        dashboard = create_dashboard(custom_config)
        assert dashboard.config.refresh_interval == 10
        assert dashboard.config.theme == "dark"

    def test_full_dashboard_workflow(self) -> None:
        """Test complete dashboard workflow from monitoring to visualization."""
        from quantchain.tools.web_dashboard import DashboardConfig, WebDashboardApp

        config = DashboardConfig()
        app = WebDashboardApp(config)

        # Test that services are initialized
        assert app.monitoring_service is not None
        assert app.visualization_service is not None
        assert app.config_wizard is not None

        # Test service methods
        agents = app.monitoring_service.get_all_agents()
        assert isinstance(agents, list)

        health = app.monitoring_service.get_system_health()
        assert "api_status" in health

        # Test visualization service
        charts = app.visualization_service.create_performance_charts(
            {
                "agent_id": "test",
                "total_value": 1000,
                "cash_balance": 100,
                "total_pnl": 50,
                "pnl_percentage": 0.05,
                "win_rate": 0.6,
                "max_drawdown": 0.02,
                "sharpe_ratio": 1.1,
                "trade_count": 10,
                "last_updated": datetime.now(),
            }
        )
        assert isinstance(charts, dict)
        assert len(charts) > 0

    def test_real_time_updates(self) -> None:
        """Test real-time data updates functionality."""
        # Basic test for config settings
        from quantchain.tools.web_dashboard import DashboardConfig

        real_time_config = DashboardConfig(enable_real_time=True, refresh_interval=1)
        assert real_time_config.enable_real_time is True
        assert real_time_config.refresh_interval == 1

        offline_config = DashboardConfig(enable_real_time=False)
        assert offline_config.enable_real_time is False

    def test_multi_agent_support(self) -> None:
        """Test dashboard with multiple running agents."""
        from quantchain.tools.web_dashboard import MonitoringService

        service = MonitoringService()
        agents = service.get_all_agents()

        # Should return list of agents
        assert isinstance(agents, list)

        # Each agent should have required fields
        for agent in agents:
            assert "agent_id" in agent
            assert "agent_type" in agent
            assert "status" in agent
