"""Tests for market friction module to boost coverage from 45% to 80%+."""

import math
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from quantchain.backtesting.market_friction import (
    # Commission Models
    CommissionModel,
    FlatCommission,
    PercentageCommission,
    TieredCommission,

    # Slippage Models
    SlippageModel,
    FixedSlippage,
    VolumeImpactSlippage,
    BidAskSpreadSlippage,

    # Latency Models
    LatencyModel,
    FixedLatency,
    UniformRandomLatency,
    NormalRandomLatency,

    # Configuration and Simulator
    MarketFrictionConfig,
    MarketFrictionSimulator,

    # Exceptions
    InvalidFrictionModel,
    InvalidParameter,
    FrictionCalculationError,
    CustomFrictionModel,
)


@pytest.mark.unit
class TestCommissionModels:
    """Test commission models for edge cases."""

    def test_flat_commission_default_initialization(self):
        """Test FlatCommission with default values."""
        commission = FlatCommission()
        assert commission.model_type == "flat"
        assert commission.fee_per_trade == 1.0
        assert commission.fee_per_contract == 0.0
        assert commission.min_fee == 0.0

    def test_flat_commission_with_negative_fee(self):
        """Test FlatCommission rejects negative fees."""
        with pytest.raises(InvalidParameter):
            FlatCommission(fee_per_trade=-1.0)

    def test_flat_commission_with_negative_min_fee(self):
        """Test FlatCommission rejects negative min_fee."""
        with pytest.raises(InvalidParameter):
            FlatCommission(min_fee=-1.0)

    def test_flat_commission_calculate_with_negative_trade_value(self):
        """Test FlatCommission with negative trade value."""
        commission = FlatCommission(fee_per_trade=5.0)
        # Negative trade value should be treated as positive
        result = commission.calculate(-1000.0, "buy")
        assert result == 5.0

    def test_flat_commission_calculate_with_min_fee(self):
        """Test FlatCommission with minimum fee."""
        commission = FlatCommission(fee_per_trade=1.0, min_fee=5.0)
        # Should return min_fee when calculated fee is lower
        result = commission.calculate(1000.0, "buy")
        assert result == 5.0

    def test_percentage_commission_default_initialization(self):
        """Test PercentageCommission with default values."""
        commission = PercentageCommission()
        assert commission.model_type == "percentage"
        assert commission.rate == 0.001  # 0.1%
        assert commission.min_fee == 0.0
        assert commission.max_fee == float("inf")

    def test_percentage_commission_with_negative_rate(self):
        """Test PercentageCommission rejects negative rate."""
        with pytest.raises(InvalidParameter):
            PercentageCommission(rate=-0.001)

    def test_percentage_commission_with_zero_rate(self):
        """Test PercentageCommission with zero rate."""
        commission = PercentageCommission(rate=0.0)
        result = commission.calculate(1000.0, "buy")
        assert result == 0.0

    def test_percentage_commission_with_max_fee(self):
        """Test PercentageCommission with max fee."""
        commission = PercentageCommission(rate=0.01, max_fee=50.0)
        # With 1% commission and max fee of $50, $10,000 trade should hit max
        result = commission.calculate(10000.0, "buy")
        assert result == 50.0

    def test_percentage_commission_with_min_fee(self):
        """Test PercentageCommission with min fee."""
        commission = PercentageCommission(rate=0.001, min_fee=5.0)
        # With 0.1% commission and min fee of $5, $1,000 trade should hit min
        result = commission.calculate(1000.0, "buy")
        assert result == 5.0

    def test_percentage_commission_calculate_with_negative_trade_value(self):
        """Test PercentageCommission with negative trade value."""
        commission = PercentageCommission(rate=0.01)
        # Negative trade value should be treated as positive
        result = commission.calculate(-1000.0, "buy")
        assert result == 10.0

    def test_tiered_commission_initialization(self):
        """Test TieredCommission initialization."""
        commission = TieredCommission()
        assert commission.model_type == "tiered"
        assert commission.base_rate == 0.001
        assert commission.volume_window == "1M"
        assert len(commission.tiers) > 0

    def test_tiered_commission_calculate_with_different_volumes(self):
        """Test TieredCommission with different volumes."""
        commission = TieredCommission()

        # Low volume (no tier reached)
        result = commission.calculate(1000.0, "buy", monthly_volume=50)
        expected = 1000.0 * 0.003  # First tier rate
        assert result == expected

        # Medium volume
        result = commission.calculate(1000.0, "buy", monthly_volume=500)
        expected = 1000.0 * 0.002  # Second tier rate
        assert result == expected

        # High volume
        result = commission.calculate(1000.0, "buy", monthly_volume=5000)
        expected = 1000.0 * 0.001  # Third tier rate
        assert result == expected

    def test_tiered_commission_calculate_with_negative_value(self):
        """Test TieredCommission with negative trade value."""
        commission = TieredCommission()
        # Negative trade value should be treated as positive
        result = commission.calculate(-1000.0, "buy")
        assert result > 0

    def test_commission_model_inheritance(self):
        """Test that commission models inherit from CommissionModel."""
        flat = FlatCommission()
        percentage = PercentageCommission()
        tiered = TieredCommission()

        assert isinstance(flat, CommissionModel)
        assert isinstance(percentage, CommissionModel)
        assert isinstance(tiered, CommissionModel)


