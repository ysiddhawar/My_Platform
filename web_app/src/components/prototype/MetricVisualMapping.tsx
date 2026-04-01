import { ReactNode } from 'react';
import {
  // Journal Metrics
  TradeCountIcon,
  WinCountIcon,
  LossCountIcon,
  PayoffRatioIcon,
  CostSummaryIcon,
  // Performance Metrics
  SharpeIcon,
  SortinoIcon,
  CalmarIcon,
  CAGRIcon,
  // Risk Metrics
  VolatilityIcon,
  DrawdownIcon,
  UlcerIndexIcon,
  VaRIcon,
  ConditionalVaRIcon,
  // Distribution Metrics
  SkewnessIcon,
  KurtosisIcon,
  TailRatioIcon,
  AutocorrelationIcon,
  // Portfolio Metrics
  CorrelationIcon,
  CovarianceIcon,
  DiversificationRatioIcon,
  RiskParityIcon,
  // Capital Metrics
  KellyIcon,
  PositionSizingIcon,
  CapitalEngineIcon,
  // Risk Control Metrics
  KillSwitchIcon,
  DynamicThrottleIcon,
  // Stress Metrics
  StressEngineIcon,
  LiquidityShockIcon,
  CrashSimulationIcon,
  // Survival Metrics
  FragilityScoreIcon,
  DeployableLeverageIcon,
  RiskOfRuinIcon,
  SurvivalScoreIcon,
} from './ComprehensiveMetricIcons';

export type MetricIconMap = Record<string, ReactNode>;

export const metricIconMap: MetricIconMap = {
  // Journal Metrics
  'trade_count': <TradeCountIcon />,
  'win_count': <WinCountIcon />,
  'loss_count': <LossCountIcon />,
  'win_rate': <WinCountIcon />,
  'loss_rate': <LossCountIcon />,
  'average_win': <PayoffRatioIcon />,
  'average_loss': <PayoffRatioIcon />,
  'payoff_ratio': <PayoffRatioIcon />,
  'profit_factor': <PayoffRatioIcon />,
  'expectancy': <PayoffRatioIcon />,
  'cost_summary': <CostSummaryIcon />,
  'adjusted_pnl': <CostSummaryIcon />,

  // Performance Metrics
  'sharpe': <SharpeIcon />,
  'sortino': <SortinoIcon />,
  'calmar': <CalmarIcon />,
  'cagr': <CAGRIcon />,
  'rolling_sharpe': <SharpeIcon />,
  'net_sharpe': <SharpeIcon />,
  'net_sortino': <SortinoIcon />,
  'net_cagr': <CAGRIcon />,

  // Risk Metrics
  'volatility': <VolatilityIcon />,
  'rolling_volatility': <VolatilityIcon />,
  'adaptive_rolling_volatility': <VolatilityIcon />,
  'max_drawdown': <DrawdownIcon />,
  'rolling_drawdown': <DrawdownIcon />,
  'drawdown_duration': <DrawdownIcon />,
  'ulcer_index': <UlcerIndexIcon />,
  'downside_deviation': <VolatilityIcon />,
  'value_at_risk': <VaRIcon />,
  'conditional_var': <ConditionalVaRIcon />,

  // Distribution Metrics
  'normality_test': <SkewnessIcon />,
  'skewness': <SkewnessIcon />,
  'kurtosis': <KurtosisIcon />,
  'fat_tail_index': <TailRatioIcon />,
  'tail_ratio': <TailRatioIcon />,
  'student_t_fit': <SkewnessIcon />,
  'pareto_fit': <TailRatioIcon />,
  'power_law_exponent': <TailRatioIcon />,
  'lognormal_test': <SkewnessIcon />,
  'autocorrelation': <AutocorrelationIcon />,
  'pareto_tail_estimator': <TailRatioIcon />,
  'power_law_fit': <TailRatioIcon />,

  // Regime Metrics
  'volatility_regime': <VolatilityIcon />,
  'regime_labeling': <VolatilityIcon />,
  'regime_sharpe': <SharpeIcon />,
  'regime_drawdown': <DrawdownIcon />,
  'regime_transition_matrix': <CorrelationIcon />,
  'regime_switching': <VolatilityIcon />,
  'volatility_clustering': <VolatilityIcon />,
  'garch_volatility': <VolatilityIcon />,
  'regime_breakdown': <VolatilityIcon />,
  'regime_fragility': <FragilityScoreIcon />,

  // Robustness Metrics
  'walk_forward': <StressEngineIcon />,
  'bootstrap': <StressEngineIcon />,
  'block_bootstrap': <StressEngineIcon />,
  'parameter_sensitivity': <VolatilityIcon />,
  'noise_stability': <VolatilityIcon />,
  'regime_stability': <VolatilityIcon />,
  'monte_carlo_stability': <StressEngineIcon />,
  'stability_score': <SurvivalScoreIcon />,

  // Portfolio Metrics
  'correlation': <CorrelationIcon />,
  'covariance_matrix': <CovarianceIcon />,
  'portfolio_variance': <VolatilityIcon />,
  'risk_contribution': <RiskParityIcon />,
  'risk_parity': <RiskParityIcon />,
  'target_volatility': <VolatilityIcon />,
  'drawdown_correlation': <CorrelationIcon />,
  'crash_overlap': <CrashSimulationIcon />,
  'systemic_fragility': <FragilityScoreIcon />,
  'portfolio_fragility_index': <FragilityScoreIcon />,
  'portfolio_preprocessor': <CapitalEngineIcon />,
  'diversification_ratio': <DiversificationRatioIcon />,
  'effective_number_of_bets': <DiversificationRatioIcon />,
  'hierarchical_risk_parity': <RiskParityIcon />,
  'dynamic_cluster_risk_budgeting': <RiskParityIcon />,
  'drawdown_aware_capital_allocator': <CapitalEngineIcon />,

  // Capital Metrics
  'risk_budgeting': <CapitalEngineIcon />,
  'kelly': <KellyIcon />,
  'portfolio_position_sizer': <PositionSizingIcon />,
  'position_sizer': <PositionSizingIcon />,
  'capital_engine': <CapitalEngineIcon />,

  // Risk Control Metrics
  'kill_switch': <KillSwitchIcon />,
  'dynamic_throttle': <DynamicThrottleIcon />,
  'capital_throttle_engine': <DynamicThrottleIcon />,

  // Stress Metrics
  'stress_engine': <StressEngineIcon />,
  'volatility_spike': <VolatilityIcon />,
  'liquidity_shock': <LiquidityShockIcon />,
  'correlation_spike': <CorrelationIcon />,
  'crash_simulation': <CrashSimulationIcon />,
  'stress_scenarios': <StressEngineIcon />,
  'regime_path_generator': <VolatilityIcon />,
  'spread_regime_generator': <VolatilityIcon />,
  'execution_impact_model': <LiquidityShockIcon />,

  // Survival Metrics
  'fragility_score': <FragilityScoreIcon />,
  'deployable_leverage': <DeployableLeverageIcon />,
  'kill_switch_threshold': <KillSwitchIcon />,
  'capital_throttle_policy': <DynamicThrottleIcon />,
  'drawdown_percentile': <DrawdownIcon />,
  'capital_decay': <RiskOfRuinIcon />,
  'risk_of_ruin': <RiskOfRuinIcon />,
  'ruin_probability_mc': <RiskOfRuinIcon />,
  'survival_score': <SurvivalScoreIcon />,
  'survival_engine': <SurvivalScoreIcon />,
};

export const getMetricIcon = (metricKey: string): ReactNode => {
  return metricIconMap[metricKey] || <TradeCountIcon />;
};
