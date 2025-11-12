# Stub package for ib_async
import sys

class IB:
    pass

class Contract:
    pass

class Forex:
    pass

class Future:
    pass

class LimitOrder:
    pass

class MarketOrder:
    pass

class Option:
    pass

class Order:
    pass

class RequestError(Exception):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code

class Stock(Contract):
    pass

class StopLimitOrder:
    pass

class StopOrder:
    pass

class Trade:
    pass

# Prevent real ib_async from being imported
sys.modules['ib_async'] = sys.modules[__name__]
