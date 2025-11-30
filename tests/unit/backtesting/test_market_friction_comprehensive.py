"""Comprehensive tests for market friction simulation module."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from quantchain.backtesting.market_friction import (
    BidAskSpreadSlippage,
    FixedLatency,
    FixedSlippage,
    FlatCommission,
    FrictionCalculationError,
    InvalidFrictionModel,
    InvalidParameter,
    MarketFrictionConfig,
    MarketFrictionSimulator,
    NormalRandomLatency,
    PercentageCommission,
    TieredCommission,
    UniformRandomLatency,
    VolumeImpactSlippage,
)


class TestMarketFrictionExceptions:
    """Test market friction exception classes."""

    @pytest.mark.unit
    def test_friction_calculation_error(self):
        """Test FrictionCalculationError exception."""
        error = FrictionCalculationError("Calculation failed")
        assert str(error) == "Calculation failed"
        assert isinstance(error, Exception)

    @pytest.mark.unit
    def test_invalid_parameter(self):
        """Test InvalidParameter exception."""
        error = InvalidParameter("Invalid parameter value")
        assert str(error) == "Invalid parameter value"
        assert isinstance(error, Exception)

    @pytest.mark.unit
    def test_invalid_friction_model(self):
        """Test InvalidFrictionModel exception."""
        error = InvalidFrictionModel("Invalid model type")
        assert str(error) == "Invalid model type"
        assert isinstance(error, Exception)


class TestMarketFrictionConfig:
    """Test MarketFrictionConfig class."""

    @pytest.mark.unit
    def test_config_creation_with_models(self):
        """Test creating config with specific models."""
        commission_model = FlatCommission(fee_per_trade=2.0)
        slippage_model = FixedSlippage(slippage_amount=0.02)
        latency_model = FixedLatency(latency_ms=50)
        asset_specific = {"AAPL": {"commission": FlatCommission(fee_per_trade=1.0)}}

        config = MarketFrictionConfig(
            commission_model=commission_model,
            slippage_model=slippage_model,
            latency_model=latency_model,
            asset_specific=asset_specific,
        )

        assert config.commission_model == commission_model
        assert config.slippage_model == slippage_model
        assert config.latency_model == latency_model
        assert config.asset_specific == asset_specific

    @pytest.mark.unit
    def test_config_default_asset_specific(self):
        """Test config with default asset_specific."""
        commission_model = PercentageCommission(rate=0.001)
        slippage_model = FixedSlippage()
        latency_model = FixedLatency()

        config = MarketFrictionConfig(
            commission_model=commission_model,
            slippage_model=slippage_model,
            latency_model=latency_model,
        )

        assert config.asset_specific == {}


class TestFlatCommission:
    """Test FlatCommission model."""

    @pytest.fixture
    def flat_commission(self):
        """Create a flat commission model for testing."""
        return FlatCommission(fee_per_trade=1.0, fee_per_contract=0.001, min_fee=0.5)

    @pytest.mark.unit
    def test_flat_commission_init(self):
        """Test flat commission initialization."""
        commission = FlatCommission(
            fee_per_trade=2.0, fee_per_contract=0.005, min_fee=1.0
        )
        assert commission.model_type == "flat"
        assert commission.fee_per_trade == 2.0
        assert commission.fee_per_contract == 0.005
        assert commission.min_fee == 1.0

    @pytest.mark.unit
    def test_flat_commission_calculate_basic(self, flat_commission):
        """Test basic commission calculation."""
        trade_value = 10000.0
        commission = flat_commission.calculate(trade_value, "buy")

        expected = 1.0 + (
            0.001 * abs(trade_value)
        )  # fee_per_trade + fee_per_contract * trade_value
        expected = max(expected, 0.5)  # Apply min_fee
        assert commission == expected

    @pytest.mark.unit
    def test_flat_commission_calculate_sell(self, flat_commission):
        """Test commission calculation for sell orders."""
        trade_value = -5000.0
        commission = flat_commission.calculate(trade_value, "sell")

        # Should use absolute value
        expected = 1.0 + (0.001 * abs(trade_value))
        expected = max(expected, 0.5)
        assert commission == expected

    @pytest.mark.unit
    def test_flat_commission_min_fee(self, flat_commission):
        """Test minimum fee enforcement."""
        trade_value = 100.0  # Small trade value
        commission = flat_commission.calculate(trade_value, "buy")

        expected = max(1.0 + (0.001 * trade_value), 0.5)
        assert commission == expected

    @pytest.mark.unit
    def test_flat_commission_with_symbol(self, flat_commission):
        """Test commission calculation with symbol parameter."""
        commission = flat_commission.calculate(1000.0, "buy", symbol="AAPL")
        assert commission > 0

    @pytest.mark.unit
    def test_flat_commission_with_kwargs(self, flat_commission):
        """Test commission calculation with additional kwargs."""
        commission = flat_commission.calculate(
            1000.0, "buy", symbol="AAPL", exchange="NYSE"
        )
        assert commission > 0


class TestPercentageCommission:
    """Test PercentageCommission model."""

    @pytest.fixture
    def percentage_commission(self):
        """Create a percentage commission model for testing."""
        return PercentageCommission(rate=0.001, min_fee=1.0, max_fee=100.0)

    @pytest.mark.unit
    def test_percentage_commission_init(self):
        """Test percentage commission initialization."""
        commission = PercentageCommission(rate=0.002, min_fee=0.5, max_fee=50.0)
        assert commission.model_type == "percentage"
        assert commission.rate == 0.002
        assert commission.min_fee == 0.5
        assert commission.max_fee == 50.0

    @pytest.mark.unit
    def test_percentage_commission_calculate_basic(self, percentage_commission):
        """Test basic percentage commission calculation."""
        trade_value = 10000.0
        commission = percentage_commission.calculate(trade_value, "buy")

        expected = abs(trade_value) * 0.001
        expected = max(min(expected, 100.0), 1.0)  # Apply min/max bounds
        assert commission == expected

    @pytest.mark.unit
    def test_percentage_commission_min_fee(self, percentage_commission):
        """Test minimum fee enforcement."""
        trade_value = 500.0
        commission = percentage_commission.calculate(trade_value, "buy")

        expected = abs(trade_value) * 0.001  # 0.5
        expected = max(expected, 1.0)  # Should be increased to min_fee
        assert commission == 1.0

    @pytest.mark.unit
    def test_percentage_commission_max_fee(self, percentage_commission):
        """Test maximum fee enforcement."""
        trade_value = 200000.0
        commission = percentage_commission.calculate(trade_value, "buy")

        expected = abs(trade_value) * 0.001  # 200.0
        expected = min(expected, 100.0)  # Should be reduced to max_fee
        assert commission == 100.0

    @pytest.mark.unit
    def test_percentage_commission_no_bounds(self):
        """Test percentage commission without min/max bounds."""
        commission = PercentageCommission(rate=0.0015)
        trade_value = 5000.0

        result = commission.calculate(trade_value, "buy")
        expected = abs(trade_value) * 0.0015
        assert result == expected


class TestTieredCommission:
    """Test TieredCommission model."""

    @pytest.fixture
    def tiered_commission(self):
        """Create a tiered commission model for testing."""
        custom_tiers = [
            (0.0, 0.005),  # >0: 0.5%
            (1000.0, 0.003),  # >1000: 0.3%
            (10000.0, 0.001),  # >10000: 0.1%
        ]
        return TieredCommission(tiers=custom_tiers, base_rate=0.005, volume_window="1M")

    @pytest.mark.unit
    def test_tiered_commission_init_default(self):
        """Test tiered commission initialization with default tiers."""
        commission = TieredCommission()
        assert commission.model_type == "tiered"
        assert commission.base_rate == 0.001
        assert commission.volume_window == "1M"
        assert len(commission.tiers) == 4
        assert commission.volume_tracker == {}

    @pytest.mark.unit
    def test_tiered_commission_init_custom(self, tiered_commission):
        """Test tiered commission initialization with custom tiers."""
        assert tiered_commission.model_type == "tiered"
        assert tiered_commission.base_rate == 0.005
        assert tiered_commission.volume_window == "1M"
        assert len(tiered_commission.tiers) == 3

    @pytest.mark.unit
    def test_tiered_commission_calculate_low_volume(self, tiered_commission):
        """Test commission calculation for low volume."""
        trade_value = 5000.0
        monthly_volume = 500.0

        commission = tiered_commission.calculate(
            trade_value, "buy", monthly_volume=monthly_volume
        )
        # Should use base rate since volume < 1000
        expected = abs(trade_value) * 0.005
        assert commission == expected

    @pytest.mark.unit
    def test_tiered_commission_calculate_medium_volume(self, tiered_commission):
        """Test commission calculation for medium volume."""
        trade_value = 5000.0
        monthly_volume = 5000.0

        commission = tiered_commission.calculate(
            trade_value, "buy", monthly_volume=monthly_volume
        )
        # Should use tier 2 rate since volume > 1000 but < 10000
        expected = abs(trade_value) * 0.003
        assert commission == expected

    @pytest.mark.unit
    def test_tiered_commission_calculate_high_volume(self, tiered_commission):
        """Test commission calculation for high volume."""
        trade_value = 5000.0
        monthly_volume = 15000.0

        commission = tiered_commission.calculate(
            trade_value, "buy", monthly_volume=monthly_volume
        )
        # Should use tier 3 rate since volume > 10000
        expected = abs(trade_value) * 0.001
        assert commission == expected

    @pytest.mark.unit
    def test_tiered_commission_boundary_conditions(self, tiered_commission):
        """Test commission calculation at tier boundaries."""
        trade_value = 1000.0

        # Exactly at boundary - should use base rate since logic uses > not >=
        commission = tiered_commission.calculate(
            trade_value, "buy", monthly_volume=1000.0
        )
        expected = abs(trade_value) * 0.005  # Should use base rate
        assert commission == expected

        # Just above boundary
        commission = tiered_commission.calculate(
            trade_value, "buy", monthly_volume=1000.1
        )
        expected = abs(trade_value) * 0.003  # Should use second tier (>1000)
        assert commission == expected

        # Just below boundary (should use base rate)
        commission = tiered_commission.calculate(
            trade_value, "buy", monthly_volume=999.9
        )
        expected = abs(trade_value) * 0.005  # Should use base rate
        assert commission == expected

    @pytest.mark.unit
    def test_tiered_commission_no_monthly_volume(self, tiered_commission):
        """Test commission calculation without monthly volume parameter."""
        trade_value = 1000.0

        commission = tiered_commission.calculate(trade_value, "buy")
        # Should use base rate when no volume provided
        expected = abs(trade_value) * tiered_commission.base_rate
        assert commission == expected


class TestFixedSlippage:
    """Test FixedSlippage model."""

    @pytest.fixture
    def fixed_slippage(self):
        """Create a fixed slippage model for testing."""
        return FixedSlippage(slippage_amount=0.05)

    @pytest.mark.unit
    def test_fixed_slippage_init(self):
        """Test fixed slippage initialization."""
        slippage = FixedSlippage(slippage_amount=0.02)
        assert slippage.model_type == "fixed"
        assert slippage.slippage_amount == 0.02

    @pytest.mark.unit
    def test_fixed_slippage_calculate_buy(self, fixed_slippage):
        """Test slippage calculation for buy orders."""
        price = 100.0
        quantity = 100
        slippage = fixed_slippage.calculate(price, quantity, "buy")

        # Buy orders should have positive slippage (price increases)
        assert slippage == fixed_slippage.slippage_amount

    @pytest.mark.unit
    def test_fixed_slippage_calculate_sell(self, fixed_slippage):
        """Test slippage calculation for sell orders."""
        price = 100.0
        quantity = 100
        slippage = fixed_slippage.calculate(price, quantity, "sell")

        # Sell orders should have negative slippage (price decreases)
        assert slippage == -fixed_slippage.slippage_amount

    @pytest.mark.unit
    def test_fixed_slippage_case_insensitive(self, fixed_slippage):
        """Test slippage calculation with case insensitive side."""
        price = 100.0
        quantity = 100

        buy_slippage = fixed_slippage.calculate(price, quantity, "BUY")
        sell_slippage = fixed_slippage.calculate(price, quantity, "SELL")

        assert buy_slippage == fixed_slippage.slippage_amount
        assert sell_slippage == -fixed_slippage.slippage_amount

    @pytest.mark.unit
    def test_fixed_slippage_with_optional_params(self, fixed_slippage):
        """Test slippage calculation with optional parameters."""
        slippage = fixed_slippage.calculate(
            price=100.0,
            quantity=100,
            side="buy",
            market_depth={"bid": 99.95, "ask": 100.05},
            symbol="AAPL",
        )
        assert slippage == fixed_slippage.slippage_amount


class TestVolumeImpactSlippage:
    """Test VolumeImpactSlippage model."""

    @pytest.fixture
    def volume_impact_slippage(self):
        """Create a volume impact slippage model for testing."""
        return VolumeImpactSlippage(impact_factor=0.0001, volume_window="1D")

    @pytest.mark.unit
    def test_volume_impact_slippage_init(self):
        """Test volume impact slippage initialization."""
        slippage = VolumeImpactSlippage(impact_factor=0.0002, volume_window="1H")
        assert slippage.model_type == "volume_impact"
        assert slippage.impact_factor == 0.0002
        assert slippage.volume_window == "1H"

    @pytest.mark.unit
    def test_volume_impact_calculate_buy(self, volume_impact_slippage):
        """Test volume impact slippage for buy orders."""
        price = 100.0
        quantity = 1000
        slippage = volume_impact_slippage.calculate(price, quantity, "buy")

        # Calculate expected slippage: price * quantity * impact_factor
        expected = price * quantity * 0.0001
        assert slippage == expected
        assert slippage > 0  # Positive for buy

    @pytest.mark.unit
    def test_volume_impact_calculate_sell(self, volume_impact_slippage):
        """Test volume impact slippage for sell orders."""
        price = 100.0
        quantity = 1000
        slippage = volume_impact_slippage.calculate(price, quantity, "sell")

        # Calculate expected slippage: price * quantity * impact_factor
        expected = price * quantity * 0.0001
        assert slippage == -expected  # Negative for sell

    @pytest.mark.unit
    def test_volume_impact_different_quantities(self, volume_impact_slippage):
        """Test slippage with different quantities."""
        price = 100.0

        # Small quantity
        slippage_small = volume_impact_slippage.calculate(price, 100, "buy")
        expected_small = price * 100 * 0.0001
        assert slippage_small == expected_small

        # Large quantity
        slippage_large = volume_impact_slippage.calculate(price, 10000, "buy")
        expected_large = price * 10000 * 0.0001
        assert slippage_large == expected_large

        # Large quantity should have more slippage
        assert slippage_large > slippage_small


class TestBidAskSpreadSlippage:
    """Test BidAskSpreadSlippage model."""

    @pytest.fixture
    def bid_ask_slippage(self):
        """Create a bid-ask spread slippage model for testing."""
        return BidAskSpreadSlippage(spread_pct=0.002, random_factor=0.5)

    @pytest.mark.unit
    def test_bid_ask_slippage_init(self):
        """Test bid-ask spread slippage initialization."""
        slippage = BidAskSpreadSlippage(spread_pct=0.001, random_factor=0.3)
        assert slippage.model_type == "bid_ask_spread"
        assert slippage.spread_pct == 0.001
        assert slippage.random_factor == 0.3

    @pytest.mark.unit
    def test_bid_ask_slippage_calculate_buy(self, bid_ask_slippage):
        """Test bid-ask spread slippage for buy orders."""
        price = 100.0
        quantity = 100

        with patch("random.random", return_value=0.5):  # Center random value
            slippage = bid_ask_slippage.calculate(price, quantity, "buy")

        # Base slippage should be half the spread
        base_slippage = price * 0.002 * 0.5  # 0.1
        # With random factor = 0.5 and random() = 0.5, random_slippage = 0
        expected = base_slippage

        assert slippage == expected
        assert slippage > 0  # Positive for buy

    @pytest.mark.unit
    def test_bid_ask_slippage_calculate_sell(self, bid_ask_slippage):
        """Test bid-ask spread slippage for sell orders."""
        price = 100.0
        quantity = 100

        with patch("random.random", return_value=0.5):
            slippage = bid_ask_slippage.calculate(price, quantity, "sell")

        # Should be negative for sell
        assert slippage < 0

    @pytest.mark.unit
    def test_bid_ask_slippage_random_variation(self, bid_ask_slippage):
        """Test bid-ask spread slippage random variation."""
        price = 100.0
        quantity = 100

        # Test with different random values
        with patch("random.random", return_value=0.0):  # Minimum random
            slippage_min = bid_ask_slippage.calculate(price, quantity, "buy")

        with patch("random.random", return_value=1.0):  # Maximum random
            slippage_max = bid_ask_slippage.calculate(price, quantity, "buy")

        # Max should be greater than min
        assert slippage_max > slippage_min


class TestFixedLatency:
    """Test FixedLatency model."""

    @pytest.fixture
    def fixed_latency(self):
        """Create a fixed latency model for testing."""
        return FixedLatency(latency_ms=150)

    @pytest.mark.unit
    def test_fixed_latency_init(self):
        """Test fixed latency initialization."""
        latency = FixedLatency(latency_ms=200)
        assert latency.model_type == "fixed"
        assert latency.latency_ms == 200

    @pytest.mark.unit
    def test_fixed_latency_apply(self, fixed_latency):
        """Test applying fixed latency."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        result = fixed_latency.apply(timestamp)

        expected = timestamp + timedelta(milliseconds=150)
        assert result == expected

    @pytest.mark.unit
    def test_fixed_latency_apply_with_symbol(self, fixed_latency):
        """Test applying fixed latency with symbol parameter."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        result = fixed_latency.apply(timestamp, symbol="AAPL")

        expected = timestamp + timedelta(milliseconds=150)
        assert result == expected


class TestUniformRandomLatency:
    """Test UniformRandomLatency model."""

    @pytest.fixture
    def uniform_latency(self):
        """Create a uniform random latency model for testing."""
        return UniformRandomLatency(min_ms=50, max_ms=150)

    @pytest.mark.unit
    def test_uniform_latency_init(self):
        """Test uniform random latency initialization."""
        latency = UniformRandomLatency(min_ms=100, max_ms=300)
        assert latency.model_type == "uniform_random"
        assert latency.min_ms == 100
        assert latency.max_ms == 300

    @pytest.mark.unit
    def test_uniform_latency_apply(self, uniform_latency):
        """Test applying uniform random latency."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)

        with patch("random.randint", return_value=100):
            result = uniform_latency.apply(timestamp)

        expected = timestamp + timedelta(milliseconds=100)
        assert result == expected

    @pytest.mark.unit
    def test_uniform_latency_range_check(self, uniform_latency):
        """Test that latency is within specified range."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)

        # Test multiple calls to ensure range adherence
        for _ in range(10):
            with patch("random.randint", return_value=75):
                result = uniform_latency.apply(timestamp)
                latency_ms = (result - timestamp).total_seconds() * 1000
                assert 50 <= latency_ms <= 150


class TestNormalRandomLatency:
    """Test NormalRandomLatency model."""

    @pytest.fixture
    def normal_latency(self):
        """Create a normal random latency model for testing."""
        return NormalRandomLatency(mean_ms=100, std_ms=30)

    @pytest.mark.unit
    def test_normal_latency_init(self):
        """Test normal random latency initialization."""
        latency = NormalRandomLatency(mean_ms=150, std_ms=50)
        assert latency.model_type == "normal_random"
        assert latency.mean_ms == 150
        assert latency.std_ms == 50

    @pytest.mark.unit
    def test_normal_latency_apply_positive(self, normal_latency):
        """Test applying normal random latency with positive result."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)

        with patch("numpy.random.normal", return_value=120):
            result = normal_latency.apply(timestamp)

        expected = timestamp + timedelta(milliseconds=120)
        assert result == expected

    @pytest.mark.unit
    def test_normal_latency_apply_negative_to_zero(self, normal_latency):
        """Test applying normal random latency with negative result (should be clamped to 0)."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)

        with patch("numpy.random.normal", return_value=-10):
            result = normal_latency.apply(timestamp)

        # Negative latency should be clamped to 0
        expected = timestamp
        assert result == expected


class TestMarketFrictionSimulator:
    """Test MarketFrictionSimulator class."""

    @pytest.fixture
    def simulator(self):
        """Create a market friction simulator for testing."""
        config = {
            "commission_model": PercentageCommission(rate=0.001),
            "slippage_model": FixedSlippage(slippage_amount=0.01),
            "latency_model": FixedLatency(latency_ms=100),
        }
        return MarketFrictionSimulator(config)

    @pytest.mark.unit
    def test_simulator_init_default(self):
        """Test simulator initialization with default config."""
        simulator = MarketFrictionSimulator()

        assert isinstance(simulator.commission_model, PercentageCommission)
        assert isinstance(simulator.slippage_model, VolumeImpactSlippage)
        assert isinstance(simulator.latency_model, FixedLatency)
        assert simulator.asset_specific == {}

    @pytest.mark.unit
    def test_simulator_init_custom(self):
        """Test simulator initialization with custom config."""
        config = {
            "commission_model": FlatCommission(fee_per_trade=2.0),
            "slippage_model": FixedSlippage(slippage_amount=0.02),
            "latency_model": UniformRandomLatency(50, 150),
            "asset_specific": {
                "AAPL": {"commission": FlatCommission(fee_per_trade=1.0)}
            },
        }
        simulator = MarketFrictionSimulator(config)

        assert isinstance(simulator.commission_model, FlatCommission)
        assert isinstance(simulator.slippage_model, FixedSlippage)
        assert isinstance(simulator.latency_model, UniformRandomLatency)

    @pytest.mark.unit
    def test_apply_commission_basic(self, simulator):
        """Test applying commission to a trade."""
        trade_value = 10000.0
        commission = simulator.apply_commission(trade_value, "buy", symbol="AAPL")

        # Should use percentage commission: 10000 * 0.001 = 10
        expected = abs(trade_value) * 0.001
        assert commission == expected

    @pytest.mark.unit
    def test_apply_commission_asset_specific(self, simulator):
        """Test applying commission with asset-specific model."""
        # Set up asset-specific commission
        simulator.asset_specific["AAPL"] = {
            "commission": FlatCommission(fee_per_trade=5.0)
        }

        commission = simulator.apply_commission(1000.0, "buy", symbol="AAPL")
        assert commission == 5.0  # Should use flat fee for AAPL

    @pytest.mark.unit
    def test_apply_slippage_basic(self, simulator):
        """Test applying slippage to a trade."""
        price = 100.0
        quantity = 100
        slippage = simulator.apply_slippage(price, quantity, "buy", symbol="AAPL")

        # Should use fixed slippage: 0.01 for buy
        assert slippage == 0.01

    @pytest.mark.unit
    def test_apply_slippage_asset_specific(self, simulator):
        """Test applying slippage with asset-specific model."""
        # Set up asset-specific slippage
        simulator.asset_specific["AAPL"] = {
            "slippage": FixedSlippage(slippage_amount=0.02)
        }

        slippage = simulator.apply_slippage(100.0, 100, "buy", symbol="AAPL")
        assert slippage == 0.02

    @pytest.mark.unit
    def test_apply_latency_basic(self, simulator):
        """Test applying latency to a timestamp."""
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        result = simulator.apply_latency(timestamp, symbol="AAPL")

        expected = timestamp + timedelta(milliseconds=100)
        assert result == expected

    @pytest.mark.unit
    def test_apply_latency_asset_specific(self, simulator):
        """Test applying latency with asset-specific model."""
        # Set up asset-specific latency
        simulator.asset_specific["AAPL"] = {"latency": FixedLatency(latency_ms=200)}

        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        result = simulator.apply_latency(timestamp, symbol="AAPL")

        expected = timestamp + timedelta(milliseconds=200)
        assert result == expected

    @pytest.mark.unit
    def test_get_total_cost_comprehensive(self, simulator):
        """Test getting total friction costs for a trade."""
        price = 100.0
        quantity = 100
        side = "buy"
        timestamp = datetime(2023, 1, 1, 12, 0, 0)

        costs = simulator.get_total_cost(price, quantity, side, timestamp=timestamp)

        # Check that all cost components are present
        assert "commission" in costs
        assert "slippage" in costs
        assert "slippage_cost" in costs
        assert "total_cost" in costs
        assert "execution_time" in costs

        # Check values
        assert costs["commission"] == 10000.0 * 0.001  # 10.0
        assert costs["slippage"] == 0.01  # Fixed slippage for buy
        assert costs["slippage_cost"] == 0.01 * quantity  # 1.0
        assert costs["total_cost"] == costs["commission"] + costs["slippage_cost"]
        assert costs["execution_time"] == timestamp + timedelta(milliseconds=100)

    @pytest.mark.unit
    def test_get_total_cost_sell_order(self, simulator):
        """Test getting total costs for a sell order."""
        price = 100.0
        quantity = 100
        side = "sell"

        costs = simulator.get_total_cost(price, quantity, side)

        # Commission should be the same regardless of side
        assert costs["commission"] == 10000.0 * 0.001

        # Slippage should be negative for sell
        assert costs["slippage"] < 0
        assert costs["slippage_cost"] == costs["slippage"] * quantity

    @pytest.mark.unit
    def test_get_total_cost_no_timestamp(self, simulator):
        """Test getting total costs without timestamp."""
        costs = simulator.get_total_cost(100.0, 100, "buy")

        # execution_time should be None when no timestamp provided
        assert costs["execution_time"] is None

    @pytest.mark.unit
    def test_get_total_cost_with_market_depth(self, simulator):
        """Test getting total costs with market depth."""
        market_depth = {"bid": 99.95, "ask": 100.05, "volume": 1000000}

        costs = simulator.get_total_cost(
            price=100.0, quantity=100, side="buy", market_depth=market_depth
        )

        # Should calculate costs normally (fixed slippage doesn't use market depth)
        assert "total_cost" in costs
        assert costs["total_cost"] > 0

    @pytest.mark.unit
    def test_get_total_cost_with_kwargs(self, simulator):
        """Test getting total costs with additional kwargs."""
        costs = simulator.get_total_cost(
            price=100.0,
            quantity=100,
            side="buy",
            symbol="AAPL",
            exchange="NYSE",
            order_type="market",
        )

        # Should handle extra kwargs gracefully
        assert "total_cost" in costs
        assert costs["total_cost"] > 0

    @pytest.mark.unit
    def test_complex_friction_scenario(self):
        """Test a complex scenario with different friction models."""
        config = {
            "commission_model": TieredCommission(
                tiers=[(0.0, 0.003), (1000.0, 0.002), (10000.0, 0.001)]
            ),
            "slippage_model": VolumeImpactSlippage(impact_factor=0.0002),
            "latency_model": NormalRandomLatency(mean_ms=150, std_ms=50),
            "asset_specific": {
                "AAPL": {
                    "commission": FlatCommission(
                        fee_per_trade=1.0, fee_per_contract=0.0001
                    ),
                    "slippage": BidAskSpreadSlippage(
                        spread_pct=0.001, random_factor=0.3
                    ),
                    "latency": FixedLatency(latency_ms=75),
                }
            },
        }
        simulator = MarketFrictionSimulator(config)

        # Test trade for AAPL (should use asset-specific models)
        timestamp = datetime(2023, 1, 1, 12, 0, 0)
        costs = simulator.get_total_cost(
            price=150.0, quantity=1000, side="buy", symbol="AAPL", timestamp=timestamp
        )

        # Should use flat commission for AAPL: 1.0 + (0.0001 * 150000) = 16.0
        expected_commission = 1.0 + (0.0001 * 150000.0)
        assert abs(costs["commission"] - expected_commission) < 0.01

        # Should use bid-ask spread slippage for AAPL
        assert costs["slippage"] > 0  # Positive for buy

        # Should use fixed latency for AAPL
        expected_time = timestamp + timedelta(milliseconds=75)
        assert costs["execution_time"] == expected_time

    @pytest.mark.unit
    def test_edge_case_zero_trade_value(self, simulator):
        """Test handling of zero trade value."""
        costs = simulator.get_total_cost(price=0.0, quantity=0, side="buy")

        # Commission should be zero for zero trade value
        assert costs["commission"] == 0.0

    @pytest.mark.unit
    def test_edge_case_negative_price(self, simulator):
        """Test handling of negative prices (should use absolute value)."""
        costs = simulator.get_total_cost(price=-100.0, quantity=100, side="buy")

        # Should calculate based on absolute trade value
        assert costs["commission"] == 10000.0 * 0.001
