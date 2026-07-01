import { useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from 'react-query';

import {
  connectMt5FileBridge,
  fetchAccountIntegrations,
  fetchAccounts,
  fetchTrades,
  importTradeCsv,
  validateMt5FileBridge,
} from '@/api/prototype';
import { ThemeToggle } from '@/components/foundation/ThemeToggle';
import { usePrototypeStore } from '@/state/prototypeStore';
import { useThemeStore } from '@/state/themeStore';
import type { Mt5FileBridgeInput } from '@/types/prototype';

const AVATAR_STORAGE_KEY = 'my_platform_account_avatar';
const ACCOUNT_PROFILE_KEY = 'my_platform_account_profile';

type AccountProfile = {
  accountName: string;
  baseCurrency: string;
  supportedMarkets: string[];
  timezone: string;
};

const MARKET_OPTIONS = ['stock', 'forex', 'crypto', 'futures', 'indices', 'commodities'];
const CURRENCY_OPTIONS = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SGD', 'HKD'];
const TIMEZONE_OPTIONS = [
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Berlin',
  'Europe/Paris',
  'Asia/Tokyo',
  'Asia/Hong_Kong',
  'Asia/Singapore',
  'Asia/Kolkata',
  'Asia/Dubai',
  'Australia/Sydney',
  'Pacific/Auckland',
  'UTC',
];

function loadAvatar(accountId: string): string | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(`${AVATAR_STORAGE_KEY}_${accountId}`);
    return raw || null;
  } catch {
    return null;
  }
}

function saveAvatar(accountId: string, dataUrl: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(`${AVATAR_STORAGE_KEY}_${accountId}`, dataUrl);
}

function loadProfile(accountId: string): AccountProfile | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(`${ACCOUNT_PROFILE_KEY}_${accountId}`);
    return raw ? (JSON.parse(raw) as AccountProfile) : null;
  } catch {
    return null;
  }
}

function saveProfile(accountId: string, profile: AccountProfile) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(`${ACCOUNT_PROFILE_KEY}_${accountId}`, JSON.stringify(profile));
}

function generateCsvContent(trades: unknown[]): string {
  if (!trades.length) return '';
  const headers = Object.keys(trades[0] as Record<string, unknown>);
  const rows = trades.map((trade) => {
    const record = trade as Record<string, unknown>;
    return headers
      .map((header) => {
        const value = record[header];
        if (value === null || value === undefined) return '';
        const str = String(value);
        if (str.includes(',') || str.includes('"') || str.includes('\n')) {
          return `"${str.replace(/"/g, '""')}"`;
        }
        return str;
      })
      .join(',');
  });
  return [headers.join(','), ...rows].join('\n');
}

