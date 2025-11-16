# Stub implementation of ib_async classes used in tests


class IB:

    def __init__(self):
        pass

    def connect_async(self, *args, **kwargs):
        # Fake async connect
        async def inner():
            return True

        return inner()

    RaiseRequestErrors = False


class Contract:

    def __init__(self, *args, **kwargs):
        pass


class Forex(Contract):
    pass


class Future(Contract):
    pass


class Stock(Contract):
    pass


class Order:

    def __init__(self, *args, **kwargs):
        pass


class LimitOrder(Order):
    pass


class MarketOrder(Order):
    pass


class StopOrder(Order):
    pass


class StopLimitOrder(Order):
    pass


class Option(Contract):

    def __init__(self, *args, **kwargs):
        pass


class RequestError(Exception):
    pass


class Trade:

    def __init__(self, *args, **kwargs):
        pass
