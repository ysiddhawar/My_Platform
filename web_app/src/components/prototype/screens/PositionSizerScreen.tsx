import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery } from 'react-query';

import { fetchAccounts, fetchStrategies, prepareOrderTicket, previewPositionPlan, updateExecutionConfig } from '@/api/prototype';
import { StatCard } from '@/components/prototype/domain/StatCard';
import { usePrototypeStore } from '@/state/prototypeStore';
import type { StrategyRecord } from '@/types/prototype';
import { formatCurrency, formatNumber } from '@/utils/format';

const probabilityOptions = ['<40%', '40%', '50%', '60%', '>60%'];

type PlannerState = {
  account_balance: number;
  symbol: string;
  side: 'buy' | 'sell';
  entry_price: number;
  stop_loss_price: number;
  target_price: number;
  strategy_setup: string;
  probability_bucket: string;
  selected_checklist: string[];
  notes: string;
  lot_size: number;
  leverage_used: number;
};

const defaultPlannerState: PlannerState = {
  account_balance: 100000,
  symbol: 'AAPL',
  side: 'buy',
  entry_price: 184.5,
  stop_loss_price: 181.9,
  target_price: 189.8,
  strategy_setup: '',
  probability_bucket: '',
  selected_checklist: [],
  notes: '',
  lot_size: 1,
  leverage_used: 1,
};

function detectMarketType(symbol: string): string {
  const normalized = symbol.toUpperCase().trim();
  if (normalized.includes('/')) return 'forex';
  if (normalized.endsWith('USDT') || normalized.endsWith('USDTPERP') || normalized.includes('BTC') || normalized.includes('ETH')) return 'crypto';
  if (normalized.length <= 6 && /^[A-Z]+$/.test(normalized)) return 'stock';
  return 'futures';
}

