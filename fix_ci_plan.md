# CI Fix Plan for PR 60

## Current Status
- Test Coverage: 71.34% (required: 80%)
- Failed tests: 398
- Main issue categories:
  1. Test coverage below 80%
  2. Backtesting engine issues
  3. Performance metrics problems
  4. Secret manager configuration issues
  5. Agent engine problems
  6. Web dashboard missing methods

## Priority Fixes

### 1. High Priority: Test Coverage Issues (71.34% → 80%)
- [ ] Add missing test coverage for backtesting.engine.py (82% coverage)
- [ ] Add missing test coverage for performance_metrics.py (48% coverage)
- [ ] Add missing test coverage for langgraph_adapter.py (46% coverage)
- [ ] Add missing test coverage for web_dashboard.py (52% coverage)
- [ ] Add missing test coverage for security.py (39% coverage)

### 2. Medium Priority: Backtesting Engine Fixes
- [ ] Fix BacktestResult missing attributes (initial_cash, total_trades, winning_trades)
- [ ] Fix MetricsResult constructor parameters
- [ ] Fix datetime comparison issues in validation functions
- [ ] Fix PositionManager methods (calculate_equity, close_position, etc.)

### 3. Medium Priority: Performance Metrics Fixes
- [ ] Fix pandas datetime operations for newer pandas version
- [ ] Fix equity curve calculation issues
- [ ] Add missing methods (_validate_insufficient_data, _validate_frequency)
- [ ] Fix trade log format expectations

### 4. Low Priority: Other Issues
- [ ] Fix secret manager mock instantiation
- [ ] Fix agent engine configuration
- [ ] Fix web dashboard missing methods
- [ ] Fix async test issues for IB connectors

## Implementation Strategy
1. Focus on test coverage first (highest impact)
2. Fix critical backtesting issues
3. Address performance metrics problems
4. Clean up remaining issues

## Success Criteria
- Test coverage ≥ 80%
- All CI checks passing
- No test regressions