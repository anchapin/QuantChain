"""
Web Dashboard for QuantChain
Interactive web-based dashboard for monitoring trading strategies and portfolios.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import warnings

# Handle optional dependencies gracefully
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    go = None
    px = None
    make_subplots = None
    warnings.warn("plotly not available. Charts will be disabled.", ImportWarning)

try:
    import streamlit as st
    from streamlit.components.v1 import html
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False
    st = None
    html = None
    warnings.warn("streamlit not available. Web app will be disabled.", ImportWarning)

# Core dependencies
import pandas as pd
import numpy as np
from quantchain.core.config import Config
from quantchain.core.exceptions import QuantChainError

logger = logging.getLogger(__name__)


class DashboardCharts:
    """Chart creation functionality for the dashboard."""
    
    def __init__(self, theme: str = "plotly_white"):
        """Initialize charts with theme."""
        self.theme = theme
        if not HAS_PLOTLY:
            logger.warning("Plotly not available - charts disabled")
    
    def create_line_chart(self, x_data: List, y_data: List, title: str = "Chart") -> Optional[Any]:
        """Create a line chart."""
        if not HAS_PLOTLY:
            logger.warning("Cannot create line chart - plotly not available")
            return None
            
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x_data, y=y_data, mode='lines', name='Data'))
        fig.update_layout(title=title, template=self.theme)
        return fig
    
    def create_candlestick_chart(self, df: pd.DataFrame, title: str = "Price Chart") -> Optional[Any]:
        """Create a candlestick chart."""
        if not HAS_PLOTLY:
            logger.warning("Cannot create candlestick chart - plotly not available")
            return None
            
        if not all(col in df.columns for col in ['open', 'high', 'low', 'close']):
            raise ValueError("DataFrame must have columns: open, high, low, close")
            
        fig = go.Figure(data=go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close']
        ))
        fig.update_layout(title=title, template=self.theme)
        return fig
    
    def create_performance_chart(self, returns: pd.Series, title: str = "Performance") -> Optional[Any]:
        """Create cumulative performance chart."""
        if not HAS_PLOTLY:
            logger.warning("Cannot create performance chart - plotly not available")
            return None
            
        cumulative = (1 + returns).cumprod()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=cumulative.index, y=cumulative.values, mode='lines', name='Cumulative Return'))
        fig.update_layout(title=title, template=self.theme, yaxis_title="Cumulative Return")
        return fig


class WebDashboardApp:
    """Streamlit-based web dashboard application."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the dashboard app."""
        self.config = config or Config()
        self.charts = DashboardCharts()
        
        if not HAS_STREAMLIT:
            logger.warning("Streamlit not available - web app disabled")
    
    def render_sidebar(self) -> Dict[str, Any]:
        """Render sidebar with controls."""
        if not HAS_STREAMLIT:
            return {}
            
        st.sidebar.title("QuantChain Dashboard")
        
        # Strategy selection
        strategy_options = ["Mean Reversion", "Momentum", "ML Strategy", "Custom"]
        selected_strategy = st.sidebar.selectbox("Select Strategy", strategy_options)
        
        # Date range
        start_date = st.sidebar.date_input("Start Date", datetime.now() - timedelta(days=30))
        end_date = st.sidebar.date_input("End Date", datetime.now())
        
        # Risk parameters
        risk_tolerance = st.sidebar.slider("Risk Tolerance", 0.0, 1.0, 0.5)
        
        return {
            "strategy": selected_strategy,
            "start_date": start_date,
            "end_date": end_date,
            "risk_tolerance": risk_tolerance
        }
    
    def render_main_content(self, params: Dict[str, Any]) -> None:
        """Render main dashboard content."""
        if not HAS_STREAMLIT:
            return
            
        st.title("Strategy Performance Dashboard")
        
        # Generate sample data (in real app, this would come from backtesting)
        dates = pd.date_range(start=params["start_date"], end=params["end_date"])
        returns = np.random.normal(0.001, 0.02, len(dates))
        df = pd.DataFrame(index=dates, data={"returns": returns})
        
        # Performance chart
        perf_chart = self.charts.create_performance_chart(df["returns"])
        if perf_chart:
            st.plotly_chart(perf_chart, use_container_width=True)
        
        # Statistics
        st.subheader("Performance Statistics")
        total_return = (1 + df["returns"]).prod() - 1
        sharpe_ratio = df["returns"].mean() / df["returns"].std() * np.sqrt(252)
        max_drawdown = self._calculate_max_drawdown(df["returns"])
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Return", f"{total_return:.2%}")
        col2.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
        col3.metric("Max Drawdown", f"{max_drawdown:.2%}")
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown."""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def run(self) -> None:
        """Run the dashboard app."""
        if not HAS_STREAMLIT:
            logger.error("Cannot run dashboard - streamlit not available")
            print("Error: Streamlit is required to run the web dashboard")
            print("Install with: pip install streamlit")
            return
            
        params = self.render_sidebar()
        self.render_main_content(params)


def create_dashboard(config: Optional[Config] = None, include_plots: bool = True) -> Dict[str, Any]:
    """Create a dashboard instance with configurable features."""
    
    dashboard = {
        "charts": DashboardCharts(),
        "app": WebDashboardApp(config),
        "has_plotly": HAS_PLOTLY,
        "has_streamlit": HAS_STREAMLIT,
        "config": config or Config()
    }
    
    if not HAS_PLOTLY and include_plots:
        logger.warning("Dashboard created without plotly support - charts disabled")
    
    if not HAS_STREAMLIT:
        logger.warning("Dashboard created without streamlit support - web app disabled")
    
    return dashboard


def render_static_dashboard(data: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """Render a static HTML dashboard."""
    if not HAS_PLOTLY:
        logger.error("Cannot render static dashboard - plotly not available")
        return "<html><body><h1>Plotly not available for dashboard rendering</h1></body></html>"
    
    # Create HTML content
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>QuantChain Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .chart { margin: 20px 0; }
        </style>
    </head>
    <body>
        <h1>QuantChain Dashboard</h1>
    """
    
    # Add charts if data is provided
    if "performance_data" in data:
        fig = DashboardCharts().create_performance_chart(data["performance_data"])
        if fig:
            chart_html = fig.to_html(include_plotlyjs=False, div_id="performance_chart")
            html_content += f'<div class="chart">{chart_html}</div>'
    
    html_content += """
    </body>
    </html>
    """
    
    if output_path:
        with open(output_path, 'w') as f:
            f.write(html_content)
        logger.info(f"Static dashboard saved to {output_path}")
    
    return html_content


# Convenience function for easy dashboard creation
def main():
    """Main entry point for dashboard."""
    import argparse
    
    parser = argparse.ArgumentParser(description="QuantChain Web Dashboard")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--port", type=int, default=8501, help="Port for streamlit app")
    parser.add_argument("--static", type=str, help="Generate static HTML dashboard")
    
    args = parser.parse_args()
    
    # Load configuration
    config = None
    if args.config:
        config = Config.from_file(args.config)
    
    if args.static:
        # Generate static dashboard
        dashboard = create_dashboard(config)
        html = render_static_dashboard({}, args.static)
        print(f"Static dashboard generated: {args.static}")
    else:
        # Run interactive dashboard
        app = WebDashboardApp(config)
        app.run()


if __name__ == "__main__":
    main()