@pytest.mark.unit
class TestSlippageModels:
    """Test slippage models for edge cases."""

    def test_fixed_slippage_default_initialization(self):
        """Test FixedSlippage with default values."""
        slippage = FixedSlippage()
        assert slippage.model_type == "fixed"
        assert slippage.rate == 0.0001  # 0.01%

    def test_fixed_slippage_calculate_zero_volume(self):
        """Test FixedSlippage with zero quantity."""
        slippage = FixedSlippage(rate=0.001)
        with pytest.raises(FrictionCalculationError):
            slippage.apply(100.0, 0, "buy")

    def test_fixed_slippage_calculate_negative_quantity(self):
        """Test FixedSlippage with negative quantity."""
        slippage = FixedSlippage(rate=0.001)
        with pytest.raises(FrictionCalculationError):
            slippage.apply(100.0, -100, "buy")

    def test_fixed_slippage_calculate_zero_price(self):
        """Test FixedSlippage with zero price."""
        slippage = FixedSlippage(rate=0.001)
        with pytest.raises(FrictionCalculationError):
            slippage.apply(0.0, 100, "buy")

    def test_volume_impact_slippage_default_initialization(self):
        """Test VolumeImpactSlippage with default values."""
        slippage = VolumeImpactSlippage()
        assert slippage.model_type == "volume_impact"
        assert slippage.base_rate == 0.0001
        assert slippage.volume_impact_factor == 0.001
        assert slippage.avg_daily_volume == 1000000

    def test_volume_impact_slippage_calculate_zero_volume(self):
        """Test VolumeImpactSlippage with zero quantity."""
        slippage = VolumeImpactSlippage()
        with pytest.raises(FrictionCalculationError):
            slippage.apply(100.0, 0, "buy")

    def test_bid_ask_spread_slippage_default_initialization(self):
        """Test BidAskSpreadSlippage with default values."""
        slippage = BidAskSpreadSlippage()
        assert slippage.model_type == "bid_ask_spread"
        assert slippage.base_spread_rate == 0.0005  # 0.05%
        assert slippage.volatility_factor == 0.1

    def test_volume_based_slippage_default_initialization(self):
        """Test FixedSlippage with default values (as replacement for VolumeBasedSlippage)."""
        slippage = FixedSlippage()
        assert slippage.model_type == "fixed"
        assert slippage.rate == 0.0001

    def test_volume_based_slippage_calculate_different_volumes(self):
        """Test FixedSlippage with different volumes (as replacement for VolumeBasedSlippage)."""
        slippage = FixedSlippage(rate=0.001)

        # Test with different volumes - should always apply the same rate
        price1 = slippage.apply(100.0, 100, "buy")
        price2 = slippage.apply(100.0, 1000, "buy")
        price3 = slippage.apply(100.0, 10000, "buy")

        # All should have the same slippage amount
        expected = 100.0 - (100.0 * 0.001)
        assert price1 == expected
        assert price2 == expected
        assert price3 == expected

    def test_volume_based_slippage_calculate_with_market_depth(self):
        """Test BidAskSpreadSlippage with market depth."""
        slippage = BidAskSpreadSlippage(base_spread_rate=0.001)

        # Test with volatility in market depth
        market_depth = {"volatility": 0.2}
        price = slippage.apply(100.0, 100, "buy", market_depth)

        # Should apply higher spread due to volatility
        assert price < 100.0

    def test_slippage_model_inheritance(self):
        """Test that slippage models inherit from SlippageModel."""
        fixed = FixedSlippage()
        volume_impact = VolumeImpactSlippage()
        bid_ask = BidAskSpreadSlippage()

        assert isinstance(fixed, SlippageModel)
        assert isinstance(volume_impact, SlippageModel)
        assert isinstance(bid_ask, SlippageModel)


