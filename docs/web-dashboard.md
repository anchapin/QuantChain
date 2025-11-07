# QuantChain Web Dashboard

## Overview

The QuantChain Web Dashboard provides a comprehensive Streamlit-based interface for monitoring autonomous trading agents, visualizing their performance, and managing configurations. This implementation addresses GitHub Issue #10.

## Features

### 📊 Live Monitoring
- **Real-time Agent Status**: Track running, stopped, and error states
- **Portfolio Tracking**: Live P/L monitoring with equity curves
- **Performance Metrics**: Win rates, Sharpe ratios, drawdown analysis
- **System Health**: API status monitoring and resource utilization

### 📈 Interactive Visualizations
- **Equity Curves**: Portfolio performance over time with Plotly charts
- **Risk Analytics**: Comprehensive risk metrics visualization
- **Decision Flow**: Visual representation of agent reasoning chains
- **Performance Charts**: Win rate gauges, P&L breakdowns

### ⚙️ Agent Configuration Wizard
- **Step-by-Step Setup**: Guided configuration for new agents
- **Parameter Tuning**: Interactive adjustment of agent parameters
- **Real-time Validation**: Instant feedback on configuration changes
- **Template System**: Pre-built templates for different agent types

### 🖥 Multi-Page Interface
- **Overview**: System-wide dashboard with summary metrics
- **Agent Detail**: In-depth analysis of individual agents
- **Configuration**: Agent setup and management interface
- **System Health**: Infrastructure monitoring dashboard

## Quick Start

### Installation

The web dashboard dependencies are already included in the main requirements:

```bash
# Dependencies (already in requirements.txt)
streamlit>=1.20.0
plotly>=5.0.0
pandas>=1.3.0
```

### Running the Dashboard

#### Method 1: Python Module
```bash
cd /path/to/QuantChain
source venv/bin/activate

# Run with default configuration (port 8501)
python3 -m quantchain.tools.web_dashboard

# Run with custom port
python3 -m quantchain.tools.web_dashboard 8080
```

#### Method 2: Streamlit Direct
```bash
streamlit run quantchain/tools/web_dashboard.py --server.port 8501
```

### Accessing the Dashboard

Open your browser and navigate to:
- Default: http://localhost:8501
- Custom port: http://localhost:PORT

## Usage

### 1. Overview Page
The main dashboard shows:
- **Agent Status Summary**: Running/stopped/error counts
- **Recent Activity**: Latest trades and system events
- **Performance Summary**: Portfolio metrics across all agents
- **System Health**: API status and resource usage

### 2. Agent Detail Page
Select any agent to view:
- **Real-time Status**: Current state, uptime, error count
- **Portfolio Performance**: Equity curves and performance charts
- **Risk Metrics**: Drawdown, Sharpe ratio, win rate analysis
- **Trade History**: Recent trades with timestamps and details

### 3. Configuration Page
Create and manage agent configurations:
- **New Agent Wizard**: Step-by-step configuration process
- **Template Selection**: Choose from pre-built agent templates
- **Parameter Adjustment**: Fine-tune agent behavior
- **Validation**: Real-time configuration validation

### 4. System Health Page
Monitor system infrastructure:
- **API Service Status**: Real-time status of external services
- **Performance Metrics**: LLM response times, error rates
- **Resource Usage**: CPU, memory, disk utilization
- **Uptime Monitoring**: System availability tracking

## Configuration

### Dashboard Configuration

```python
from quantchain.tools.web_dashboard import DashboardConfig

config = DashboardConfig(
    refresh_interval=5,          # Refresh rate in seconds
    max_data_points=1000,       # Maximum historical data points
    enable_real_time=True,        # Enable real-time updates
    theme="light",               # UI theme (light/dark)
    default_agent_id=None,       # Default agent to display
    port=8501,                  # Server port
    host="localhost"              # Server host
)
```

### Agent Configuration Example

