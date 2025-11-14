"""
Comprehensive tests for web_dashboard.py to improve coverage from 51.7% to 90%+
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import warnings

# Import the actual classes from the web_dashboard module
from quantchain.tools.web_dashboard import (
    DashboardCharts,
    WebDashboardApp,
    create_dashboard,
    render_static_dashboard
)


class TestDashboardCharts:
    """Test cases for the DashboardCharts class."""

    def test_init_default_theme(self):
        """Test initialization with default theme."""
        charts = DashboardCharts()
        assert charts.theme == "plotly_white"

    def test_init_custom_theme(self):
        """Test initialization with custom theme."""
        charts = DashboardCharts(theme="plotly_dark")
        assert charts.theme == "plotly_dark"

    @patch('quantchain.tools.web_dashboard.HAS_PLOTLY', True)
    def test_create_line_chart_with_plotly(self):
        """Test creating a line chart with plotly available."""
        from quantchain.tools.web_dashboard import go

        charts = DashboardCharts()
        x_data = [1, 2, 3, 4, 5]
        y_data = [10, 20, 15, 25, 30]
        title = "Test Chart"

        with patch('quantchain.tools.web_dashboard.go.Figure') as mock_figure:
            fig = charts.create_line_chart(x_data, y_data, title)

            mock_figure.assert_called_once()
            fig_instance = mock_figure.return_value
            fig_instance.add_trace.assert_called_once()
            fig_instance.update_layout.assert_called_once_with(title=title, template=charts.theme)

    @patch('quantchain.tools.web_dashboard.HAS_PLOTLY', False)
    def test_create_line_chart_without_plotly(self):
        """Test creating a line chart without plotly."""
        charts = DashboardCharts()

        with patch('quantchain.tools.web_dashboard.logger') as mock_logger:
            result = charts.create_line_chart([1, 2, 3], [1, 2, 3])

            mock_logger.warning.assert_called_once_with("Cannot create line chart - plotly not available")
            assert result is None

    @patch('quantchain.tools.web_dashboard.HAS_PLOTLY', True)
    def test_create_candlestick_chart_with_plotly(self):
        """Test creating a candlestick chart with plotly available."""
        from quantchain.tools.web_dashboard import go

        charts = DashboardCharts()

        # Create valid DataFrame
        df = pd.DataFrame({
            "open": [100, 101, 102, 103],
            "high": [105, 106, 107, 108],
            "low": [99, 100, 101, 102],
            "close": [104, 105, 106, 107]
        })
        title = "Price Chart"

        with patch('quantchain.tools.web_dashboard.go.Figure') as mock_figure:
            fig = charts.create_candlestick_chart(df, title)

            mock_figure.assert_called_once()
            fig_instance = mock_figure.return_value
            fig_instance.update_layout.assert_called_once_with(title=title, template=charts.theme)

    @patch('quantchain.tools.web_dashboard.HAS_PLOTLY', True)
    def test_create_candlestick_chart_invalid_dataframe(self):
        """Test creating a candlestick chart with invalid DataFrame."""
        charts = DashboardCharts()

        # Create invalid DataFrame (missing columns)
        df = pd.DataFrame({
            "price": [100, 101, 102, 103]
        })

        with pytest.raises(ValueError, match="DataFrame must have columns"):
            charts.create_candlestick_chart(df)

    @patch('quantchain.tools.web_dashboard.HAS_PLOTLY', False)
    def test_create_candlestick_chart_without_plotly(self):
        """Test creating a candlestick chart without plotly."""
        charts = DashboardCharts()

        with patch('quantchain.tools.web_dashboard.logger') as mock_logger:
            df = pd.DataFrame({
                "open": [100, 101],
                "high": [105, 106],
                "low": [99, 100],
                "close": [104, 105]
            })

            result = charts.create_candlestick_chart(df)

            mock_logger.warning.assert_called_once_with("Cannot create candlestick chart - plotly not available")
            assert result is None

    @patch('quantchain.tools.web_dashboard.HAS_PLOTLY', True)
    def test_create_performance_chart_with_plotly(self):
        """Test creating a performance chart with plotly available."""
        from quantchain.tools.web_dashboard import go

        charts = DashboardCharts()

        # Create returns series
        returns = pd.Series([0.01, 0.02, -0.01, 0.03])
        title = "Performance"

        with patch('quantchain.tools.web_dashboard.go.Figure') as mock_figure:
            fig = charts.create_performance_chart(returns, title)

            mock_figure.assert_called_once()
            fig_instance = mock_figure.return_value
            fig_instance.update_layout.assert_called_once()
            # Check that yaxis_title was set
            args, kwargs = fig_instance.update_layout.call_args
            assert kwargs.get('yaxis_title') == "Cumulative Return"

    @patch('quantchain.tools.web_dashboard.HAS_PLOTLY', False)
    def test_create_performance_chart_without_plotly(self):
        """Test creating a performance chart without plotly."""
        charts = DashboardCharts()

        with patch('quantchain.tools.web_dashboard.logger') as mock_logger:
            returns = pd.Series([0.01, 0.02, -0.01])

            result = charts.create_performance_chart(returns)

            mock_logger.warning.assert_called_once_with("Cannot create performance chart - plotly not available")
            assert result is None


class TestWebDashboardApp:
    """Test cases for the WebDashboardApp class."""

    @patch('quantchain.tools.web_dashboard.HAS_STREAMLIT', True)
    def test_init_with_config(self):
        """Test initialization with config."""
        from quantchain.tools.web_dashboard import Config

        config = Config()
        app = WebDashboardApp(config)

        assert app.config == config
        assert isinstance(app.charts, DashboardCharts)

    @patch('quantchain.tools.web_dashboard.HAS_STREAMLIT', False)
    def test_init_without_streamlit(self):
        """Test initialization without streamlit."""
        with patch('quantchain.tools.web_dashboard.logger') as mock_logger:
            app = WebDashboardApp()

            mock_logger.warning.assert_called_once_with("Streamlit not available - web app disabled")

    @patch('quantchain.tools.web_dashboard.HAS_STREAMLIT', True)
    def test_render_sidebar(self):
        """Test rendering sidebar."""
        from quantchain.tools.web_dashboard import st

        app = WebDashboardApp()

        # Mock streamlit components
        with patch('quantchain.tools.web_dashboard.st.title') as mock_title, \
             patch('quantchain.tools.web_dashboard.st.selectbox') as mock_selectbox, \
             patch('quantchain.tools.web_dashboard.st.date_input') as mock_date_input, \
             patch('quantchain.tools.web_dashboard.st.slider') as mock_slider:

            mock_selectbox.return_value = "Mean Reversion"
            mock_date_input.side_effect = [datetime(2023, 1, 1), datetime(2023, 1, 31)]
            mock_slider.return_value = 0.5

            params = app.render_sidebar()

            # Verify all components were called
            mock_title.assert_called_once_with("QuantChain Dashboard")
            mock_selectbox.assert_called_once()
            assert mock_date_input.call_count == 2
            mock_slider.assert_called_once()

            # Verify returned parameters
            assert params["strategy"] == "Mean Reversion"
            assert params["risk_tolerance"] == 0.5

    @patch('quantchain.tools.web_dashboard.HAS_STREAMLIT', True)
    def test_render_main_content(self):
        """Test rendering main content."""
        from quantchain.tools.web_dashboard import st

        app = WebDashboardApp()
        params = {
            "strategy": "Mean Reversion",
            "start_date": datetime(2023, 1, 1),
            "end_date": datetime(2023, 1, 31),
            "risk_tolerance": 0.5
        }

        with patch('quantchain.tools.web_dashboard.st.title') as mock_title, \
             patch('quantchain.tools.web_dashboard.st.plotly_chart') as mock_plotly_chart, \
             patch('quantchain.tools.web_dashboard.st.subheader') as mock_subheader, \
             patch('quantchain.tools.web_dashboard.st.columns') as mock_columns, \
             patch('quantchain.tools.web_dashboard.st.metric') as mock_metric, \
             patch.object(app.charts, 'create_performance_chart') as mock_chart:

            # Mock chart creation
            mock_chart.return_value = {"test": "chart"}

            app.render_main_content(params)

            # Verify components were called
            mock_title.assert_called_once_with("Strategy Performance Dashboard")
            mock_subheader.assert_called_once_with("Performance Statistics")
            mock_plotly_chart.assert_called_once()
            mock_columns.assert_called_once()
            assert mock_metric.call_count == 3

    def test_calculate_max_drawdown(self):
        """Test calculating maximum drawdown."""
        app = WebDashboardApp()

        # Create test returns
        returns = pd.Series([0.01, -0.05, 0.02, -0.02, 0.01])

        max_drawdown = app._calculate_max_drawdown(returns)

        # The max drawdown should be approximately -0.05 (5%)
        assert max_drawdown < 0
        assert abs(max_drawdown - (-0.05)) < 0.01

    @patch('quantchain.tools.web_dashboard.HAS_STREAMLIT', True)
    def test_run_with_streamlit(self):
        """Test running the dashboard with streamlit."""
        app = WebDashboardApp()

        with patch.object(app, 'render_sidebar') as mock_sidebar, \
             patch.object(app, 'render_main_content') as mock_content:

            mock_sidebar.return_value = {"test": "params"}

            app.run()

            mock_sidebar.assert_called_once()
            mock_content.assert_called_once_with({"test": "params"})

    @patch('quantchain.tools.web_dashboard.HAS_STREAMLIT', False)
    def test_run_without_streamlit(self):
        """Test running the dashboard without streamlit."""
        app = WebDashboardApp()

        with patch('quantchain.tools.web_dashboard.logger') as mock_logger:
            with patch('builtins.print') as mock_print:
                app.run()

                mock_logger.error.assert_called_once_with("Cannot run dashboard - streamlit not available")
                mock_print.assert_called_with("Error: Streamlit is required to run the web dashboard")


class TestDashboardFunctions:
    """Test cases for dashboard utility functions."""

    @patch('quantchain.tools.web_dashboard.HAS_PLOTLY', True)
    @patch('quantchain.tools.web_dashboard.HAS_STREAMLIT', True)
    def test_create_dashboard_with_all_features(self):
        """Test creating a dashboard with all features."""
        from quantchain.tools.web_dashboard import Config

        config = Config()
        dashboard = create_dashboard(config)

        assert "charts" in dashboard
        assert "app" in dashboard
        assert "has_plotly" in dashboard
        assert "has_streamlit" in dashboard
        assert "config" in dashboard

        assert dashboard["has_plotly"] is True
        assert dashboard["has_streamlit"] is True
        assert dashboard["config"] == config
        assert isinstance(dashboard["charts"], DashboardCharts)
        assert isinstance(dashboard["app"], WebDashboardApp)

    @patch('quantchain.tools.web_dashboard.HAS_PLOTLY', False)
    def test_create_dashboard_without_plotly(self):
        """Test creating a dashboard without plotly."""
        with patch('quantchain.tools.web_dashboard.logger') as mock_logger:
            dashboard = create_dashboard()

            mock_logger.warning.assert_called_once_with("Dashboard created without plotly support - charts disabled")
            assert dashboard["has_plotly"] is False

    @patch('quantchain.tools.web_dashboard.HAS_STREAMLIT', False)
    def test_create_dashboard_without_streamlit(self):
        """Test creating a dashboard without streamlit."""
        with patch('quantchain.tools.web_dashboard.logger') as mock_logger:
            dashboard = create_dashboard()

            mock_logger.warning.assert_called_once_with("Dashboard created without streamlit support - web app disabled")
            assert dashboard["has_streamlit"] is False

    @patch('quantchain.tools.web_dashboard.HAS_PLOTLY', True)
    def test_render_static_dashboard_with_plotly(self):
        """Test rendering a static dashboard with plotly."""
        data = {
            "performance_data": pd.Series([0.01, 0.02, -0.01, 0.03])
        }

        with patch.object(DashboardCharts, 'create_performance_chart') as mock_chart:
            mock_chart.return_value = {"test": "chart"}

            result = render_static_dashboard(data)

            # Should contain HTML structure
            assert "<!DOCTYPE html>" in result
            assert "<title>QuantChain Dashboard</title>" in result
            assert "<h1>QuantChain Dashboard</h1>" in result

    @patch('quantchain.tools.web_dashboard.HAS_PLOTLY', False)
    def test_render_static_dashboard_without_plotly(self):
        """Test rendering a static dashboard without plotly."""
        with patch('quantchain.tools.web_dashboard.logger') as mock_logger:
            result = render_static_dashboard({})

            mock_logger.error.assert_called_once_with("Cannot render static dashboard - plotly not available")
            assert result == "<html><body><h1>Plotly not available for dashboard rendering</h1></body></html>"

    def test_render_static_dashboard_with_no_data(self):
        """Test rendering a static dashboard with no performance data."""
        # Mock plotly as available
        with patch('quantchain.tools.web_dashboard.HAS_PLOTLY', True):
            result = render_static_dashboard({})

            # Should contain HTML structure but no chart
            assert "<!DOCTYPE html>" in result
            assert "<title>QuantChain Dashboard</title>" in result
            assert "<h1>QuantChain Dashboard</h1>" in result
            # Should not contain performance chart when no data
            assert "performance_data" not in result


class TestOptionalDependencies:
    """Test cases for optional dependencies handling."""

    def test_plotly_import_warning(self):
        """Test that a warning is issued when plotly is not available."""
        with patch.dict('sys.modules', {'plotly': None}):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")

                # Re-import the module to trigger the warning
                import importlib
                import quantchain.tools.web_dashboard
                importlib.reload(quantchain.tools.web_dashboard)

                # Should have issued an ImportWarning
                assert any("plotly not available" in str(warning.message) for warning in w)

    def test_streamlit_import_warning(self):
        """Test that a warning is issued when streamlit is not available."""
        with patch.dict('sys.modules', {'streamlit': None}):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")

                # Re-import the module to trigger the warning
                import importlib
                import quantchain.tools.web_dashboard
                importlib.reload(quantchain.tools.web_dashboard)

                # Should have issued an ImportWarning
                assert any("streamlit not available" in str(warning.message) for warning in w)

    @patch('quantchain.tools.web_dashboard.HAS_PLOTLY', False)
    def test_charts_disabled_without_plotly(self):
        """Test that charts are disabled when plotly is not available."""
        charts = DashboardCharts()

        # All chart creation methods should return None
        assert charts.create_line_chart([1, 2, 3], [1, 2, 3]) is None
        assert charts.create_candlestick_chart(
            pd.DataFrame({"open": [1], "high": [2], "low": [0.5], "close": [1.5]})
        ) is None
        assert charts.create_performance_chart(pd.Series([0.01, 0.02])) is None

    @patch('quantchain.tools.web_dashboard.HAS_STREAMLIT', False)
    def test_app_disabled_without_streamlit(self):
        """Test that the app is disabled when streamlit is not available."""
        app = WebDashboardApp()

        # Run should do nothing but log an error
        with patch('quantchain.tools.web_dashboard.logger') as mock_logger:
            with patch('builtins.print'):
                app.run()

                mock_logger.error.assert_called_once_with("Cannot run dashboard - streamlit not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
