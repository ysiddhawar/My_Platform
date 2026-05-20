import type { TradeRecord } from '@/types/prototype';
import { formatCurrency, formatDate, formatNumber, formatRatio, formatTime } from '@/utils/format';

type TradeTableProps = {
  trades: TradeRecord[];
  selectedTradeId: string | null;
  onSelectTrade: (tradeId: string) => void;
};

const headers = [
  'Trade ID',
  'Symbol',
  'Market',
  'Side',
  'SETUP',
  'Entry Price',
  'Entry Time',
  'Entry Date',
  'Entry Day',
  'Stop Loss',
  'Target',
  'Exit Price',
  'Exit Time',
  'Exit Date',
  'Exit Day',
  'Exit Reason',
  'Quantity',
  'Commission',
  'Swaps',
  'Slippage Cost',
  'Gross PnL',
  'Net PnL',
  'Risk Amount',
  'RRR',
  'R Multiple',
  'Confidence',
  'Emotion',
  'Probability',
  'Closed Early',
  'Status',
];

export function TradeTable({ trades, selectedTradeId, onSelectTrade }: TradeTableProps) {
  return (
    <div className="overflow-hidden rounded-[26px] border border-black/10 bg-white dark:border-white/10 dark:bg-[#060606]">
      <div className="overflow-x-auto">
        <table className="min-w-[2400px] border-separate border-spacing-0">
          <thead>
            <tr className="bg-gray-50 dark:bg-[#0d0d0d]">
              {headers.map((label) => (
                <th key={label} className="border-b border-black/8 px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-600 dark:border-white/10 dark:text-slate-400">
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {trades.map((trade) => {
              const tradeId = trade.trade_id || '—';
              const isSelected = tradeId === selectedTradeId;
              const pnl = Number(trade.net_pnl || 0);
              const rowTone = !trade.is_closed
                ? 'bg-white hover:bg-gray-50 dark:bg-[#060606] dark:hover:bg-[#0b0b0b]'
                : pnl > 0
                  ? 'bg-emerald-50/70 hover:bg-emerald-50 dark:bg-emerald-500/10 dark:hover:bg-emerald-500/14'
                  : pnl < 0
                    ? 'bg-rose-50/70 hover:bg-rose-50 dark:bg-rose-500/10 dark:hover:bg-rose-500/14'
                    : 'bg-white hover:bg-gray-50 dark:bg-[#060606] dark:hover:bg-[#0b0b0b]';
              return (
                <tr
                  key={tradeId}
                  onClick={() => {
                    if (trade.trade_id) {
                      onSelectTrade(trade.trade_id);
                    }
                  }}
                  className={`cursor-pointer transition duration-200 hover:shadow-[inset_0_0_0_1px_rgba(255,89,0,0.72)] ${isSelected ? 'bg-black text-white dark:bg-[#12142b]' : rowTone}`}
                >
                  <Cell selected={isSelected}>{trade.trade_id ? trade.trade_id.replace(/^mt5_/, '') : '—'}</Cell>
                  <Cell selected={isSelected} strong>{trade.symbol}</Cell>
                  <Cell selected={isSelected}>{trade.market_type || '—'}</Cell>
                  <Cell selected={isSelected}>{trade.side}</Cell>
                  <Cell selected={isSelected}>{(() => {
                      const tag = trade.strategy_tag && trade.strategy_tag !== 'MT5 Historical Sync' ? trade.strategy_tag : null;
                      const strat = trade.strategy && trade.strategy !== 'MT5 Historical Sync' ? trade.strategy : null;
                      return tag || strat || '—';
                    })()}</Cell>
                  <Cell selected={isSelected}>{formatNumber(Number(trade.entry_price || 0))}</Cell>
                  <Cell selected={isSelected}>{formatTime(trade.entry_time, trade.entry_timezone || 'UTC')}</Cell>
                  <Cell selected={isSelected}>{formatDate(trade.entry_time, trade.entry_timezone || 'UTC')}</Cell>
                  <Cell selected={isSelected}>{trade.entry_day_of_week || '—'}</Cell>
                  <Cell selected={isSelected}>{formatNumber(Number(trade.stop_loss_at_entry || 0))}</Cell>
                  <Cell selected={isSelected}>{formatNumber(Number(trade.target_at_entry || 0))}</Cell>
                  <Cell selected={isSelected}>{trade.exit_price != null ? formatNumber(Number(trade.exit_price)) : '—'}</Cell>
                  <Cell selected={isSelected}>{formatTime(trade.exit_time, trade.entry_timezone || 'UTC')}</Cell>
                  <Cell selected={isSelected}>{formatDate(trade.exit_time, trade.entry_timezone || 'UTC')}</Cell>
                  <Cell selected={isSelected}>{trade.exit_day_of_week || '—'}</Cell>
                  <Cell selected={isSelected}>{trade.exit_reason || '—'}</Cell>
                  <Cell selected={isSelected}>{formatNumber(Number(trade.quantity || 0))}</Cell>
                  <Cell selected={isSelected}>{formatCurrency(Number(trade.commission || 0))}</Cell>
                  <Cell selected={isSelected}>{formatCurrency(Number(trade.swaps || 0))}</Cell>
                  <Cell selected={isSelected}>{formatCurrency(Number(trade.slippage_cost || 0))}</Cell>
                  <Cell selected={isSelected}>{formatCurrency(Number(trade.gross_pnl || 0))}</Cell>
                  <Cell selected={isSelected} className={pnl >= 0 ? (isSelected ? 'text-emerald-200' : 'text-emerald-700 dark:text-emerald-300') : (isSelected ? 'text-rose-200' : 'text-rose-700 dark:text-rose-300')}>
                    {formatCurrency(pnl)}
                  </Cell>
                  <Cell selected={isSelected}>{formatCurrency(Number(trade.risk_amount || 0))}</Cell>
                  <Cell selected={isSelected}>{formatRatio(Number(trade.rrr_at_entry || 0))}</Cell>
                  <Cell selected={isSelected}>{formatRatio(Number(trade.r_multiple || 0))}</Cell>
                  <Cell selected={isSelected}>{trade.confidence_score != null ? formatNumber(Number(trade.confidence_score)) : '—'}</Cell>
                  <Cell selected={isSelected}>{trade.emotion_tag || '—'}</Cell>
                  <Cell selected={isSelected}>{trade.probability_bucket || '—'}</Cell>
                  <Cell selected={isSelected}>{trade.closed_before_plan ? 'Yes' : 'No'}</Cell>
                  <Cell selected={isSelected}>{trade.close_classification || (trade.is_closed ? 'Closed' : 'Open')}</Cell>
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
}: {
  children: React.ReactNode;
  selected: boolean;
  strong?: boolean;
  className?: string;
}) {
  return (
    <td
      className={`border-b border-black/8 px-4 py-3 text-sm ${strong ? 'font-semibold' : ''} ${
        selected ? 'border-white/10 text-white' : 'text-black dark:border-white/10 dark:text-white'
      } ${className}`}
    >
      {children}
    </td>
  );
}
