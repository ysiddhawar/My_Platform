import { useState } from 'react';
import type { TradeBundle } from '@/types/prototype';
import { asArray, asRecord, formatCurrency, formatDate, formatDateTime, formatNumber, formatRatio, formatTime } from '@/utils/format';

type TradeBundlePanelProps = {
  bundle: TradeBundle;
  onSave?: (updates: Record<string, unknown>) => Promise<void>;
  isSaving?: boolean;
};

export function TradeBundlePanel({ bundle, onSave, isSaving }: TradeBundlePanelProps) {
  const trade = bundle.trade;
  if (!trade) {
    return null;
  }

  const preTrade = asRecord(trade.pre_trade_capture);
  const postTrade = asRecord(trade.post_trade_capture);
  const screenshot = bundle.attachments[0];
  const screenshotMeta = asRecord(screenshot?.metadata);
  const preChecklist = asArray<string>(preTrade.selected_checklist);
  const preMandatory = asArray<string>(preTrade.mandatory_checklist);
  const postChecklist = asArray<string>(postTrade.selected_checklist);
  const postMandatory = asArray<string>(postTrade.mandatory_checklist);

  // ── Editable fields (only when onSave is provided) ──
  const [editableSetup, setEditableSetup] = useState(
    (() => {
      const tag = trade.strategy_tag && trade.strategy_tag !== 'MT5 Historical Sync' ? trade.strategy_tag : null;
      const strat = trade.strategy && trade.strategy !== 'MT5 Historical Sync' ? trade.strategy : null;
      return tag || strat || '';
    })(),
  );
  const [editableProbability, setEditableProbability] = useState(trade.probability_bucket || '');
  const [editableConfidence, setEditableConfidence] = useState(trade.confidence_score != null ? String(trade.confidence_score) : '');
  const [editableNotes, setEditableNotes] = useState(trade.notes || bundle.notes[0]?.body || '');
  const [editableTags, setEditableTags] = useState(bundle.tags.map((tag) => tag.name).join(', '));
  const [dirty, setDirty] = useState(false);

  const markDirty = () => setDirty(true);

  const handleSave = async () => {
    if (!onSave) return;
    await onSave({
      strategy_tag: editableSetup || null,
      probability_bucket: editableProbability || null,
      confidence_score: editableConfidence ? Number(editableConfidence) : null,
      notes: editableNotes || null,
      tags: editableTags ? editableTags.split(',').map((t) => t.trim()).filter(Boolean) : [],
    });
    setDirty(false);
  };

  const setupValue = (() => {
    const tag = trade.strategy_tag && trade.strategy_tag !== 'MT5 Historical Sync' ? trade.strategy_tag : null;
    const strat = trade.strategy && trade.strategy !== 'MT5 Historical Sync' ? trade.strategy : null;
    return tag || strat || '—';
  })();

  return (
    <div className="space-y-6 text-black dark:text-white">
      {/* Editable header bar when in overlay mode */}
      {onSave && (
        <div className="flex items-center justify-between gap-4 rounded-[22px] border border-[#FF5900]/30 bg-[#FF5900]/5 px-5 py-3 dark:border-[#FF5900]/20 dark:bg-[#FF5900]/10">
          <p className="text-sm font-semibold text-[#FF5900]">Editing Mode</p>
          <div className="flex items-center gap-2">
            {dirty && <span className="text-xs text-gray-500 dark:text-slate-400">Unsaved changes</span>}
            <button
              type="button"
              onClick={handleSave}
              disabled={!dirty || isSaving}
              className={`rounded-full px-5 py-2 text-sm font-semibold transition ${
                dirty && !isSaving
                  ? 'bg-[#FF5900] text-white hover:brightness-110'
                  : 'bg-gray-200 text-gray-500 cursor-not-allowed dark:bg-gray-800 dark:text-gray-500'
              }`}
            >
              {isSaving ? 'Saving…' : 'Save Changes'}
            </button>
          </div>
        </div>
      )}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <SummaryCard label="Trade ID" value={(trade.trade_id || '').replace(/^mt5_/, '')} helper={`${trade.symbol} · ${trade.market_type || '—'} · ${trade.side}`} />
        <SummaryCard label="Net PnL" value={formatCurrency(Number(trade.net_pnl || 0))} helper={`Gross ${formatCurrency(Number(trade.gross_pnl || 0))} · Cost ${formatCurrency(Number(trade.total_cost || 0))}`} />
        <SummaryCard label="Entry / Exit" value={formatDateTime(trade.entry_time, trade.entry_timezone || 'UTC')} helper={trade.exit_time ? `Exit ${formatDateTime(trade.exit_time, trade.entry_timezone || 'UTC')}` : 'Trade still open'} />
        <SummaryCard label="Setup" value={setupValue} helper={`${trade.probability_bucket || '—'} · ${trade.is_closed ? 'Closed' : 'Open'}`} />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-6">
          <Group title="Trade Overview">
            {onSave ? (
              <EditableFieldGrid
                items={[
                  ['Account', trade.account_id, false],
                  ['Broker', trade.broker_id || '—', false],
                  ['Symbol', trade.symbol, false],
                  ['Market Type', trade.market_type || '—', false],
                  ['Side', trade.side, false],
                  ['Setup', setupValue, true],
                ]}
                onEdit={(field, value) => { if (field === 'Setup') { setEditableSetup(value); markDirty(); } }}
                values={{ Setup: editableSetup }}
              />
            ) : (
              <FieldGrid
                items={[
                  ['Account', trade.account_id],
                  ['Broker', trade.broker_id || '—'],
                  ['Symbol', trade.symbol],
                  ['Market Type', trade.market_type || '—'],
                  ['Side', trade.side],
                  ['Setup', setupValue],
                ]}
              />
            )}
          </Group>

          <Group title="Entry Snapshot">
            <FieldGrid
              items={[
                ['Entry Price', formatNumber(Number(trade.entry_price || 0))],
                ['Entry Time', formatDateTime(trade.entry_time)],
                ['Entry Date', formatDate(trade.entry_time)],
                ['Entry Day', trade.entry_day_of_week || '—'],
                ['Stop Loss at Entry', formatNumber(Number(trade.stop_loss_at_entry || 0))],
                ['Target at Entry', formatNumber(Number(trade.target_at_entry || 0))],
                ['Minimum Target Price', trade.minimum_target_price != null ? formatNumber(Number(trade.minimum_target_price)) : '—'],
              ]}
            />
          </Group>

          <Group title="Exit Snapshot">
            <FieldGrid
              items={[
                ['Exit Price', trade.exit_price != null ? formatNumber(Number(trade.exit_price)) : '—'],
                ['Exit Time', formatDateTime(trade.exit_time)],
                ['Exit Date', formatDate(trade.exit_time)],
                ['Exit Day', trade.exit_day_of_week || '—'],
                ['Exit Reason', trade.exit_reason || '—'],
                ['Closed Before Plan', trade.closed_before_plan ? 'Yes' : 'No'],
              ]}
            />
          </Group>

          <Group title="Economics">
            <FieldGrid
              items={[
                ['Quantity', formatNumber(Number(trade.quantity || 0))],
                ['Commission', formatCurrency(Number(trade.commission || 0))],
                ['Swaps', formatCurrency(Number(trade.swaps || 0))],
                ['Slippage Cost', formatCurrency(Number(trade.slippage_cost || 0))],
                ['Gross PnL', formatCurrency(Number(trade.gross_pnl || 0))],
                ['Net PnL', formatCurrency(Number(trade.net_pnl || 0))],
                ['Risk Amount', formatCurrency(Number(trade.risk_amount || 0))],
                ['Risk Reward Ratio', formatRatio(Number(trade.rrr_at_entry || 0))],
                ['R Multiple', formatRatio(Number(trade.r_multiple || 0))],
              ]}
            />
          </Group>

          <Group title="Execution and Rule Tracking">
            {onSave ? (
              <>
                <FieldGrid
                  items={[
                    ['Checklist Before', asArray<string>(trade.checklist_before).join(', ') || '—'],
                    ['Checklist After', asArray<string>(trade.checklist_after).join(', ') || '—'],
                    ['Rule Violation Snapshot', asArray<string>(trade.rule_violations_snapshot).join(', ') || '—'],
                    ['Rating', bundle.rating?.value != null ? String(bundle.rating.value) : '—'],
                    ['Rating Rationale', bundle.rating?.rationale || '—'],
                  ]}
                />
                <div className="mt-4">
                  <EditableLabel label="Notes">
                    <textarea
                      value={editableNotes}
                      onChange={(e) => { setEditableNotes(e.target.value); markDirty(); }}
                      className="w-full rounded-[14px] border border-black/10 bg-gray-50 px-3 py-2 text-sm text-black outline-none transition hover:border-[#FF5900] focus:border-[#FF5900] dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white"
                      rows={3}
                    />
                  </EditableLabel>
                </div>
                <div className="mt-4">
                  <EditableLabel label="Tags">
                    <input
                      type="text"
                      value={editableTags}
                      onChange={(e) => { setEditableTags(e.target.value); markDirty(); }}
                      className="w-full rounded-[14px] border border-black/10 bg-gray-50 px-3 py-2 text-sm text-black outline-none transition hover:border-[#FF5900] focus:border-[#FF5900] dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white"
                      placeholder="tag1, tag2, tag3"
                    />
                  </EditableLabel>
                </div>
              </>
            ) : (
              <FieldGrid
                items={[
                  ['Checklist Before', asArray<string>(trade.checklist_before).join(', ') || '—'],
                  ['Checklist After', asArray<string>(trade.checklist_after).join(', ') || '—'],
                  ['Rule Violation Snapshot', asArray<string>(trade.rule_violations_snapshot).join(', ') || '—'],
                  ['Notes', trade.notes || bundle.notes[0]?.body || '—'],
                  ['Rating', bundle.rating?.value != null ? String(bundle.rating.value) : '—'],
                  ['Rating Rationale', bundle.rating?.rationale || '—'],
                  ['Tags', bundle.tags.map((tag) => tag.name).join(', ') || '—'],
                ]}
              />
            )}
          </Group>
        </div>

        <div className="space-y-6">
          <Group title="Pre-Trade Capture">
            <FieldGrid
              items={[
                ['Strategy', String(preTrade.strategy_name || '—')],
                ['Probability', String(preTrade.probability_bucket || '—')],
                ['Confidence Score', trade.confidence_score != null ? formatNumber(Number(trade.confidence_score)) : '—'],
                ['Checklist Selected', preChecklist.join(', ') || '—'],
                ['Mandatory Checklist', preMandatory.join(', ') || '—'],
                ['All Criteria Selected', preTrade.all_criteria_selected ? 'Yes' : 'No'],
              ]}
            />
            {onSave && (
              <div className="mt-4 space-y-4">
                <EditableLabel label="Probability Bucket">
                  <select
                    value={editableProbability}
                    onChange={(e) => { setEditableProbability(e.target.value); markDirty(); }}
                    className="w-full rounded-[14px] border border-black/10 bg-gray-50 px-3 py-2 text-sm text-black outline-none transition hover:border-[#FF5900] focus:border-[#FF5900] dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white"
                  >
                    <option value="">—</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                  </select>
                </EditableLabel>
                <EditableLabel label="Confidence Score">
                  <input
                    type="number"
                    value={editableConfidence}
                    onChange={(e) => { setEditableConfidence(e.target.value); markDirty(); }}
                    className="w-full rounded-[14px] border border-black/10 bg-gray-50 px-3 py-2 text-sm text-black outline-none transition hover:border-[#FF5900] focus:border-[#FF5900] dark:border-white/10 dark:bg-[#0b0b0b] dark:text-white"
                    min={0}
                    max={100}
                    step={0.1}
                  />
                </EditableLabel>
              </div>
            )}
          </Group>

          <Group title="Post-Trade Capture">
            <FieldGrid
              items={[
                ['Strategy', String(postTrade.strategy_name || '—')],
                ['Probability', String(postTrade.probability_bucket || '—')],
                ['Confidence Score', trade.confidence_score != null ? formatNumber(Number(trade.confidence_score)) : '—'],
                ['Checklist Selected', postChecklist.join(', ') || '—'],
                ['Mandatory Checklist', postMandatory.join(', ') || '—'],
                ['All Criteria Selected', postTrade.all_criteria_selected ? 'Yes' : 'No'],
                ['Notes', String(postTrade.notes || '—')],
              ]}
            />
          </Group>

          <Group title="Screenshot / Attachment">
            <FieldGrid
              items={[
                ['Attachment Type', screenshot?.attachment_type || '—'],
                ['File Path', screenshot?.file_path || '—'],
                ['Content Type', screenshot?.content_type || '—'],
                ['Capture Request', String(screenshotMeta.capture_request_id || '—')],
              ]}
            />
          </Group>
        </div>
      </section>
    </div>
  );
}

