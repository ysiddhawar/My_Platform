import { useMemo } from 'react';
import { useQuery } from 'react-query';

import { fetchAIInsightsSummary } from '@/api/prototype';
import type {
  AIInsightFinding,
  AIRecommendation,
  InsightDrilldownTarget,
  InsightWorkspacePanelPayload,
} from '@/types/prototype';
import { usePrototypeStore } from '@/state/prototypeStore';

type DrilldownAction = {
  label: string;
  payload: InsightWorkspacePanelPayload;
};

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
  title?: string | null;
  items: AIInsightFinding[];
  emptyMessage: string;
  getDrilldown?: (finding: AIInsightFinding) => DrilldownAction | null;
  onOpenDrilldown?: (payload: InsightWorkspacePanelPayload) => void;
}) {
  return (
    <section>
      {title ? (
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-lg font-semibold tracking-[-0.03em]">{title}</h3>
          <span className="rounded-full bg-black/6 px-3 py-1 text-xs font-semibold text-black/70 dark:bg-white/10 dark:text-white/70">{items.length}</span>
        </div>
      ) : null}
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
  title?: string | null;
  items: AIRecommendation[];
  emptyMessage: string;
  getDrilldown?: (recommendation: AIRecommendation) => DrilldownAction | null;
  onOpenDrilldown?: (payload: InsightWorkspacePanelPayload) => void;
}) {
  return (
    <section>
      {title ? (
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-lg font-semibold tracking-[-0.03em]">{title}</h3>
          <span className="rounded-full bg-black/6 px-3 py-1 text-xs font-semibold text-black/70 dark:bg-white/10 dark:text-white/70">{items.length}</span>
        </div>
      ) : null}
      <div className="mt-4 space-y-4">
        {items.length ? items.map((item) => <RecommendationCard key={item.id} item={item} drilldown={getDrilldown?.(item)} onDrilldown={onOpenDrilldown} />) : <EmptyState message={emptyMessage} />}
      </div>
    </section>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <p className="rounded-[20px] border border-dashed border-black/10 px-4 py-5 text-sm text-black/60 dark:border-white/10 dark:text-white/60">
      {message}
    </p>
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

export function AIInsightsScreen({ activeTab, onTabChange }: { activeTab: 'good' | 'bad' | 'recommended'; onTabChange: (tab: 'good' | 'bad' | 'recommended') => void }) {
  const accountId = usePrototypeStore((state) => state.accountId);
  const openInsightDrilldown = usePrototypeStore((state) => state.openInsightDrilldown);
  const { data, isLoading, error } = useQuery(
    ['prototype-ai-insights-summary', accountId],
    () => fetchAIInsightsSummary(accountId as string),
    { enabled: Boolean(accountId), staleTime: 60000 },
  );



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
    <>

        {isLoading ? (
        <div className="px-2 md:px-3 xl:px-4">
          <div className="rounded-[24px] border border-black/10 bg-white px-5 py-8 text-sm text-black/65 dark:border-white/10 dark:bg-[#222] dark:text-white/70">
            Building your AI review across all sections…
          </div>
        </div>
      ) : null}

        {error instanceof Error ? (
        <div className="px-2 md:px-3 xl:px-4">
          <div className="rounded-[24px] border border-rose-500/20 bg-rose-50 px-5 py-4 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">
            {error.message}
          </div>
      </div>
      ) : null}

      {!isLoading && !(error instanceof Error) && data ? (
<>
          {/* Tab Content */}
              {activeTab === 'good' && (
                <InsightSection
                  items={data.summary.what_is_going_right}
                  emptyMessage="No top-ranked strengths were returned for this account yet."
                  getDrilldown={buildFindingDrilldown}
                  onOpenDrilldown={openInsightDrilldown}
                />
              )}

              {activeTab === 'bad' && (
                <div className="space-y-4">
                  <InsightSection
                    items={data.summary.what_is_going_wrong}
                    emptyMessage="No top-ranked weaknesses were returned for this account yet."
                    getDrilldown={buildFindingDrilldown}
                    onOpenDrilldown={openInsightDrilldown}
                  />
                  <InsightSection
                    items={data.summary.why_it_is_going_wrong}
                    emptyMessage="No top-ranked causes were returned for this account yet."
                    getDrilldown={buildFindingDrilldown}
                    onOpenDrilldown={openInsightDrilldown}
                  />
                </div>
              )}

              {activeTab === 'recommended' && (
                <RecommendationSection
                  items={data.summary.what_to_do_next}
                  emptyMessage="No top-ranked next steps were returned for this account yet."
                  getDrilldown={(item) => buildRecommendationDrilldown(item, findingLookup)}
                  onOpenDrilldown={openInsightDrilldown}
                />
            )}
        </>
      ) : null}
    </>
  );
}