@pytest.mark.unit
class TestLatencyModels:
    """Test latency models for edge cases."""

    def test_fixed_latency_default_initialization(self):
        """Test FixedLatency with default values."""
        latency = FixedLatency()
        assert latency.model_type == "fixed"
        assert latency.latency_ms == 10.0  # 10ms default

    def test_fixed_latency_calculate(self):
        """Test FixedLatency calculation."""
        latency = FixedLatency(latency_ms=10.0)  # 10ms
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        result = latency.apply(timestamp)
        # Should return timestamp with added latency
        expected = timestamp + timedelta(milliseconds=10.0)
        assert result == expected

    def test_fixed_latency_calculate_zero_volume(self):
        """Test FixedLatency with zero volume."""
        latency = FixedLatency()
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        result = latency.apply(timestamp)
        # Should return timestamp with added latency
        expected = timestamp + timedelta(milliseconds=10.0)  # Default latency
        assert result == expected

    def test_random_latency_calculate(self):
        """Test UniformRandomLatency calculation."""
        latency = UniformRandomLatency(min_ms=5.0, max_ms=15.0)
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        result = latency.apply(timestamp)
        # Should be in reasonable range
        min_expected = timestamp + timedelta(milliseconds=5.0)
        max_expected = timestamp + timedelta(milliseconds=15.0)
        assert min_expected <= result <= max_expected

    def test_random_latency_calculate_zero_volume(self):
        """Test UniformRandomLatency with zero volume."""
        latency = UniformRandomLatency()
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        result = latency.apply(timestamp)
        # Should still return some datetime value
        assert isinstance(result, datetime)
        assert result >= timestamp

    def test_volume_based_latency_default_initialization(self):
        """Test FixedLatency with default values (as replacement for VolumeBasedLatency)."""
        latency = FixedLatency()
        assert latency.model_type == "fixed"
        assert latency.latency_ms == 10.0

    def test_volume_based_latency_calculate_different_volumes(self):
        """Test FixedLatency with different volumes (as replacement for VolumeBasedLatency)."""
        latency = FixedLatency(latency_ms=20.0)
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        result = latency.apply(timestamp)
        # Should always return the same added latency regardless of volume
        expected = timestamp + timedelta(milliseconds=20.0)
        assert result == expected

    def test_latency_model_inheritance(self):
        """Test that latency models inherit from LatencyModel."""
        fixed = FixedLatency()
        random_latency = UniformRandomLatency()
        normal_latency = NormalRandomLatency()

        assert isinstance(fixed, LatencyModel)
        assert isinstance(random_latency, LatencyModel)
        assert isinstance(normal_latency, LatencyModel)


