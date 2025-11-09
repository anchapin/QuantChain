"""
Tests for market friction simulation components.
"""

import pytest
from datetime import datetime
import pandas as pd

# Import classes that will be implemented
from quantchain.backtesting.market_friction import (
    MarketFrictionSimulator,
    FlatCommission,
    PercentageCommission,
    TieredCommission,
    FixedSlippage,
    VolumeImpactSlippage,
    BidAskSpreadSlippage,
    FixedLatency,
    UniformRandomLatency,
    NormalRandomLatency,
    MarketFrictionConfig,
    InvalidParameter,
    FrictionCalculationError,
)


class TestCommissionModels:
    """Test commission models."""

    def test_flat_commission_calculation(self) -> None: """Test flat commission calculation."""
        commission = FlatCommission(
            fee_per_trade=1.0, fee_per_contract=0.1, min_fee=0.5
        )

        # Test basic calculation
        result = commission.calculate(1000.0, "buy")
        assert result == 101.0  # 1.0 + (0.1 * 1000.0)

        # Test minimum fee - very small trade
        commission_small = FlatCommission(
            fee_per_trade=0.1, fee_per_contract=0.01, min_fee=0.5
        )
        result = commission_small.calculate(1.0, "sell")
        assert result == 0.5  # min_fee applies since 0.1 + 0.01 = 0.11 < 0.5

        # Test zero fee
        commission_zero = FlatCommission(fee_per_trade=0.0, fee_per_contract=0.0)
        result = commission_zero.calculate(1000.0, "buy")
        assert result == 0.0

    def test_percentage_commission_calculation(self) -> None: """Test percentage commission calculation."""
        commission = PercentageCommission(rate=0.001, min_fee=1.0, max_fee=10.0)

        # Test normal calculation
        result = commission.calculate(1000.0, "buy")
        assert result == 1.0  # 1000 * 0.001

        # Test minimum fee
        result = commission.calculate(500.0, "sell")
        assert result == 1.0  # min_fee applies

        # Test maximum fee
        result = commission.calculate(20000.0, "buy")
        assert result == 10.0  # max_fee applies

        # Test no limits
        commission_no_limits = PercentageCommission(rate=0.001)
        result = commission_no_limits.calculate(20000.0, "buy")
        assert result == 20.0

    def test_tiered_commission_calculation(self) -> None: """Test tiered commission calculation."""
        commission = TieredCommission()

        # Test default tiers
        result = commission.calculate(1000.0, "buy", monthly_volume=50)
        assert result == 1000.0 * 0.003  # base rate for <100 trades

        result = commission.calculate(1000.0, "sell", monthly_volume=500)
        assert result == 1000.0 * 0.002  # 0.2% for >100 trades

        result = commission.calculate(1000.0, "buy", monthly_volume=5000)
        assert result == 1000.0 * 0.001  # 0.1% for >1000 trades

        result = commission.calculate(1000.0, "sell", monthly_volume=50000)
        assert result == 1000.0 * 0.0005  # 0.05% for >10000 trades


class TestSlippageModels:
    """Test slippage models."""

    def test_fixed_slippage(self) -> None: """Test fixed slippage model."""
        slippage = FixedSlippage(rate=0.0001)

        # Test buy order (price goes up)
        price = 100.0
        result = slippage.apply(price, 100, "buy")
        assert result == 99.99  # price - slippage for buy

        # Test sell order (price goes down)
        result = slippage.apply(price, 100, "sell")
        assert result == 100.01  # price + slippage for sell

        # Test zero slippage
        slippage_zero = FixedSlippage(rate=0.0)
        result = slippage_zero.apply(price, 100, "buy")
        assert result == price

    def test_volume_impact_slippage(self) -> None: """Test volume impact slippage model."""
        slippage = VolumeImpactSlippage(
            base_rate=0.0001, volume_impact_factor=0.001, avg_daily_volume=1000000
        )

        price = 100.0
        quantity = 10000  # 1% of daily volume

        # Test volume impact calculation
        expected_impact = 0.001 * (10000 / 1000000) ** 0.5
        expected_total = price * (0.0001 + expected_impact)

        result = slippage.apply(price, quantity, "buy")
        expected_price = price - expected_total
        assert abs(result - expected_price) < 0.0001

    def test_bid_ask_spread_slippage(self) -> None: """Test bid-ask spread slippage model."""
        slippage = BidAskSpreadSlippage(base_spread_rate=0.0005, volatility_factor=0.1)

        price = 100.0

        # Test without market depth
        result = slippage.apply(price, 100, "buy")
        expected_spread = price * 0.0005
        expected_price = price - expected_spread / 2
        assert abs(result - expected_price) < 0.0001

        # Test with market depth
        market_depth = {"volatility": 0.2}
        result = slippage.apply(price, 100, "sell", market_depth)
        expected_spread = price * 0.0005 * (1 + 0.1 * 0.2)
        expected_price = price + expected_spread / 2
        assert abs(result - expected_price) < 0.0001


