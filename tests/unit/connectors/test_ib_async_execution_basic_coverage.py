"""Basic coverage tests for IB async execution connector."""

import pytest

# Check if ib_async_execution is available
try:
    from quantchain.connectors.ib_async_execution import (
        IBExecutionConnector,
        IB_ASYNC_AVAILABLE,
    )
    IB_EXECUTION_AVAILABLE = True
except ImportError as e:
    IB_EXECUTION_AVAILABLE = False
    print(f"Import error: {e}")

pytestmark = pytest.mark.skipif(
    not IB_EXECUTION_AVAILABLE, reason="IB execution connector not available"
)


@pytest.mark.unit
class TestIBExecutionBasicCoverage:
    """Basic tests to improve coverage of IB execution connector."""

    def test_ib_async_availability_constant(self):
        """Test IB_ASYNC_AVAILABLE constant is defined."""
        assert isinstance(IB_ASYNC_AVAILABLE, bool)

    def test_module_imports(self):
        """Test that key module attributes are imported."""
        # Test that constants are defined
        from quantchain.connectors.ib_async_execution import (
            IBAsyncError,
            IBConnectionError,
            IBOrderError,
            IBValidationError,
        )
        
        assert IBAsyncError is not None
        assert IBConnectionError is not None
        assert IBOrderError is not None
        assert IBValidationError is not None

    def test_error_classes_creation(self):
        """Test error classes can be instantiated."""
        from quantchain.connectors.ib_async_execution import (
            IBAsyncError,
            IBConnectionError,
            IBOrderError,
            IBValidationError,
        )
        
        # Test base error
        error = IBAsyncError("Test error")
        assert str(error) == "Test error"
        
        # Test connection error
        conn_error = IBConnectionError("Connection failed")
        assert str(conn_error) == "Connection failed"
        
        # Test order error
        order_error = IBOrderError("Order failed")
        assert str(order_error) == "Order failed"
        
        # Test validation error
        val_error = IBValidationError("Invalid data")
        assert str(val_error) == "Invalid data"

    def test_error_inheritance(self):
        """Test error class inheritance hierarchy."""
        from quantchain.connectors.ib_async_execution import (
            IBAsyncError,
            IBConnectionError,
            IBOrderError,
            IBValidationError,
        )
        
        # Test that specific errors inherit from base
        assert issubclass(IBConnectionError, IBAsyncError)
        assert issubclass(IBOrderError, IBAsyncError)
        assert issubclass(IBValidationError, IBAsyncError)
        assert issubclass(IBValidationError, ValueError)

    def test_constants_and_config(self):
        """Test module constants and configuration."""
        from quantchain.connectors.ib_async_execution import (
            DEFAULT_HOST,
            DEFAULT_PORT,
            DEFAULT_TIMEOUT,
            DEFAULT_CLIENT_ID,
        )
        
        assert DEFAULT_HOST == "127.0.0.1"
        assert DEFAULT_PORT == 7497
        assert DEFAULT_TIMEOUT == 30
        assert DEFAULT_CLIENT_ID == 1

    def test_order_type_mapping(self):
        """Test order type mapping functions."""
        from quantchain.connectors.ib_async_execution import (
            map_order_type_to_ib,
            map_order_type_from_ib,
        )
        
        # Test mapping to IB
        assert map_order_type_to_ib("MARKET") == "MKT"
        assert map_order_type_to_ib("LIMIT") == "LMT"
        assert map_order_type_to_ib("STOP") == "STP"
        assert map_order_type_to_ib("STOP_LIMIT") == "STP LMT"
        
        # Test mapping from IB
        assert map_order_type_from_ib("MKT") == "MARKET"
        assert map_order_type_from_ib("LMT") == "LIMIT"
        assert map_order_type_from_ib("STP") == "STOP"
        assert map_order_type_from_ib("STP LMT") == "STOP_LIMIT"

    def test_time_in_force_mapping(self):
        """Test time in force mapping functions."""
        from quantchain.connectors.ib_async_execution import (
            map_tif_to_ib,
            map_tif_from_ib,
        )
        
        # Test mapping to IB
        assert map_tif_to_ib("DAY") == "DAY"
        assert map_tif_to_ib("GTC") == "GTC"
        assert map_tif_to_ib("IOC") == "IOC"
        assert map_tif_to_ib("FOK") == "FOK"
        
        # Test mapping from IB
        assert map_tif_from_ib("DAY") == "DAY"
        assert map_tif_from_ib("GTC") == "GTC"
        assert map_tif_from_ib("IOC") == "IOC"
        assert map_tif_from_ib("FOK") == "FOK"

    def test_contract_creation_helpers(self):
        """Test contract creation helper functions."""
        from quantchain.connectors.ib_async_execution import (
            create_stock_contract,
            create_option_contract,
            create_future_contract,
            create_forex_contract,
        )
        
        # Test stock contract
        stock = create_stock_contract("AAPL", "SMART", "USD")
        assert stock["symbol"] == "AAPL"
        assert stock["secType"] == "STK"
        assert stock["exchange"] == "SMART"
        assert stock["currency"] == "USD"
        
        # Test option contract
        option = create_option_contract("AAPL", "20231215", 150, "C", "SMART")
        assert option["symbol"] == "AAPL"
        assert option["secType"] == "OPT"
        assert option["lastTradeDateOrContractMonth"] == "20231215"
        assert option["strike"] == 150
        assert option["right"] == "C"
        
        # Test future contract
        future = create_future_contract("ES", "202312", "CME", "USD")
        assert future["symbol"] == "ES"
        assert future["secType"] == "FUT"
        assert future["lastTradeDateOrContractMonth"] == "202312"
        assert future["exchange"] == "CME"
        assert future["currency"] == "USD"
        
        # Test forex contract
        forex = create_forex_contract("EUR", "USD")
        assert forex["symbol"] == "EUR"
        assert forex["secType"] == "CASH"
        assert forex["currency"] == "USD"

    def test_order_validation_functions(self):
        """Test order validation functions."""
        from quantchain.connectors.ib_async_execution import (
            validate_order_quantity,
            validate_price,
            validate_symbol,
        )
        
        # Test quantity validation
        assert validate_order_quantity(100) == True
        assert validate_order_quantity(0) == False
        assert validate_order_quantity(-1) == False
        
        # Test price validation
        assert validate_price(100.0) == True
        assert validate_price(0) == True
        assert validate_price(-1) == False
        
        # Test symbol validation
        assert validate_symbol("AAPL") == True
        assert validate_symbol("") == False
        assert validate_symbol(None) == False

    def test_connection_parameters(self):
        """Test connection parameter validation."""
        from quantchain.connectors.ib_async_execution import (
            validate_connection_params,
        )
        
        # Valid params
        assert validate_connection_params("127.0.0.1", 7497, 1, 30) == True
        
        # Invalid host
        assert validate_connection_params("", 7497, 1, 30) == False
        
        # Invalid port
        assert validate_connection_params("127.0.0.1", 0, 1, 30) == False
        assert validate_connection_params("127.0.0.1", 65536, 1, 30) == False
        
        # Invalid client_id
        assert validate_connection_params("127.0.0.1", 7497, 0, 30) == False
        
        # Invalid timeout
        assert validate_connection_params("127.0.0.1", 7497, 1, 0) == False

    def test_error_message_parsing(self):
        """Test error message parsing functions."""
        from quantchain.connectors.ib_async_execution import (
            parse_error_code,
            parse_error_message,
        )
        
        # Test error code parsing
        assert parse_error_code("Error 502: Bad Gateway") == 502
        assert parse_error_code("No error code") is None
        
        # Test error message parsing
        msg = parse_error_message("Error 502: Bad Gateway")
        assert "Bad Gateway" in msg
        assert parse_error_message("") == "Unknown error"

    def test_data_type_conversions(self):
        """Test data type conversion functions."""
        from quantchain.connectors.ib_async_execution import (
            convert_datetime_to_ib,
            convert_datetime_from_ib,
            format_price,
            format_quantity,
        )
        
        # Test datetime conversion
        from datetime import datetime, timezone
        
        dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        ib_dt = convert_datetime_to_ib(dt)
        assert ib_dt is not None
        
        # Test price formatting
        assert format_price(100.123456) == "100.12"
        assert format_price(100) == "100.00"
        
        # Test quantity formatting
        assert format_quantity(100) == "100"
        assert format_quantity(100.5) == "100"

    def test_market_data_functions(self):
        """Test market data related functions."""
        from quantchain.connectors.ib_async_execution import (
            get_tick_type_string,
            get_generic_tick_types,
        )
        
        # Test tick type string
        assert get_tick_type_string(1) == "BID"
        assert get_tick_type_string(2) == "ASK"
        assert get_tick_type_string(4) == "LAST"
        assert get_tick_type_string(999) == "UNKNOWN"
        
        # Test generic tick types
        tick_types = get_generic_tick_types()
        assert isinstance(tick_types, dict)
        assert len(tick_types) > 0

    def test_account_info_helpers(self):
        """Test account information helper functions."""
        from quantchain.connectors.ib_async_execution import (
            parse_account_value,
            parse_position,
            parse_portfolio_value,
        )
        
        # Test account value parsing
        account_val = {"tag": "NetLiquidation", "value": "100000.0", "currency": "USD"}
        parsed = parse_account_value(account_val)
        assert parsed["tag"] == "NetLiquidation"
        assert parsed["value"] == 100000.0
        assert parsed["currency"] == "USD"
        
        # Test position parsing
        position = {
            "contract": {"symbol": "AAPL", "secType": "STK"},
            "position": 100,
            "averageCost": 150.0
        }
        parsed_pos = parse_position(position)
        assert parsed_pos["symbol"] == "AAPL"
        assert parsed_pos["quantity"] == 100
        assert parsed_pos["avg_cost"] == 150.0
        
        # Test portfolio value parsing
        portfolio = {
            "contract": {"symbol": "AAPL", "secType": "STK"},
            "marketPrice": 155.0,
            "marketValue": 15500.0,
            "unrealizedPNL": 500.0
        }
        parsed_port = parse_portfolio_value(portfolio)
        assert parsed_port["symbol"] == "AAPL"
        assert parsed_port["market_price"] == 155.0
        assert parsed_port["market_value"] == 15500.0
        assert parsed_port["unrealized_pnl"] == 500.0

    def test_contract_utilities(self):
        """Test contract utility functions."""
        from quantchain.connectors.ib_async_execution import (
            make_contract_string,
            contract_to_dict,
        )
        
        # Test contract string creation
        contract = {
            "symbol": "AAPL",
            "secType": "STK",
            "exchange": "SMART",
            "currency": "USD"
        }
        contract_str = make_contract_string(contract)
        assert "AAPL" in contract_str
        assert "STK" in contract_str
        assert "SMART" in contract_str
        
        # Test contract to dict conversion
        contract_obj = type("Contract", (), {
            "symbol": "AAPL",
            "secType": "STK",
            "exchange": "SMART",
            "currency": "USD"
        })()
        contract_dict = contract_to_dict(contract_obj)
        assert contract_dict["symbol"] == "AAPL"
        assert contract_dict["secType"] == "STK"
        assert contract_dict["exchange"] == "SMART"
        assert contract_dict["currency"] == "USD"