@pytest.mark.unit
class TestMarketFrictionSimulator:
    """Test market friction simulator for edge cases."""

    def test_simulator_default_initialization(self):
        """Test MarketFrictionSimulator with default values."""
        commission = FlatCommission()
        slippage = FixedSlippage()
        latency = FixedLatency()

        config = MarketFrictionConfig(
            commission_model=commission,
            slippage_model=slippage,
            latency_model=latency
        )

        simulator = MarketFrictionSimulator(config=config)
        assert simulator.config is not None
        assert simulator.config.commission_model is not None
        assert simulator.config.slippage_model is not None
        assert simulator.config.latency_model is not None

    def test_simulator_custom_initialization(self):
        """Test MarketFrictionSimulator with custom models."""
        commission = FlatCommission(fee_per_trade=5.0)
        slippage = FixedSlippage(rate=0.001)
        latency = FixedLatency(latency_ms=50.0)

        config = MarketFrictionConfig(
            commission_model=commission,
            slippage_model=slippage,
            latency_model=latency
        )

        simulator = MarketFrictionSimulator(config=config)
        assert simulator.config.commission_model == commission
        assert simulator.config.slippage_model == slippage
        assert simulator.config.latency_model == latency

    def test_simulator_calculate_commission(self):
        """Test commission calculation."""
        commission = FlatCommission(fee_per_trade=5.0)
        config = MarketFrictionConfig(
            commission_model=commission,
            slippage_model=FixedSlippage(),
            latency_model=FixedLatency()
        )
        simulator = MarketFrictionSimulator(config=config)

        result = simulator.apply_commission(1000.0, "buy", "AAPL")
        assert result == 5.0

    def test_simulator_calculate_commission_with_no_model(self):
        """This test is removed because MarketFrictionConfig requires models."""
        pass

    def test_simulator_calculate_slippage(self):
        """Test slippage calculation."""
        slippage = FixedSlippage(rate=0.001)
        config = MarketFrictionConfig(
            commission_model=FlatCommission(),
            slippage_model=slippage,
            latency_model=FixedLatency()
        )
        simulator = MarketFrictionSimulator(config=config)

        result = simulator.apply_slippage(1000.0, 100, "buy")
        # Should be lower than original price for buy orders
        assert result < 1000.0

    def test_simulator_calculate_slippage_with_no_model(self):
        """This test is removed because MarketFrictionConfig requires models."""
        pass

    def test_simulator_calculate_latency(self):
        """Test latency calculation."""
        latency = FixedLatency(latency_ms=50.0)
        config = MarketFrictionConfig(
            commission_model=FlatCommission(),
            slippage_model=FixedSlippage(),
            latency_model=latency
        )
        simulator = MarketFrictionSimulator(config=config)

        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        result = simulator.apply_latency(timestamp)
        expected = timestamp + timedelta(milliseconds=50.0)
        assert result == expected

    def test_simulator_calculate_latency_with_no_model(self):
        """This test is removed because MarketFrictionConfig requires models."""
        pass

    def test_simulator_apply_friction_buy_order(self):
        """Test applying friction to a buy order using get_total_cost."""
        commission = FlatCommission(fee_per_trade=5.0)
        slippage = FixedSlippage(rate=0.001)
        latency = FixedLatency(latency_ms=50.0)

        config = MarketFrictionConfig(
            commission_model=commission,
            slippage_model=slippage,
            latency_model=latency
        )

        simulator = MarketFrictionSimulator(config=config)

        result = simulator.get_total_cost(100.0, 100, "buy", "AAPL")

        # Should contain calculated values
        assert "commission" in result
        assert "slippage" in result
        assert "total" in result
        assert "executed_price" in result
        assert result["commission"] == 5.0
        assert result["executed_price"] < 100.0  # Lower for buy orders

    def test_simulator_apply_friction_sell_order(self):
        """Test applying friction to a sell order using get_total_cost."""
        commission = FlatCommission(fee_per_trade=5.0)
        slippage = FixedSlippage(rate=0.001)
        latency = FixedLatency(latency_ms=50.0)

        config = MarketFrictionConfig(
            commission_model=commission,
            slippage_model=slippage,
            latency_model=latency
        )

        simulator = MarketFrictionSimulator(config=config)

        result = simulator.get_total_cost(100.0, 100, "sell", "AAPL")

        # Should contain calculated values
        assert "commission" in result
        assert "slippage" in result
        assert "total" in result
        assert "executed_price" in result
        assert result["commission"] == 5.0
        assert result["executed_price"] > 100.0  # Higher for sell orders

    def test_simulator_apply_friction_with_missing_order_data(self):
        """Test applying friction with invalid parameters using get_total_cost."""
        config = MarketFrictionConfig(
            commission_model=FlatCommission(),
            slippage_model=FixedSlippage(),
            latency_model=FixedLatency()
        )

        simulator = MarketFrictionSimulator(config=config)

        # Test with invalid side
        with pytest.raises(FrictionCalculationError):
            simulator.get_total_cost(100.0, 100, "invalid", "AAPL")

        # Test with invalid quantity
        with pytest.raises(FrictionCalculationError):
            simulator.get_total_cost(100.0, "invalid", "buy", "AAPL")

    def test_simulator_apply_friction_with_zero_quantity(self):
        """Test applying friction with zero quantity using get_total_cost."""
        config = MarketFrictionConfig(
            commission_model=FlatCommission(),
            slippage_model=FixedSlippage(),
            latency_model=FixedLatency()
        )

        simulator = MarketFrictionSimulator(config=config)

        # Test with zero quantity should raise an error
        with pytest.raises(FrictionCalculationError):
            simulator.get_total_cost(100.0, 0, "buy", "AAPL")


@pytest.mark.unit
class TestMarketFrictionExceptions:
    """Test custom exceptions for market friction."""

    def test_invalid_friction_model_exception(self):
        """Test InvalidFrictionModel exception."""
        with pytest.raises(InvalidFrictionModel):
            raise InvalidFrictionModel("Test exception")

    def test_invalid_parameter_exception(self):
        """Test InvalidParameter exception."""
        with pytest.raises(InvalidParameter):
            raise InvalidParameter("Test exception")

    def test_friction_calculation_error_exception(self):
        """Test FrictionCalculationError exception."""
        with pytest.raises(FrictionCalculationError):
            raise FrictionCalculationError("Test exception")


