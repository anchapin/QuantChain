"""Enhanced comprehensive tests for web dashboard module."""

import json
import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import pytest

from quantchain.core.exceptions import QuantChainError
from quantchain.tools.web_dashboard import (
    DashboardCharts,
    WebDashboardApp,
)


class MockGo:
    """Mock plotly.graph_objects."""
    
    def Figure(self, *args, **kwargs):
        return MagicMock()
    
    def Scatter(self, *args, **kwargs):
        return MagicMock()
    
    def Candlestick(self, *args, **kwargs):
        return MagicMock()
    
    def Bar(self, *args, **kwargs):
        return MagicMock()


class MockPx:
    """Mock plotly.express."""
    
    def line(self, *args, **kwargs):
        return MagicMock()
    
    def bar(self, *args, **kwargs):
        return MagicMock()
    
    def scatter(self, *args, **kwargs):
        return MagicMock()
    
    def histogram(self, *args, **kwargs):
        return MagicMock()


class MockMakeSubplots:
    """Mock plotly.subplots.make_subplots."""
    
    def __call__(self, *args, **kwargs):
        return MagicMock()


class MockSt:
    """Mock streamlit."""
    
    @staticmethod
    def set_page_config(*args, **kwargs):
        return MagicMock()
    
    @staticmethod
    def title(*args, **kwargs):
        return MagicMock()
    
    @staticmethod
    def sidebar(*args, **kwargs):
        return MockContext()
    
    @staticmethod
    def tabs(*args, **kwargs):
        return [MockTab() for _ in args]
    
    @staticmethod
    def header(*args, **kwargs):
        return MagicMock()
    
    @staticmethod
    def subheader(*args, **kwargs):
        return MagicMock()
    
    @staticmethod
    def markdown(*args, **kwargs):
        return MagicMock()
    
    @staticmethod
    def dataframe(*args, **kwargs):
        return MagicMock()
    
    @staticmethod
    def plotly_chart(*args, **kwargs):
        return MagicMock()
    
    @staticmethod
    def columns(*args, **kwargs):
        return [MockColumn() for _ in args]
    
    @staticmethod
    def selectbox(*args, **kwargs):
        return "option1"
    
    @staticmethod
    def date_input(*args, **kwargs):
        return datetime(2024, 1, 1)
    
    @staticmethod
    def date_range_input(*args, **kwargs):
        return (datetime(2024, 1, 1), datetime(2024, 12, 31))
    
    @staticmethod
    def number_input(*args, **kwargs):
        return 100.0
    
    @staticmethod
    def text_input(*args, **kwargs):
        return "test"
    
    @staticmethod
    def button(*args, **kwargs):
        return False
    
    @staticmethod
    def file_uploader(*args, **kwargs):
        return None
    
    @staticmethod
    def error(*args, **kwargs):
        return MagicMock()
    
    @staticmethod
    def warning(*args, **kwargs):
        return MagicMock()
    
    @staticmethod
    def info(*args, **kwargs):
        return MagicMock()
    
    @staticmethod
    def success(*args, **kwargs):
        return MagicMock()


class MockTab:
    """Mock streamlit tab."""
    
    def __call__(self, *args, **kwargs):
        return self


class MockColumn:
    """Mock streamlit column."""
    
    def __call__(self, *args, **kwargs):
        return self


class MockContext:
    """Mock streamlit context manager."""
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args, **kwargs):
        pass