class TestLatencyModels:
    """Test latency models."""

    def test_fixed_latency(self) -> None: """Test fixed latency model."""
        latency = FixedLatency(latency_ms=10.0)
        timestamp = datetime(2023, 1, 1, 12, 0, 0)

        result = latency.apply(timestamp)
        expected = timestamp + pd.Timedelta(milliseconds=10.0)
        assert result == expected

    def test_uniform_random_latency(self) -> None: """Test uniform random latency model."""
        latency = UniformRandomLatency(min_ms=5.0, max_ms=50.0)
        timestamp = datetime(2023, 1, 1, 12, 0, 0)

        result = latency.apply(timestamp)

        # Should be between min and max
        min_expected = timestamp + pd.Timedelta(milliseconds=5.0)
        max_expected = timestamp + pd.Timedelta(milliseconds=50.0)
        assert min_expected <= result <= max_expected

    def test_normal_random_latency(self) -> None: """Test normal random latency model."""
        latency = NormalRandomLatency(
            mean_ms=20.0, std_ms=5.0, min_ms=1.0, max_ms=100.0
        )
        timestamp = datetime(2023, 1, 1, 12, 0, 0)

        result = latency.apply(timestamp)

        # Should be between min and max
        min_expected = timestamp + pd.Timedelta(milliseconds=1.0)
        max_expected = timestamp + pd.Timedelta(milliseconds=100.0)
        assert min_expected <= result <= max_expected


class TestMarketFrictionConfig:
    """Test market friction configuration."""

    def test_basic_config(self) -> None: """Test basic configuration setup."""
        commission = FlatCommission(fee_per_trade=1.0)
        slippage = FixedSlippage(rate=0.0001)
        latency = FixedLatency(latency_ms=10.0)

        config = MarketFrictionConfig(
            commission_model=commission, slippage_model=slippage, latency_model=latency
        )

        assert config.commission_model == commission
        assert config.slippage_model == slippage
        assert config.latency_model == latency
        assert config.asset_specific == {}

    def test_asset_specific_config(self) -> None: """Test asset-specific configuration."""
        commission = FlatCommission(fee_per_trade=1.0)
        slippage = FixedSlippage(rate=0.0001)
        latency = FixedLatency(latency_ms=10.0)

        asset_config = {
            "AAPL": {
                "commission": PercentageCommission(rate=0.0005),
                "slippage": VolumeImpactSlippage(),
                "latency": FixedLatency(latency_ms=5.0),
            }
        }

        config = MarketFrictionConfig(
            commission_model=commission,
            slippage_model=slippage,
            latency_model=latency,
            asset_specific=asset_config,
        )

        # Test getting asset config
        aapl_config = config.get_asset_config("AAPL")
        assert "commission" in aapl_config
        assert "slippage" in aapl_config
        assert "latency" in aapl_config

        # Test default for non-existent asset
        default_config = config.get_asset_config("UNKNOWN")
        assert default_config == {}


