#!/usr/bin/env python3
"""Fix BacktestResult class to add missing properties."""

def fix_backtest_result():
    """Add missing properties to BacktestResult class."""
    file_path = r"C:\Users\ancha\Documents\projects\QuantChain\quantchain\backtesting\engine.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the BacktestResult class and add properties
    old_code = "        if not isinstance(self.config, BacktestConfig):\n            raise ValueError(\"config must be a BacktestConfig instance\")"
    
    new_code = "        if not isinstance(self.config, BacktestConfig):\n            raise ValueError(\"config must be a BacktestConfig instance\")\n\n    @property\n    def initial_cash(self) -> float:\n        \"\"\"Get initial cash from config.\"\"\"\n        return self.config.initial_cash\n\n    @property\n    def total_trades(self) -> int:\n        \"\"\"Get total number of trades.\"\"\"\n        return len(self.trade_log) if self.trade_log is not None else 0\n\n    @property\n    def winning_trades(self) -> int:\n        \"\"\"Get number of winning trades.\"\"\"\n        if self.trade_log is None or len(self.trade_log) == 0:\n            return 0\n        if 'pnl' in self.trade_log.columns:\n            return (self.trade_log['pnl'] > 0).sum()\n        return 0\n\n    @property\n    def losing_trades(self) -> int:\n        \"\"\"Get number of losing trades.\"\"\"\n        if self.trade_log is None or len(self.trade_log) == 0:\n            return 0\n        if 'pnl' in self.trade_log.columns:\n            return (self.trade_log['pnl'] < 0).sum()\n        return self.total_trades - self.winning_trades"
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        
        with open(file_path, 'w') as f:
            f.write(content)
        print("Successfully updated BacktestResult class")
    else:
        print("Could not find the target code to replace")

if __name__ == "__main__":
    fix_backtest_result()