@pytest.mark.unit
class TestDashboardCharts:
    """Test suite for DashboardCharts class."""

    @pytest.fixture
    def mock_plotly(self):
        """Mock plotly modules."""
        return {
            'plotly.graph_objects': MockGo(),
            'plotly.express': MockPx(),
            'plotly.subplots': MagicMock(make_subplots=MockMakeSubplots()),
        }

    def test_create_equity_chart(self, mock_plotly):
        """Test creating equity curve chart."""
        with patch.dict('sys.modules', mock_plotly):
            charts = DashboardCharts()
            
            # Create test data
            dates = pd.date_range("2024-01-01", periods=10, freq="D")
            equity = np.cumsum(np.random.randn(10) * 100) + 100000
            
            # Create chart
            fig = charts.create_equity_chart(dates, equity)
            
            # Verify mock was called
            assert fig is not None

    def test_create_drawdown_chart(self, mock_plotly):
        """Test creating drawdown chart."""
        with patch.dict('sys.modules', mock_plotly):
            charts = DashboardCharts()
            
            # Create test data
            dates = pd.date_range("2024-01-01", periods=10, freq="D")
            drawdown = np.random.rand(10) * 0.2  # 0-20% drawdown
            
            # Create chart
            fig = charts.create_drawdown_chart(dates, drawdown)
            
            # Verify mock was called
            assert fig is not None

    def test_create_returns_distribution(self, mock_plotly):
        """Test creating returns distribution chart."""
        with patch.dict('sys.modules', mock_plotly):
            charts = DashboardCharts()
            
            # Create test returns
            returns = np.random.randn(100) * 0.02  # Daily returns
            
            # Create chart
            fig = charts.create_returns_distribution(returns)
            
            # Verify mock was called
            assert fig is not None

    def test_create_correlation_heatmap(self, mock_plotly):
        """Test creating correlation heatmap."""
        with patch.dict('sys.modules', mock_plotly):
            charts = DashboardCharts()
            
            # Create test correlation matrix
            corr_matrix = pd.DataFrame({
                'AAPL': [1.0, 0.5, 0.3],
                'MSFT': [0.5, 1.0, 0.4],
                'GOOGL': [0.3, 0.4, 1.0],
            }, index=['AAPL', 'MSFT', 'GOOGL'])
            
            # Create chart
            fig = charts.create_correlation_heatmap(corr_matrix)
            
            # Verify mock was called
            assert fig is not None

    def test_create_performance_summary(self, mock_plotly):
        """Test creating performance summary chart."""
        with patch.dict('sys.modules', mock_plotly):
            charts = DashboardCharts()
            
            # Create test metrics
            metrics = {
                'Total Return': 0.15,
                'Annualized Return': 0.12,
                'Sharpe Ratio': 1.5,
                'Max Drawdown': -0.08,
                'Win Rate': 0.6,
            }
            
            # Create chart
            fig = charts.create_performance_summary(metrics)
            
            # Verify mock was called
            assert fig is not None

    def test_create_rolling_metrics(self, mock_plotly):
        """Test creating rolling metrics chart."""
        with patch.dict('sys.modules', mock_plotly):
            charts = DashboardCharts()
            
            # Create test data
            dates = pd.date_range("2024-01-01", periods=100, freq="D")
            rolling_sharpe = np.cumsum(np.random.randn(100) * 0.1)
            rolling_drawdown = np.random.rand(100) * 0.2
            
            # Create chart
            fig = charts.create_rolling_metrics(
                dates, rolling_sharpe, rolling_drawdown
            )
            
            # Verify mock was called
            assert fig is not None

    def test_error_handling_invalid_data(self, mock_plotly):
        """Test error handling with invalid data."""
        with patch.dict('sys.modules', mock_plotly):
            charts = DashboardCharts()
            
            # Test with empty data
            with pytest.raises(ValueError, match="Data cannot be empty"):
                charts.create_equity_chart(pd.Series(), np.array([]))
            
            # Test with mismatched lengths
            with pytest.raises(ValueError, match="Data length mismatch"):
                charts.create_equity_chart(
                    pd.date_range("2024-01-01", periods=5, freq="D"),
                    np.array([1, 2, 3])  # Only 3 values
                )


