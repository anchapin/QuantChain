# Auto-generated test file for backtestingpy_engine.py
# Generated using OpenAI API

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the parent directory to the path to import the module
sys.path.insert(0, str(Path(__file__).parent.parent))

```python
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from backtestingpy_engine import BacktestingPyEngine, BacktestConfig, ConversionError, BacktestingPyError, StrategyAdapter

# Test data
test_data = pd.DataFrame(
    {
        "open": [100.0, 101.0],
        "high": [101.0, 102.0],
        "low": [99.0, 100.0],
        "close": [100.5, 101.5],
        "volume": [1000.0, 2000.0],
    }
)

# Mock Backtest and Strategy
BacktestMock = MagicMock()
StrategyMock = MagicMock()

# Test BacktestConfig
test_config = BacktestConfig(initial_cash=10000.0, commission_rate=0.002)

# Test BacktestResult
test_result = MagicMock()

# Test BacktestingPyEngine
engine = BacktestingPyEngine(config=test_config)


def test_backtesting_py_engine_init():
    with patch("backtestingpy_engine.Backtest", new=BacktestMock):
        engine = BacktestingPyEngine(config=test_config)
        assert engine.config == test_config
        assert engine._backtest is not None


def test_backtesting_py_engine_run():
    with patch("backtestingpy_engine.Backtest", new=BacktestMock):
        engine = BacktestingPyEngine(config=test_config)
        engine.run(StrategyMock, test_data, config=test_config)
        assert engine._backtest.run.called
        assert engine._results is not None


def test_backtesting_py_engine_get_results():
    engine._results = test_result
    assert engine.get_results() == test_result


def test_backtesting_py_engine_get_equity_curve():
    engine._equity_curve_data = pd.Series([10000, 10100])
    assert engine.get_equity_curve().equals(pd.Series([10000, 10100]))


def test_backtesting_py_engine_convert_data_format():
    converted_data = engine._convert_data_format(test_data)
    assert all(
        col in converted_data.columns for col in ["Open", "High", "Low", "Close", "Volume"]
    )


def test_backtesting_py_engine_convert_data_format_failure():
    with pytest.raises(ConversionError):
        engine._convert_data_format(pd.DataFrame({"foo": [1, 2]}))


def test_backtesting_py_engine_convert_results():
    with patch("backtestingpy_engine.BacktestResult", new=MagicMock()):
        converted_result = engine._convert_results({"Return [%]": 10.0, "Sharpe Ratio": 1.0, "# Trades": 5})
        assert converted_result.metrics.total_return == 0.1
        assert converted_result.metrics.sharpe_ratio == 1.0
        assert converted_result.metrics.total_trades == 5


def test_backtesting_py_engine_run_failure():
    with patch("backtestingpy_engine.Backtest", new=BacktestMock):
        engine = BacktestingPyEngine(config=test_config)
        engine._backtest.run.side_effect = Exception("Test exception")
        with pytest.raises(BacktestingPyError):
            engine.run(StrategyMock, test_data, config=test_config)


def test_strategy_adapter_init():
    strategy = StrategyAdapter()
    strategy.init()
    assert strategy.position_size == 0.1


def test_strategy_adapter_next():
    strategy = StrategyAdapter()
    strategy.next()  # No assertion, just checking for exceptions
```
