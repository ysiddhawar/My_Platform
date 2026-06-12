import { useCallback, useMemo, useState } from 'react';
import type { TradeRecord } from '@/types/prototype';
import { formatCurrency, formatDate, formatHoldTime, formatNumber, formatRatio, formatTime } from '@/utils/format';

type TradeTableProps = {
  trades: TradeRecord[];
  selectedTradeId: string | null;
  onSelectTrade: (tradeId: string) => void;
  isRefetching?: boolean;
  onRefresh?: () => void;
};

type ColumnKey =
  | 'trade_id'
  | 'market_type'
  | 'entry_price'
  | 'entry_time'
  | 'entry_day'
  | 'stop_loss'
  | 'target'
  | 'exit_price'
  | 'exit_time'
  | 'exit_date'
  | 'exit_day'
  | 'exit_reason'
  | 'quantity'
  | 'commission'
  | 'swaps'
  | 'slippage_cost'
  | 'gross_pnl'
  | 'rrr'
  | 'confidence_score'
  | 'emotion_tag'
  | 'probability_bucket'
  | 'closed_before_plan';

const DEFAULT_COLUMNS: { key: string; label: string }[] = [
  { key: 'entry_date', label: 'Entry Date' },
  { key: 'symbol', label: 'Symbol' },
  { key: 'status', label: 'Status' },
  { key: 'net_pnl', label: 'Net PnL' },
  { key: 'setup', label: 'Setup' },
  { key: 'side', label: 'Side' },
  { key: 'hold_time', label: 'Hold Time' },
  { key: 'change_percent', label: 'Change %' },
  { key: 'risk_amount', label: 'Risk Amount' },
  { key: 'net_roi', label: 'Net ROI' },
  { key: 'r_multiple', label: 'R Multiple' },
  { key: 'commission', label: 'Brokerage' },
  { key: 'swaps', label: 'Swaps' },
  { key: 'fees', label: 'Fee' },
];

const EXTRA_COLUMNS: { key: ColumnKey; label: string }[] = [
  { key: 'trade_id', label: 'Trade ID' },
  { key: 'market_type', label: 'Market' },
  { key: 'entry_price', label: 'Entry Price' },
  { key: 'entry_time', label: 'Entry Time' },
  { key: 'entry_day', label: 'Entry Day' },
  { key: 'stop_loss', label: 'Stop Loss' },
  { key: 'target', label: 'Target' },
  { key: 'exit_price', label: 'Exit Price' },
  { key: 'exit_time', label: 'Exit Time' },
  { key: 'exit_date', label: 'Exit Date' },
  { key: 'exit_day', label: 'Exit Day' },
  { key: 'exit_reason', label: 'Exit Reason' },
  { key: 'quantity', label: 'Quantity' },
  { key: 'commission', label: 'Commission' },
  { key: 'swaps', label: 'Swaps' },
  { key: 'slippage_cost', label: 'Slippage Cost' },
  { key: 'gross_pnl', label: 'Gross PnL' },
  { key: 'rrr', label: 'RRR' },
  { key: 'confidence_score', label: 'Confidence' },
  { key: 'emotion_tag', label: 'Emotion' },
  { key: 'probability_bucket', label: 'Probability' },
  { key: 'closed_before_plan', label: 'Closed Early' },
];

const STORAGE_KEY = 'my_platform_journal_extra_columns';

function loadExtraColumns(): ColumnKey[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const keys = raw ? (JSON.parse(raw) as ColumnKey[]) : [];
    // Normalize to EXTRA_COLUMNS order to prevent header/cell misalignment
    const extraKeys = new Set(EXTRA_COLUMNS.filter(c => keys.includes(c.key)).map(c => c.key));
    const staleKeys = keys.filter(k => !extraKeys.has(k));
    if (staleKeys.length > 0) {
      // Persist cleaned set immediately
      const cleaned = EXTRA_COLUMNS.filter(c => keys.includes(c.key)).map(c => c.key);
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(cleaned));
      return cleaned;
    }
    return EXTRA_COLUMNS.filter(col => keys.includes(col.key)).map(col => col.key);
  } catch {
    return [];
  }
}