@pytest.mark.unit
class TestWebDashboardApp:
    """Test suite for WebDashboardApp class."""

    @pytest.fixture
    def mock_plotly_and_streamlit(self):
        """Mock both plotly and streamlit modules."""
        return {
            'plotly.graph_objects': MockGo(),
            'plotly.express': MockPx(),
            'plotly.subplots': MagicMock(make_subplots=MockMakeSubplots()),
            'streamlit': MockSt(),
        }

    def test_initialization(self, mock_plotly_and_streamlit):
        """Test dashboard initialization."""
        with patch.dict('sys.modules', mock_plotly_and_streamlit):
            # Should not raise during initialization
            app = WebDashboardApp()
            assert app is not None

    def test_initialization_with_config(self, mock_plotly_and_streamlit):
        """Test dashboard initialization with configuration."""
        with patch.dict('sys.modules', mock_plotly_and_streamlit):
            config = {
                'title': 'Custom Dashboard',
                'theme': 'dark',
                'auto_refresh': True,
                'refresh_interval': 30,
            }
            
            app = WebDashboardApp(config=config)
            assert app is not None

    @patch('quantchain.tools.web_dashboard.WebDashboardApp.load_data')
    def test_render_overview_page(self, mock_load_data, mock_plotly_and_streamlit):
        """Test rendering overview page."""
        # Setup mock data
        mock_load_data.return_value = {
            'equity_curve': pd.Series(
                np.cumsum(np.random.randn(100) * 100) + 100000,
                index=pd.date_range("2024-01-01", periods=100, freq="D")
            ),
            'returns': np.random.randn(100) * 0.02,
            'metrics': {
                'Total Return': 0.15,
                'Annualized Return': 0.12,
                'Sharpe Ratio': 1.5,
            },
        }
        
        with patch.dict('sys.modules', mock_plotly_and_streamlit):
            app = WebDashboardApp()
            
            # Should not raise
            app.render_overview_page()

    @patch('quantchain.tools.web_dashboard.WebDashboardApp.load_data')
    def test_render_analysis_page(self, mock_load_data, mock_plotly_and_streamlit):
        """Test rendering analysis page."""
        # Setup mock data
        mock_load_data.return_value = {
            'returns': np.random.randn(100) * 0.02,
            'correlation_matrix': pd.DataFrame({
                'AAPL': [1.0, 0.5, 0.3],
                'MSFT': [0.5, 1.0, 0.4],
                'GOOGL': [0.3, 0.4, 1.0],
            }, index=['AAPL', 'MSFT', 'GOOGL']),
        }
        
        with patch.dict('sys.modules', mock_plotly_and_streamlit):
            app = WebDashboardApp()
            
            # Should not raise
            app.render_analysis_page()

    @patch('quantchain.tools.web_dashboard.WebDashboardApp.load_data')
    def test_render_performance_page(self, mock_load_data, mock_plotly_and_streamlit):
        """Test rendering performance page."""
        # Setup mock data
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        mock_load_data.return_value = {
            'equity_curve': pd.Series(
                np.cumsum(np.random.randn(100) * 100) + 100000,
                index=dates
            ),
            'rolling_metrics': pd.DataFrame({
                'Sharpe': np.cumsum(np.random.randn(100) * 0.1),
                'Drawdown': np.random.rand(100) * 0.2,
            }, index=dates),
        }
        
        with patch.dict('sys.modules', mock_plotly_and_streamlit):
            app = WebDashboardApp()
            
            # Should not raise
            app.render_performance_page()

    @patch('quantchain.tools.web_dashboard.WebDashboardApp.load_data')
    def test_render_settings_page(self, mock_load_data, mock_plotly_and_streamlit):
        """Test rendering settings page."""
        with patch.dict('sys.modules', mock_plotly_and_streamlit):
            app = WebDashboardApp()
            
            # Should not raise
            app.render_settings_page()

    def test_load_data_from_file(self, mock_plotly_and_streamlit):
        """Test loading data from file."""
        # Create test data file
        test_data = {
            'dates': pd.date_range("2024-01-01", periods=10, freq="D").tolist(),
            'equity': np.cumsum(np.random.randn(10) * 100 + 100000).tolist(),
            'returns': np.random.randn(10).tolist(),
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            with patch.dict('sys.modules', mock_plotly_and_streamlit):
                app = WebDashboardApp()
                
                # Load from temp file
                data = app.load_data_from_file(temp_file)
                
                # Verify data structure
                assert 'equity_curve' in data
                assert len(data['equity_curve']) == 10
        finally:
            Path(temp_file).unlink()

    def test_load_data_from_directory(self, mock_plotly_and_streamlit):
        """Test loading data from directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_equity = pd.DataFrame({
                'date': pd.date_range("2024-01-01", periods=10, freq="D"),
                'equity': np.cumsum(np.random.randn(10) * 100 + 100000),
            })
            
            test_returns = pd.DataFrame({
                'date': pd.date_range("2024-01-01", periods=10, freq="D"),
                'return': np.random.randn(10) * 0.02,
            })
            
            equity_file = Path(temp_dir) / "equity.csv"
            returns_file = Path(temp_dir) / "returns.csv"
            
            test_equity.to_csv(equity_file, index=False)
            test_returns.to_csv(returns_file, index=False)
            
            with patch.dict('sys.modules', mock_plotly_and_streamlit):
                app = WebDashboardApp(data_dir=temp_dir)
                
                # Load from directory
                data = app.load_data_from_directory()
                
                # Verify data structure
                assert 'equity_curve' in data
                assert len(data['equity_curve']) == 10

    def test_load_data_missing_file(self, mock_plotly_and_streamlit):
        """Test loading data with missing file."""
        with patch.dict('sys.modules', mock_plotly_and_streamlit):
            app = WebDashboardApp()
            
            # Should handle missing file gracefully
            with pytest.raises(FileNotFoundError):
                app.load_data_from_file("nonexistent.json")

    def test_load_data_invalid_format(self, mock_plotly_and_streamlit):
        """Test loading data with invalid format."""
        # Create invalid JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            with patch.dict('sys.modules', mock_plotly_and_streamlit):
                app = WebDashboardApp()
                
                # Should handle invalid JSON gracefully
                with pytest.raises(json.JSONDecodeError):
                    app.load_data_from_file(temp_file)
        finally:
            Path(temp_file).unlink()

    def test_export_data(self, mock_plotly_and_streamlit):
        """Test data export functionality."""
        # Create test data
        test_data = {
            'equity_curve': pd.Series(
                np.cumsum(np.random.randn(10) * 100 + 100000),
                index=pd.date_range("2024-01-01", periods=10, freq="D")
            ),
            'returns': np.random.randn(10) * 0.02,
            'metrics': {'Total Return': 0.15, 'Sharpe Ratio': 1.5},
        }
        
        with patch.dict('sys.modules', mock_plotly_and_streamlit):
            app = WebDashboardApp()
            
            # Export to CSV
            with tempfile.TemporaryDirectory() as temp_dir:
                export_path = Path(temp_dir) / "export.csv"
                app.export_data(test_data, export_path, format='csv')
                
                # Verify file was created
                assert export_path.exists()
                
                # Export to JSON
                json_path = Path(temp_dir) / "export.json"
                app.export_data(test_data, json_path, format='json')
                
                # Verify file was created
                assert json_path.exists()

    def test_error_handling_export(self, mock_plotly_and_streamlit):
        """Test error handling during export."""
        with patch.dict('sys.modules', mock_plotly_and_streamlit):
            app = WebDashboardApp()
            
            # Test invalid format
            with pytest.raises(ValueError, match="Unsupported export format"):
                app.export_data({}, Path("test"), format='invalid')

    def test_data_validation(self, mock_plotly_and_streamlit):
        """Test data validation functionality."""
        with patch.dict('sys.modules', mock_plotly_and_streamlit):
            app = WebDashboardApp()
            
            # Test valid data
            valid_data = {
                'equity_curve': pd.Series([100000, 101000, 102000]),
                'returns': np.array([0.01, 0.01, 0.01]),
                'metrics': {'Total Return': 0.02},
            }
            
            assert app.validate_data(valid_data) is True
            
            # Test missing required fields
            invalid_data = {
                'equity_curve': pd.Series([100000, 101000]),
                # Missing returns and metrics
            }
            
            assert app.validate_data(invalid_data) is False

    def test_configuration_management(self, mock_plotly_and_streamlit):
        """Test configuration management."""
        with patch.dict('sys.modules', mock_plotly_and_streamlit):
            app = WebDashboardApp()
            
            # Test default config
            config = app.get_config()
            assert 'title' in config
            assert 'theme' in config
            
            # Test updating config
            new_config = {'title': 'Custom Title', 'theme': 'dark'}
            app.update_config(new_config)
            
            updated_config = app.get_config()
            assert updated_config['title'] == 'Custom Title'
            assert updated_config['theme'] == 'dark'

    def test_user_preferences(self, mock_plotly_and_streamlit):
        """Test user preferences functionality."""
        with patch.dict('sys.modules', mock_plotly_and_streamlit):
            app = WebDashboardApp()
            
            # Test default preferences
            prefs = app.get_user_preferences()
            assert 'default_page' in prefs
            assert 'chart_height' in prefs
            
            # Test setting preferences
            new_prefs = {'default_page': 'analysis', 'chart_height': 600}
            app.set_user_preferences(new_prefs)
            
            updated_prefs = app.get_user_preferences()
            assert updated_prefs['default_page'] == 'analysis'
            assert updated_prefs['chart_height'] == 600

    def test_error_logging(self, mock_plotly_and_streamlit):
        """Test error logging functionality."""
        with patch.dict('sys.modules', mock_plotly_and_streamlit):
            app = WebDashboardApp()
            
            # Capture logs
            with patch('logging.Logger.error') as mock_error:
                # Simulate error
                try:
                    raise ValueError("Test error")
                except ValueError as e:
                    app.log_error(str(e))
                
                # Verify error was logged
                mock_error.assert_called_with("Dashboard Error: Test error")

    def test_data_refresh(self, mock_plotly_and_streamlit):
        """Test data refresh functionality."""
        with patch.dict('sys.modules', mock_plotly_and_streamlit):
            app = WebDashboardApp()
            
            # Mock data loading
            with patch.object(app, 'load_data') as mock_load:
                mock_load.return_value = {'test': 'data'}
                
                # Refresh data
                app.refresh_data()
                
                # Verify data was reloaded
                mock_load.assert_called_once()

    def test_chart_interactivity(self, mock_plotly_and_streamlit):
        """Test chart interactivity features."""
        with patch.dict('sys.modules', mock_plotly_and_streamlit):
            app = WebDashboardApp()
            
            # Test interactive chart options
            options = {
                'zoom': True,
                'pan': True,
                'select': True,
                'hover': True,
            }
            
            chart_config = app.get_chart_config(options)
            
            assert 'config' in chart_config
            assert chart_config['config']['displayModeBar'] is True
