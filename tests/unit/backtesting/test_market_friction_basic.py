"""Basic tests for market friction to boost coverage."""

from datetime import datetime

import pytest

from quantchain.backtesting.market_friction import (
    FixedLatency,
    FixedSlippage,
    FlatCommission,
    InvalidParameter,
    MarketFrictionConfig,
    MarketFrictionSimulator,
    PercentageCommission,
)


@pytest.mark.unit


class TestMarketFrictionBasic:
    """Basic tests for market friction components."""



def test_flat_commission_creation(self):
        """Test flat commission model creation."""
        commission = FlatCommission(fee_per_trade=2.5)
        assert commission.model_type == "flat"
        assert commission.fee_per_trade == 2.5



def test_percentage_commission_creation(self):
        """Test percentage commission model creation."""
        commission = PercentageCommission(rate=0.001, min_fee=1.0, max_fee=10.0)
        assert commission.model_type == "percentage"
        assert commission.rate == 0.001
        assert commission.min_fee == 1.0
        assert commission.max_fee == 10.0



def test_fixed_slippage_creation(self):
        """Test fixed slippage model creation."""
        slippage = FixedSlippage(rate=0.0002)
        assert slippage.model_type == "fixed"
        assert slippage.rate == 0.0002



def test_fixed_latency_creation(self):
        """Test fixed latency model creation."""
        latency = FixedLatency(latency_ms=50)
        assert latency.model_type == "fixed"
        assert latency.latency_ms == 50



def test_market_friction_config_creation(self):
        """Test market friction configuration creation."""
        commission = FlatCommission(fee_per_trade=1.0)
        slippage = FixedSlippage(rate=0.001)
        latency = FixedLatency(latency_ms=100)

        config = MarketFrictionConfig(
            commission_model=commission, slippage_model=slippage, latency_model=latency
        )

        assert config.commission_model == commission
        assert config.slippage_model == slippage
        assert config.latency_model == latency
        assert config.asset_specific == {}



def test_market_friction_simulator_creation(self):
        """Test market friction simulator creation."""
        commission = FlatCommission(fee_per_trade=1.0)
        slippage = FixedSlippage(rate=0.001)
        latency = FixedLatency(latency_ms=100)

        config = MarketFrictionConfig(
            commission_model=commission, slippage_model=slippage, latency_model=latency
        )

        simulator = MarketFrictionSimulator(config)
        assert simulator.config == config



def test_flat_commission_calculate(self):
        """Test flat commission calculation."""
        commission = FlatCommission(fee_per_trade=5.0)
        fee = commission.calculate(trade_value=1000, side="buy")
        assert fee == 5.0



def test_percentage_commission_calculate(self):
        """Test percentage commission calculation."""
        commission = PercentageCommission(rate=0.001, min_fee=1.0, max_fee=10.0)
        # Should be 1% of 1000 = 10
        fee = commission.calculate(trade_value=10000, side="sell")
        assert fee == 10.0

        # Should hit min fee
        fee = commission.calculate(trade_value=500, side="buy")
        assert fee == 1.0



def test_fixed_slippage_apply(self):
        """Test fixed slippage application."""
        slippage = FixedSlippage(rate=0.001)
        # Buy: price - slippage
        price = slippage.apply(price=100, quantity=100, side="buy")
        assert price == 99.9  # 100 - (100 * 0.001)

        # Sell: price + slippage
        price = slippage.apply(price=100, quantity=100, side="sell")
        assert price == 100.1  # 100 + (100 * 0.001)



def test_fixed_latency_apply(self):
        """Test fixed latency application."""
        latency = FixedLatency(latency_ms=50)
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        delayed = latency.apply(timestamp)
        assert delayed > timestamp



def test_commission_validation_errors(self):
        """Test commission parameter validation."""
        with pytest.raises(InvalidParameter):
            FlatCommission(fee_per_trade=-1.0)

        with pytest.raises(InvalidParameter):
            PercentageCommission(rate=-0.001)



def test_slippage_validation_errors(self):
        """Test slippage parameter validation."""
        with pytest.raises(InvalidParameter):
            FixedSlippage(rate=-0.001)



def test_latency_validation_errors(self):
        """Test latency parameter validation."""
        with pytest.raises(InvalidParameter):
            FixedLatency(latency_ms=-10)
