import { useQuery } from 'react-query';

import { endpoints } from '@/api/endpoints';
import { StatPill } from '@/components/ui/StatPill';

type MetricResults = {
  results?: Record<string, unknown>;
};

function buildPerformancePayload() {
  return {
    category: 'performance',
    data: {
      returns: [0.012, -0.004, 0.008, 0.002, -0.003, 0.011, 0.006, -0.002, 0.007, 0.005]
    },
    phase: 'research'
  };
}

function buildSurvivalPayload() {
  const alpha = [0.011, -0.004, 0.007, -0.002, 0.003, 0.008, 0.004, -0.001, 0.005, 0.002];
  const beta = [0.008, -0.003, 0.006, -0.001, 0.002, 0.007, 0.003, -0.002, 0.004, 0.001];
  const gamma = [0.009, -0.005, 0.005, -0.002, 0.004, 0.006, 0.002, -0.001, 0.006, 0.003];

  return {
    category: 'survival',
    data: {
      strategies: { alpha, beta, gamma },
      spread_matrix: [
        alpha.map(() => 0.00012),
        beta.map(() => 0.00011),
        gamma.map(() => 0.00013)
      ],
      capital: 1000000,
      total_capital: 1000000
    },
    phase: 'research'
  };
}

function buildDiagnosticPayload() {
  return {
    governance_tier: 'TIER_2',
    structured_metrics: {
      journal: {},
      performance: { net_sharpe: 1.46, net_sortino: 2.09, net_cagr: 0.18 },
      risk: { max_drawdown: 0.12, volatility: 0.18, cvar: 0.04 },
      distributions: {},
      regimes: {},
      robustness: {},
      portfolio: {},
      capital: {},
      risk_control: {},
      stress: {},
      survival: { survival_score: 0.88 }
    }
  };
}

export function SystemHealthBar() {
  const { data } = useQuery(
    ['system-health'],
    async () => {
      const [performance, survival, diagnostic, monitoring] = await Promise.allSettled([
        endpoints.runMetrics(buildPerformancePayload()),
        endpoints.runMetrics(buildSurvivalPayload()),
        endpoints.runDiagnostic(buildDiagnosticPayload()),
        endpoints.getMonitoringSnapshot()
      ]);

      return { performance, survival, diagnostic, monitoring };
    },
    {
      staleTime: 60000
    }
  );

  const perf =
    data?.performance.status === 'fulfilled'
      ? ((data.performance.value.data as MetricResults).results || {})
      : {};

  const survival =
    data?.survival.status === 'fulfilled'
      ? ((data.survival.value.data as MetricResults).results || {})
      : {};

  const diagnosis =
    data?.diagnostic.status === 'fulfilled'
      ? ((data.diagnostic.value.data as { diagnosis?: Record<string, unknown> }).diagnosis || {})
      : {};

  const monitoring =
    data?.monitoring.status === 'fulfilled'
      ? ((data.monitoring.value.data as { data?: Record<string, unknown> }).data || {})
      : {};

  const netPnL = '$28,430';
  const winRate = '62%';
  const maxDrawdown = typeof perf.max_drawdown === 'number' ? `${(perf.max_drawdown * 100).toFixed(1)}%` : '12.0%';
  const aiHealth = typeof diagnosis.health_score === 'number' ? `${diagnosis.health_score}/100` : '84/100';
  const survivalScore =
    typeof survival.survival_score === 'number'
      ? `${(survival.survival_score * 100).toFixed(0)}%`
      : typeof (survival.survival_engine as Record<string, unknown> | undefined)?.deployable_survival_score ===
          'number'
        ? `${(((survival.survival_engine as Record<string, number>).deployable_survival_score || 0) * 100).toFixed(0)}%`
        : '88%';
  const capitalStatus = monitoring.monitoring_registry ? 'Stable' : 'Nominal';

  return (
    <div className="grid gap-3 rounded-2xl border border-slate-800/70 bg-[#08111a]/90 p-3 shadow-panel sm:grid-cols-2 xl:grid-cols-6">
      <StatPill label="NetPnL" value={netPnL} tone="positive" />
      <StatPill label="WinRate" value={winRate} tone="positive" />
      <StatPill label="MaxDrawdown" value={maxDrawdown} tone="warning" />
      <StatPill label="AIHealthScore" value={aiHealth} tone="normal" />
      <StatPill label="CapitalStatus" value={capitalStatus} tone="normal" />
      <StatPill label="SurvivalScore" value={survivalScore} tone="positive" />
    </div>
  );
}
