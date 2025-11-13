"""Comprehensive tests for web dashboard module."""

import json
import logging
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from quantchain.core.exceptions import QuantChainError
from quantchain.tools.web_dashboard import DashboardCharts, WebDashboardApp


class MockGo:
    """Mock plotly.graph_objects."""

    def __init__(self):
        self.Figure = MagicMock
        self.Scatter = MagicMock
        self.Candlestick = MagicMock


class MockPx:
    """Mock plotly.express."""

    pass


class MockMakeSubplots:
    """Mock plotly.subplots.make_subplots."""

    pass


class MockSt:
    """Mock streamlit."""

    @staticmethod
    def set_page_config(*args, **kwargs):
        pass

    @staticmethod
    def title(*args, **kwargs):
        pass

    @staticmethod
    def sidebar(*args, **kwargs):
        return MockContext()

    @staticmethod
    def tabs(*args):
        return args

    @staticmethod
    def plotly_chart(*args, **kwargs):
        pass

    @staticmethod
    def dataframe(*args, **kwargs):
        pass

    @staticmethod
    def metrics(*args, **kwargs):
        pass

    @staticmethod
    def error(*args, **kwargs):
        pass

    @staticmethod
    def success(*args, **kwargs):
        pass

    @staticmethod
    def info(*args, **kwargs):
        pass


