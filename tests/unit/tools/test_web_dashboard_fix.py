"""
Fixed web dashboard tests that handle missing optional dependencies gracefully.
"""

import pytest
import sys
from unittest.mock import Mock, patch

# Optional imports with graceful fallback
try:
    import plotly
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    plotly = Mock()

try:
    import streamlit
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False
    streamlit = Mock()

# Mock modules if not available
if not HAS_PLOTLY:
    sys.modules['plotly'] = plotly
    sys.modules['plotly.graph_objects'] = Mock()
    sys.modules['plotly.express'] = Mock()

if not HAS_STREAMLIT:
    sys.modules['streamlit'] = streamlit
    sys.modules['streamlit.components'] = Mock()


class TestWebDashboardFixed:
    """Test web dashboard functionality with optional dependencies."""
    
    @pytest.mark.skipif(not HAS_PLOTLY, reason="plotly not available")
    def test_plotly_charts_creation(self):
        """Test that plotly charts can be created."""
        from quantchain.tools.web_dashboard import DashboardCharts
        
        charts = DashboardCharts()
        
        # Test line chart
        fig = charts.create_line_chart([1, 2, 3], [1, 4, 2])
        assert fig is not None
        
    @pytest.mark.skipif(not HAS_STREAMLIT, reason="streamlit not available") 
    def test_streamlit_app_initialization(self):
        """Test that streamlit app can be initialized."""
        from quantchain.tools.web_dashboard import WebDashboardApp
        
        app = WebDashboardApp()
        assert app is not None
        
    def test_missing_dependencies_graceful_fallback(self):
        """Test graceful handling of missing dependencies."""
        # This should work even if dependencies are missing
        from quantchain.tools.web_dashboard import create_dashboard
        
        # Should not raise an error
        dashboard = create_dashboard(include_plots=False)
        assert dashboard is not None