export function PositionSizerScreen() {
  const accountId = usePrototypeStore((state) => state.accountId);
  const [planner, setPlanner] = useState<PlannerState>(defaultPlannerState);
  const [riskPercent, setRiskPercent] = useState(1);
  const [appDisciplineMode, setAppDisciplineMode] = useState(true);
  const [toolDisciplineMode, setToolDisciplineMode] = useState(true);
  const [activeField, setActiveField] = useState<'strategy' | 'probability' | 'checklist' | null>(null);
  const [attemptedSubmit, setAttemptedSubmit] = useState(false);
  const [mt5SyncNotice, setMt5SyncNotice] = useState<string | null>(null);

  const marketType = useMemo(() => detectMarketType(planner.symbol), [planner.symbol]);
  const { data: accounts = [] } = useQuery(['prototype-accounts'], fetchAccounts);
  const { data: strategies } = useQuery(['prototype-strategies'], fetchStrategies);
  const brokerId = useMemo(
    () => accounts.find((account) => account.account_id === accountId)?.broker_id || 'BROKER',
    [accounts, accountId],
  );

  const selectedStrategy = useMemo(
    () => (strategies || []).find((strategy) => strategy.name === planner.strategy_setup),
    [planner.strategy_setup, strategies],
  );

  useEffect(() => {
    void updateExecutionConfig({
      position_sizer: {
        max_risk_percent: riskPercent,
        app_discipline_mode_enabled: appDisciplineMode,
        position_sizer_discipline_enabled: toolDisciplineMode,
      },
    }, accountId);
  }, [riskPercent, appDisciplineMode, toolDisciplineMode, accountId]);

  const previewQuery = useQuery(
    ['prototype-position-preview', accountId, brokerId, planner, marketType, riskPercent, appDisciplineMode, toolDisciplineMode],
    () =>
      previewPositionPlan({
        account_id: accountId as string,
        broker_id: brokerId,
        market_type: marketType,
        ...planner,
      }),
    { keepPreviousData: true, enabled: Boolean(accountId) },
  );

  const proceedMutation = useMutation(
    () =>
      prepareOrderTicket({
        account_id: accountId as string,
        broker_id: brokerId,
        market_type: marketType,
        ...planner,
      }),
  );

  const disciplineEnabled = appDisciplineMode && toolDisciplineMode;
  const missingFields = disciplineEnabled
    ? [
        planner.strategy_setup ? null : 'strategy',
        planner.probability_bucket ? null : 'probability',
        planner.selected_checklist.length ? null : 'checklist',
      ].filter(Boolean)
    : [];

  const plan = (previewQuery.data?.position_plan || {}) as Record<string, unknown>;
  const disciplineState = previewQuery.data?.discipline_state;

  const setField = <K extends keyof PlannerState>(field: K, value: PlannerState[K]) => {
    setPlanner((current) => ({ ...current, [field]: value }));
  };

  const openNextField = (nextPlanner: PlannerState) => {
    if (!nextPlanner.strategy_setup) {
      setActiveField('strategy');
      return;
    }
    if (!nextPlanner.probability_bucket) {
      setActiveField('probability');
      return;
    }
    if (nextPlanner.selected_checklist.length === 0) {
      setActiveField('checklist');
      return;
    }
    setActiveField(null);
  };

  const handleProceed = () => {
    if (disciplineEnabled && missingFields.length > 0) {
      setAttemptedSubmit(true);
      setActiveField((missingFields[0] as 'strategy' | 'probability' | 'checklist') || 'strategy');
      return;
    }
    if (brokerId === 'MT5') {
      setMt5SyncNotice(
        'MT5 sync is active. Place and manage the trade in MT5 directly. MyPlatform will import historical trades plus future opens, closes, SL/TP changes, scale-ins, and partial exits automatically.',
      );
      return;
    }
    setMt5SyncNotice(null);
    proceedMutation.mutate();
  };

  return (
    <div className="space-y-8 text-black dark:text-white">
      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <section className="rounded-[26px] border border-black/10 bg-white p-6 dark:border-white/10 dark:bg-[#060606]">
          <div className="grid gap-4 md:grid-cols-2">
            <LabeledInput label="Connected Symbol" value={planner.symbol} onChange={(value) => setField('symbol', value.toUpperCase())} />
            <ReadOnlyField label="Detected Market" value={marketType} />
            <LabeledSelect label="Side" value={planner.side} onChange={(value) => setField('side', value as 'buy' | 'sell')} options={['buy', 'sell']} />
            <LabeledNumber label="Account Balance" value={planner.account_balance} onChange={(value) => setField('account_balance', value)} />
            <LabeledNumber label="Risk %" value={riskPercent} onChange={setRiskPercent} />
            <ReadOnlyField label="Risk Amount" value={formatCurrency(Number(plan.risk_amount || 0))} />
            <LabeledNumber label="Entry Line" value={planner.entry_price} onChange={(value) => setField('entry_price', value)} tone="entry" />
            <LabeledNumber label="Stop Loss Line" value={planner.stop_loss_price} onChange={(value) => setField('stop_loss_price', value)} tone="stop" />
            <LabeledNumber label="Target Line" value={planner.target_price} onChange={(value) => setField('target_price', value)} tone="target" />
            <ReadOnlyField label="Minimum Target Line" value={plan.minimum_target_price != null ? formatNumber(Number(plan.minimum_target_price)) : '—'} />
            <LabeledNumber label="Lot Size" value={planner.lot_size} onChange={(value) => setField('lot_size', value)} />
            <LabeledNumber label="Leverage Used" value={planner.leverage_used} onChange={(value) => setField('leverage_used', value)} />
          </div>

          <div className="mt-6 grid gap-4 xl:grid-cols-3">
            <FieldCard
              label="Strategy / Setup"
              value={planner.strategy_setup}
              placeholder="Select strategy"
              isMissing={attemptedSubmit && missingFields.includes('strategy')}
              onOpen={() => setActiveField('strategy')}
            >
              {activeField === 'strategy' ? (
                <div className="mt-3 space-y-2">
                  {(strategies || []).map((strategy) => (
                    <button
                      key={strategy.name}
                      type="button"
                      className="w-full rounded-[14px] border border-black/10 bg-white px-3 py-2 text-left text-sm text-black hover:border-black/25 dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white"
                      onClick={() => {
                        const nextPlanner = { ...planner, strategy_setup: strategy.name };
                        setPlanner(nextPlanner);
                        openNextField(nextPlanner);
                      }}
                    >
                      {strategy.name}
                    </button>
                  ))}
                </div>
              ) : null}
            </FieldCard>

            <FieldCard
              label="Probability"
              value={planner.probability_bucket}
              placeholder="Select probability"
              isMissing={attemptedSubmit && missingFields.includes('probability')}
              onOpen={() => setActiveField('probability')}
            >
              {activeField === 'probability' ? (
                <div className="mt-3 grid gap-2">
                  {probabilityOptions.map((option) => (
                    <button
                      key={option}
                      type="button"
                      className="rounded-[14px] border border-black/10 bg-white px-3 py-2 text-left text-sm text-black hover:border-black/25 dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white"
                      onClick={() => {
                        const nextPlanner = { ...planner, probability_bucket: option };
                        setPlanner(nextPlanner);
                        openNextField(nextPlanner);
                      }}
                    >
                      {option}
                    </button>
                  ))}
                </div>
              ) : null}
            </FieldCard>

            <FieldCard
              label="Checklist / Criteria"
              value={planner.selected_checklist.length ? `${planner.selected_checklist.length} selected` : ''}
              placeholder="Select criteria"
              isMissing={attemptedSubmit && missingFields.includes('checklist')}
              onOpen={() => setActiveField('checklist')}
            >
              {activeField === 'checklist' ? (
                <div className="mt-3 space-y-2">
                  {selectedStrategy ? (
                    (selectedStrategy.checklist_items || []).map((item) => (
                      <label
                        key={item}
                        className="flex items-center gap-3 rounded-[14px] border border-black/10 bg-white px-3 py-2 text-sm text-black dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white"
                      >
                        <input
                          type="checkbox"
                          checked={planner.selected_checklist.includes(item)}
                          onChange={() => {
                            const selected_checklist = planner.selected_checklist.includes(item)
                              ? planner.selected_checklist.filter((value) => value !== item)
                              : [...planner.selected_checklist, item];
                            const nextPlanner = { ...planner, selected_checklist };
                            setPlanner(nextPlanner);
                            openNextField(nextPlanner);
                          }}
                        />
                        <span>{item}</span>
                      </label>
                    ))
                  ) : (
                    <div className="rounded-[14px] border border-dashed border-black/15 bg-black/[0.02] px-3 py-3 text-sm text-black/75 dark:border-white/10 dark:bg-white/[0.03] dark:text-white/70">
                      Select `Strategy / Setup` first. The checklist items shown here are loaded from the selected strategy.
                    </div>
                  )}
                </div>
              ) : null}
            </FieldCard>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <ToggleRow label="App Discipline Mode" checked={appDisciplineMode} onChange={setAppDisciplineMode} />
            <ToggleRow label="Tool Discipline Mode" checked={toolDisciplineMode} onChange={setToolDisciplineMode} />
          </div>

          <label className="mt-6 block text-sm font-medium text-black dark:text-white">
            Notes
            <textarea
              className="mt-2 h-24 w-full rounded-[18px] border border-black/10 bg-white px-4 py-3 text-sm text-black outline-none dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white"
              value={planner.notes}
              onChange={(event) => setField('notes', event.target.value)}
            />
          </label>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={handleProceed}
              className={`inline-flex items-center rounded-full px-5 py-3 text-sm font-semibold ${
                disciplineEnabled && missingFields.length > 0
                  ? 'bg-rose-100 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300'
                  : 'bg-black text-white dark:bg-white dark:text-black'
              }`}
            >
              {proceedMutation.isLoading ? 'Preparing…' : 'Proceed'}
            </button>
            {attemptedSubmit && missingFields.length > 0 ? (
              <span className="text-sm text-rose-700 dark:text-rose-300">
                Complete strategy, probability, and checklist before preparing the broker ticket.
              </span>
            ) : null}
            {proceedMutation.isSuccess ? <span className="text-sm text-emerald-700 dark:text-emerald-300">Broker order ticket prepared.</span> : null}
          </div>
          {brokerId === 'MT5' ? (
            <p className="mt-3 text-sm text-black/70 dark:text-white/70">
              MT5 is connected in sync-only mode. This screen can still help you plan the trade, but execution and management stay inside MT5.
            </p>
          ) : null}
          {mt5SyncNotice ? <p className="mt-3 text-sm text-emerald-700 dark:text-emerald-300">{mt5SyncNotice}</p> : null}
          {proceedMutation.data?.launch?.message ? (
            <p className="mt-3 text-sm text-black/70 dark:text-white/70">{proceedMutation.data.launch.message}</p>
          ) : null}
          {proceedMutation.error instanceof Error ? <p className="mt-3 text-sm text-rose-700 dark:text-rose-300">{proceedMutation.error.message}</p> : null}
        </section>

        <div className="space-y-4">
          <StatCard label="Required Capital" value={formatCurrency(Number(plan.required_capital || 0))} helper="Amount required above the entry line." />
          <StatCard label="Quantity" value={formatNumber(Number(plan.quantity || 0))} helper="Calculated position size." tone="accent" />
          <StatCard label="Projected Profit" value={formatCurrency(Number(plan.reward_amount || 0))} helper="Projected reward at target." tone="success" />
          <StatCard label="Minimum Target" value={plan.minimum_target_price != null ? formatNumber(Number(plan.minimum_target_price)) : '—'} helper="Appears after discipline inputs are completed." />

          <section className="rounded-[26px] border border-black/10 bg-white p-6 dark:border-white/10 dark:bg-[#060606]">
            <h2 className="text-lg font-semibold text-black dark:text-white">Discipline State</h2>
            {previewQuery.isLoading ? <p className="mt-4 text-sm text-gray-600 dark:text-slate-400">Calculating preview…</p> : null}
            {previewQuery.error instanceof Error ? <p className="mt-4 text-sm text-rose-700 dark:text-rose-300">{previewQuery.error.message}</p> : null}
            {disciplineState ? (
              <div className="mt-4 space-y-3">
                <p className={`text-sm font-semibold ${disciplineState.blocked ? 'text-rose-700 dark:text-rose-300' : 'text-emerald-700 dark:text-emerald-300'}`}>
                  {disciplineState.blocked ? 'Blocked until required fields are filled.' : 'Ready for broker handoff.'}
                </p>
                {(disciplineState.alerts || []).map((alert) => (
                  <div key={alert} className="rounded-[16px] border border-black/8 bg-gray-50 px-4 py-3 text-sm text-black dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white">
                    {alert}
                  </div>
                ))}
              </div>
            ) : null}
          </section>
        </div>
      </section>
    </div>
  );
}