class MockContext:
    """Mock streamlit context manager."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


@pytest.mark.unit
class TestDashboardCharts:
    """Test DashboardCharts class."""

    def test_init_with_plotly(self):
        """Test DashboardCharts initialization with plotly available."""
        with patch("quantchain.tools.web_dashboard.HAS_PLOTLY", True):
            charts = DashboardCharts(theme="test_theme")
            assert charts.theme == "test_theme"

    def test_init_without_plotly(self, caplog):
        """Test DashboardCharts initialization without plotly."""
        with patch("quantchain.tools.web_dashboard.HAS_PLOTLY", False):
            with caplog.at_level("WARNING"):
                charts = DashboardCharts()
                assert charts.theme == "plotly_white"  # default theme

    def test_create_line_chart_with_plotly(self):
        """Test creating line chart when plotly is available."""
        mock_go = MockGo()
        mock_fig = MagicMock()
        mock_go.Figure.return_value = mock_fig

        with patch("quantchain.tools.web_dashboard.HAS_PLOTLY", True):
            with patch("quantchain.tools.web_dashboard.go", mock_go):
                charts = DashboardCharts()
                result = charts.create_line_chart([1, 2, 3], [4, 5, 6], "Test Chart")

                assert result == mock_fig
                mock_go.Figure.assert_called_once()
                mock_fig.add_trace.assert_called_once()
                mock_fig.update_layout.assert_called_once()

    def test_create_line_chart_without_plotly(self, caplog):
        """Test creating line chart when plotly is not available."""
        with patch("quantchain.tools.web_dashboard.HAS_PLOTLY", False):
            with caplog.at_level("WARNING"):
                charts = DashboardCharts()
                result = charts.create_line_chart([1, 2, 3], [4, 5, 6], "Test Chart")

                assert result is None

    def test_create_candlestick_chart_with_plotly(self):
        """Test creating candlestick chart when plotly is available."""
        mock_go = MockGo()
        mock_fig = MagicMock()
        mock_go.Figure.return_value = mock_fig

        df = pd.DataFrame(
            {
                "open": [100, 101, 102],
                "high": [105, 106, 107],
                "low": [95, 96, 97],
                "close": [104, 105, 106],
            }
        )

        with patch("quantchain.tools.web_dashboard.HAS_PLOTLY", True):
            with patch("quantchain.tools.web_dashboard.go", mock_go):
                charts = DashboardCharts()
                result = charts.create_candlestick_chart(df, "Candlestick Test")

                assert result == mock_fig
                mock_go.Figure.assert_called_once()
                mock_fig.update_layout.assert_called_once()

    def test_create_candlestick_chart_missing_columns(self):
        """Test creating candlestick chart with missing required columns."""
        df = pd.DataFrame(
            {
                "open": [100, 101, 102],
                "high": [105, 106, 107],
                # Missing low and close
            }
        )

        with patch("quantchain.tools.web_dashboard.HAS_PLOTLY", True):
            charts = DashboardCharts()

            with pytest.raises(ValueError, match="DataFrame must have columns"):
                charts.create_candlestick_chart(df)

    def test_create_candlestick_chart_without_plotly(self, caplog):
        """Test creating candlestick chart when plotly is not available."""
        df = pd.DataFrame(
            {
                "open": [100, 101, 102],
                "high": [105, 106, 107],
                "low": [95, 96, 97],
                "close": [104, 105, 106],
            }
        )

        with patch("quantchain.tools.web_dashboard.HAS_PLOTLY", False):
            with caplog.at_level("WARNING"):
                charts = DashboardCharts()
                result = charts.create_candlestick_chart(df)

                assert result is None

    def test_create_performance_chart_with_plotly(self):
        """Test creating performance chart when plotly is available."""
        mock_go = MockGo()
        mock_fig = MagicMock()
        mock_go.Figure.return_value = mock_fig

        returns = pd.Series(
            [0.01, 0.02, -0.01, 0.03], index=pd.date_range("2023-01-01", periods=4)
        )

        with patch("quantchain.tools.web_dashboard.HAS_PLOTLY", True):
            with patch("quantchain.tools.web_dashboard.go", mock_go):
                charts = DashboardCharts()
                result = charts.create_performance_chart(returns, "Performance Test")

                assert result == mock_fig
                mock_go.Figure.assert_called_once()
                mock_fig.add_trace.assert_called_once()
                mock_fig.update_layout.assert_called_once()

    def test_create_performance_chart_without_plotly(self, caplog):
        """Test creating performance chart when plotly is not available."""
        returns = pd.Series([0.01, 0.02, -0.01, 0.03])

        with patch("quantchain.tools.web_dashboard.HAS_PLOTLY", False):
            with caplog.at_level("WARNING"):
                charts = DashboardCharts()
                result = charts.create_performance_chart(returns)

                assert result is None


@pytest.mark.unit
class TestWebDashboardApp:
    """Test WebDashboardApp class."""

    def test_init_with_streamlit_and_plotly(self):
        """Test WebDashboardApp initialization with dependencies available."""
        with patch("quantchain.tools.web_dashboard.HAS_STREAMLIT", True):
            with patch("quantchain.tools.web_dashboard.HAS_PLOTLY", True):
                app = WebDashboardApp()
                assert app.charts is not None
                assert isinstance(app.charts, DashboardCharts)

    def test_init_without_streamlit(self, caplog):
        """Test WebDashboardApp initialization without streamlit."""
        with patch("quantchain.tools.web_dashboard.HAS_STREAMLIT", False):
            with caplog.at_level("WARNING"):
                app = WebDashboardApp()
                # Should still initialize but log warning

    def test_init_without_plotly(self):
        """Test WebDashboardApp initialization without plotly."""
        with patch("quantchain.tools.web_dashboard.HAS_STREAMLIT", True):
            with patch("quantchain.tools.web_dashboard.HAS_PLOTLY", False):
                app = WebDashboardApp()
                # Should still initialize charts but without plotly functionality

    def test_load_portfolio_data(self):
        """Test loading portfolio data."""
        mock_portfolio_data = {
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "avg_cost": 150.0,
                    "current_price": 155.0,
                },
                {
                    "symbol": "GOOGL",
                    "quantity": 50,
                    "avg_cost": 2000.0,
                    "current_price": 2100.0,
                },
            ],
            "cash": 10000.0,
            "last_updated": "2023-01-01T00:00:00",
        }

        with patch("builtins.open", mock_open_read(json.dumps(mock_portfolio_data))):
            with patch("os.path.exists", return_value=True):
                with patch("quantchain.tools.web_dashboard.HAS_STREAMLIT", True):
                    app = WebDashboardApp()
                    data = app.load_portfolio_data()

                    assert len(data["positions"]) == 2
                    assert data["cash"] == 10000.0

    def test_load_portfolio_data_file_not_found(self):
        """Test loading portfolio data when file doesn't exist."""
        with patch("os.path.exists", return_value=False):
            with patch("quantchain.tools.web_dashboard.HAS_STREAMLIT", True):
                app = WebDashboardApp()
                data = app.load_portfolio_data()

                assert data == {"positions": [], "cash": 0.0}

    def test_save_portfolio_data(self):
        """Test saving portfolio data."""
        portfolio_data = {
            "positions": [{"symbol": "AAPL", "quantity": 100}],
            "cash": 10000.0,
        }

        with patch("builtins.open", mock_open_write()):
            with patch("json.dump") as mock_dump:
                with patch("quantchain.tools.web_dashboard.HAS_STREAMLIT", True):
                    app = WebDashboardApp()
                    app.save_portfolio_data(portfolio_data)

                    mock_dump.assert_called_once()

    def test_calculate_portfolio_metrics(self):
        """Test calculating portfolio metrics."""
        portfolio_data = {
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "avg_cost": 150.0,
                    "current_price": 155.0,
                },
                {
                    "symbol": "GOOGL",
                    "quantity": 50,
                    "avg_cost": 2000.0,
                    "current_price": 1900.0,
                },
            ],
            "cash": 10000.0,
        }

        with patch("quantchain.tools.web_dashboard.HAS_STREAMLIT", True):
            app = WebDashboardApp()
            metrics = app.calculate_portfolio_metrics(portfolio_data)

            assert "total_value" in metrics
            assert "total_cost" in metrics
            assert "total_pnl" in metrics
            assert "pnl_percentage" in metrics
            assert metrics["total_pnl"] == -5000.0  # GOOGL loss

    def test_get_market_data(self):
        """Test getting market data."""
        mock_data = pd.DataFrame(
            {
                "date": pd.date_range("2023-01-01", periods=10),
                "open": [100 + i for i in range(10)],
                "high": [105 + i for i in range(10)],
                "low": [95 + i for i in range(10)],
                "close": [104 + i for i in range(10)],
                "volume": [1000000] * 10,
            }
        )

        with patch("pandas.read_csv", return_value=mock_data):
            with patch("os.path.exists", return_value=True):
                with patch("quantchain.tools.web_dashboard.HAS_STREAMLIT", True):
                    app = WebDashboardApp()
                    data = app.get_market_data("AAPL")

                    assert len(data) == 10
                    assert "close" in data.columns

    def test_get_market_data_file_not_found(self):
        """Test getting market data when file doesn't exist."""
        with patch("os.path.exists", return_value=False):
            with patch("quantchain.tools.web_dashboard.HAS_STREAMLIT", True):
                app = WebDashboardApp()
                data = app.get_market_data("AAPL")

                assert data is None

    def test_render_portfolio_summary_with_streamlit(self):
        """Test rendering portfolio summary with streamlit."""
        mock_st = MockSt()
        portfolio_data = {
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "avg_cost": 150.0,
                    "current_price": 155.0,
                }
            ],
            "cash": 10000.0,
        }

        with patch("quantchain.tools.web_dashboard.HAS_STREAMLIT", True):
            with patch("quantchain.tools.web_dashboard.st", mock_st):
                app = WebDashboardApp()
                app.render_portfolio_summary(portfolio_data)
                # Should not raise exceptions

    def test_render_portfolio_charts_with_plotly(self):
        """Test rendering portfolio charts with plotly available."""
        mock_st = MockSt()
        mock_go = MockGo()
        mock_fig = MagicMock()
        mock_go.Figure.return_value = mock_fig

        portfolio_data = {
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "avg_cost": 150.0,
                    "current_price": 155.0,
                }
            ],
            "cash": 10000.0,
        }

        with patch("quantchain.tools.web_dashboard.HAS_STREAMLIT", True):
            with patch("quantchain.tools.web_dashboard.HAS_PLOTLY", True):
                with patch("quantchain.tools.web_dashboard.st", mock_st):
                    with patch("quantchain.tools.web_dashboard.go", mock_go):
                        app = WebDashboardApp()
                        app.render_portfolio_charts(portfolio_data)

    def test_run_with_streamlit(self):
        """Test running the dashboard app with streamlit."""
        mock_st = MockSt()

        with patch("quantchain.tools.web_dashboard.HAS_STREAMLIT", True):
            with patch("quantchain.tools.web_dashboard.st", mock_st):
                app = WebDashboardApp()
                app.run()
                # Should not raise exceptions

    def test_run_without_streamlit(self):
        """Test running the dashboard app without streamlit."""
        with patch("quantchain.tools.web_dashboard.HAS_STREAMLIT", False):
            app = WebDashboardApp()

            with pytest.raises(QuantChainError, match="Streamlit not available"):
                app.run()


