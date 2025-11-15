from quantchain.backtesting.performance_metrics import PerformanceMetrics
import pandas as pd

calc = PerformanceMetrics()
eq = pd.Series([], dtype=float)
try:
    calc.calculate_total_return(eq)
except Exception as e:
    print(f"Exception type: {type(e).__name__}")
    print(f"Exception message: {e}")