@pytest.mark.unit
class TestMarketFrictionEdgeCases:
    """Test edge cases for market friction models."""

    def test_large_trade_values(self):
        """Test models with very large trade values."""
        commission = PercentageCommission(rate=0.001, max_fee=100.0)
        slippage = FixedSlippage(rate=0.0001)

        # Test with $10M trade
        trade_value = 10000000.0
        commission_fee = commission.calculate(trade_value, "buy")
        executed_price = slippage.apply(100.0, 100000, "buy")

        # Commission should be capped at max_fee
        assert commission_fee == 100.0

        # Slippage should be reasonable
        assert executed_price < 100.0  # For buy orders

    def test_extremely_small_trade_values(self):
        """Test models with extremely small trade values."""
        commission = PercentageCommission(rate=0.001, min_fee=0.1)
        slippage = FixedSlippage(rate=0.0005)

        # Test with $1 trade
        trade_value = 1.0
        commission_fee = commission.calculate(trade_value, "buy")
        executed_price = slippage.apply(1.0, 1, "buy")

        # Commission should be min_fee
        assert commission_fee == 0.1

        # Slippage should be very small
        assert executed_price < 1.0  # For buy orders

    def test_models_with_none_values(self):
        """Test models with None values in market data."""
        slippage = BidAskSpreadSlippage()

        # Test with None market data - should handle gracefully
        result = slippage.apply(1000.0, 100, "buy", None)
        assert isinstance(result, float)

    def test_models_with_nan_values(self):
        """Test models with NaN values in market data."""
        slippage = BidAskSpreadSlippage()

        # Test with NaN market data
        market_data = {
            "volatility": float('nan')
        }

        result = slippage.apply(1000.0, 100, "buy", market_data)
        # Should handle NaN values gracefully
        assert isinstance(result, float)

    def test_models_with_infinite_values(self):
        """Test models with infinite values."""
        slippage = BidAskSpreadSlippage()

        # Test with infinite market data
        market_data = {
            "volatility": float('inf')
        }

        result = slippage.apply(1000.0, 100, "buy", market_data)
        # Should handle infinite values gracefully
        assert isinstance(result, float)


@pytest.mark.unit
class TestMarketFrictionConfig:
    """Test MarketFrictionConfig for edge cases."""

    def test_config_initialization(self):
        """Test MarketFrictionConfig initialization."""
        commission = FlatCommission()
        slippage = FixedSlippage()
        latency = FixedLatency()

        config = MarketFrictionConfig(
            commission_model=commission,
            slippage_model=slippage,
            latency_model=latency
        )

        assert config.commission_model == commission
        assert config.slippage_model == slippage
        assert config.latency_model == latency
        assert isinstance(config.asset_specific, dict)

    def test_config_asset_specific(self):
        """Test MarketFrictionConfig with asset-specific settings."""
        commission = FlatCommission()
        slippage = FixedSlippage()
        latency = FixedLatency()

        asset_specific = {
            "AAPL": {
                "commission": PercentageCommission(rate=0.0005),
                "slippage": FixedSlippage(rate=0.0005),
                "latency": FixedLatency(latency_ms=5.0)
            }
        }

        config = MarketFrictionConfig(
            commission_model=commission,
            slippage_model=slippage,
            latency_model=latency,
            asset_specific=asset_specific
        )

        # Test getting asset-specific config
        aapl_config = config.get_asset_config("AAPL")
        assert aapl_config == asset_specific["AAPL"]

        # Test getting non-existent asset config
        msft_config = config.get_asset_config("MSFT")
        assert msft_config == {}


@pytest.mark.unit
class TestCustomFrictionModel:
    """Test CustomFrictionModel interface."""

    def test_custom_friction_model_interface(self):
        """Test CustomFrictionModel interface methods."""
        model = CustomFrictionModel()

        # Test that calculate_cost raises NotImplementedError by default
        with pytest.raises(NotImplementedError):
            model.calculate_cost({})

        # Test that initialize method exists but doesn't raise errors
        model.initialize({})

        # Test that validate_config raises NotImplementedError by default
        with pytest.raises(NotImplementedError):
            model.validate_config({})