class MockOpenRead:
    """Mock open for reading."""

    def __init__(self, content):
        self.content = content

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        return self.content


class MockOpenWrite:
    """Mock open for writing."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def write(self, content):
        pass


def mock_open_read(content):
    """Return mock open for reading."""
    return lambda *args, **kwargs: MockOpenRead(content)


def mock_open_write():
    """Return mock open for writing."""
    return lambda *args, **kwargs: MockOpenWrite()


@pytest.mark.unit
class TestWebDashboardIntegration:
    """Integration tests for web dashboard."""

    def test_full_workflow(self):
        """Test full workflow of loading data and rendering dashboard."""
        # Mock data
        portfolio_data = {
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "avg_cost": 150.0,
                    "current_price": 155.0,
                },
                {
                    "symbol": "GOOGL",
                    "quantity": 50,
                    "avg_cost": 2000.0,
                    "current_price": 2100.0,
                },
            ],
            "cash": 10000.0,
        }

        mock_st = MockSt()

        with patch("quantchain.tools.web_dashboard.HAS_STREAMLIT", True):
            with patch("quantchain.tools.web_dashboard.HAS_PLOTLY", True):
                with patch("quantchain.tools.web_dashboard.st", mock_st):
                    with patch(
                        "builtins.open", mock_open_read(json.dumps(portfolio_data))
                    ):
                        with patch("os.path.exists", return_value=True):
                            app = WebDashboardApp()

                            # Load data
                            loaded_data = app.load_portfolio_data()
                            assert loaded_data == portfolio_data

                            # Calculate metrics
                            metrics = app.calculate_portfolio_metrics(loaded_data)
                            assert "total_value" in metrics

                            # Render components
                            app.render_portfolio_summary(loaded_data)
                            app.render_portfolio_charts(loaded_data)

    def test_error_handling(self):
        """Test error handling in dashboard operations."""
        mock_st = MockSt()

        with patch("quantchain.tools.web_dashboard.HAS_STREAMLIT", True):
            with patch("quantchain.tools.web_dashboard.st", mock_st):
                app = WebDashboardApp()

                # Test with empty portfolio
                empty_portfolio = {"positions": [], "cash": 0.0}
                metrics = app.calculate_portfolio_metrics(empty_portfolio)
                assert metrics["total_value"] == 0.0
                assert metrics["total_pnl"] == 0.0

    def test_data_persistence(self):
        """Test data persistence operations."""
        portfolio_data = {
            "positions": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "avg_cost": 150.0,
                    "current_price": 155.0,
                }
            ],
            "cash": 10000.0,
        }

        with patch("builtins.open") as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            mock_open.return_value.__exit__.return_value = None

            with patch("json.dump") as mock_dump:
                with patch("quantchain.tools.web_dashboard.HAS_STREAMLIT", True):
                    app = WebDashboardApp()
                    app.save_portfolio_data(portfolio_data)

                    mock_dump.assert_called_once_with(
                        portfolio_data, mock_file, indent=2
                    )
