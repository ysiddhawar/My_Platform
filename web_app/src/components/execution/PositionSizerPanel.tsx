import type { ReactNode } from 'react';
import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery } from 'react-query';

import { endpoints } from '@/api/endpoints';
import { Panel } from '@/components/ui/Panel';
import { StatPill } from '@/components/ui/StatPill';

const probabilityOptions = ['<40%', '40%', '50%', '60%', '>60%'];
const marketOptions = ['stock', 'forex', 'crypto', 'futures', 'options'];

type StrategyRecord = {
  name: string;
  checklist_items: string[];
  mandatory_checklist_items: string[];
};

type PlannerState = {
  account_balance: number;
  symbol: string;
  market_type: string;
  side: 'buy' | 'sell';
  entry_price: number;
  stop_loss_price: number;
  target_price: number;
  strategy_setup: string;
  probability_bucket: string;
  selected_checklist: string[];
  notes: string;
};

const defaultPlannerState: PlannerState = {
  account_balance: 100000,
  symbol: 'EURUSD',
  market_type: 'forex',
  side: 'buy',
  entry_price: 1.1,
  stop_loss_price: 1.095,
  target_price: 1.11,
  strategy_setup: '',
  probability_bucket: '',
  selected_checklist: [],
  notes: '',
};

export function PositionSizerPanel() {
  const [planner, setPlanner] = useState<PlannerState>(defaultPlannerState);
  const [appDisciplineMode, setAppDisciplineMode] = useState(true);
  const [toolDisciplineMode, setToolDisciplineMode] = useState(true);
  const [activeField, setActiveField] = useState<'strategy' | 'probability' | 'checklist' | null>(null);
  const [attemptedSubmit, setAttemptedSubmit] = useState(false);

  const { data: strategyData } = useQuery('strategies', async () => {
    const response = await endpoints.listStrategies();
    return (response.data?.strategies || []) as StrategyRecord[];
  });

  const strategies = strategyData || [];
  const selectedStrategy = useMemo(
    () => strategies.find((strategy) => strategy.name === planner.strategy_setup),
    [planner.strategy_setup, strategies]
  );

  useEffect(() => {
    if (!selectedStrategy) {
      return;
    }
    setPlanner((current) => ({
      ...current,
      selected_checklist: current.selected_checklist.filter((item) =>
        selectedStrategy.checklist_items.includes(item)
      )
    }));
  }, [selectedStrategy]);

  const previewQuery = useQuery(
    ['position-preview', planner, appDisciplineMode, toolDisciplineMode],
    async () => {
      const response = await endpoints.previewTrade({
        ...planner,
        selected_checklist: planner.selected_checklist,
      });
      return response.data?.result || {};
    },
    { keepPreviousData: true }
  );

  const updateConfigMutation = useMutation(async (payload: { appEnabled: boolean; toolEnabled: boolean }) => {
    return endpoints.updateExecutionConfig({
      config: {
        position_sizer: {
          app_discipline_mode_enabled: payload.appEnabled,
          position_sizer_discipline_enabled: payload.toolEnabled,
        }
      }
    });
  });

  const proceedMutation = useMutation(async () => {
    return endpoints.prepareOrderTicket({
      ...planner,
      selected_checklist: planner.selected_checklist,
    });
  });

  const plan = previewQuery.data?.position_plan;
  const disciplineState = previewQuery.data?.discipline_state;
  const disciplineEnabled = Boolean(appDisciplineMode && toolDisciplineMode);
  const missingFields = disciplineEnabled
    ? [
        planner.strategy_setup ? null : 'strategy',
        planner.probability_bucket ? null : 'probability',
        planner.selected_checklist.length ? null : 'checklist',
      ].filter(Boolean)
    : [];

  const setField = <K extends keyof PlannerState>(field: K, value: PlannerState[K]) => {
    setPlanner((current) => ({ ...current, [field]: value }));
  };

  const handleProbabilitySelect = (value: string) => {
    setField('probability_bucket', value);
    setActiveField(planner.selected_checklist.length ? null : 'checklist');
  };

  const handleStrategySelect = (value: string) => {
    setField('strategy_setup', value);
    setActiveField(planner.probability_bucket ? 'checklist' : 'probability');
  };

  const handleChecklistToggle = (item: string) => {
    setPlanner((current) => ({
      ...current,
      selected_checklist: current.selected_checklist.includes(item)
        ? current.selected_checklist.filter((value) => value !== item)
        : [...current.selected_checklist, item]
    }));
  };

  const handleSelectAllChecklist = () => {
    if (!selectedStrategy) {
      return;
    }
    setField('selected_checklist', selectedStrategy.checklist_items);
  };

  const handleToggleDiscipline = (kind: 'app' | 'tool', checked: boolean) => {
    if (kind === 'app') {
      setAppDisciplineMode(checked);
      updateConfigMutation.mutate({ appEnabled: checked, toolEnabled: toolDisciplineMode });
      return;
    }
    setToolDisciplineMode(checked);
    updateConfigMutation.mutate({ appEnabled: appDisciplineMode, toolEnabled: checked });
  };

  const handleProceed = () => {
    if (disciplineEnabled && missingFields.length > 0) {
      setAttemptedSubmit(true);
      setActiveField((missingFields[0] as 'strategy' | 'probability' | 'checklist') || 'strategy');
      return;
    }
    proceedMutation.mutate();
  };

  const checklistAllSelected = selectedStrategy
    ? selectedStrategy.mandatory_checklist_items.length > 0 &&
      selectedStrategy.mandatory_checklist_items.every((item) => planner.selected_checklist.includes(item))
    : false;

  return (
    <Panel title="Unified Position Sizer" subtitle="Live trade planning, discipline capture, and broker handoff gating" className="h-full">
      <div className="space-y-5">
        <div className="grid gap-3 lg:grid-cols-3">
          <label className="text-sm text-slate-300">
            Symbol
            <input className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={planner.symbol} onChange={(event) => setField('symbol', event.target.value.toUpperCase())} />
          </label>
          <label className="text-sm text-slate-300">
            Market
            <select className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={planner.market_type} onChange={(event) => setField('market_type', event.target.value)}>
              {marketOptions.map((market) => <option key={market} value={market}>{market}</option>)}
            </select>
          </label>
          <label className="text-sm text-slate-300">
            Side
            <select className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={planner.side} onChange={(event) => setField('side', event.target.value as 'buy' | 'sell')}>
              <option value="buy">Buy</option>
              <option value="sell">Sell</option>
            </select>
          </label>
          <label className="text-sm text-slate-300">
            Account Balance
            <input className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" type="number" value={planner.account_balance} onChange={(event) => setField('account_balance', Number(event.target.value))} />
          </label>
          <label className="text-sm text-slate-300">
            Entry Price
            <input className="mt-2 w-full rounded-xl border border-sky-700/80 bg-slate-950 px-3 py-2 text-sky-100" type="number" value={planner.entry_price} onChange={(event) => setField('entry_price', Number(event.target.value))} />
          </label>
          <label className="text-sm text-slate-300">
            Stop Loss
            <input className="mt-2 w-full rounded-xl border border-rose-700/80 bg-slate-950 px-3 py-2 text-rose-100" type="number" value={planner.stop_loss_price} onChange={(event) => setField('stop_loss_price', Number(event.target.value))} />
          </label>
          <label className="text-sm text-slate-300">
            Target
            <input className="mt-2 w-full rounded-xl border border-emerald-700/80 bg-slate-950 px-3 py-2 text-emerald-100" type="number" value={planner.target_price} onChange={(event) => setField('target_price', Number(event.target.value))} />
          </label>
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-sm text-slate-300">
            <p className="text-xs uppercase tracking-[0.2em] text-slate-500">Discipline Mode</p>
            <label className="mt-3 flex items-center justify-between gap-3">
              <span>App level</span>
              <input type="checkbox" checked={appDisciplineMode} onChange={(event) => handleToggleDiscipline('app', event.target.checked)} />
            </label>
            <label className="mt-2 flex items-center justify-between gap-3">
              <span>Position sizer</span>
              <input type="checkbox" checked={toolDisciplineMode} onChange={(event) => handleToggleDiscipline('tool', event.target.checked)} />
            </label>
          </div>
          <label className="text-sm text-slate-300">
            Notes
            <textarea className="mt-2 h-[92px] w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={planner.notes} onChange={(event) => setField('notes', event.target.value)} />
          </label>
        </div>

        <div className="grid gap-4 xl:grid-cols-3">
          <FieldCard
            label="Strategy / Setup"
            value={planner.strategy_setup}
            placeholder="Choose setup"
            isRequired={disciplineEnabled}
            isMissing={attemptedSubmit && missingFields.includes('strategy')}
            onOpen={() => setActiveField('strategy')}
          >
            {activeField === 'strategy' && (
              <div className="mt-3 space-y-2">
                {strategies.length === 0 ? <p className="text-sm text-amber-300">Create strategies on the Discipline page first.</p> : null}
                {strategies.map((strategy) => (
                  <button key={strategy.name} className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-left text-sm text-slate-100 hover:border-teal-500" onClick={() => handleStrategySelect(strategy.name)}>
                    <span className="font-semibold">{strategy.name}</span>
                    <span className="block text-xs text-slate-400">{strategy.checklist_items.length} criteria</span>
                  </button>
                ))}
              </div>
            )}
          </FieldCard>

          <FieldCard
            label="Probability"
            value={planner.probability_bucket}
            placeholder="Choose probability"
            isRequired={disciplineEnabled}
            isMissing={attemptedSubmit && missingFields.includes('probability')}
            onOpen={() => setActiveField('probability')}
          >
            {activeField === 'probability' && (
              <div className="mt-3 grid gap-2">
                {probabilityOptions.map((option) => (
                  <button key={option} className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-left text-sm text-slate-100 hover:border-amber-400" onClick={() => handleProbabilitySelect(option)}>
                    {option}
                  </button>
                ))}
              </div>
            )}
          </FieldCard>

          <FieldCard
            label="Checklist / Criteria"
            value={planner.selected_checklist.length ? `${planner.selected_checklist.length} selected` : ''}
            placeholder="Select checklist items"
            isRequired={disciplineEnabled}
            isMissing={attemptedSubmit && missingFields.includes('checklist')}
            onOpen={() => setActiveField('checklist')}
          >
            {activeField === 'checklist' && (
              <div className="mt-3 space-y-3">
                <button className="rounded-lg border border-teal-800 bg-teal-950/40 px-3 py-2 text-sm font-semibold text-teal-200" onClick={handleSelectAllChecklist}>
                  Select All
                </button>
                <div className="space-y-2">
                  {(selectedStrategy?.checklist_items || []).map((item) => (
                    <label key={item} className="flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-950/60 px-3 py-2 text-sm text-slate-200">
                      <input type="checkbox" checked={planner.selected_checklist.includes(item)} onChange={() => handleChecklistToggle(item)} />
                      <span className={selectedStrategy?.mandatory_checklist_items.includes(item) ? 'font-semibold text-white' : ''}>{item}</span>
                    </label>
                  ))}
                  {!selectedStrategy ? <p className="text-sm text-slate-500">Select a strategy/setup to load its criteria.</p> : null}
                </div>
              </div>
            )}
          </FieldCard>
        </div>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <StatPill label="Entry Line" value={plan ? `${plan.required_capital.toFixed(2)} capital` : '--'} tone="normal" />
          <StatPill label="Stop Loss" value={plan ? `${plan.risk_amount.toFixed(2)} risk` : '--'} tone="danger" />
          <StatPill label="Target" value={plan ? `${plan.reward_amount.toFixed(2)} reward` : '--'} tone="positive" />
          <StatPill label="Minimum Target" value={plan?.minimum_target_price ? `${Number(plan.minimum_target_price).toFixed(4)}` : 'Awaiting probability'} tone="warning" />
        </div>

        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          <LineInfo colorClass="bg-sky-400" title="Entry Line" detail={plan ? `Capital ${plan.required_capital.toFixed(2)} including margin logic` : 'Waiting for valid prices'} />
          <LineInfo colorClass="bg-rose-400" title="Stop Loss Line" detail={plan ? `Risk ${plan.risk_amount.toFixed(2)} with brokerage/slippage considered` : 'Waiting for valid prices'} />
          <LineInfo colorClass="bg-emerald-400" title="Target Line" detail={plan ? `Projected reward ${plan.reward_amount.toFixed(2)}` : 'Waiting for target price'} />
          <LineInfo colorClass="bg-amber-400" title="Minimum Target Line" detail={plan?.minimum_target_price ? `Required price ${Number(plan.minimum_target_price).toFixed(4)} | reward ${Number(plan.minimum_target_reward || 0).toFixed(2)}` : 'Visible after strategy, probability, and checklist are selected'} />
          <LineInfo colorClass="bg-fuchsia-400" title="Checklist State" detail={disciplineEnabled ? (checklistAllSelected ? 'All mandatory criteria selected' : 'Broker ticket allowed, but incomplete checklist will be recorded for AI') : 'Discipline mode disabled'} />
          <LineInfo colorClass="bg-cyan-400" title="Engine Alerts" detail={(disciplineState?.alerts || []).join(' ') || 'No active broker handoff alerts'} />
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            className={`rounded-xl px-4 py-2 text-sm font-semibold text-white ${disciplineEnabled && missingFields.length ? 'cursor-not-allowed bg-slate-700' : 'bg-accent hover:bg-teal-500'}`}
            onClick={handleProceed}
          >
            {proceedMutation.isLoading ? 'Preparing Ticket...' : 'Proceed'}
          </button>
          {proceedMutation.data?.data?.result?.status === 'ready' ? (
            <span className="text-xs text-slate-400">Broker order ticket prepared.</span>
          ) : null}
          {attemptedSubmit && missingFields.length > 0 ? (
            <p className="text-sm text-rose-300">Complete strategy/setup, probability, and checklist selection before preparing the broker ticket.</p>
          ) : null}
          {proceedMutation.data?.data?.result?.launch?.message ? (
            <p className="text-sm text-slate-400">{proceedMutation.data.data.result.launch.message}</p>
          ) : null}
        </div>
      </div>
    </Panel>
  );
}