function persistExtraColumns(keys: ColumnKey[]) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(keys));
}

function computeHoldTime(entryTime: string, exitTime: string | null | undefined): string {
  if (!exitTime) return '—';
  const entry = new Date(entryTime).getTime();
  const exit = new Date(exitTime).getTime();
  if (Number.isNaN(entry) || Number.isNaN(exit)) return '—';
  const diffMs = exit - entry;
  if (diffMs <= 0) return '—';
  return formatHoldTime(diffMs);
}



function formatChangePercent(trade: TradeRecord): string {
  const entry = Number(trade.entry_price || 0);
  const exit = trade.exit_price != null ? Number(trade.exit_price) : null;
  if (!entry || exit == null) return '—';
  const change = ((exit - entry) / entry) * 100;
  return `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`;
}

function formatNetROI(trade: TradeRecord): string {
  const pnl = Number(trade.net_pnl || 0);
  if (!trade.risk_amount || Number(trade.risk_amount) <= 0 || !Number.isFinite(pnl)) return '—';
  const roi = (pnl / Number(trade.risk_amount)) * 100;
  return `${roi >= 0 ? '+' : ''}${roi.toFixed(2)}%`;
}



function renderExtraCell(trade: TradeRecord, key: ColumnKey, isSelected: boolean): { value: string; className?: string } {
  switch (key) {
    case 'trade_id':
      return { value: trade.trade_id ? trade.trade_id.replace(/^mt5_/, '') : '—' };
    case 'market_type':
      return { value: trade.market_type || '—' };
    case 'entry_price':
      return { value: formatNumber(Number(trade.entry_price || 0)) };
    case 'entry_time':
      return { value: trade.entry_time ? formatTime(trade.entry_time, trade.entry_timezone || 'UTC') : '—' };
    case 'entry_day':
      return { value: trade.entry_day_of_week || '—' };
    case 'stop_loss': {
      const sl = Number(trade.stop_loss_at_entry);
      const safe = Number.isFinite(sl) && sl !== 0 ? sl : null;
      return { value: safe !== null ? formatNumber(safe) : '—' };
    }
    case 'target': {
      const tgt = Number(trade.target_at_entry);
      const safe = Number.isFinite(tgt) && tgt !== 0 ? tgt : null;
      return { value: safe !== null ? formatNumber(safe) : '—' };
    }
    case 'exit_price':
      return { value: trade.exit_price != null ? formatNumber(Number(trade.exit_price)) : '—' };
    case 'exit_time':
      return { value: trade.exit_time ? formatTime(trade.exit_time, trade.entry_timezone || 'UTC') : '—' };
    case 'exit_date':
      return { value: trade.exit_date ? formatDate(trade.exit_date) : '—' };
    case 'exit_day':
      return { value: trade.exit_day_of_week || '—' };
    case 'exit_reason':
      return { value: trade.exit_reason || '—' };
    case 'quantity':
      return { value: formatNumber(Number(trade.quantity || 0)) };
    case 'commission':
      return { value: formatCurrency(Number(trade.commission || 0)) };
    case 'swaps':
      return { value: formatCurrency(Number(trade.swaps || 0)) };
    case 'slippage_cost':
      return { value: formatCurrency(Number(trade.slippage_cost || 0)) };
    case 'gross_pnl':
      return { value: formatCurrency(Number(trade.gross_pnl || 0)) };
    case 'rrr':
      return { value: formatRatio(Number(trade.rrr_at_entry || 0)) };
    case 'confidence_score':
      return { value: trade.confidence_score != null ? formatNumber(Number(trade.confidence_score)) : '—' };
    case 'emotion_tag':
      return { value: trade.emotion_tag || '—' };
    case 'probability_bucket':
      return { value: trade.probability_bucket || '—' };
    case 'closed_before_plan':
      return { value: trade.closed_before_plan ? 'Yes' : 'No' };
    default:
      return { value: '—' };
  }
}

