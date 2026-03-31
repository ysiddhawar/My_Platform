import type { MissedOpportunityRecord } from '@/types/prototype';
import { formatDate, formatNumber, formatTime } from '@/utils/format';

type MissedOpportunityTableProps = {
  opportunities: MissedOpportunityRecord[];
};

export function MissedOpportunityTable({ opportunities }: MissedOpportunityTableProps) {
  return (
    <div className="overflow-hidden rounded-[26px] border border-black/10 bg-white dark:border-white/10 dark:bg-[#060606]">
      <div className="overflow-x-auto">
        <table className="min-w-[1500px] border-separate border-spacing-0">
          <thead>
            <tr className="bg-gray-50 dark:bg-[#0d0d0d]">
              {[
                'Symbol',
                'Market',
                'Side',
                'Strategy',
                'Probability',
                'Checklist',
                'Entry Price',
                'Entry Time',
                'Entry Date',
                'Entry Day',
                'Timezone',
                'Stop Loss',
                'Target',
                'Minimum Target',
                'Exit Price',
                'Exit Time',
                'Exit Date',
                'Exit Day',
                'Exit Reason',
                'Note',
              ].map((label) => (
                <th key={label} className="border-b border-black/8 px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-600 dark:border-white/10 dark:text-slate-400">
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {opportunities.map((item) => (
              <tr key={item.opportunity_id} className="cursor-pointer transition duration-200 hover:bg-gray-50 hover:shadow-[inset_0_0_0_1px_rgba(255,89,0,0.72)] dark:hover:bg-[#0b0b0b]">
                <Cell strong>{item.symbol}</Cell>
                <Cell>{item.market_type}</Cell>
                <Cell>{item.side}</Cell>
                <Cell>{item.strategy_name}</Cell>
                <Cell>{item.probability_bucket}</Cell>
                <Cell>{(item.checklist_items || []).length ? item.checklist_items!.join(', ') : '—'}</Cell>
                <Cell>{formatNumber(item.entry_price)}</Cell>
                <Cell>{formatTime(item.observed_at)}</Cell>
                <Cell>{formatDate(item.observed_at)}</Cell>
                <Cell>{item.local_day_of_week}</Cell>
                <Cell>{item.timezone_name}</Cell>
                <Cell>{formatNumber(item.stop_loss_price)}</Cell>
                <Cell>{formatNumber(item.target_price)}</Cell>
                <Cell>{item.minimum_target_price != null ? formatNumber(item.minimum_target_price) : '—'}</Cell>
                <Cell>{item.exit_price != null ? formatNumber(item.exit_price) : '—'}</Cell>
                <Cell>{formatTime(item.exit_at)}</Cell>
                <Cell>{item.exit_at ? formatDate(item.exit_at) : '—'}</Cell>
                <Cell>{item.exit_day_of_week || '—'}</Cell>
                <Cell>{item.exit_reason || '—'}</Cell>
                <Cell>{item.notes || '—'}</Cell>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Cell({ children, strong = false }: { children: React.ReactNode; strong?: boolean }) {
  return (
    <td className={`border-b border-black/8 px-4 py-3 text-sm text-black dark:border-white/10 dark:text-white ${strong ? 'font-semibold' : ''}`}>
      {children}
    </td>
  );
}
