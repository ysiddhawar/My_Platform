import { useMemo, useState } from 'react';
import { useQuery } from 'react-query';

import { fetchAIInsightsSummary } from '@/api/prototype';
import type {
  AIDashboardChartReview,
  AIDashboardMetricReview,
  AIInsightFinding,
  AIRecommendation,
  AISectionReview,
  InsightDrilldownTarget,
  InsightWorkspacePanelPayload,
} from '@/types/prototype';
import { usePrototypeStore } from '@/state/prototypeStore';

type DrilldownAction = {
  label: string;
  payload: InsightWorkspacePanelPayload;
};

function SummaryCard({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note: string;
}) {
  return (
    <article className="rounded-[22px] border border-black/10 bg-white px-5 py-4 text-black shadow-[0_16px_40px_rgba(15,23,42,0.05)] dark:border-white/10 dark:bg-[#222] dark:text-white">
      <p className="text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-black/55 dark:text-white/55">{label}</p>
      <p className="mt-2 text-[1.45rem] font-semibold tracking-[-0.04em]">{value}</p>
      <p className="mt-2 text-xs text-black/65 dark:text-white/65">{note}</p>
    </article>
  );
}

function AccordionSection({
  title,
  subtitle,
  badges,
  preview,
  open,
  onToggle,
  children,
}: {
  title: string;
  subtitle?: string;
  badges?: Array<{
    tone: 'low' | 'medium' | 'high' | 'critical' | 'info' | 'good' | 'satisfactory' | 'bad' | 'unknown' | 'now' | 'soon' | 'later';
    label: string;
  }>;
  preview?: React.ReactNode;
  open: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-[24px] border border-black/10 bg-white dark:border-white/10 dark:bg-[#222]">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-start justify-between gap-4 px-5 py-4 text-left transition-colors hover:bg-[#FF5900] hover:text-white"
      >
        <div className="min-w-0 flex-1">
          <h3 className="text-base font-semibold tracking-[-0.03em]">{title}</h3>
          {subtitle ? <p className="mt-1 text-xs text-black/60 dark:text-white/60">{subtitle}</p> : null}
          {preview ? <div className="mt-3 text-sm text-black/70 dark:text-white/70">{preview}</div> : null}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {badges?.length ? (
            <div className="hidden flex-wrap items-center justify-end gap-2 md:flex">
              {badges.map((badge) => (
                <ToneBadge key={`${title}-${badge.label}`} tone={badge.tone} label={badge.label} />
              ))}
            </div>
          ) : null}
          <span className="text-lg font-semibold">{open ? '−' : '+'}</span>
        </div>
      </button>
      {open ? <div className="border-t border-black/8 px-5 py-5 dark:border-white/8">{children}</div> : null}
    </section>
  );
}

function ToneBadge({
  tone,
  label,
}: {
  tone: 'low' | 'medium' | 'high' | 'critical' | 'info' | 'good' | 'satisfactory' | 'bad' | 'unknown' | 'now' | 'soon' | 'later';
  label: string;
}) {
  const styles: Record<string, string> = {
    low: 'bg-amber-500/12 text-amber-700 dark:bg-amber-400/12 dark:text-amber-300',
    medium: 'bg-orange-500/12 text-orange-700 dark:bg-orange-400/12 dark:text-orange-300',
    high: 'bg-rose-500/12 text-rose-700 dark:bg-rose-400/12 dark:text-rose-300',
    critical: 'bg-red-500/15 text-red-700 dark:bg-red-400/15 dark:text-red-300',
    info: 'bg-slate-950/8 text-slate-700 dark:bg-white/10 dark:text-white',
    good: 'bg-emerald-500/12 text-emerald-700 dark:bg-emerald-400/12 dark:text-emerald-300',
    satisfactory: 'bg-sky-500/12 text-sky-700 dark:bg-sky-400/12 dark:text-sky-300',
    bad: 'bg-rose-500/12 text-rose-700 dark:bg-rose-400/12 dark:text-rose-300',
    unknown: 'bg-slate-500/12 text-slate-700 dark:bg-slate-400/12 dark:text-slate-300',
    now: 'bg-[#FF5900]/15 text-[#FF5900]',
    soon: 'bg-amber-500/12 text-amber-700 dark:bg-amber-400/12 dark:text-amber-300',
    later: 'bg-slate-950/8 text-slate-700 dark:bg-white/10 dark:text-white',
  };

  return <span className={`rounded-full px-3 py-1 text-[0.68rem] font-semibold capitalize ${styles[tone] || styles.info}`}>{label}</span>;
}

function ConfidenceLine({ confidence, sampleSize }: { confidence: string; sampleSize: number }) {
  return (
    <p className="text-xs text-black/60 dark:text-white/60">
      Confidence: <span className="font-semibold capitalize">{confidence}</span> · Based on {sampleSize} trades/events
    </p>
  );
}

function TagStrip({ label, items }: { label: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div className="flex flex-wrap gap-2">
      <span className="text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-black/45 dark:text-white/45">{label}</span>
      {items.map((item) => (
        <span
          key={`${label}-${item}`}
          className="rounded-full border border-black/10 px-2.5 py-1 text-[0.68rem] font-medium text-black/70 dark:border-white/10 dark:text-white/70"
        >
          {item.replaceAll('_', ' ')}
        </span>
      ))}
    </div>
  );
}

function InsightCard({
  item,
  drilldown,
  onDrilldown,
}: {
  item: AIInsightFinding;
  drilldown?: DrilldownAction | null;
  onDrilldown?: (payload: InsightWorkspacePanelPayload) => void;
}) {
  return (
    <article className="rounded-[22px] border border-black/8 bg-black/[0.02] p-4 dark:border-white/8 dark:bg-black/25">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h4 className="text-base font-semibold tracking-[-0.03em]">{item.title}</h4>
          <p className="mt-2 text-sm leading-6 text-black/75 dark:text-white/75">{item.explanation}</p>
        </div>
        <ToneBadge tone={item.severity} label={item.severity} />
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <ToneBadge tone="info" label={`Impact ${Math.round(item.impact_score * 100)}%`} />
        <ConfidenceLine confidence={item.confidence} sampleSize={item.sample_size} />
      </div>

      {item.evidence.length ? (
        <div className="mt-4 rounded-[18px] border border-black/8 bg-white/70 p-3 dark:border-white/8 dark:bg-white/[0.03]">
          <p className="text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-black/45 dark:text-white/45">Evidence</p>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {item.evidence.map((evidence) => (
              <div key={`${item.id}-${evidence.label}`} className="rounded-[16px] bg-black/[0.03] px-3 py-2 dark:bg-black/30">
                <p className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-black/40 dark:text-white/40">{evidence.label}</p>
                <p className="mt-1 text-sm font-semibold">{evidence.value}</p>
                {evidence.comparison ? <p className="mt-1 text-xs text-black/60 dark:text-white/60">{evidence.comparison}</p> : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {item.impact_description ? (
        <div className="mt-4 rounded-[18px] bg-[#FF5900]/8 px-3 py-3 text-sm leading-6 text-black/80 dark:text-white/80">
          <span className="font-semibold">Why it matters:</span> {item.impact_description}
        </div>
      ) : null}

      <div className="mt-4 space-y-2">
        <TagStrip label="Categories" items={item.categories} />
        <TagStrip label="Dimensions" items={item.dimensions} />
        <TagStrip label="Behavior" items={item.behavior_tags} />
      </div>

      {drilldown && onDrilldown ? (
        <div className="mt-4 flex justify-end">
          <button
            type="button"
            onClick={() => onDrilldown(drilldown.payload)}
            className="rounded-full bg-[#FF5900] px-4 py-2 text-xs font-semibold text-white transition hover:bg-[#e65100]"
          >
            {drilldown.label}
          </button>
        </div>
      ) : null}
    </article>
  );
}

function RecommendationCard({
  item,
  drilldown,
  onDrilldown,
}: {
  item: AIRecommendation;
  drilldown?: DrilldownAction | null;
  onDrilldown?: (payload: InsightWorkspacePanelPayload) => void;
}) {
  return (
    <article className="rounded-[22px] border border-black/8 bg-black/[0.02] p-4 dark:border-white/8 dark:bg-black/25">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h4 className="text-base font-semibold tracking-[-0.03em]">{item.title}</h4>
          <p className="mt-2 text-sm font-medium text-black/80 dark:text-white/80">{item.action}</p>
        </div>
        <ToneBadge tone={item.priority} label={item.priority} />
      </div>

      <p className="mt-3 text-sm leading-6 text-black/75 dark:text-white/75">{item.why}</p>

      {item.implementation.length ? (
        <div className="mt-4 rounded-[18px] border border-black/8 bg-white/70 p-3 dark:border-white/8 dark:bg-white/[0.03]">
          <p className="text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-black/45 dark:text-white/45">How to do it</p>
          <ol className="mt-3 space-y-2 text-sm leading-6 text-black/75 dark:text-white/75">
            {item.implementation.map((step, index) => (
              <li key={`${item.id}-${index}`} className="flex gap-3">
                <span className="mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#FF5900] text-[0.68rem] font-semibold text-white">
                  {index + 1}
                </span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </div>
      ) : null}

      {item.expected_benefit ? (
        <p className="mt-4 text-sm leading-6 text-black/70 dark:text-white/70">
          <span className="font-semibold">Expected benefit:</span> {item.expected_benefit}
        </p>
      ) : null}

      {item.source_insight_ids.length ? (
        <p className="mt-3 text-xs text-black/55 dark:text-white/55">Triggered by {item.source_insight_ids.length} supporting insight{item.source_insight_ids.length > 1 ? 's' : ''}.</p>
      ) : null}

      {drilldown && onDrilldown ? (
        <div className="mt-4 flex justify-end">
          <button
            type="button"
            onClick={() => onDrilldown(drilldown.payload)}
            className="rounded-full bg-[#FF5900] px-4 py-2 text-xs font-semibold text-white transition hover:bg-[#e65100]"
          >
            {drilldown.label}
          </button>
        </div>
      ) : null}
    </article>
  );
}

function InsightSection({
  title,
  items,
  emptyMessage,
  getDrilldown,
  onOpenDrilldown,
}: {
  title: string;
  items: AIInsightFinding[];
  emptyMessage: string;
  getDrilldown?: (finding: AIInsightFinding) => DrilldownAction | null;
  onOpenDrilldown?: (payload: InsightWorkspacePanelPayload) => void;
}) {
  return (
    <section className="rounded-[26px] border border-black/10 bg-white p-5 dark:border-white/10 dark:bg-[#222]">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-semibold tracking-[-0.03em]">{title}</h3>
        <span className="rounded-full bg-black/6 px-3 py-1 text-xs font-semibold text-black/70 dark:bg-white/10 dark:text-white/70">{items.length}</span>
      </div>
      <div className="mt-4 space-y-4">
        {items.length ? items.map((item) => <InsightCard key={item.id} item={item} drilldown={getDrilldown?.(item)} onDrilldown={onOpenDrilldown} />) : <EmptyState message={emptyMessage} />}
      </div>
    </section>
  );
}

function RecommendationSection({
  title,
  items,
  emptyMessage,
  getDrilldown,
  onOpenDrilldown,
}: {
  title: string;
  items: AIRecommendation[];
  emptyMessage: string;
  getDrilldown?: (recommendation: AIRecommendation) => DrilldownAction | null;
  onOpenDrilldown?: (payload: InsightWorkspacePanelPayload) => void;
}) {
  return (
    <section className="rounded-[26px] border border-black/10 bg-white p-5 dark:border-white/10 dark:bg-[#222]">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-semibold tracking-[-0.03em]">{title}</h3>
        <span className="rounded-full bg-black/6 px-3 py-1 text-xs font-semibold text-black/70 dark:bg-white/10 dark:text-white/70">{items.length}</span>
      </div>
      <div className="mt-4 space-y-4">
        {items.length ? items.map((item) => <RecommendationCard key={item.id} item={item} drilldown={getDrilldown?.(item)} onDrilldown={onOpenDrilldown} />) : <EmptyState message={emptyMessage} />}
      </div>
    </section>
  );
}

function MetricReviewCard({ item }: { item: AIDashboardMetricReview }) {
  return (
    <article className="rounded-[20px] border border-black/8 bg-black/[0.02] p-4 dark:border-white/8 dark:bg-black/25">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h4 className="text-base font-semibold tracking-[-0.03em]">{item.label}</h4>
          <p className="mt-1 text-sm text-black/65 dark:text-white/65">{item.current_value_summary}</p>
        </div>
        <ToneBadge tone={item.status} label={item.status} />
      </div>
      <p className="mt-3 text-sm leading-6 text-black/75 dark:text-white/75">{item.meaning}</p>
      <p className="mt-3 text-sm leading-6 text-black/70 dark:text-white/70">{item.what_it_shows}</p>
      <div className="mt-4 grid gap-2 text-xs text-black/65 dark:text-white/65">
        {item.healthy_range ? <p><span className="font-semibold">Good:</span> {item.healthy_range}</p> : null}
        {item.satisfactory_range ? <p><span className="font-semibold">Satisfactory:</span> {item.satisfactory_range}</p> : null}
        {item.weak_range ? <p><span className="font-semibold">Weak:</span> {item.weak_range}</p> : null}
      </div>
    </article>
  );
}

function ChartReviewCard({ item }: { item: AIDashboardChartReview }) {
  return (
    <article className="rounded-[20px] border border-black/8 bg-black/[0.02] p-4 dark:border-white/8 dark:bg-black/25">
      <h4 className="text-base font-semibold tracking-[-0.03em]">{item.label}</h4>
      <p className="mt-3 text-sm leading-6 text-black/75 dark:text-white/75">{item.meaning}</p>
      <p className="mt-3 text-sm leading-6 text-black/70 dark:text-white/70">{item.what_it_shows}</p>
      <p className="mt-3 text-sm leading-6 text-black/80 dark:text-white/80">
        <span className="font-semibold">Important takeaway:</span> {item.important_takeaway}
      </p>
    </article>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <p className="rounded-[20px] border border-dashed border-black/10 px-4 py-5 text-sm text-black/60 dark:border-white/10 dark:text-white/60">
      {message}
    </p>
  );
}

function SectionCountStrip({
  wrong,
  why,
  right,
  next,
}: {
  wrong: number;
  why: number;
  right: number;
  next: number;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      <ToneBadge tone={wrong > 0 ? 'high' : 'info'} label={`${wrong} wrong`} />
      <ToneBadge tone={why > 0 ? 'medium' : 'info'} label={`${why} why`} />
      <ToneBadge tone={right > 0 ? 'good' : 'info'} label={`${right} right`} />
      <ToneBadge tone={next > 0 ? 'now' : 'info'} label={`${next} next`} />
    </div>
  );
}

function buildReviewPreview(review: AISectionReview) {
  const firstWrong = review.what_is_going_wrong[0]?.title;
  const firstRight = review.what_is_going_right[0]?.title;
  const firstNext = review.what_to_do_next[0]?.action;

  return (
    <div className="space-y-2">
      <SectionCountStrip
        wrong={review.what_is_going_wrong.length}
        why={review.why_it_is_going_wrong.length}
        right={review.what_is_going_right.length}
        next={review.what_to_do_next.length}
      />
      <div className="space-y-1 text-xs leading-5 text-black/60 dark:text-white/60">
        {firstWrong ? <p><span className="font-semibold">Top issue:</span> {firstWrong}</p> : null}
        {firstRight ? <p><span className="font-semibold">Top strength:</span> {firstRight}</p> : null}
        {firstNext ? <p><span className="font-semibold">Top next step:</span> {firstNext}</p> : null}
      </div>
    </div>
  );
}

function getEvidenceValue(finding: AIInsightFinding, labelFragment: string) {
  const fragment = labelFragment.toLowerCase();
  return finding.evidence.find((item) => item.label.toLowerCase().includes(fragment))?.value || null;
}

function parseSetupSymbolPair(value?: string | null) {
  if (!value) return null;
  const separator = ' on ';
  const index = value.lastIndexOf(separator);
  if (index === -1) return null;
  return {
    setup: value.slice(0, index).trim(),
    symbol: value.slice(index + separator.length).trim(),
  };
}

function findWeekday(text: string) {
  return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].find((weekday) =>
    text.toLowerCase().includes(weekday.toLowerCase()),
  ) || null;
}

function makePanelPayload(
  findingOrRecommendation: {
    title: string;
    explanation?: string;
    action?: string;
    why?: string;
    evidence?: AIInsightFinding['evidence'];
  },
  target: InsightDrilldownTarget,
  actionLabel: string,
): InsightWorkspacePanelPayload {
  return {
    target,
    title: findingOrRecommendation.title,
    summary:
      findingOrRecommendation.action ||
      findingOrRecommendation.explanation ||
      findingOrRecommendation.why ||
      null,
    actionLabel,
    evidence: findingOrRecommendation.evidence || [],
  };
}

function normalizeBackendDrilldown(
  item: {
    title: string;
    explanation?: string;
    action?: string;
    why?: string;
    evidence?: AIInsightFinding['evidence'];
  },
  target?: AIInsightFinding['drilldown'] | AIRecommendation['drilldown'] | null,
): DrilldownAction | null {
  if (!target?.view) return null;
  const label =
    target.view === 'dashboard'
      ? 'Open in Dashboard'
      : target.view === 'journal'
        ? 'Open in Journal'
        : target.view === 'calendar'
          ? 'Open in Calendar'
          : target.view === 'missed-opportunities'
            ? 'Open in Missed Opportunities'
            : 'Open Insight View';

  return {
    label,
    payload: makePanelPayload(item, {
      view: target.view,
      dashboardFiltersPatch: target.dashboard_filters_patch,
      dashboardFocusGroup: target.dashboard_focus_group,
      dashboardFocusChart: target.dashboard_focus_chart,
      journalSearchText: target.journal_search_text ?? undefined,
      missedOpportunitySearchText: target.missed_opportunity_search_text ?? undefined,
      selectedTradeId: target.selected_trade_id ?? undefined,
      selectedDay: target.selected_day ?? undefined,
      calendarVisibleMonth: target.calendar_visible_month ?? undefined,
      calendarVisibleYear: target.calendar_visible_year ?? undefined,
    }, label),
  };
}

function buildFindingDrilldown(finding: AIInsightFinding): DrilldownAction | null {
  const backendDrilldown = normalizeBackendDrilldown(finding, finding.drilldown);
  if (backendDrilldown) return backendDrilldown;
  const title = finding.title.toLowerCase();

  if (title.includes('same setup is not working equally well across symbols') || title.includes('repeatable setup-symbol edge')) {
    const pairValue = getEvidenceValue(finding, 'weakest setup-symbol pair') || getEvidenceValue(finding, 'strongest setup-symbol pair');
    const pair = parseSetupSymbolPair(pairValue);
    if (!pair) return null;
    return {
      label: 'Open in Dashboard',
      payload: makePanelPayload(finding, {
        view: 'dashboard',
        dashboardFiltersPatch: {
          strategyFilter: pair.setup,
          symbolFilter: pair.symbol,
        },
      }, 'Open in Dashboard'),
    };
  }

  if (title.includes('early exits are likely reducing reward capture')) {
    return {
      label: 'Open in Dashboard',
      payload: makePanelPayload(finding, {
        view: 'dashboard',
        dashboardFiltersPatch: {
          closedEarlyFilter: 'yes',
        },
      }, 'Open in Dashboard'),
    };
  }

  const weekday = findWeekday(finding.title);
  if (weekday && finding.dimensions.includes('day')) {
    return {
      label: 'Open in Dashboard',
      payload: makePanelPayload(finding, {
        view: 'dashboard',
        dashboardFiltersPatch: {
          dayFilter: weekday,
        },
      }, 'Open in Dashboard'),
    };
  }

  if (title.includes('missed opportunities are concentrated') || title.includes('large portion of valid setups are being missed')) {
    const searchText = getEvidenceValue(finding, 'top missed symbol') || getEvidenceValue(finding, 'most missed strategy') || getEvidenceValue(finding, 'top missed setup');
    if (!searchText) return null;
    return {
      label: 'Open in Missed Opportunities',
      payload: makePanelPayload(finding, {
        view: 'missed-opportunities',
        missedOpportunitySearchText: searchText,
      }, 'Open in Missed Opportunities'),
    };
  }

  return null;
}

function buildRecommendationDrilldown(
  recommendation: AIRecommendation,
  findingLookup: Record<string, AIInsightFinding>,
): DrilldownAction | null {
  const sourceFinding = recommendation.source_insight_ids.map((id) => findingLookup[id]).find(Boolean);
  const backendDrilldown = normalizeBackendDrilldown(
    {
      title: recommendation.title,
      action: recommendation.action,
      why: recommendation.why,
      evidence: sourceFinding?.evidence || [],
    },
    recommendation.drilldown,
  );
  if (backendDrilldown) return backendDrilldown;
  for (const sourceId of recommendation.source_insight_ids) {
    const finding = findingLookup[sourceId];
    if (!finding) continue;
    const drilldown = buildFindingDrilldown(finding);
    if (drilldown) return drilldown;
  }
  return null;
}

function formatDate(value?: string | null) {
  if (!value) return 'n/a';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(date);
}

export function AIInsightsScreen() {
  const accountId = usePrototypeStore((state) => state.accountId);
  const openInsightDrilldown = usePrototypeStore((state) => state.openInsightDrilldown);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    dashboard: false,
    journal: false,
    missed_opportunities: false,
    calendar: false,
  });
  const [dashboardPanels, setDashboardPanels] = useState<Record<string, boolean>>({
    metrics: true,
    charts: false,
    findings: true,
  });

  const { data, isLoading, error } = useQuery(
    ['prototype-ai-insights-summary', accountId],
    () => fetchAIInsightsSummary(accountId as string),
    { enabled: Boolean(accountId), staleTime: 60000 },
  );

  const headlineSummary = useMemo(() => data?.headline_summary || [], [data?.headline_summary]);
  const findingLookup = useMemo(() => {
    if (!data) return {} as Record<string, AIInsightFinding>;
    const allFindings = [
      ...data.summary.what_is_going_wrong,
      ...data.summary.why_it_is_going_wrong,
      ...data.summary.what_is_going_right,
      ...data.detailed_review.dashboard.what_is_going_wrong,
      ...data.detailed_review.dashboard.why_it_is_going_wrong,
      ...data.detailed_review.dashboard.what_is_going_right,
      ...data.detailed_review.journal.what_is_going_wrong,
      ...data.detailed_review.journal.why_it_is_going_wrong,
      ...data.detailed_review.journal.what_is_going_right,
      ...data.detailed_review.missed_opportunities.what_is_going_wrong,
      ...data.detailed_review.missed_opportunities.why_it_is_going_wrong,
      ...data.detailed_review.missed_opportunities.what_is_going_right,
      ...data.detailed_review.calendar.what_is_going_wrong,
      ...data.detailed_review.calendar.why_it_is_going_wrong,
      ...data.detailed_review.calendar.what_is_going_right,
    ];
    return Object.fromEntries(allFindings.map((item) => [item.id, item]));
  }, [data]);
  const generatedAt = formatDate(data?.metadata?.generated_at);
  const visiblePeriod = data?.metadata?.visible_period;
  const visibleRange =
    visiblePeriod?.start && visiblePeriod?.end ? `${formatDate(visiblePeriod.start)} to ${formatDate(visiblePeriod.end)}` : 'n/a';

  const toggleSection = (key: string) => {
    setOpenSections((current) => ({ ...current, [key]: !current[key] }));
  };
  const toggleDashboardPanel = (key: string) => {
    setDashboardPanels((current) => ({ ...current, [key]: !current[key] }));
  };

  if (!accountId) {
    return (
      <section className="rounded-[26px] border border-black/10 bg-white p-6 text-black dark:border-white/10 dark:bg-[#222] dark:text-white">
        <h2 className="text-[1.9rem] font-semibold tracking-[-0.05em]">AI Insights</h2>
        <p className="mt-3 text-sm text-black/65 dark:text-white/70">
          Select an account to generate the full insight layer. We’ll use your dashboard, journal, calendar, missed opportunities, and behavioral data together to show what is going wrong, why it is happening, what is working, and what to do next.
        </p>
      </section>
    );
  }

  return (
    <section className="space-y-5 text-black dark:text-white">
      <div className="rounded-[26px] border border-black/10 bg-white p-6 dark:border-white/10 dark:bg-[#222]">
        <h2 className="text-[1.9rem] font-semibold tracking-[-0.05em]">AI Insights</h2>
        <p className="mt-3 text-sm leading-6 text-black/65 dark:text-white/70">
          This view now reads the unified backend insight engine. It cross-references your dashboard metrics, journal trades, missed opportunities, calendar behavior, and trading sessions to produce ranked findings and actionable next steps.
        </p>
      </div>

      {isLoading ? (
        <div className="rounded-[24px] border border-black/10 bg-white px-5 py-8 text-sm text-black/65 dark:border-white/10 dark:bg-[#222] dark:text-white/70">
          Building your AI review across all sections…
        </div>
      ) : null}

      {error instanceof Error ? (
        <div className="rounded-[24px] border border-rose-500/20 bg-rose-50 px-5 py-4 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">
          {error.message}
        </div>
      ) : null}

      {!isLoading && !(error instanceof Error) && data ? (
        <>
          <div className="grid gap-4 xl:grid-cols-4">
            <SummaryCard label="Trades Analysed" value={String(data.metadata.trade_count || 0)} note="All trades considered in the current insight run." />
            <SummaryCard label="Closed Trades" value={String(data.metadata.closed_trade_count || 0)} note="Closed trades used for most evidence-backed findings." />
            <SummaryCard label="Missed Opportunities" value={String(data.metadata.missed_opportunity_count || 0)} note="Observed valid setups that were not executed." />
            <SummaryCard label="Analysis Stage" value={data.metadata.analysis_stage || 'n/a'} note={`Generated ${generatedAt} · Range ${visibleRange}`} />
          </div>

          <section className="rounded-[26px] border border-black/10 bg-white p-5 dark:border-white/10 dark:bg-[#222]">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-black/55 dark:text-white/55">Headline Summary</p>
                <h3 className="mt-2 text-lg font-semibold tracking-[-0.03em]">Immediate read on the account</h3>
              </div>
              <ToneBadge tone="info" label={`${headlineSummary.length} highlights`} />
            </div>
            <div className="mt-4 space-y-3">
              {headlineSummary.length ? (
                headlineSummary.map((line) => (
                  <p key={line} className="rounded-[18px] bg-black/[0.03] px-4 py-3 text-sm leading-6 text-black/80 dark:bg-black/25 dark:text-white/80">
                    {line}
                  </p>
                ))
              ) : (
                <EmptyState message="No headline summary is available yet for this account." />
              )}
            </div>
          </section>

          <AccordionSection
            title="Detailed review of each section"
            subtitle="Open this to inspect dashboard, journal, missed opportunities, and calendar reviews in detail."
            badges={[
              { tone: 'high', label: `${data.detailed_review.dashboard.what_is_going_wrong.length + data.detailed_review.journal.what_is_going_wrong.length + data.detailed_review.missed_opportunities.what_is_going_wrong.length + data.detailed_review.calendar.what_is_going_wrong.length} issues` },
              { tone: 'good', label: `${data.detailed_review.dashboard.what_is_going_right.length + data.detailed_review.journal.what_is_going_right.length + data.detailed_review.missed_opportunities.what_is_going_right.length + data.detailed_review.calendar.what_is_going_right.length} strengths` },
              { tone: 'now', label: `${data.summary.what_to_do_next.length} priority actions` },
            ]}
            preview={
              <div className="space-y-2">
                <p className="text-sm leading-6">
                  This is the full, section-by-section inspection layer. Keep it closed for the quick answer flow above, or open it when you want the evidence and recommendations broken down by dashboard, journal, missed opportunities, and calendar behavior.
                </p>
                <SectionCountStrip
                  wrong={
                    data.detailed_review.dashboard.what_is_going_wrong.length +
                    data.detailed_review.journal.what_is_going_wrong.length +
                    data.detailed_review.missed_opportunities.what_is_going_wrong.length +
                    data.detailed_review.calendar.what_is_going_wrong.length
                  }
                  why={
                    data.detailed_review.dashboard.why_it_is_going_wrong.length +
                    data.detailed_review.journal.why_it_is_going_wrong.length +
                    data.detailed_review.missed_opportunities.why_it_is_going_wrong.length +
                    data.detailed_review.calendar.why_it_is_going_wrong.length
                  }
                  right={
                    data.detailed_review.dashboard.what_is_going_right.length +
                    data.detailed_review.journal.what_is_going_right.length +
                    data.detailed_review.missed_opportunities.what_is_going_right.length +
                    data.detailed_review.calendar.what_is_going_right.length
                  }
                  next={
                    data.detailed_review.dashboard.what_to_do_next.length +
                    data.detailed_review.journal.what_to_do_next.length +
                    data.detailed_review.missed_opportunities.what_to_do_next.length +
                    data.detailed_review.calendar.what_to_do_next.length
                  }
                />
              </div>
            }
            open={detailsOpen}
            onToggle={() => setDetailsOpen((current) => !current)}
          >
            <div className="space-y-4">
              <AccordionSection
                title="Detailed Dashboard Review"
                badges={[
                  { tone: 'info', label: `${data.detailed_review.dashboard.metric_reviews.length} metrics` },
                  { tone: 'info', label: `${data.detailed_review.dashboard.chart_reviews.length} charts` },
                ]}
                preview={buildReviewPreview(data.detailed_review.dashboard)}
                open={openSections.dashboard}
                onToggle={() => toggleSection('dashboard')}
              >
                <div className="space-y-5">
                  <SectionCountStrip
                    wrong={data.detailed_review.dashboard.what_is_going_wrong.length}
                    why={data.detailed_review.dashboard.why_it_is_going_wrong.length}
                    right={data.detailed_review.dashboard.what_is_going_right.length}
                    next={data.detailed_review.dashboard.what_to_do_next.length}
                  />

                  <AccordionSection
                    title="Metric Reviews"
                    subtitle="What each important dashboard metric means, what your current value shows, and what counts as good, satisfactory, or weak."
                    badges={[{ tone: 'info', label: `${data.detailed_review.dashboard.metric_reviews.length} items` }]}
                    open={dashboardPanels.metrics}
                    onToggle={() => toggleDashboardPanel('metrics')}
                  >
                    <div className="grid gap-4 xl:grid-cols-2">
                      {data.detailed_review.dashboard.metric_reviews.map((item) => (
                        <MetricReviewCard key={item.metric_key} item={item} />
                      ))}
                    </div>
                  </AccordionSection>

                  <AccordionSection
                    title="Chart Reviews"
                    subtitle="Plain-language explanation of what each dashboard visualization is showing and what deserves attention."
                    badges={[{ tone: 'info', label: `${data.detailed_review.dashboard.chart_reviews.length} items` }]}
                    open={dashboardPanels.charts}
                    onToggle={() => toggleDashboardPanel('charts')}
                  >
                    <div className="grid gap-4 xl:grid-cols-2">
                      {data.detailed_review.dashboard.chart_reviews.map((item) => (
                        <ChartReviewCard key={item.chart_key} item={item} />
                      ))}
                    </div>
                  </AccordionSection>

                  <AccordionSection
                    title="Dashboard Findings And Actions"
                    subtitle="The ranked dashboard-specific issues, causes, strengths, and recommended adjustments."
                    badges={[
                      { tone: 'high', label: `${data.detailed_review.dashboard.what_is_going_wrong.length} wrong` },
                      { tone: 'good', label: `${data.detailed_review.dashboard.what_is_going_right.length} right` },
                      { tone: 'now', label: `${data.detailed_review.dashboard.what_to_do_next.length} next` },
                    ]}
                    open={dashboardPanels.findings}
                    onToggle={() => toggleDashboardPanel('findings')}
                  >
                    <div className="grid gap-4 xl:grid-cols-2">
                      <InsightSection title="What is going wrong" items={data.detailed_review.dashboard.what_is_going_wrong} emptyMessage="No dashboard weaknesses were ranked yet." getDrilldown={buildFindingDrilldown} onOpenDrilldown={openInsightDrilldown} />
                      <InsightSection title="Why it is going wrong" items={data.detailed_review.dashboard.why_it_is_going_wrong} emptyMessage="No dashboard causes were ranked yet." getDrilldown={buildFindingDrilldown} onOpenDrilldown={openInsightDrilldown} />
                      <InsightSection title="What is going right" items={data.detailed_review.dashboard.what_is_going_right} emptyMessage="No dashboard strengths were ranked yet." getDrilldown={buildFindingDrilldown} onOpenDrilldown={openInsightDrilldown} />
                      <RecommendationSection title="What to do next" items={data.detailed_review.dashboard.what_to_do_next} emptyMessage="No dashboard recommendations were generated yet." getDrilldown={(item) => buildRecommendationDrilldown(item, findingLookup)} onOpenDrilldown={openInsightDrilldown} />
                    </div>
                  </AccordionSection>
                </div>
              </AccordionSection>

              <AccordionSection
                title="Detailed Journal Review"
                preview={buildReviewPreview(data.detailed_review.journal)}
                open={openSections.journal}
                onToggle={() => toggleSection('journal')}
              >
                <div className="grid gap-4 xl:grid-cols-2">
                  <InsightSection title="What is going wrong" items={data.detailed_review.journal.what_is_going_wrong} emptyMessage="No journal weaknesses were ranked yet." getDrilldown={buildFindingDrilldown} onOpenDrilldown={openInsightDrilldown} />
                  <InsightSection title="Why it is going wrong" items={data.detailed_review.journal.why_it_is_going_wrong} emptyMessage="No journal causes were ranked yet." getDrilldown={buildFindingDrilldown} onOpenDrilldown={openInsightDrilldown} />
                  <InsightSection title="What is going right" items={data.detailed_review.journal.what_is_going_right} emptyMessage="No journal strengths were ranked yet." getDrilldown={buildFindingDrilldown} onOpenDrilldown={openInsightDrilldown} />
                  <RecommendationSection title="What to do next" items={data.detailed_review.journal.what_to_do_next} emptyMessage="No journal recommendations were generated yet." getDrilldown={(item) => buildRecommendationDrilldown(item, findingLookup)} onOpenDrilldown={openInsightDrilldown} />
                </div>
              </AccordionSection>

              <AccordionSection
                title="Detailed Missed Opportunities Review"
                preview={buildReviewPreview(data.detailed_review.missed_opportunities)}
                open={openSections.missed_opportunities}
                onToggle={() => toggleSection('missed_opportunities')}
              >
                <div className="grid gap-4 xl:grid-cols-2">
                  <InsightSection title="What is going wrong" items={data.detailed_review.missed_opportunities.what_is_going_wrong} emptyMessage="No missed-opportunity weaknesses were ranked yet." getDrilldown={buildFindingDrilldown} onOpenDrilldown={openInsightDrilldown} />
                  <InsightSection title="Why it is going wrong" items={data.detailed_review.missed_opportunities.why_it_is_going_wrong} emptyMessage="No missed-opportunity causes were ranked yet." getDrilldown={buildFindingDrilldown} onOpenDrilldown={openInsightDrilldown} />
                  <InsightSection title="What is going right" items={data.detailed_review.missed_opportunities.what_is_going_right} emptyMessage="No missed-opportunity strengths were ranked yet." getDrilldown={buildFindingDrilldown} onOpenDrilldown={openInsightDrilldown} />
                  <RecommendationSection title="What to do next" items={data.detailed_review.missed_opportunities.what_to_do_next} emptyMessage="No missed-opportunity recommendations were generated yet." getDrilldown={(item) => buildRecommendationDrilldown(item, findingLookup)} onOpenDrilldown={openInsightDrilldown} />
                </div>
              </AccordionSection>

              <AccordionSection
                title="Detailed Calendar Review"
                preview={buildReviewPreview(data.detailed_review.calendar)}
                open={openSections.calendar}
                onToggle={() => toggleSection('calendar')}
              >
                <div className="grid gap-4 xl:grid-cols-2">
                  <InsightSection title="What is going wrong" items={data.detailed_review.calendar.what_is_going_wrong} emptyMessage="No calendar weaknesses were ranked yet." getDrilldown={buildFindingDrilldown} onOpenDrilldown={openInsightDrilldown} />
                  <InsightSection title="Why it is going wrong" items={data.detailed_review.calendar.why_it_is_going_wrong} emptyMessage="No calendar causes were ranked yet." getDrilldown={buildFindingDrilldown} onOpenDrilldown={openInsightDrilldown} />
                  <InsightSection title="What is going right" items={data.detailed_review.calendar.what_is_going_right} emptyMessage="No calendar strengths were ranked yet." getDrilldown={buildFindingDrilldown} onOpenDrilldown={openInsightDrilldown} />
                  <RecommendationSection title="What to do next" items={data.detailed_review.calendar.what_to_do_next} emptyMessage="No calendar recommendations were generated yet." getDrilldown={(item) => buildRecommendationDrilldown(item, findingLookup)} onOpenDrilldown={openInsightDrilldown} />
                </div>
              </AccordionSection>
            </div>
          </AccordionSection>

          <div className="grid gap-4 xl:grid-cols-2">
            <InsightSection title="1. What is going wrong" items={data.summary.what_is_going_wrong} emptyMessage="No top-ranked weaknesses were returned for this account yet." getDrilldown={buildFindingDrilldown} onOpenDrilldown={openInsightDrilldown} />
            <InsightSection title="2. Why it is going wrong" items={data.summary.why_it_is_going_wrong} emptyMessage="No top-ranked causes were returned for this account yet." getDrilldown={buildFindingDrilldown} onOpenDrilldown={openInsightDrilldown} />
            <InsightSection title="3. What is going right" items={data.summary.what_is_going_right} emptyMessage="No top-ranked strengths were returned for this account yet." getDrilldown={buildFindingDrilldown} onOpenDrilldown={openInsightDrilldown} />
            <RecommendationSection title="4. What to do next" items={data.summary.what_to_do_next} emptyMessage="No top-ranked next steps were returned for this account yet." getDrilldown={(item) => buildRecommendationDrilldown(item, findingLookup)} onOpenDrilldown={openInsightDrilldown} />
          </div>
        </>
      ) : null}
    </section>
  );
}
