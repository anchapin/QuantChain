# Stub package for ib_async


import sys


class IB:
    def __init__(self):
        self.errorEvent = None
        self.orderStatusEvent = None
        self.updatePortfolioEvent = None
        self.positionEvent = None
        self.accountValueEvent = None
        self.contractDetailsEvent = None

    async def connectAsync(self, host, port, clientId, timeout=10):
        pass

    def disconnect(self):
        pass

    def isConnected(self):
        return False

    async def placeOrderAsync(self, contract, order):
        pass

    async def cancelOrderAsync(self, order):
        pass

    async def positionsAsync(self):
        return []

    async def accountSummaryAsync(self):
        return []

    async def ibkrAccountSummaryAsync(self):
        return []

    async def reqHistoricalDataAsync(self, *args, **kwargs):
        return []

    async def reqMktDataAsync(self, *args, **kwargs):
        pass

    async def reqContractDetailsAsync(self, contract):
        return []

    async def qualifyContractsAsync(self, contract):
        return []

    def openTrades(self):
        return []


class Contract:
    def __init__(self, symbol="", secType="", exchange="", currency="", **kwargs):
        self.symbol = symbol
        self.secType = secType
        self.exchange = exchange
        self.currency = currency
        for k, v in kwargs.items():
            setattr(self, k, v)


class Forex(Contract):
    pass


class Future(Contract):
    pass


class LimitOrder:
    pass


class MarketOrder:
    pass


class Option(Contract):
    pass


class Order:
    def __init__(self, action="", orderType="", totalQuantity=0, **kwargs):
        self.action = action
        self.orderType = orderType
        self.totalQuantity = totalQuantity
        self.permId = 0
        self.lmtPrice = 0.0
        self.auxPrice = 0.0
        for k, v in kwargs.items():
            setattr(self, k, v)


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
    contract = None
    order = None
    orderStatus = None
    fills = None
    log = None
    filled = 0.0
    remaining = 0.0
    avgFillPrice = 0.0

    def __init__(
        self, contract=None, order=None, orderStatus=None, fills=None, log=None
    ):
        self.contract = contract or Contract()
        self.order = order or Order()
        self.orderStatus = orderStatus
        self.fills = fills or []
        self.log = log or []
        self.filled = 0.0
        self.remaining = 0.0
        self.avgFillPrice = 0.0


class PortfolioItem:
    def __init__(self):
        self.contract = Contract()
        self.position = 0.0
        self.marketPrice = 0.0
        self.marketValue = 0.0
        self.averageCost = 0.0
        self.unrealizedPNL = 0.0
        self.realizedPNL = 0.0
        self.account = ""


class Position:
    def __init__(self, account="", contract=None, position=0.0, avgCost=0.0):
        self.account = account
        self.contract = contract or Contract()
        self.position = position
        self.avgCost = avgCost


# Prevent real ib_async from being imported
sys.modules["ib_async"] = sys.modules[__name__]