function SummaryCard({ label, value, helper }: { label: string; value: string; helper: string }) {
  return (
    <article className="rounded-[22px] border border-black/10 bg-white p-5 dark:border-white/10 dark:bg-[#060606]">
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-500 dark:text-slate-400">{label}</p>
      <p className="mt-3 break-all text-lg font-semibold text-black dark:text-white">{value}</p>
      <p className="mt-2 text-sm text-gray-600 dark:text-slate-300">{helper}</p>
    </article>
  );
}

function Group({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-[26px] border border-black/10 bg-white p-6 dark:border-white/10 dark:bg-[#060606]">
      <h2 className="text-lg font-semibold text-black dark:text-white">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function FieldGrid({ items }: { items: Array<[string, string]> }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {items.map(([label, value]) => (
        <div key={label} className="rounded-[18px] border border-black/8 bg-gray-50 px-4 py-3 dark:border-white/10 dark:bg-[#0b0b0b]">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-gray-500 dark:text-slate-400">{label}</p>
          <p className="mt-2 break-words text-sm text-black dark:text-white">{value}</p>
        </div>
      ))}
    </div>
  );
}

function EditableLabel({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="mb-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-gray-500 dark:text-slate-400">{label}</p>
      {children}
    </div>
  );
}

function EditableFieldGrid({
  items,
  onEdit,
  values,
}: {
  items: Array<[string, string, boolean]>;
  onEdit?: (field: string, value: string) => void;
  values?: Record<string, string>;
}) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {items.map(([label, displayValue, isEditable]) => {
        const fieldName = label;
        const currentValue = values?.[fieldName] ?? displayValue;

        return (
          <div key={label} className="rounded-[18px] border border-black/8 bg-gray-50 px-4 py-3 dark:border-white/10 dark:bg-[#0b0b0b]">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-gray-500 dark:text-slate-400">{label}</p>
            {isEditable && onEdit ? (
              <input
                type="text"
                value={currentValue}
                onChange={(e) => onEdit(fieldName, e.target.value)}
                className="mt-2 w-full bg-transparent text-sm text-black outline-none dark:text-white"
              />
            ) : (
              <p className="mt-2 break-words text-sm text-black dark:text-white">{displayValue}</p>
            )}
          </div>
        );
      })}
    </div>
  );
}