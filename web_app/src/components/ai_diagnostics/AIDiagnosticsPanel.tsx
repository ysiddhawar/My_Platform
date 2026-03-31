import { useQuery } from 'react-query';

import { endpoints } from '@/api/endpoints';
import { Panel } from '@/components/ui/Panel';

import { AIDiagnosisCard } from './AIDiagnosisCard';
import { BehavioralSignals } from './BehavioralSignals';
import { ImprovementSuggestions } from './ImprovementSuggestions';
import { WeaknessAnalysis } from './WeaknessAnalysis';

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
    },
    behavioral_signals: {
      loss_streak_length: 2,
      risk_drift: 0.08,
      strategy_switch_frequency: 0.11
    }
  };
}

export function AIDiagnosticsPanel() {
  const { data } = useQuery(
    ['ai-diagnostics'],
    () => endpoints.runDiagnostic(buildDiagnosticPayload()),
    { staleTime: 60000 }
  );

  const diagnosis = (data?.data as { diagnosis?: Record<string, unknown> } | undefined)?.diagnosis || {};
  const healthScore = typeof diagnosis.health_score === 'number' ? `${diagnosis.health_score}/100` : '84/100';
  const riskTier = typeof diagnosis.risk_tier === 'string' ? diagnosis.risk_tier : 'TIER_2';

  return (
    <Panel title="AI Diagnostics Panel" subtitle="Diagnostic findings, behaviors, and prescriptive suggestions">
      <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
        <AIDiagnosisCard title="AI Health" value={healthScore} note="Composite health from structured diagnosis." />
        <AIDiagnosisCard title="Risk Tier" value={riskTier} note="Governance-aligned diagnostic tiering." />
        <AIDiagnosisCard title="Signal Mode" value="Adaptive" note="Behavior and metric interpretation are active." />
        <AIDiagnosisCard title="Action Bias" value="Protective" note="Recommendations currently prioritize drawdown control." />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <WeaknessAnalysis
          items={[
            'Drawdown clustering remains elevated during regime transitions.',
            'Tail-risk sensitivity is higher than desired for current capital posture.'
          ]}
        />
        <BehavioralSignals
          items={[
            'Position size volatility drift detected over recent trades.',
            'Strategy switching frequency is mildly above baseline.'
          ]}
        />
        <ImprovementSuggestions
          items={[
            'Tighten spread guard during unstable volatility regimes.',
            'Reduce risk allocation by 10% until drawdown slope normalizes.'
          ]}
        />
      </div>
    </Panel>
  );
}