function downloadCsv(content: string, filename: string) {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function SettingsScreen() {
  const queryClient = useQueryClient();

  // Core state from stores
  const accountId = usePrototypeStore((state) => state.accountId);
  const setAccountId = usePrototypeStore((state) => state.setAccountId);
  const resetSidebarOrder = usePrototypeStore((state) => state.resetSidebarOrder);
  const resetDashboardLayout = usePrototypeStore((state) => state.resetDashboardLayout);
  const themeMode = useThemeStore((state) => state.mode);

  // Queries
  const { data: accounts = [] } = useQuery(['prototype-settings-accounts'], fetchAccounts, {
    refetchInterval: 10000,
  });
  const { data: integrations = [] } = useQuery(
    ['prototype-settings-integrations'],
    fetchAccountIntegrations,
    { refetchInterval: 10000 },
  );
  const { data: allTrades = [] } = useQuery(
    ['prototype-settings-trades', accountId],
    () => fetchTrades(accountId as string),
    { enabled: Boolean(accountId) },
  );

  const selectedAccount = accounts.find((a) => a.account_id === accountId) || null;
  const integration = integrations.find((i) => i.account_id === accountId) || null;
  const health = integration?.health || null;

  // --- Account Profile State ---
  const storedProfile = accountId ? loadProfile(accountId) : null;
  const [localAccountName, setLocalAccountName] = useState(
    storedProfile?.accountName || selectedAccount?.account_name || '',
  );
  const [localCurrency, setLocalCurrency] = useState(
    storedProfile?.baseCurrency || selectedAccount?.base_currency || 'USD',
  );
  const [localMarkets, setLocalMarkets] = useState<string[]>(
    storedProfile?.supportedMarkets || selectedAccount?.supported_market_types || ['stock', 'forex', 'crypto'],
  );
  const [localTimezone, setLocalTimezone] = useState(
    storedProfile?.timezone || 'Asia/Kolkata',
  );
  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- Import CSV State ---
  const [selectedFileName, setSelectedFileName] = useState<string | null>(null);
  const [confirmClear, setConfirmClear] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);

  const importMutation = useMutation(
    (csvText: string) => importTradeCsv(csvText, accountId as string),
    {
      onSuccess: async () => {
        await Promise.all([
          queryClient.invalidateQueries(['prototype-overview', accountId]),
          queryClient.invalidateQueries(['prototype-trades', accountId]),
          queryClient.invalidateQueries(['prototype-missed-opportunities', accountId]),
          queryClient.invalidateQueries(['prototype-calendar-summaries', accountId]),
        ]);
      },
    },
  );

  const handleCsvUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setSelectedFileName(file.name);
    const csvText = await file.text();
    importMutation.mutate(csvText);
  };

  const handleExportCsv = async () => {
    if (!allTrades.length) return;
    setExportLoading(true);
    try {
      const csv = generateCsvContent(allTrades);
      const timestamp = new Date().toISOString().slice(0, 10);
      downloadCsv(csv, `trades_export_${timestamp}.csv`);
    } finally {
      setExportLoading(false);
    }
  };

  const handleClearLocalCache = () => {
    localStorage.clear();
    window.location.reload();
  };

  const handleAvatarUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !accountId) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target?.result as string;
      saveAvatar(accountId, dataUrl);
      setLocalAccountName((prev) => prev);
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveAvatar = () => {
    if (!accountId) return;
    localStorage.removeItem(`${AVATAR_STORAGE_KEY}_${accountId}`);
    setLocalAccountName((prev) => prev);
  };

  const handleSaveProfile = () => {
    if (!accountId) return;
    saveProfile(accountId, {
      accountName: localAccountName,
      baseCurrency: localCurrency,
      supportedMarkets: localMarkets,
      timezone: localTimezone,
    });
  };

  const toggleMarket = (market: string) => {
    setLocalMarkets((prev) =>
      prev.includes(market) ? prev.filter((m) => m !== market) : [...prev, market],
    );
  };

  const currentAvatarUrl = accountId ? loadAvatar(accountId) : null;

  return (
    <div className="space-y-6 text-black dark:text-white">
        {/* ─── Card 1: Account Profile ─── */}
        <div>
          <div className="rounded-[26px] border border-black/10 bg-white p-6 dark:border-white/10 dark:bg-[#060606]">
            <h3 className="text-xl font-semibold text-black dark:text-white">Account Profile</h3>
            <div className="mt-4 space-y-5">
              {/* Account Selector */}
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-black/50 dark:text-white/50">
                  Active Account
                </p>
                <select
                  value={accountId || ''}
                  onChange={(event) => {
                    const next = event.target.value;
                    if (next) {
                      setAccountId(next);
                      const profile = loadProfile(next);
                      const acct = accounts.find((a) => a.account_id === next);
                      setLocalAccountName(profile?.accountName || acct?.account_name || '');
                      setLocalCurrency(profile?.baseCurrency || acct?.base_currency || 'USD');
                      setLocalMarkets(
                        profile?.supportedMarkets || acct?.supported_market_types || ['stock', 'forex', 'crypto'],
                      );
                      setLocalTimezone(profile?.timezone || 'Asia/Kolkata');
                    }
                  }}
                  className="w-full rounded-[18px] border border-black/10 bg-white px-4 py-3 text-sm font-medium text-black outline-none dark:border-white/10 dark:bg-[#0a0a0a] dark:text-white"
                >
                  {accounts.map((acct) => (
                    <option key={acct.account_id} value={acct.account_id}>
                      {acct.account_name || acct.account_id}
                    </option>
                  ))}
                </select>
              </div>

              {/* Avatar */}
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-black/50 dark:text-white/50">
                  Account Photo
                </p>
                <div className="flex items-center gap-4">
                  <div className="relative h-16 w-16 shrink-0 overflow-hidden rounded-full border-2 border-black/10 dark:border-white/10">
                    {currentAvatarUrl ? (
                      <img
                        src={currentAvatarUrl}
                        alt="Account avatar"
                        className="h-full w-full rounded-full object-cover"
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center bg-black/5 text-xl font-bold text-black/40 dark:bg-white/10 dark:text-white/40">
                        {(localAccountName || accountId || '?').charAt(0).toUpperCase()}
                      </div>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="inline-flex rounded-full border border-black/10 bg-white px-3 py-1.5 text-xs font-semibold text-black transition hover:border-[#ff5900] hover:text-[#ff5900] dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white dark:hover:border-[#ff5900] dark:hover:text-[#ff5900]"
                    >
                      Upload Photo
                    </button>
                    {currentAvatarUrl ? (
                      <button
                        type="button"
                        onClick={handleRemoveAvatar}
                        className="inline-flex rounded-full border border-rose-300 px-3 py-1.5 text-xs font-semibold text-rose-600 transition hover:border-rose-500 hover:bg-rose-50 dark:border-rose-800 dark:text-rose-400 dark:hover:border-rose-600 dark:hover:bg-rose-950"
                      >
                        Remove
                      </button>
                    ) : null}
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={handleAvatarUpload}
                    />
                  </div>
                </div>
              </div>

              <InputField label="Account Name" value={localAccountName} onChange={setLocalAccountName} />

              {/* Account ID (read-only) */}
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-black/50 dark:text-white/50">
                  Account ID
                </p>
                <p className="w-full rounded-[18px] border border-black/10 bg-black/[0.03] px-4 py-3 text-sm font-medium text-black/60 dark:border-white/10 dark:bg-white/[0.03] dark:text-white/60">
                  {accountId || 'No account selected'}
                </p>
              </div>

              <SelectField label="Base Currency" value={localCurrency} options={CURRENCY_OPTIONS} onChange={setLocalCurrency} />
              <SelectField label="Timezone" value={localTimezone} options={TIMEZONE_OPTIONS} onChange={setLocalTimezone} />

              {/* Supported Markets */}
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-black/50 dark:text-white/50">
                  Supported Markets
                </p>
                <div className="flex flex-wrap gap-2">
                  {MARKET_OPTIONS.map((market) => (
                    <button
                      key={market}
                      type="button"
                      onClick={() => toggleMarket(market)}
                      className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                        localMarkets.includes(market)
                          ? 'border-[#ff5900] bg-[#ff5900] text-white'
                          : 'border-black/10 bg-white text-black hover:border-[#ff5900] hover:text-[#ff5900] dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white dark:hover:border-[#ff5900] dark:hover:text-[#ff5900]'
                      }`}
                    >
                      {market.charAt(0).toUpperCase() + market.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="button"
                onClick={handleSaveProfile}
                className="inline-flex rounded-full bg-[#ff5900] px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-[#e04f00]"
              >
                Save Profile
              </button>
            </div>
          </div>
        </div>

        {/* ─── Card 2: Broker Connection ─── */}
        <div>
          <div className="rounded-[26px] border border-black/10 bg-white p-6 dark:border-white/10 dark:bg-[#060606]">
            <h3 className="text-xl font-semibold text-black dark:text-white">Broker Connection</h3>
            <div className="mt-4 space-y-4">
              {/* Broker name */}
              <div className="flex items-center justify-between rounded-[18px] border border-black/10 bg-black/[0.02] px-4 py-3 dark:border-white/10 dark:bg-white/[0.03]">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-black/50 dark:text-white/50">
                    Broker
                  </p>
                  <p className="mt-1 text-sm font-semibold text-black dark:text-white">
                    {selectedAccount?.broker_id || 'MetaTrader 5'}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex h-2.5 w-2.5 rounded-full ${
                      health?.bridge_alive ? 'bg-emerald-500' : 'bg-amber-500'
                    }`}
                  />
                  <span className="text-sm font-semibold">
                    {health?.bridge_alive ? 'Bridge Active' : health ? 'Inactive' : 'Not Connected'}
                  </span>
                </div>
              </div>

              <p className="text-xs text-black/60 dark:text-white/60">
                Connection is managed via the Account setup flow. Use the account picker in the top bar to add or change broker connections.
              </p>
            </div>
          </div>
        </div>

        {/* ─── Card 3: Trading Preferences ─── */}
        <div>
          <div className="rounded-[26px] border border-black/10 bg-white p-6 dark:border-white/10 dark:bg-[#060606]">
            <h3 className="text-xl font-semibold text-black dark:text-white">Trading Preferences</h3>
            <div className="mt-4 flex min-h-[120px] items-center justify-center">
              <p className="text-sm text-black/40 dark:text-white/40">Coming soon.</p>
            </div>
          </div>
        </div>

        {/* ─── Card 4: Workspace & Data ─── */}
        <div>
          <div className="rounded-[26px] border border-black/10 bg-white p-6 dark:border-white/10 dark:bg-[#060606]">
            <h3 className="text-xl font-semibold text-black dark:text-white">Workspace & Data</h3>
            <div className="mt-4 space-y-5">
              {/* Theme */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-black dark:text-white">Theme</p>
                  <p className="text-xs text-black/60 dark:text-white/60">
                    Currently {themeMode === 'dark' ? 'Dark' : 'Light'} mode
                  </p>
                </div>
                <ThemeToggle />
              </div>

              <div className="border-t border-black/10 dark:border-white/10" />

              {/* Reset Sidebar */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-black dark:text-white">Reset Sidebar Order</p>
                  <p className="text-xs text-black/60 dark:text-white/60">
                    Restore default sidebar navigation order
                  </p>
                </div>
                <button
                  type="button"
                  onClick={resetSidebarOrder}
                  className="inline-flex shrink-0 rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-semibold text-black transition hover:border-[#ff5900] hover:text-[#ff5900] dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white dark:hover:border-[#ff5900] dark:hover:text-[#ff5900]"
                >
                  Reset
                </button>
              </div>

              <div className="border-t border-black/10 dark:border-white/10" />

              {/* Import CSV */}
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-black/50 dark:text-white/50">
                  Import Trades
                </p>
                <p className="text-sm text-black/60 dark:text-white/60">
                  Upload a CSV file with trade rows to import them into your journal.
                </p>
                <label className="mt-3 inline-flex cursor-pointer items-center rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-semibold text-black transition hover:border-[#ff5900] hover:text-[#ff5900] dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white dark:hover:border-[#ff5900] dark:hover:text-[#ff5900]">
                  Choose CSV File
                  <input type="file" accept=".csv,text/csv" className="hidden" onChange={handleCsvUpload} />
                </label>
                {selectedFileName ? <p className="mt-2 text-xs text-black/60 dark:text-white/60">{selectedFileName}</p> : null}
                {importMutation.isLoading ? <p className="mt-2 text-xs text-black/60 dark:text-white/60">Importing…</p> : null}
                {importMutation.data ? (
                  <div className="mt-2 text-xs">
                    <p className="text-emerald-700 dark:text-emerald-300">
                      Imported {importMutation.data.imported_count} trade(s).
                    </p>
                    {importMutation.data.errors.length > 0 ? (
                      <ul className="mt-1 space-y-0.5 text-amber-700 dark:text-amber-300">
                        {importMutation.data.errors.slice(0, 3).map((item) => (
                          <li key={`${item.row}-${item.detail}`}>Row {item.row}: {item.detail}</li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                ) : null}
                {importMutation.error instanceof Error ? (
                  <p className="mt-2 text-xs text-rose-600 dark:text-rose-400">{importMutation.error.message}</p>
                ) : null}
              </div>

              <div className="border-t border-black/10 dark:border-white/10" />

              {/* Export CSV */}
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-black/50 dark:text-white/50">
                  Export Trades
                </p>
                <p className="text-sm text-black/60 dark:text-white/60">
                  Download all trades as a CSV file for external analysis.
                </p>
                <button
                  type="button"
                  onClick={handleExportCsv}
                  disabled={exportLoading || !allTrades.length}
                  className="mt-3 inline-flex rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-semibold text-black transition hover:border-[#ff5900] hover:text-[#ff5900] disabled:opacity-40 dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white dark:hover:border-[#ff5900] dark:hover:text-[#ff5900]"
                >
                  {exportLoading ? 'Preparing…' : allTrades.length ? `Export CSV (${allTrades.length} trades)` : 'No trades to export'}
                </button>
              </div>

              <div className="border-t border-black/10 dark:border-white/10" />

              {/* Reset Dashboard Layout */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-black dark:text-white">Reset Dashboard Layout</p>
                  <p className="text-xs text-black/60 dark:text-white/60">
                    Restore default metric groups, widget visibility, and filters
                  </p>
                </div>
                <button
                  type="button"
                  onClick={resetDashboardLayout}
                  className="inline-flex shrink-0 rounded-full border border-black/10 bg-white px-4 py-2 text-sm font-semibold text-black transition hover:border-[#ff5900] hover:text-[#ff5900] dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white dark:hover:border-[#ff5900] dark:hover:text-[#ff5900]"
                >
                  Reset
                </button>
              </div>

              <div className="border-t border-black/10 dark:border-white/10" />

              {/* Clear Local Cache */}
              <div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-black dark:text-white">Clear Local Cache</p>
                    <p className="text-xs text-black/60 dark:text-white/60">
                      Remove all locally stored settings and reload the app
                    </p>
                  </div>
                  {!confirmClear ? (
                    <button
                      type="button"
                      onClick={() => setConfirmClear(true)}
                      className="inline-flex shrink-0 rounded-full border border-rose-300 px-4 py-2 text-sm font-semibold text-rose-600 transition hover:border-rose-500 hover:bg-rose-50 dark:border-rose-800 dark:text-rose-400 dark:hover:border-rose-600 dark:hover:bg-rose-950"
                    >
                      Clear
                    </button>
                  ) : (
                    <div className="flex shrink-0 items-center gap-1.5">
                      <span className="text-xs font-semibold text-rose-600 dark:text-rose-400">Confirm?</span>
                      <button
                        type="button"
                        onClick={handleClearLocalCache}
                        className="inline-flex rounded-full bg-rose-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-rose-700"
                      >
                        Yes, Clear
                      </button>
                      <button
                        type="button"
                        onClick={() => setConfirmClear(false)}
                        className="inline-flex rounded-full border border-black/10 bg-white px-2.5 py-1.5 text-xs font-semibold text-black dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white"
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
    </div>
  );
}

/* ─── Shared Sub-Components ─── */

function InputField({
  label,
  value,
  onChange,
  type = 'text',
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <div>
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-black/50 dark:text-white/50">
        {label}
      </p>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="w-full rounded-[18px] border border-black/10 bg-white px-4 py-3 text-sm font-medium text-black outline-none dark:border-white/10 dark:bg-[#0a0a0a] dark:text-white"
      />
    </div>
  );
}

function SelectField({
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
    <div>
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-black/50 dark:text-white/50">
        {label}
      </p>
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
    </div>
  );
}