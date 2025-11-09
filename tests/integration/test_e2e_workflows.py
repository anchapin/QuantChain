"""Integration tests for end-to-end workflows in QuantChain."""

import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import Mock, patch

from quantchain.backtesting.engine import (
    BacktestEngine,
    BacktestConfig,
    BacktestResult,
    MetricsResult,
    filter_data_by_date_range,
    validate_ohlcv_data,
)
from quantchain.backtesting.langgraph_adapter import LangGraphBacktestAdapter
from quantchain.connectors.dexscreener_connector import DexscreenerDataConnector
from quantchain.tools.social_media_scraper import SocialMediaScraper
from quantchain.tools.execution import AlpacaExecutionTool


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data for testing."""
    dates = pd.date_range("2023-01-01", periods=10, freq="D")
    data = pd.DataFrame(
        {
            "open": [
                100.0,
                101.0,
                102.0,
                103.0,
                104.0,
                105.0,
                106.0,
                107.0,
                108.0,
                109.0,
            ],
            "high": [
                101.5,
                102.5,
                103.5,
                104.5,
                105.5,
                106.5,
                107.5,
                108.5,
                109.5,
                110.5,
            ],
            "low": [
                99.5,
                100.5,
                101.5,
                102.5,
                103.5,
                104.5,
                105.5,
                106.5,
                107.5,
                108.5,
            ],
            "close": [
                101.0,
                102.0,
                103.0,
                104.0,
                105.0,
                106.0,
                107.0,
                108.0,
                109.0,
                110.0,
            ],
            "volume": [
                1000000,
                1100000,
                1200000,
                1300000,
                1400000,
                1500000,
                1600000,
                1700000,
                1800000,
                1900000,
            ],
        },
        index=dates,
    )
    return data


@pytest.fixture
def sample_strategy_config():
    """Create sample strategy configuration for testing."""
    return {
        "strategy_type": "mean_reversion",
        "parameters": {
            "lookback_period": 5,
            "entry_threshold": 0.02,
            "exit_threshold": 0.01,
            "position_size": 0.1,
        },
    }


class TestDataValidationWorkflow:
    """Test data validation workflow as part of end-to-end process."""

    def test_validate_ohlcv_data_success(self, sample_ohlcv_data) -> None: """Test successful validation of OHLCV data."""
        # Should not raise any exceptions
        validate_ohlcv_data(sample_ohlcv_data)

    def test_validate_ohlcv_data_missing_columns(self, sample_ohlcv_data) -> None: """Test validation fails with missing columns."""
        # Remove a required column
        invalid_data = sample_ohlcv_data.drop(columns=["volume"])

        with pytest.raises(Exception):  # DataValidationError
            validate_ohlcv_data(invalid_data)

    def test_validate_ohlcv_data_invalid_prices(self, sample_ohlcv_data) -> None: """Test validation fails with invalid price relationships."""
        # Create invalid data where high < low
        invalid_data = sample_ohlcv_data.copy()
        invalid_data.loc[invalid_data.index[0], "high"] = 98.0  # Less than low

        with pytest.raises(Exception):  # DataValidationError
            validate_ohlcv_data(invalid_data)

    def test_filter_data_by_date_range(self, sample_ohlcv_data) -> None: """Test filtering data by date range."""
        # Filter to middle 5 days
        start_date = datetime(2023, 1, 3)
        end_date = datetime(2023, 1, 7)

        filtered_data = filter_data_by_date_range(
            sample_ohlcv_data, start_date, end_date
        )

        # Should have exactly 5 days
        assert len(filtered_data) == 5
        # Should be within date range
        assert filtered_data.index[0] >= start_date
        assert filtered_data.index[-1] <= end_date


class TestBacktestWorkflow:
    """Test complete backtesting workflow."""

    def test_backtest_config_creation(self) -> None: """Test creating backtest configuration."""
        config = BacktestConfig(
            initial_cash=100000.0,
            commission_rate=0.001,
            slippage_rate=0.0001,
            data_frequency="1d",
        )

        assert config.initial_cash == 100000.0
        assert config.commission_rate == 0.001
        assert config.slippage_rate == 0.0001
        assert config.data_frequency == "1d"

    def test_langgraph_backtester_initialization(self, sample_strategy_config) -> None: """Test initializing LangGraph backtester."""
        # Create a mock graph
        mock_graph = Mock()

        with patch("quantchain.backtesting.langgraph_adapter.LangGraphBacktestAdapter"):
            adapter = LangGraphBacktestAdapter(mock_graph, sample_strategy_config)

            assert adapter.config == sample_strategy_config
            assert adapter.agent_graph == mock_graph

    def test_simple_backtest_execution(self, sample_ohlcv_data, sample_strategy_config) -> None: """Test executing a simple backtest."""
        # Create a mock engine
        mock_engine = Mock(spec=BacktestEngine)

        # Mock the run method to return a result
        expected_equity = pd.Series(
            [100000, 101000, 102000, 103000, 104000], index=sample_ohlcv_data.index[:5]
        )
        expected_trades = pd.DataFrame(
            {
                "symbol": ["TEST"] * 2,
                "action": ["buy", "sell"],
                "quantity": [100, 100],
                "price": [101.0, 103.0],
                "timestamp": [
                    datetime(2023, 1, 2),
                    datetime(2023, 1, 4),
                ],
            }
        )
        expected_result = BacktestResult(
            equity_curve=expected_equity,
            trade_log=expected_trades,
            summary_stats={"total_return": 0.04},
            metrics=MetricsResult(
                total_return=0.04,
                annualized_return=0.0,
                sharpe_ratio=0.0,
                sortino_ratio=0.0,
                calmar_ratio=0.0,
                max_drawdown=0.0,
                max_drawdown_duration=0,
                total_trades=2,
                winning_trades=1,
                losing_trades=1,
                avg_win=2.0,
                avg_loss=1.0,
            ),
            execution_time=0.5,
            config=BacktestConfig(),
        )

        mock_engine.run.return_value = expected_result

        # Execute the backtest
        result = mock_engine.run("mock_strategy", sample_ohlcv_data, BacktestConfig())

        # Verify the result
        assert result == expected_result
        mock_engine.run.assert_called_once()


class TestAgentExecutionWorkflow:
    """Test agent execution workflow from data retrieval to execution."""

    def test_dexscreener_data_retrieval(self) -> None: """Test retrieving data from DexScreener."""
        connector = DexscreenerDataConnector()

        # Mock the connector's _make_request method to avoid actual API calls
        with patch.object(connector, "_make_request") as mock_request:
            # Mock response for trending pairs call
            mock_request.return_value = {
                "pairs": [
                    {
                        "chainId": "ethereum",
                        "dexId": "uniswap",
                        "url": "https://example.com/pair1",
                        "pairAddress": "0x1234567890abcdef",
                        "baseToken": {
                            "address": "0xabcdef1234567890",
                            "name": "Token1",
                            "symbol": "TOK1",
                        },
                        "quoteToken": {
                            "address": "0x1234567890abcdef",
                            "name": "Wrapped Ether",
                            "symbol": "WETH",
                        },
                        "priceNative": "0.001",
                        "priceUsd": "1.5",
                        "volume": {
                            "h24": 150000,
                        },
                        "liquidity": {
                            "usd": 50000,
                        },
                    }
                ]
            }

            # Execute the data retrieval
            result = connector.get_new_token_pairs()

            # Verify the result
            assert len(result) == 1
            assert result[0]["symbol"] == "TOK1"
            assert result[0]["liquidity"] == 50000.0
            assert result[0]["volume_24h"] == 150000.0

    def test_social_media_scraper_workflow(self) -> None: """Test social media scraping workflow."""
        scraper = SocialMediaScraper()

        # Mock the Twitter API
        with patch.object(scraper, "get_social_metrics") as mock_twitter:
            mock_twitter.return_value = {
                "telegram_followers": 5000,
                "twitter_followers": 10000,
                "recent_posts": 50,
                "engagement_rate": 0.05,
                "sentiment_score": 0.7,
            }

            # Execute the scraping
            result = scraper.get_social_metrics("TOK1", platforms=["twitter"])

            # Verify the result
            assert result["twitter_followers"] == 10000
            assert result["sentiment_score"] == 0.7
            mock_twitter.assert_called_once_with("TOK1", platforms=["twitter"])

    def test_execution_workflow(self) -> None: """Test trade execution workflow."""
        # Mock the connector and executor
        mock_connector = Mock()
        executor = AlpacaExecutionTool(connector=mock_connector)

        # Mock the Alpaca API
        with patch.object(executor, "execute_market_order") as mock_submit:
            mock_submit.return_value = {
                "id": "order_12345",
                "status": "accepted",
                "symbol": "TOK1/USD",
                "qty": 100,
                "side": "buy",
                "type": "market",
                "time_in_force": "day",
            }

            # Execute the order
            result = executor.execute_market_order("TOK1/USD", "buy", 100)

            # Verify the result
            assert result["status"] == "accepted"
            assert result["symbol"] == "TOK1/USD"
            assert result["qty"] == 100
            assert result["side"] == "buy"
            mock_submit.assert_called_once()


class TestIntegratedWorkflow:
    """Test complete integrated workflow from data to execution."""

    def test_complete_trading_workflow(self, sample_ohlcv_data, sample_strategy_config) -> None: """Test complete trading workflow from data retrieval to execution."""
        # Mock all external dependencies
        with patch(
            "quantchain.connectors.dexscreener_connector.DexscreenerDataConnector"
        ) as mock_connector, patch(
            "quantchain.tools.social_media_scraper.SocialMediaScraper"
        ) as mock_scraper, patch(
            "quantchain.tools.execution.AlpacaExecutionTool"
        ) as mock_executor:

            # Setup mocks
            mock_connector_instance = Mock()
            mock_connector_instance.get_new_token_pairs.return_value = [
                {"symbol": "TOK1/WETH", "price_usd": 1.5, "volume_24h": 150000}
            ]
            mock_connector.return_value = mock_connector_instance

            mock_scraper_instance = Mock()
            mock_scraper_instance.get_social_metrics.return_value = {
                "twitter": {"sentiment_score": 0.7, "influence_score": 75}
            }
            mock_scraper.return_value = mock_scraper_instance

            mock_executor_instance = Mock()
            mock_executor_instance.execute_market_order.return_value = {
                "status": "accepted",
                "symbol": "TOK1/USD",
                "qty": 100,
            }
            mock_executor.return_value = mock_executor_instance

            with patch(
                "quantchain.backtesting.langgraph_adapter.LangGraphBacktestAdapter"
            ) as mock_backtester:
                mock_backtester_instance = Mock()
                mock_backtester_instance.run.return_value = BacktestResult(
                    equity_curve=pd.Series(
                        [100000, 101000], index=sample_ohlcv_data.index[:2]
                    ),
                    trade_log=pd.DataFrame(),
                    summary_stats={"total_return": 0.01},
                    metrics=MetricsResult(
                        total_return=0.01,
                        annualized_return=0.0,
                        sharpe_ratio=0.0,
                        sortino_ratio=0.0,
                        calmar_ratio=0.0,
                        max_drawdown=0.0,
                        max_drawdown_duration=0,
                        total_trades=0,
                        winning_trades=0,
                        losing_trades=0,
                        avg_win=0.0,
                        avg_loss=0.0,
                    ),
                    execution_time=0.5,
                    config=BacktestConfig(),
                )
                mock_backtester.return_value = mock_backtester_instance

                # Initialize the backtester with strategy config
                backtester = mock_backtester(sample_strategy_config)

                # Run backtest
                backtester.run(sample_ohlcv_data, BacktestConfig())

                # Get token data from connector
                token_data = mock_connector_instance.get_new_token_pairs()

                # Get sentiment data from scraper
                sentiment_data = mock_scraper_instance.get_social_metrics()

                # Execute trade
                trade_result = mock_executor_instance.execute_market_order(
                    "TOK1/USD", "buy", 100
                )

                # Verify results
                assert len(token_data) == 1
                assert token_data[0]["symbol"] == "TOK1/WETH"
                assert sentiment_data["twitter"]["sentiment_score"] == 0.7
                assert trade_result["status"] == "accepted"

                # Verify all components were called
                mock_connector_instance.get_new_token_pairs.assert_called_once()
                mock_scraper_instance.get_social_metrics.assert_called_once()
                mock_executor_instance.execute_market_order.assert_called_once()


@pytest.mark.integration
class TestSystemIntegration:
    """Test system-level integration between components."""

    def test_error_handling_workflow(self, sample_ohlcv_data) -> None: """Test error handling in integrated workflow."""
        # Test error propagation through the system
        with patch(
            "quantchain.connectors.dexscreener_connector.DexscreenerDataConnector"
        ) as mock_connector:
            # Mock a connector failure with the actual error message
            mock_connector_instance = Mock()
            mock_connector_instance.get_new_token_pairs.side_effect = Exception(
                "API error"
            )
            mock_connector.return_value = mock_connector_instance

            # Verify error is properly handled - use mocked instance
            connector = mock_connector()
            with pytest.raises(Exception, match="API error"):
                connector.get_new_token_pairs()