const STATUS_COLORS = {
  win: '#55B685',
  loss: '#DD524C',
  breakeven: '#EAB308',
} as const;

function getStatusStyle(pnl: number, isClosed: boolean): React.CSSProperties {
  if (!isClosed) return {};
  if (pnl > 0) return { color: STATUS_COLORS.win };
  if (pnl < 0) return { color: STATUS_COLORS.loss };
  return { color: STATUS_COLORS.breakeven };
}

export function TradeTable({ trades, selectedTradeId, onSelectTrade, isRefetching, onRefresh }: TradeTableProps) {
  const [extraColumns, setExtraColumns] = useState<ColumnKey[]>(loadExtraColumns);
  const [showColumnSelector, setShowColumnSelector] = useState(false);

  const toggleExtraColumn = useCallback((key: ColumnKey) => {
    setExtraColumns((prev) => {
      const next = prev.includes(key) ? prev.filter((c) => c !== key) : [...prev, key];
      persistExtraColumns(next);
      return next;
    });
  }, []);

  const allColumns = useMemo(() => {
    const extra = EXTRA_COLUMNS.filter((col) => extraColumns.includes(col.key));
    return [...DEFAULT_COLUMNS, ...extra];
  }, [extraColumns]);

  return (
    <div className="flex flex-col h-full overflow-hidden rounded-[26px] border border-black/10 bg-white dark:border-white/10 dark:bg-[#060606]">
      <div className="sticky top-0 z-20 bg-white dark:bg-[#060606] flex-shrink-0 flex items-center justify-between border-b border-black/8 px-4 py-2 dark:border-white/10">
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowColumnSelector((prev) => !prev)}
            className="rounded-full border border-black/10 bg-gray-50 px-4 py-1.5 text-xs font-semibold text-gray-700 transition hover:border-[#FF5900] hover:text-[#FF5900] dark:border-white/10 dark:bg-[#0d0d0d] dark:text-slate-300 dark:hover:border-[#FF5900] dark:hover:text-[#FF5900]"
          >
            {showColumnSelector ? 'Done' : '+ Add Columns'}
          </button>
          {showColumnSelector && (
            <div className="absolute left-0 top-full z-20 mt-1 w-56 rounded-xl border border-black/10 bg-white p-3 shadow-lg dark:border-white/10 dark:bg-[#121212]">
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-gray-500 dark:text-slate-400">Show extra columns</p>
              <div className="max-h-64 space-y-1 overflow-y-auto">
                {EXTRA_COLUMNS.map((col) => (
                  <label key={col.key} className="flex cursor-pointer items-center gap-2 rounded-lg px-2 py-1.5 text-sm text-black transition hover:bg-gray-100 dark:text-white dark:hover:bg-white/10">
                    <input
                      type="checkbox"
                      checked={extraColumns.includes(col.key)}
                      onChange={() => toggleExtraColumn(col.key)}
                      className="accent-[#FF5900]"
                    />
                    {col.label}
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>
        <button
          type="button"
          onClick={onRefresh}
          className="inline-flex items-center rounded-full bg-black px-5 py-3 text-sm font-semibold text-white transition hover:border-[#ff5900] hover:text-white hover:shadow-[0_10px_24px_-18px_rgba(255,89,0,0.28),0_0_0_1px_rgba(255,89,0,0.26)] dark:bg-white dark:text-black dark:hover:text-black"
        >
          {isRefetching ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      <div className="overflow-y-auto overflow-x-auto flex-1 min-h-0">
        <table className="min-w-[1500px] border-separate border-spacing-0">
          <thead className="sticky top-0 z-10">
            <tr className="bg-gray-50 dark:bg-[#0d0d0d]">
              {allColumns.map(({ key, label }) => (
                <th
                  key={key}
                  className="border-b border-black/8 px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-600 dark:border-white/10 dark:text-slate-400"
                >
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {trades.map((trade) => {
              const tradeId = trade.trade_id || '—';
              const isSelected = tradeId === selectedTradeId;
              const pnl = Math.round(Number(trade.net_pnl || 0) * 100) / 100;
              const statusStyle = getStatusStyle(pnl, trade.is_closed);
              const pnlStyle = getStatusStyle(pnl, trade.is_closed);
              const sideStyle = (trade.side || '').toLowerCase() === 'buy'
                ? { color: STATUS_COLORS.win }
                : (trade.side || '').toLowerCase() === 'sell'
                  ? { color: STATUS_COLORS.loss }
                  : {};

              return (
                <tr
                  key={tradeId}
                  onClick={() => {
                    if (trade.trade_id) {
                      onSelectTrade(trade.trade_id);
                    }
                  }}
                  className={`cursor-pointer transition duration-200 hover:shadow-[inset_0_0_0_1.5px_#FF5900] ${
                    isSelected ? 'bg-black text-white dark:bg-[#12142b]' : 'bg-white hover:bg-gray-50/50 dark:bg-[#060606] dark:hover:bg-[#0b0b0b]/50'
                  }`}
                >
                  <Cell selected={isSelected}>{trade.entry_date ? formatDate(trade.entry_date, trade.entry_timezone || 'UTC') : '—'}</Cell>
                  <Cell selected={isSelected} strong>{trade.symbol}</Cell>
                  <Cell selected={isSelected} className="font-semibold" style={statusStyle}>
                    {!trade.is_closed ? 'OPEN' : (pnl > 0 ? 'WIN' : pnl < 0 ? 'LOSS' : 'BREAKEVEN')}
                  </Cell>
                  <Cell selected={isSelected} style={pnlStyle}>{formatCurrency(pnl)}</Cell>
                  <Cell selected={isSelected}>
                    {(() => {
                      const tag = trade.strategy_tag && trade.strategy_tag !== 'MT5 Historical Sync' ? trade.strategy_tag : null;
                      const strat = trade.strategy && trade.strategy !== 'MT5 Historical Sync' ? trade.strategy : null;
                      return tag || strat || '—';
                    })()}
                  </Cell>
                  <Cell selected={isSelected} style={sideStyle}>{(trade.side || '').toUpperCase()}</Cell>
                  <Cell selected={isSelected}>{computeHoldTime(trade.entry_time, trade.exit_time)}</Cell>
                  <Cell selected={isSelected}>{formatChangePercent(trade)}</Cell>
                  <Cell selected={isSelected}>
                    {trade.risk_amount != null ? formatCurrency(Number(trade.risk_amount)) : '—'}
                  </Cell>
                  <Cell selected={isSelected}>{formatNetROI(trade)}</Cell>
                  <Cell selected={isSelected}>{formatRatio(Number(trade.r_multiple || 0))}</Cell>
                  <Cell selected={isSelected}>{formatCurrency(Number(trade.commission || 0))}</Cell>
                  <Cell selected={isSelected}>{formatCurrency(Number(trade.swaps || 0))}</Cell>
                  <Cell selected={isSelected}>{formatCurrency(Number(trade.fees || 0))}</Cell>
                  {allColumns.slice(DEFAULT_COLUMNS.length).map(({ key }) => {
                    const { value, className } = renderExtraCell(trade, key as ColumnKey, isSelected);
                    return (
                      <Cell key={key} selected={isSelected} className={className}>
                        {value}
                      </Cell>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Cell({
  children,
  selected,
  strong = false,
  className = '',
  style,
}: {
  children: React.ReactNode;
  selected: boolean;
  strong?: boolean;
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <td
      className={`border-b border-black/8 px-5 py-4 text-sm ${strong ? 'font-semibold' : ''} ${
        selected ? 'border-white/10 text-white' : 'text-black dark:border-white/10 dark:text-white'
      } ${className}`}
      style={style}
    >
      {children}
    </td>
  );
}