class TestMarketFrictionSimulator:
    """Test main market friction simulator."""

    def test_initialization(self) -> None: """Test simulator initialization."""
        commission = FlatCommission(fee_per_trade=1.0)
        slippage = FixedSlippage(rate=0.0001)
        latency = FixedLatency(latency_ms=10.0)

        config = MarketFrictionConfig(
            commission_model=commission, slippage_model=slippage, latency_model=latency
        )

        simulator = MarketFrictionSimulator(config)
        assert simulator.config == config

    def test_commission_application(self) -> None: """Test commission application."""
        commission = PercentageCommission(rate=0.001)
        slippage = FixedSlippage(rate=0.0001)
        latency = FixedLatency(latency_ms=10.0)

        config = MarketFrictionConfig(
            commission_model=commission, slippage_model=slippage, latency_model=latency
        )

        simulator = MarketFrictionSimulator(config)

        # Test commission calculation
        result = simulator.apply_commission(1000.0, "buy", "AAPL")
        assert result == 1.0  # 1000 * 0.001

    def test_slippage_application(self) -> None: """Test slippage application."""
        commission = FlatCommission(fee_per_trade=1.0)
        slippage = FixedSlippage(rate=0.0001)
        latency = FixedLatency(latency_ms=10.0)

        config = MarketFrictionConfig(
            commission_model=commission, slippage_model=slippage, latency_model=latency
        )

        simulator = MarketFrictionSimulator(config)

        # Test slippage application
        result = simulator.apply_slippage(100.0, 100, "buy")
        assert result == 99.99  # price - slippage

    def test_latency_application(self) -> None: """Test latency application."""
        commission = FlatCommission(fee_per_trade=1.0)
        slippage = FixedSlippage(rate=0.0001)
        latency = FixedLatency(latency_ms=10.0)

        config = MarketFrictionConfig(
            commission_model=commission, slippage_model=slippage, latency_model=latency
        )

        simulator = MarketFrictionSimulator(config)

        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        result = simulator.apply_latency(timestamp)

        expected = timestamp + pd.Timedelta(milliseconds=10.0)
        assert result == expected

    def test_total_cost_calculation(self) -> None: """Test total cost calculation."""
        commission = PercentageCommission(rate=0.001)
        slippage = FixedSlippage(rate=0.0001)
        latency = FixedLatency(latency_ms=10.0)

        config = MarketFrictionConfig(
            commission_model=commission, slippage_model=slippage, latency_model=latency
        )

        simulator = MarketFrictionSimulator(config)

        result = simulator.get_total_cost(100.0, 100, "buy")

        # Should include commission and slippage cost
        expected_commission = 100.0 * 100 * 0.001  # 10.0
        expected_slippage = 100.0 * 0.0001 * 100  # 1.0

        assert "commission" in result
        assert "slippage" in result
        assert "total" in result
        assert abs(result["commission"] - expected_commission) < 0.01
        assert abs(result["slippage"] - expected_slippage) < 0.01

    def test_asset_specific_override(self) -> None: """Test asset-specific configuration override."""
        commission = FlatCommission(fee_per_trade=1.0)
        slippage = FixedSlippage(rate=0.0001)
        latency = FixedLatency(latency_ms=10.0)

        asset_config = {
            "AAPL": {
                "commission": PercentageCommission(rate=0.0005),
                "slippage": FixedSlippage(rate=0.0002),
                "latency": FixedLatency(latency_ms=5.0),
            }
        }

        config = MarketFrictionConfig(
            commission_model=commission,
            slippage_model=slippage,
            latency_model=latency,
            asset_specific=asset_config,
        )

        simulator = MarketFrictionSimulator(config)

        # Test with AAPL (should use asset-specific config)
        result = simulator.apply_commission(1000.0, "buy", "AAPL")
        assert result == 0.5  # 1000 * 0.0005

        result = simulator.apply_slippage(100.0, 100, "buy", symbol="AAPL")
        assert result == 99.98  # 100 - 0.02

        # Test with non-existent asset (should use default config)
        result = simulator.apply_commission(1000.0, "buy", "GOOGL")
        assert result == 1.0  # default flat fee


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_commission_parameters(self) -> None: """Test invalid commission parameters."""
        with pytest.raises(InvalidParameter):
            commission = PercentageCommission(rate=-0.1)  # Negative rate
            commission.calculate(1000.0, "buy")

    def test_invalid_slippage_parameters(self) -> None: """Test invalid slippage parameters."""
        with pytest.raises(InvalidParameter):
            slippage = FixedSlippage(rate=-0.1)  # Negative rate
            slippage.apply(100.0, 100, "buy")

    def test_invalid_latency_parameters(self) -> None: """Test invalid latency parameters."""
        with pytest.raises(InvalidParameter):
            latency = FixedLatency(latency_ms=-10.0)  # Negative latency
            latency.apply(datetime.now())

    def test_friction_calculation_errors(self) -> None: """Test friction calculation errors."""
        # Test with invalid trade parameters
        commission = FlatCommission(fee_per_trade=1.0)
        slippage = FixedSlippage(rate=0.0001)
        latency = FixedLatency(latency_ms=10.0)

        config = MarketFrictionConfig(
            commission_model=commission, slippage_model=slippage, latency_model=latency
        )

        simulator = MarketFrictionSimulator(config)

        # Test with negative quantity
        with pytest.raises(FrictionCalculationError):
            simulator.apply_slippage(100.0, -100, "buy")


if __name__ == "__main__":
    pytest.main([__file__])


