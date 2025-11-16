"""
Web Dashboard for QuantChain Agent Monitoring and Configuration.

This module provides a Streamlit-based web interface for monitoring autonomous
trading agents, visualizing their reasoning processes, and managing their
configurations.
"""

import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

# Optional imports for web dashboard
try:
    import plotly.graph_objects as go

    HAS_PLOTLY = True
except ImportError:
    go = None
    HAS_PLOTLY = False

try:
    import streamlit as st

    HAS_STREAMLIT = True
except ImportError:
    st = None
    HAS_STREAMLIT = False

# Add the project root to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


@dataclass
class DashboardConfig:
    """Configuration for the web dashboard."""

    refresh_interval: int = 5  # seconds
    max_data_points: int = 1000
    enable_real_time: bool = True
    theme: str = "light"
    default_agent_id: Optional[str] = None
    port: int = 8501
    host: str = "localhost"


@dataclass
class AgentStatus:
    """Status information for an agent."""

    agent_id: str
    agent_type: str
    status: str  # "RUNNING", "STOPPED", "ERROR"
    last_update: datetime
    current_positions: List[Dict[str, Any]]
    recent_trades: List[Dict[str, Any]]
    error_count: int
    uptime: timedelta


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics."""

    agent_id: str
    total_value: float
    cash_balance: float
    total_pnl: float
    pnl_percentage: float
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    trade_count: int
    last_updated: datetime


@dataclass
class SystemHealth:
    """System health information."""

    api_status: Dict[str, bool]
    llm_response_time_ms: float
    error_rate_24h: float
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_space_gb: float
    uptime_hours: float


@dataclass
class AgentConfig:
    """Agent configuration structure."""

    agent_id: str
    agent_type: str
    name: str
    description: str


class DashboardCharts:
    """Chart creation utilities for the dashboard."""

    @staticmethod
    def create_equity_curve(
        data: List[Dict[str, Any]], title: str = "Portfolio Equity Curve"
    ) -> Any:
        """
        Create an equity curve chart.

        Args:
            data: List of portfolio snapshots over time
            title: Chart title

        Returns:
            Plotly figure object or None if Plotly not available
        """
        if not HAS_PLOTLY or not data:
            return None

        # Convert to DataFrame for easier plotting
        df = pd.DataFrame(data)
        if "timestamp" not in df.columns or "value" not in df.columns:
            return None

        # Create figure
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["value"],
                mode="lines",
                name="Portfolio Value",
                line=dict(color="royalblue", width=2),
            )
        )

        # Add layout
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Portfolio Value ($)",
            template="plotly_white",
        )

        return fig

    @staticmethod
    def create_candlestick_chart(data: pd.DataFrame, title: str = "Price Chart") -> Any:
        """
        Create a candlestick chart for price data.

        Args:
            data: DataFrame with OHLC data
            title: Chart title

        Returns:
            Plotly figure object or None if Plotly not available
        """
        if not HAS_PLOTLY or data.empty:
            return None

        required_columns = ["open", "high", "low", "close"]
        if not all(col in data.columns for col in required_columns):
            return None

        # Create figure
        fig = go.Figure(
            data=go.Candlestick(
                x=data.index,
                open=data["open"],
                high=data["high"],
                low=data["low"],
                close=data["close"],
            )
        )

        # Add layout
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Price",
            template="plotly_white",
        )

        return fig

    @staticmethod
    def create_performance_chart(
        metrics: Dict[str, float], title: str = "Performance Metrics"
    ) -> Any:
        """
        Create a performance metrics bar chart.

        Args:
            metrics: Dictionary of metric name -> value
            title: Chart title

        Returns:
            Plotly figure object or None if Plotly not available
        """
        if not HAS_PLOTLY or not metrics:
            return None

        # Create figure
        fig = go.Figure(
            data=[
                go.Bar(
                    x=list(metrics.keys()),
                    y=list(metrics.values()),
                    marker_color=["royalblue", "crimson", "green", "orange", "purple"][
                        : len(metrics)
                    ],
                )
            ]
        )

        # Add layout
        fig.update_layout(
            title=title,
            xaxis_title="Metric",
            yaxis_title="Value",
            template="plotly_white",
        )

        return fig


class MonitoringService:
    """Service for monitoring agent status and system health."""

    def __init__(self):
        """Initialize the monitoring service."""
        self.agents = {}

    def get_agent_status(self, agent_id: str) -> AgentStatus:
        """
        Get current status of a specific agent.

        Args:
            agent_id: Unique identifier for agent

        Returns:
            AgentStatus object with current state
        """
        # In a real implementation, this would query the actual agent
        # For now, return mock data
        if agent_id in self.agents:
            return self.agents[agent_id]

        return AgentStatus(
            agent_id=agent_id,
            agent_type="QuantTrader",
            status="UNKNOWN",
            last_update=datetime.now(),
            current_positions=[],
            recent_trades=[],
            error_count=0,
            uptime=timedelta(0),
        )

    def get_portfolio_metrics(self, agent_id: str) -> PortfolioMetrics:
        """
        Get portfolio performance metrics for an agent.

        Args:
            agent_id: Unique identifier for agent

        Returns:
            PortfolioMetrics with performance data
        """
        # In a real implementation, this would query the actual agent
        # For now, return mock data
        return PortfolioMetrics(
            agent_id=agent_id,
            total_value=100000.0,
            cash_balance=50000.0,
            total_pnl=1000.0,
            pnl_percentage=1.0,
            win_rate=0.55,
            max_drawdown=0.05,
            sharpe_ratio=1.2,
            trade_count=100,
            last_updated=datetime.now(),
        )

    def get_system_health(self) -> SystemHealth:
        """
        Get overall system health status.

        Returns:
            SystemHealth object with status metrics
        """
        # In a real implementation, this would query the actual system
        # For now, return mock data
        return SystemHealth(
            api_status={"alpaca": True, "polygon": True},
            llm_response_time_ms=250.0,
            error_rate_24h=0.01,
            cpu_usage_percent=35.0,
            memory_usage_percent=60.0,
            disk_space_gb=100.0,
            uptime_hours=24.5,
        )

    def list_agents(self) -> List[str]:
        """
        Get list of all available agents.

        Returns:
            List of agent IDs
        """
        # In a real implementation, this would query the actual agents
        return ["demo_agent_1", "demo_agent_2"]

    def update_agent_status(self, agent_status: AgentStatus) -> None:
        """
        Update the status of an agent.

        Args:
            agent_status: Updated agent status
        """
        self.agents[agent_status.agent_id] = agent_status


class ConfigurationService:
    """Service for managing agent configurations."""

    def __init__(self):
        """Initialize the configuration service."""
        self.configs = {}

    def get_agent_config(self, agent_id: str) -> AgentConfig:
        """
        Get configuration for an agent.

        Args:
            agent_id: Unique identifier for agent

        Returns:
            AgentConfig object
        """
        # In a real implementation, this would query the actual config
        # For now, return mock data
        if agent_id in self.configs:
            return self.configs[agent_id]

        return AgentConfig(
            agent_id=agent_id,
            agent_type="QuantTrader",
            name=f"Agent {agent_id}",
            description="A quantitative trading agent",
        )

    def update_agent_config(self, config: AgentConfig) -> None:
        """
        Update configuration for an agent.

        Args:
            config: Updated agent configuration
        """
        self.configs[config.agent_id] = config

    def save_config(self, agent_id: str) -> bool:
        """
        Save configuration to persistent storage.

        Args:
            agent_id: Unique identifier for agent

        Returns:
            True if successful, False otherwise
        """
        # In a real implementation, this would save to a database or file
        return True


class WebDashboardApp:
    """Main dashboard application class."""

    def __init__(self, config: DashboardConfig):
        """
        Initialize web dashboard.

        Args:
            config: Dashboard configuration object
        """
        self.config = config
        self.monitoring_service = MonitoringService()
        self.config_service = ConfigurationService()
        self.charts = DashboardCharts()

    def run(self, host: str = "localhost", port: int = 8501) -> None:
        """
        Start Streamlit application.

        Args:
            host: Host address to bind to
            port: Port number to run on
        """
        if not HAS_STREAMLIT:
            print("Streamlit is not available. Cannot run web dashboard.")
            return

        # In a real implementation, we would use subprocess to call:
        # streamlit run _streamlit_app.py --server.port=port --server.address=host
        print(f"Starting Streamlit app at http://{host}:{port}")

    def _render_sidebar(self) -> Dict[str, Any]:
        """
        Render sidebar navigation.

        Returns:
            Dictionary with sidebar state
        """
        if not HAS_STREAMLIT:
            return {}

        with st.sidebar:
            st.title("QuantChain Dashboard")

            # Agent selection
            agents = self.monitoring_service.list_agents()
            agent_id = st.selectbox(
                "Select Agent",
                agents,
                index=(
                    0
                    if not self.config.default_agent_id
                    else agents.index(self.config.default_agent_id)
                ),
            )

            # Page selection
            page = st.selectbox(
                "Select Page", ["Overview", "Portfolio", "Reasoning", "Configuration"]
            )

            # Refresh button
            if st.button("Refresh Data"):
                st.experimental_rerun()

            return {"agent_id": agent_id, "page": page}

    def _render_overview_page(self, agent_id: str) -> None:
        """
        Render overview page.

        Args:
            agent_id: ID of the selected agent
        """
        if not HAS_STREAMLIT:
            return

        st.header("Agent Overview")

        # Get agent status
        status = self.monitoring_service.get_agent_status(agent_id)
        metrics = self.monitoring_service.get_portfolio_metrics(agent_id)

        # Display status metrics
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Status")
            st.info(f"Status: {status.status}")
            st.info(f"Uptime: {status.uptime}")

            with col2:
                st.subheader("Performance")
                st.info(
                    f"Total Return: {metrics.total_pnl:.2f} ({metrics.pnl_percentage:.2f}%)"
                )
                st.info(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")

        # System health
        st.subheader("System Health")
        health = self.monitoring_service.get_system_health()
        health_df = pd.DataFrame(
            {
                "Metric": [
                    "API Status",
                    "LLM Response Time",
                    "Error Rate",
                    "CPU Usage",
                    "Memory Usage",
                ],
                "Value": [
                    (
                        "All APIs Up"
                        if all(health.api_status.values())
                        else "Some APIs Down"
                    ),
                    f"{health.llm_response_time_ms:.0f}ms",
                    f"{health.error_rate_24h * 100:.2f}%",
                    f"{health.cpu_usage_percent:.1f}%",
                    f"{health.memory_usage_percent:.1f}%",
                ],
            }
        )
        st.dataframe(health_df)

    def _render_portfolio_page(self, agent_id: str) -> None:
        """
        Render portfolio page.

        Args:
            agent_id: ID of the selected agent
        """
        if not HAS_STREAMLIT:
            return

        st.header("Portfolio Analysis")

        # Get portfolio data
        metrics = self.monitoring_service.get_portfolio_metrics(agent_id)
        status = self.monitoring_service.get_agent_status(agent_id)

        # Display portfolio metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Value", f"${metrics.total_value:,.2f}")
            st.metric("Cash Balance", f"${metrics.cash_balance:,.2f}")

        with col2:
            st.metric("Win Rate", f"{metrics.win_rate * 100:.1f}%")
            st.metric("Trade Count", f"{metrics.trade_count}")

        with col3:
            st.metric("Max Drawdown", f"{metrics.max_drawdown * 100:.1f}%")
            st.metric("Sharpe Ratio", f"{metrics.sharpe_ratio:.2f}")

        # Create equity curve chart
        if HAS_PLOTLY:
            # Generate sample data for demonstration
            dates = pd.date_range(end=datetime.now(), periods=30, freq="D")
            values = [100000 * (1 + i * 0.001) for i in range(30)]
            data = [
                {"timestamp": date, "value": value}
                for date, value in zip(dates, values)
            ]

            equity_fig = self.charts.create_equity_curve(
                data, f"Equity Curve - {agent_id}"
            )
            if equity_fig:
                st.plotly_chart(equity_fig, use_container_width=True)

        # Display current positions
        st.subheader("Current Positions")
        if status.current_positions:
            positions_df = pd.DataFrame(status.current_positions)
            st.dataframe(positions_df)
        else:
            st.info("No open positions")

        # Display recent trades
        st.subheader("Recent Trades")
        if status.recent_trades:
            trades_df = pd.DataFrame(status.recent_trades)
            st.dataframe(trades_df)
        else:
            st.info("No recent trades")

    def _render_reasoning_page(self, agent_id: str) -> None:
        """
        Render reasoning page.

        Args:
            agent_id: ID of the selected agent
        """
        if not HAS_STREAMLIT:
            return

        st.header("Agent Reasoning")

        # In a real implementation, this would show the agent's reasoning process
        # For now, show mock data
        st.info("Reasoning visualization not yet implemented")

        # Example of what could be displayed:
        # - LLM prompts and responses
        # - Decision trees
        # - Trade rationales
        # - Signal strength indicators

    def _render_configuration_page(self, agent_id: str) -> None:
        """
        Render configuration page.

        Args:
            agent_id: ID of the selected agent
        """
        if not HAS_STREAMLIT:
            return

        st.header("Agent Configuration")

        # Get current config
        config = self.config_service.get_agent_config(agent_id)

        # Display editable configuration
        with st.form("agent_config_form"):
            name = st.text_input("Agent Name", value=config.name)
            description = st.text_area("Description", value=config.description)

            # In a real implementation, there would be many more configuration options
            # such as trading parameters, risk settings, etc.

            submitted = st.form_submit_button("Save Configuration")
            if submitted:
                # Update configuration
                updated_config = AgentConfig(
                    agent_id=agent_id,
                    agent_type=config.agent_type,
                    name=name,
                    description=description,
                )
                self.config_service.update_agent_config(updated_config)
                self.config_service.save_config(agent_id)
                st.success("Configuration saved successfully!")


# Create and export a function to run the dashboard
def create_dashboard_app(config: DashboardConfig = None) -> WebDashboardApp:
    """
    Create a dashboard application instance.

    Args:
        config: Optional dashboard configuration

    Returns:
        WebDashboardApp instance
    """
    if config is None:
        config = DashboardConfig()

    return WebDashboardApp(config)


# Export functions for compatibility with tests
def render_sidebar(app: WebDashboardApp) -> Dict[str, Any]:
    """Render sidebar for the given app."""
    return app._render_sidebar()


def render_overview_page(app: WebDashboardApp, agent_id: str) -> None:
    """Render overview page for the given app."""
    app._render_overview_page(agent_id)


def render_portfolio_page(app: WebDashboardApp, agent_id: str) -> None:
    """Render portfolio page for the given app."""
    app._render_portfolio_page(agent_id)


def render_reasoning_page(app: WebDashboardApp, agent_id: str) -> None:
    """Render reasoning page for the given app."""
    app._render_reasoning_page(agent_id)


def render_configuration_page(app: WebDashboardApp, agent_id: str) -> None:
    """Render configuration page for the given app."""
    app._render_configuration_page(agent_id)


def create_line_chart(data: List[Dict[str, Any]], title: str = "Chart") -> Any:
    """
    Create a line chart using Plotly.

    Args:
        data: List of data points
        title: Chart title

    Returns:
        Plotly figure object or None
    """
    if not HAS_PLOTLY:
        return None

    if not data or len(data) < 2:
        return None

    df = pd.DataFrame(data)
    x_col = df.columns[0] if len(df.columns) > 0 else "x"
    y_col = df.columns[1] if len(df.columns) > 1 else "y"

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df[x_col], y=df[y_col], mode="lines", name=y_col))

    fig.update_layout(
        title=title, xaxis_title=x_col, yaxis_title=y_col, template="plotly_white"
    )

    return fig


def calculate_max_drawdown(equity_curve: List[float]) -> float:
    """
    Calculate maximum drawdown from equity curve.

    Args:
        equity_curve: List of portfolio values over time

    Returns:
        Maximum drawdown as a percentage
    """
    if not equity_curve or len(equity_curve) < 2:
        return 0.0

    # Convert to numpy array for easier calculation
    import numpy as np

    values = np.array(equity_curve)

    # Calculate running maximum
    running_max = np.maximum.accumulate(values)

    # Calculate drawdown
    drawdown = (values - running_max) / running_max

    # Return maximum drawdown (as positive percentage)
    return abs(np.min(drawdown))


# Main function for running the dashboard directly
def main():
    """Main function to run the dashboard directly."""
    # Parse command line arguments
    import argparse

    parser = argparse.ArgumentParser(description="QuantChain Web Dashboard")
    parser.add_argument("--host", default="localhost", help="Host address to bind to")
    parser.add_argument("--port", type=int, default=8501, help="Port number to run on")
    parser.add_argument("--agent-id", help="Default agent ID to display")
    args = parser.parse_args()

    # Create configuration
    config = DashboardConfig(
        host=args.host, port=args.port, default_agent_id=args.agent_id
    )

    # Create and run the app
    app = create_dashboard_app(config)
    app.run(host=config.host, port=config.port)


if __name__ == "__main__":
    # Allow running the dashboard directly
    main()
