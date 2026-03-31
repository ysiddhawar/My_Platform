import { useMemo, useState } from 'react';

import type { AccountIntegration, AccountSummary, CreateAccountInput, Mt5FileBridgeInput } from '@/types/prototype';

type AccountPickerModalProps = {
  accounts: AccountSummary[];
  integrations: AccountIntegration[];
  selectedAccountId: string | null;
  onSelect: (accountId: string) => void;
  onClose?: () => void;
  onCreateAccount: (payload: CreateAccountInput) => Promise<AccountSummary>;
  onConnectMt5: (payload: Mt5FileBridgeInput) => Promise<void>;
  onValidateMt5: (payload: { inbox_dir: string; archive_dir?: string }) => Promise<{
    ok: boolean;
    inbox_dir: string;
    archive_dir: string;
    inbox_exists: boolean;
    archive_exists: boolean;
    inbox_writable: boolean;
    archive_writable: boolean;
    warnings: string[];
    instructions: string[];
  }>;
  onCreateDemoAccount: (payload: { account_id: string; broker_id: string; account_name: string }) => Promise<void>;
  open: boolean;
};

const brokerOptions = ['MT5', 'Binance', 'Interactive Brokers', 'Simulated'];

export function AccountPickerModal({
  accounts,
  integrations,
  selectedAccountId,
  onSelect,
  onClose,
  onCreateAccount,
  onConnectMt5,
  onValidateMt5,
  onCreateDemoAccount,
  open,
}: AccountPickerModalProps) {
  const [mode, setMode] = useState<'browse' | 'create'>('browse');
  const [form, setForm] = useState<CreateAccountInput>({
    account_name: '',
    broker_id: 'MT5',
    initial_balance: 100000,
    risk_level: 'survival',
    base_currency: 'USD',
    supported_market_types: ['stock', 'forex', 'crypto', 'futures'],
    timezone_name: 'Asia/Kolkata',
    auto_connect_simulated: true,
  });
  const [demoSeed, setDemoSeed] = useState({
    account_id: 'DEFAULT',
    broker_id: 'BROKER',
    account_name: 'Prototype Workspace',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionMode, setConnectionMode] = useState<'simulated' | 'mt5_file_bridge'>('simulated');
  const [mt5Config, setMt5Config] = useState({
    inbox_dir: '',
    archive_dir: '',
    poll_interval_seconds: '0.25',
  });
  const [mt5Validation, setMt5Validation] = useState<{
    ok: boolean;
    inbox_dir: string;
    archive_dir: string;
    inbox_exists: boolean;
    archive_exists: boolean;
    inbox_writable: boolean;
    archive_writable: boolean;
    warnings: string[];
    instructions: string[];
  } | null>(null);

  const integrationByAccount = useMemo(
    () => new Map(integrations.map((item) => [item.account_id, item])),
    [integrations],
  );

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 px-4 backdrop-blur-sm">
      <div className="max-h-[88vh] w-full max-w-5xl overflow-y-auto rounded-[28px] border border-black/10 bg-white p-6 shadow-[0_30px_80px_rgba(15,23,42,0.18)] dark:border-white/10 dark:bg-[#060606]">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-black/55 dark:text-white/55">Accounts</p>
            <h2 className="mt-2 text-[1.8rem] font-semibold tracking-[-0.04em] text-black dark:text-white">
              Select, create, or seed an account
            </h2>
            <p className="mt-2 text-sm text-black/70 dark:text-white/70">
              The workspace stays visible. Data-heavy sections load once an account is selected.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setMode('browse')}
              className={`rounded-full px-4 py-2 text-sm font-semibold ${
                mode === 'browse'
                  ? 'bg-black text-white dark:bg-white dark:text-black'
                  : 'border border-black/10 text-black dark:border-white/10 dark:text-white'
              }`}
            >
              Browse
            </button>
            <button
              type="button"
              onClick={() => setMode('create')}
              className={`rounded-full px-4 py-2 text-sm font-semibold ${
                mode === 'create'
                  ? 'bg-black text-white dark:bg-white dark:text-black'
                  : 'border border-black/10 text-black dark:border-white/10 dark:text-white'
              }`}
            >
              Add Account
            </button>
            {onClose ? (
              <button type="button" onClick={onClose} className="rounded-full border border-black/10 px-4 py-2 text-sm font-semibold text-black dark:border-white/10 dark:text-white">
                Close
              </button>
            ) : null}
          </div>
        </div>

        {mode === 'browse' ? (
          <div className="mt-6 space-y-6">
            <section>
              <div className="grid gap-4 md:grid-cols-2">
                {accounts.map((account) => {
                  const isActive = account.account_id === selectedAccountId;
                  const integration = integrationByAccount.get(account.account_id);
                  return (
                    <button
                      key={account.account_id}
                      type="button"
                      onClick={() => onSelect(account.account_id)}
                      className={`rounded-[22px] border px-5 py-5 text-left transition ${
                        isActive
                          ? 'border-black bg-black text-white dark:border-[#6a5cff] dark:bg-[#101225]'
                          : 'border-black/10 bg-white text-black hover:border-black/20 dark:border-white/10 dark:bg-[#0a0a0a] dark:text-white dark:hover:border-white/20'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-base font-semibold">{account.account_name || account.account_id}</div>
                        <span className={`rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] ${isActive ? 'bg-white/12 text-white' : 'bg-black/5 text-black/70 dark:bg-white/10 dark:text-white/70'}`}>
                          {account.account_id}
                        </span>
                      </div>
                      <div className={`mt-3 text-sm ${isActive ? 'text-white/75' : 'text-black/65 dark:text-white/65'}`}>
                        {account.broker_id || 'Broker'} · {account.base_currency || 'USD'} · {account.risk_level || 'survival'}
                      </div>
                      <div className={`mt-2 text-xs ${isActive ? 'text-white/65' : 'text-black/55 dark:text-white/55'}`}>
                        Markets: {(account.supported_market_types || []).join(', ') || 'Not specified'}
                      </div>
                      <div className={`mt-3 text-xs font-semibold uppercase tracking-[0.18em] ${isActive ? 'text-white/70' : 'text-black/50 dark:text-white/50'}`}>
                        {integration?.connected ? `${integration.adapter_type || 'adapter'} connected` : 'Not connected'}
                      </div>
                    </button>
                  );
                })}
              </div>
            </section>

            <section className="rounded-[22px] border border-dashed border-black/12 bg-black/[0.02] p-5 dark:border-white/12 dark:bg-white/[0.03]">
              <p className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-black/50 dark:text-white/50">Fast Demo</p>
              <h3 className="mt-2 text-xl font-semibold text-black dark:text-white">Create a reviewable demo account with seeded data</h3>
              <div className="mt-4 grid gap-3 md:grid-cols-3">
                <Input label="Account ID" value={demoSeed.account_id} onChange={(value) => setDemoSeed((current) => ({ ...current, account_id: value.toUpperCase() }))} />
                <Input label="Broker ID" value={demoSeed.broker_id} onChange={(value) => setDemoSeed((current) => ({ ...current, broker_id: value }))} />
                <Input label="Account Name" value={demoSeed.account_name} onChange={(value) => setDemoSeed((current) => ({ ...current, account_name: value }))} />
              </div>
              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={async () => {
                    setError(null);
                    setIsSubmitting(true);
                    try {
                      await onCreateDemoAccount(demoSeed);
                      setMode('browse');
                    } catch (createError) {
                      setError(createError instanceof Error ? createError.message : 'Failed to seed demo account');
                    } finally {
                      setIsSubmitting(false);
                    }
                  }}
                  className="rounded-full bg-black px-5 py-3 text-sm font-semibold text-white dark:bg-white dark:text-black"
                >
                  {isSubmitting ? 'Creating…' : 'Create Demo Account'}
                </button>
              </div>
            </section>
          </div>
        ) : (
          <div className="mt-6 space-y-5">
            <div className="grid gap-4 md:grid-cols-2">
              <Input label="Account Name" value={form.account_name || ''} onChange={(value) => setForm((current) => ({ ...current, account_name: value }))} />
              <Input label="Account ID (optional)" value={form.account_id || ''} onChange={(value) => setForm((current) => ({ ...current, account_id: value.toUpperCase() || undefined }))} />
              <Select label="Broker" value={form.broker_id} options={brokerOptions} onChange={(value) => setForm((current) => ({ ...current, broker_id: value }))} />
              <Input
                label="Initial Balance"
                value={String(form.initial_balance || 100000)}
                onChange={(value) => setForm((current) => ({ ...current, initial_balance: Number(value || 0) }))}
                type="number"
              />
              <Select label="Risk Level" value={form.risk_level || 'survival'} options={['survival', 'consistency', 'profitable']} onChange={(value) => setForm((current) => ({ ...current, risk_level: value }))} />
              <Input label="Base Currency" value={form.base_currency || 'USD'} onChange={(value) => setForm((current) => ({ ...current, base_currency: value.toUpperCase() }))} />
            </div>

            <label className="flex items-center gap-3 text-sm text-black/75 dark:text-white/75">
              <input
                type="checkbox"
                checked={connectionMode === 'simulated'}
                onChange={(event) => {
                  const nextMode = event.target.checked ? 'simulated' : 'mt5_file_bridge';
                  setConnectionMode(nextMode);
                  setForm((current) => ({ ...current, auto_connect_simulated: nextMode === 'simulated' }));
                }}
              />
              Use simulated broker connection
            </label>

            {connectionMode === 'mt5_file_bridge' ? (
              <div className="space-y-4">
                <div className="rounded-[22px] border border-black/10 bg-black/[0.02] p-4 dark:border-white/10 dark:bg-white/[0.03]">
                  <p className="text-[0.72rem] font-semibold uppercase tracking-[0.18em] text-black/55 dark:text-white/55">MT5 Bridge Setup</p>
                  <h4 className="mt-2 text-base font-semibold text-black dark:text-white">How this works</h4>
                  <ol className="mt-3 space-y-2 text-sm leading-6 text-black/70 dark:text-white/70">
                    <li>1. Point your MT5 exporter or EA to a local inbox directory.</li>
                    <li>2. MyPlatform watches that inbox for JSON trade-event files.</li>
                    <li>3. Processed files move into the archive directory so they are not replayed.</li>
                    <li>4. Use Validate before saving to confirm the paths are usable on this machine.</li>
                  </ol>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <Input label="MT5 Inbox Directory" value={mt5Config.inbox_dir} onChange={(value) => setMt5Config((current) => ({ ...current, inbox_dir: value }))} />
                  <Input label="MT5 Archive Directory" value={mt5Config.archive_dir} onChange={(value) => setMt5Config((current) => ({ ...current, archive_dir: value }))} />
                </div>
                <Input
                  label="Poll Interval Seconds"
                  value={mt5Config.poll_interval_seconds}
                  onChange={(value) => setMt5Config((current) => ({ ...current, poll_interval_seconds: value }))}
                  type="number"
                />
                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={async () => {
                      setError(null);
                      try {
                        const result = await onValidateMt5({
                          inbox_dir: mt5Config.inbox_dir,
                          archive_dir: mt5Config.archive_dir || undefined,
                        });
                        setMt5Validation(result);
                      } catch (validationError) {
                        setError(validationError instanceof Error ? validationError.message : 'Failed to validate MT5 directories');
                      }
                    }}
                    className="rounded-full border border-black/10 px-4 py-2.5 text-sm font-semibold text-black dark:border-white/10 dark:text-white"
                  >
                    Validate Directories
                  </button>
                </div>
                {mt5Validation ? (
                  <div className={`rounded-[22px] border p-4 ${mt5Validation.ok ? 'border-emerald-500/30 bg-emerald-50 dark:bg-emerald-500/10' : 'border-amber-500/30 bg-amber-50 dark:bg-amber-500/10'}`}>
                    <p className="text-sm font-semibold text-black dark:text-white">
                      {mt5Validation.ok ? 'Validation passed' : 'Validation needs attention'}
                    </p>
                    <div className="mt-3 space-y-1 text-sm text-black/75 dark:text-white/75">
                      <p>Inbox: {mt5Validation.inbox_dir}</p>
                      <p>Archive: {mt5Validation.archive_dir}</p>
                      <p>Inbox ready: {mt5Validation.inbox_writable ? 'Yes' : 'No'}</p>
                      <p>Archive ready: {mt5Validation.archive_writable ? 'Yes' : 'No'}</p>
                    </div>
                    {mt5Validation.warnings.length ? (
                      <div className="mt-3">
                        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-black/55 dark:text-white/55">Warnings</p>
                        <ul className="mt-2 space-y-1 text-sm text-black/75 dark:text-white/75">
                          {mt5Validation.warnings.map((warning) => (
                            <li key={warning}>- {warning}</li>
                          ))}
                        </ul>
                      </div>
                    ) : null}
                    {mt5Validation.instructions.length ? (
                      <div className="mt-3">
                        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-black/55 dark:text-white/55">Instructions</p>
                        <ul className="mt-2 space-y-1 text-sm text-black/75 dark:text-white/75">
                          {mt5Validation.instructions.map((instruction) => (
                            <li key={instruction}>- {instruction}</li>
                          ))}
                        </ul>
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </div>
            ) : (
              <p className="text-sm text-black/70 dark:text-white/70">The account will be connected immediately to a simulated broker so it is usable right away.</p>
            )}

            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={async () => {
                  setError(null);
                  setIsSubmitting(true);
                  try {
                    const payload = {
                      ...form,
                      auto_connect_simulated: connectionMode === 'simulated',
                    };
                    const createdAccount = await onCreateAccount(payload);
                    if (connectionMode === 'mt5_file_bridge') {
                      await onConnectMt5({
                        account_id: createdAccount.account_id,
                        broker_id: payload.broker_id,
                        inbox_dir: mt5Config.inbox_dir,
                        archive_dir: mt5Config.archive_dir || undefined,
                        poll_interval_seconds: Number(mt5Config.poll_interval_seconds || 0.25),
                      });
                    }
                    setMode('browse');
                  } catch (createError) {
                    setError(createError instanceof Error ? createError.message : 'Failed to create account');
                  } finally {
                    setIsSubmitting(false);
                  }
                }}
                className="rounded-full bg-black px-5 py-3 text-sm font-semibold text-white dark:bg-white dark:text-black"
              >
                {isSubmitting ? 'Saving…' : 'Create Account'}
              </button>
            </div>
          </div>
        )}

        {error ? <p className="mt-5 text-sm text-rose-700 dark:text-rose-300">{error}</p> : null}
      </div>
    </div>
  );
}

function Input({
  label,
  value,
  onChange,
  type = 'text',
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-black/50 dark:text-white/50">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-[18px] border border-black/10 bg-white px-4 py-3 text-sm font-medium text-black outline-none dark:border-white/10 dark:bg-[#0a0a0a] dark:text-white"
      />
    </label>
  );
}

function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.18em] text-black/50 dark:text-white/50">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-[18px] border border-black/10 bg-white px-4 py-3 text-sm font-medium text-black outline-none dark:border-white/10 dark:bg-[#0a0a0a] dark:text-white"
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