function LabeledInput({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="text-sm font-medium text-black dark:text-white">
      {label}
      <input
        className="mt-2 w-full rounded-[18px] border border-black/10 bg-white px-4 py-3 text-sm text-black outline-none dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function LabeledNumber({
  label,
  value,
  onChange,
  tone = 'default',
}: {
  label: string;
  value: number;
  onChange: (value: number) => void;
  tone?: 'default' | 'entry' | 'stop' | 'target';
}) {
  const border =
    tone === 'entry' ? 'border-sky-500/30' : tone === 'stop' ? 'border-rose-500/30' : tone === 'target' ? 'border-emerald-500/30' : 'border-black/10 dark:border-white/10';
  return (
    <label className="text-sm font-medium text-black dark:text-white">
      {label}
      <input
        className={`mt-2 w-full rounded-[18px] border bg-white px-4 py-3 text-sm text-black outline-none dark:bg-[#0b0b0b] dark:text-white ${border}`}
        type="number"
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}

function LabeledSelect({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: string[] }) {
  return (
    <label className="text-sm font-medium text-black dark:text-white">
      {label}
      <select
        className="mt-2 w-full rounded-[18px] border border-black/10 bg-white px-4 py-3 text-sm text-black outline-none dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}

function ReadOnlyField({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-sm font-medium text-black dark:text-white">
      {label}
      <div className="mt-2 rounded-[18px] border border-black/10 bg-gray-50 px-4 py-3 text-sm text-black dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white">
        {value}
      </div>
    </div>
  );
}

function FieldCard({
  label,
  value,
  placeholder,
  isMissing,
  onOpen,
  children,
}: {
  label: string;
  value: string;
  placeholder: string;
  isMissing: boolean;
  onOpen: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className={`rounded-[22px] border p-4 ${isMissing ? 'border-rose-500 bg-rose-50 dark:border-rose-400/40 dark:bg-rose-500/10' : 'border-black/10 bg-white dark:border-white/10 dark:bg-[#060606]'}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-gray-500 dark:text-slate-400">{label}</p>
          <p className="mt-2 text-sm font-medium text-black dark:text-white">{value || placeholder}</p>
        </div>
        <button type="button" onClick={onOpen} className="rounded-full border border-black/10 px-3 py-1 text-xs font-semibold text-black dark:border-white/10 dark:text-white">
          Open
        </button>
      </div>
      {isMissing ? <p className="mt-2 text-xs text-rose-700 dark:text-rose-300">Required before trade placement.</p> : null}
      {children}
    </div>
  );
}

function ToggleRow({ label, checked, onChange }: { label: string; checked: boolean; onChange: (value: boolean) => void }) {
  return (
    <label className="flex items-center justify-between rounded-[18px] border border-black/10 bg-white px-4 py-3 text-sm text-black dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white">
      <span>{label}</span>
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
    </label>
  );
}
