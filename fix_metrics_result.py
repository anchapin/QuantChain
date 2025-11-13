import re

def fix_metrics_result():
    file_path = r"C:\Users\ancha\Documents\projects\QuantChain\quantchain\backtesting\engine.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find MetricsResult class and fix missing avg_trade field and add default values
    # Pattern to match the class definition up to avg_loss
    pattern1 = r'(class MetricsResult:.*?\n    """Performance metrics from backtest."""\n\n    total_return: float\n    annualized_return: float\n    sharpe_ratio: float\n    sortino_ratio: float\n    calmar_ratio: float\n    max_drawdown: float\n    max_drawdown_duration: int\n    max_drawdown_start: Optional\[datetime\] = None\n    max_drawdown_end: Optional\[datetime\] = None\n    volatility: float = 0\.0\n    win_rate: float = 0\.0\n    profit_factor: float = 0\.0\n    total_trades: int = 0\n    winning_trades: int = 0\n    losing_trades: int = 0\n    avg_win: float = 0\.0\n    avg_loss: float = 0\.0\n    best_trade: float = 0\.0\n    worst_trade: float = 0\.0\n    avg_trade_duration: float = 0\.0\n    avg_trade_duration_days: float = 0\.0)'
    
    # Replacement with avg_trade added and default values for all fields
    replacement = r'    total_return: float = 0.0\n    annualized_return: float = 0.0\n    sharpe_ratio: float = 0.0\n    sortino_ratio: float = 0.0\n    calmar_ratio: float = 0.0\n    max_drawdown: float = 0.0\n    max_drawdown_duration: int = 0\n    max_drawdown_start: Optional\[datetime\] = None\n    max_drawdown_end: Optional\[datetime\] = None\n    volatility: float = 0\.0\n    win_rate: float = 0\.0\n    profit_factor: float = 0\.0\n    total_trades: int = 0\n    winning_trades: int = 0\n    losing_trades: int = 0\n    avg_win: float = 0\.0\n    avg_loss: float = 0\.0\n    best_trade: float = 0\.0\n    worst_trade: float = 0\.0\n    avg_trade: float = 0\.0\n    avg_trade_duration: float = 0\.0\n    avg_trade_duration_days: float = 0\.0'
    
    if re.search(pattern1, content, re.MULTILINE):
        content = re.sub(pattern1, replacement, content)
        print("Successfully updated MetricsResult class")
        with open(file_path, 'w') as f:
            f.write(content)
    else:
        print("Could not find MetricsResult class definition")
        return False
    
    return True

if __name__ == "__main__":
    fix_metrics_result()