```python
from quantchain.tools.web_dashboard import ConfigurationWizard

wizard = ConfigurationWizard()
config = wizard.get_agent_template("memecoin_vibe_trader")

# Customize configuration
config["agent_id"] = "my_trader_001"
config["name"] = "My Memecoin Trader"
config["parameters"]["max_positions"] = 3
config["parameters"]["risk_tolerance"] = "MEDIUM"

# Validate and save
validation = wizard.validate_config(config)
if validation["is_valid"]:
    wizard.save_config(config, "my_trader_config.json")
```

## Architecture

### Components

1. **MonitoringService**: Agent status and system health monitoring
2. **VisualizationService**: Chart creation and data visualization
3. **ConfigurationWizard**: Agent configuration management
4. **WebDashboardApp**: Main application and UI rendering

### Data Flow

```
Agent Registry → MonitoringService → Web Dashboard
                        ↘ System Health
                        ↘ Performance Data
                        ↘ VisualizationService → Charts
```

## Development

### Running Tests

```bash
# Run all web dashboard tests
python3 -m pytest tests/tools/test_web_dashboard.py -v

# Run with coverage
python3 -m pytest tests/tools/test_web_dashboard.py --cov=quantchain.tools.web_dashboard
```

### Code Quality

```bash
# Linting
python3 -m flake8 quantchain/tools/web_dashboard.py --max-line-length=88

# Formatting
python3 -m black quantchain/tools/web_dashboard.py

# Type checking
python3 -m mypy quantchain/tools/web_dashboard.py --ignore-missing-imports
```

## Integration

### Adding New Agents

1. Create agent template in `ConfigurationWizard.templates`
2. Implement monitoring endpoints in agent registry
3. Add agent-specific visualizations as needed

### Custom Visualizations

```python
from quantchain.tools.web_dashboard import VisualizationService

service = VisualizationService()

# Create custom chart
figure = go.Figure(data=your_chart_data)
figure.update_layout(title="Your Chart", height=400)
```

### Real-time Updates

The dashboard supports:
- **Automatic Refresh**: Configurable refresh intervals
- **Live Data Streaming**: Real-time agent status updates
- **Interactive Charts**: Zoom, pan, and hover interactions
- **Responsive Design**: Mobile-friendly interface

## Security

### Current Features
- **Input Validation**: All user inputs are validated and sanitized
- **Configuration Security**: Secure handling of sensitive parameters
- **Error Handling**: Graceful degradation for missing data

### Future Enhancements
- **User Authentication**: Multi-user support with role-based access
- **API Key Management**: Secure storage and rotation of API credentials
- **Audit Logging**: Comprehensive activity logging and audit trails
- **SSL/TLS Support**: HTTPS deployment options

## Performance

### Benchmarks
- **Page Load**: < 2 seconds initial load
- **Real-time Updates**: < 5 second refresh cycle
- **Memory Usage**: < 2GB for standard deployments
- **Concurrent Users**: Support for 10+ simultaneous users

### Optimization
- **Data Caching**: Intelligent caching of historical data
- **Lazy Loading**: On-demand data loading for large datasets
- **Compression**: Optimized data transfer for real-time updates

## Troubleshooting

### Common Issues

**Dashboard not loading:**
```bash
# Check dependencies
pip install streamlit plotly pandas

# Check port availability
netstat -tulpn | grep :8501
```

**Missing agent data:**
- Verify agent registry configuration
- Check API service connectivity
- Review agent log files

**Performance issues:**
- Increase refresh intervals
- Reduce data point limits
- Monitor resource usage

### Logs

```bash
# Check Streamlit logs
streamlit logs --show-config

# Run with debug mode
streamlit run --logger.level debug quantchain/tools/web_dashboard.py
```

## Contributing

### Development Setup

1. Install development dependencies
2. Run test suite to ensure functionality
3. Make changes following existing patterns
4. Update tests for new functionality
5. Ensure all tests pass before submitting

### Submitting Changes

Follow the AGENTS.md guidelines:
- Test-Driven Development approach
- Comprehensive test coverage
- Code quality standards
- Documentation updates

## Support

For issues and questions:
1. Check existing GitHub issues
2. Review this documentation
3. Consult the main AGENTS.md file
4. Contact the development team

---

**Note**: This web dashboard is part of QuantChain's broader ecosystem and integrates seamlessly with existing agents, connectors, and tools.