function FieldCard({
  label,
  value,
  placeholder,
  isRequired,
  isMissing,
  onOpen,
  children,
}: {
  label: string;
  value: string;
  placeholder: string;
  isRequired: boolean;
  isMissing: boolean;
  onOpen: () => void;
  children: ReactNode;
}) {
  return (
    <div className={`rounded-2xl border p-4 ${isMissing ? 'animate-pulse border-rose-500 bg-rose-950/30' : 'border-slate-800 bg-slate-950/60'}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{label}</p>
          <p className={`mt-2 text-sm ${value ? 'font-semibold text-white' : 'text-slate-400'}`}>{value || placeholder}</p>
        </div>
        <button className="rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-200" onClick={onOpen}>
          {isRequired ? 'Required' : 'Open'}
        </button>
      </div>
      {isMissing ? <p className="mt-2 text-xs font-semibold text-rose-300">Required before the trade button can be used.</p> : null}
      {children}
    </div>
  );
}

function LineInfo({ colorClass, title, detail }: { colorClass: string; title: string; detail: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
      <div className="mb-2 flex items-center gap-3">
        <span className={`h-1.5 w-10 rounded-full ${colorClass}`} />
        <p className="text-sm font-semibold text-white">{title}</p>
      </div>
      <p className="text-sm text-slate-400">{detail}</p>
    </div>
  );
}
