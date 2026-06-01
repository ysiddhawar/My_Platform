import { useEffect, useMemo, useState } from 'react';
import { useQuery } from 'react-query';

import { fetchAIInsightsSummary } from '@/api/prototype';
import type {
  AIInsightFinding,
  AIInsightMetricProjection,
  AIInsightProjectionGroup,
  AIInsightSummaryTabs,
  AIInsightTabCard,
  AIRecommendation,
} from '@/types/prototype';
import { usePrototypeStore } from '@/state/prototypeStore';

type InsightTab = 'good' | 'bad' | 'recommended';
type Tone = 'low' | 'medium' | 'high' | 'critical' | 'now' | 'soon' | 'later' | 'good';

const TAB_EMPTY: Record<InsightTab, string> = {
  good: 'No top-ranked strengths were returned for this account yet.',
  bad: 'No top-ranked weaknesses were returned for this account yet.',
  recommended: 'No top-ranked focus areas were returned for this account yet.',
};

const GROUP_LABELS: Record<AIInsightProjectionGroup['key'], string> = {
  continued: 'If continued',
  fixed: 'If fixed',
  long_term: 'Long-term focus',
};

const TONE_STYLES: Record<Tone, string> = {
  low: 'bg-amber-500/12 text-amber-700 dark:bg-amber-400/12 dark:text-amber-300',
  medium: 'bg-orange-500/12 text-orange-700 dark:bg-orange-400/12 dark:text-orange-300',
  high: 'bg-rose-500/12 text-rose-700 dark:bg-rose-400/12 dark:text-rose-300',
  critical: 'bg-red-500/15 text-red-700 dark:bg-red-400/15 dark:text-red-300',
  now: 'bg-[#FF5900]/15 text-[#FF5900]',
  soon: 'bg-amber-500/12 text-amber-700 dark:bg-amber-400/12 dark:text-amber-300',
  later: 'bg-black/6 text-black/65 dark:bg-white/10 dark:text-white/70',
  good: 'bg-emerald-500/12 text-emerald-700 dark:bg-emerald-400/12 dark:text-emerald-300',
};

function ToneBadge({ tone, label }: { tone: Tone; label: string }) {
  return <span className={`rounded-full px-3 py-1 text-[0.68rem] font-semibold capitalize ${TONE_STYLES[tone]}`}>{label}</span>;
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-[28px] border border-dashed border-black/12 bg-white/70 px-6 py-10 text-sm text-black/60 dark:border-white/12 dark:bg-[#222] dark:text-white/65">
      {message}
    </div>
  );
}

function clampIndex(index: number, total: number) {
  if (total <= 0) return 0;
  return Math.min(Math.max(index, 0), total - 1);
}

function confidenceLabel(card: AIInsightTabCard) {
  const label = card.confidence_basis_label || 'closed trades';
  const count = Number.isFinite(card.confidence_basis_count) ? card.confidence_basis_count : card.sample_size;
  return `Confidence: ${card.confidence} · Based on ${count} ${label}`;
}

function directionClass(direction: AIInsightMetricProjection['direction']) {
  if (direction === 'better') return 'text-emerald-600 dark:text-emerald-300';
  if (direction === 'worse') return 'text-rose-600 dark:text-rose-300';
  return 'text-black/65 dark:text-white/65';
}

function makeLinePath(points: number[], width: number, height: number) {
  if (points.length < 2) return '';
  const max = Math.max(...points);
  const min = Math.min(...points);
  const range = max - min || 1;
  return points
    .map((point, index) => {
      const x = (index / (points.length - 1)) * width;
      const y = height - ((point - min) / range) * height;
      return `${index === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(' ');
}

function CurveVisual({ metric }: { metric: AIInsightMetricProjection }) {
  const projected = metric.points || [];
  const baseline = metric.baseline_points || [];
  if (projected.length < 2 && baseline.length < 2) return <DirectionGlyph direction={metric.direction} />;
  const allPoints = [...projected, ...baseline];
  const width = 240;
  const height = 74;
  const max = Math.max(...allPoints);
  const min = Math.min(...allPoints);
  const range = max - min || 1;
  const pathFor = (points: number[]) => points
    .map((point, index) => {
      const x = (index / Math.max(points.length - 1, 1)) * width;
      const y = height - ((point - min) / range) * height;
      return `${index === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(' ');
  return (
    <svg aria-hidden="true" viewBox={`0 0 ${width} ${height}`} className="h-20 w-full overflow-visible">
      {baseline.length >= 2 ? <path d={pathFor(baseline)} fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="5 5" className="text-black/25 dark:text-white/25" /> : null}
      {projected.length >= 2 ? <path d={pathFor(projected)} fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" className={directionClass(metric.direction)} /> : null}
    </svg>
  );
}

function WeekdayVisual({ metric }: { metric: AIInsightMetricProjection }) {
  const projected = metric.points || [];
  const baseline = metric.baseline_points || [];
  const labels = metric.labels || [];
  const max = Math.max(...projected.map(Math.abs), ...baseline.map(Math.abs), 1);
  return (
    <div className="grid grid-cols-5 items-end gap-2 pt-2" aria-hidden="true">
      {projected.slice(0, 5).map((value, index) => {
        const baselineValue = baseline[index] || 0;
        const projectedHeight = Math.max(10, (Math.abs(value) / max) * 64);
        const baselineHeight = Math.max(6, (Math.abs(baselineValue) / max) * 64);
        const color = value >= 0 ? 'bg-emerald-500' : 'bg-rose-500';
        return (
          <div key={`${metric.metric_key}-${index}`} className="flex flex-col items-center gap-1">
            <div className="flex h-16 items-end gap-1">
              <span className="w-2 rounded-t bg-black/20 dark:bg-white/20" style={{ height: baselineHeight }} />
              <span className={`w-3 rounded-t ${color}`} style={{ height: projectedHeight }} />
            </div>
            <span className="text-[0.6rem] font-semibold text-black/45 dark:text-white/45">{labels[index] || index + 1}</span>
          </div>
        );
      })}
    </div>
  );
}

function DirectionGlyph({ direction }: { direction: AIInsightMetricProjection['direction'] }) {
  return (
    <div className={`text-right text-2xl font-semibold tracking-[-0.04em] ${directionClass(direction)}`} aria-hidden="true">
      {direction === 'worse' ? '↓' : direction === 'better' ? '↑' : '→'}
    </div>
  );
}

function MiniLineVisual({ metric }: { metric: AIInsightMetricProjection }) {
  const points = metric.points || [];
  if (points.length < 2) return <DirectionGlyph direction={metric.direction} />;
  return (
    <svg aria-hidden="true" viewBox="0 0 120 40" className="h-10 w-28 overflow-visible">
      <path d={makeLinePath(points, 120, 40)} fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" className={directionClass(metric.direction)} />
    </svg>
  );
}

function MetricVisual({ metric }: { metric: AIInsightMetricProjection }) {
  if (metric.visual_type === 'curve') return <CurveVisual metric={metric} />;
  if (metric.visual_type === 'weekday_bar') return <WeekdayVisual metric={metric} />;
  if (metric.visual_type === 'mini_line') return <MiniLineVisual metric={metric} />;
  if (metric.visual_type === 'bar' && (metric.points?.length || 0) >= 1) return <WeekdayVisual metric={{ ...metric, labels: ['Now', 'Then'] }} />;
  return <DirectionGlyph direction={metric.direction} />;
}

function MetricProjectionCard({ metric }: { metric: AIInsightMetricProjection }) {
  const isWide = metric.visual_type === 'curve' || metric.visual_type === 'weekday_bar';
  return (
    <div className={`rounded-[22px] border border-black/8 bg-white/80 p-4 shadow-[0_16px_45px_rgba(0,0,0,0.04)] dark:border-white/8 dark:bg-white/[0.04] ${isWide ? 'md:col-span-2' : ''}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[0.67rem] font-semibold uppercase tracking-[0.18em] text-black/45 dark:text-white/45">{metric.label}</p>
          <p className="mt-2 text-2xl font-semibold tracking-[-0.06em] text-black/90 dark:text-white/90">{metric.projected_value}</p>
        </div>
        {metric.visual_type === 'metric' || metric.visual_type === 'comparison' ? <DirectionGlyph direction={metric.direction} /> : null}
      </div>
      {metric.visual_type !== 'metric' && metric.visual_type !== 'comparison' ? <div className="mt-3"><MetricVisual metric={metric} /></div> : null}
      <div className="mt-4 flex items-center justify-between gap-3 text-xs text-black/58 dark:text-white/60">
        <span>Current {metric.current_value}</span>
        <span className={`font-semibold ${directionClass(metric.direction)}`}>{metric.delta_label}</span>
      </div>
    </div>
  );
}

function ProjectionGroupView({ group }: { group: AIInsightProjectionGroup }) {
  if (!group.metrics.length) return null;
  return (
    <section className="relative rounded-[30px] border border-black/8 bg-black/[0.025] p-4 dark:border-white/8 dark:bg-black/25 md:p-5">
      <h4 className="sticky top-0 z-10 bg-white dark:bg-[#1e1e1e] pb-2 border-b border-black/8 dark:border-white/8 rounded-t-[30px] text-sm font-semibold uppercase tracking-[0.22em] text-black/55 dark:text-white/60">{GROUP_LABELS[group.key]}</h4>
      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {group.metrics.map((metric) => <MetricProjectionCard key={`${group.key}-${metric.metric_key}`} metric={metric} />)}
      </div>
    </section>
  );
}

function EvidenceChips({ card }: { card: AIInsightTabCard }) {
  if (!card.evidence_highlights.length) return null;
  return (
    <div className="grid gap-2 sm:grid-cols-3">
      {card.evidence_highlights.slice(0, 3).map((evidence) => (
        <div key={`${card.id}-${evidence.label}-${evidence.value}`} className="rounded-[18px] border border-black/8 bg-black/[0.025] px-3 py-3 dark:border-white/8 dark:bg-black/25">
          <p className="text-[0.62rem] font-semibold uppercase tracking-[0.18em] text-black/40 dark:text-white/45">{evidence.label}</p>
          <p className="mt-1 text-sm font-semibold text-black/85 dark:text-white/90">{evidence.value}</p>
          {evidence.comparison ? <p className="mt-1 text-xs text-black/55 dark:text-white/60">{evidence.comparison}</p> : null}
        </div>
      ))}
    </div>
  );
}

function InsightNavigator({ index, total, onNext, onPrev, onJump }: { index: number; total: number; onNext: () => void; onPrev: () => void; onJump: (index: number) => void }) {
  const [inputValue, setInputValue] = useState(String(total ? index + 1 : 0));
  const nextDisabled = total <= 1 || index >= total - 1;
  const prevDisabled = total <= 1 || index <= 0;

  useEffect(() => {
    setInputValue(String(total ? index + 1 : 0));
  }, [index, total]);

  const commitJump = () => {
    const parsed = Number.parseInt(inputValue, 10);
    if (!Number.isFinite(parsed)) {
      setInputValue(String(total ? index + 1 : 0));
      return;
    }
    const next = clampIndex(parsed - 1, total);
    setInputValue(String(total ? next + 1 : 0));
    onJump(next);
  };

  return (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-[22px] border border-black/8 bg-white/80 px-4 py-3 dark:border-white/8 dark:bg-[#222]">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onPrev}
          disabled={prevDisabled}
          className="rounded-full border border-black/10 px-4 py-2 text-xs font-semibold text-black/70 transition hover:border-[#FF5900] hover:bg-transparent hover:text-[#FF5900] disabled:cursor-not-allowed disabled:text-black/35 disabled:hover:border-black/10 disabled:hover:text-black/35 dark:border-white/10 dark:text-white/75 dark:hover:border-[#FF5900] dark:hover:text-[#FF5900] dark:disabled:text-white/35 dark:disabled:hover:border-white/10"
        >
          Prev
        </button>
        <input
          aria-label="Current insight number"
          value={inputValue}
          inputMode="numeric"
          onChange={(event) => setInputValue(event.target.value.replace(/[^0-9]/g, ''))}
          onBlur={commitJump}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.currentTarget.blur();
            }
          }}
          className="h-9 w-20 rounded-full border border-black/10 bg-black/[0.03] px-4 text-center text-xs font-semibold text-black/75 outline-none transition focus:border-[#FF5900] dark:border-white/10 dark:bg-white/[0.04] dark:text-white/75"
        />
        <button
          type="button"
          onClick={onNext}
          disabled={nextDisabled}
          className="rounded-full border border-black/10 px-4 py-2 text-xs font-semibold text-black/70 transition hover:border-[#FF5900] hover:bg-transparent hover:text-[#FF5900] disabled:cursor-not-allowed disabled:text-black/35 disabled:hover:border-black/10 disabled:hover:text-black/35 dark:border-white/10 dark:text-white/75 dark:hover:border-[#FF5900] dark:hover:text-[#FF5900] dark:disabled:text-white/35 dark:disabled:hover:border-white/10"
        >
          Next
        </button>
      </div>
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-black/45 dark:text-white/45">Total findings: {total}</p>
    </div>
  );
}

function InsightTabCardView({ card, activeTab }: { card: AIInsightTabCard; activeTab: InsightTab }) {
  return (
    <article className="overflow-hidden rounded-[32px] border border-black/8 bg-white text-black shadow-[0_24px_80px_rgba(0,0,0,0.08)] dark:border-white/8 dark:bg-[#222] dark:text-white">
      <div className="bg-[radial-gradient(circle_at_top_left,rgba(255,89,0,0.18),transparent_35%),linear-gradient(135deg,rgba(0,0,0,0.04),transparent)] px-5 py-5 dark:bg-[radial-gradient(circle_at_top_left,rgba(255,89,0,0.22),transparent_38%),linear-gradient(135deg,rgba(255,255,255,0.08),transparent)] md:px-7">
        <div className="flex flex-wrap justify-end gap-2">
          {activeTab === 'bad' && card.severity ? <ToneBadge tone={card.severity} label={card.severity} /> : null}
          {activeTab === 'recommended' && card.priority ? <ToneBadge tone={card.priority} label={card.priority} /> : null}
          {activeTab === 'good' ? <ToneBadge tone="good" label="strength" /> : null}
        </div>
        <h3 className="mt-4 max-w-4xl text-[clamp(1.9rem,4vw,3.7rem)] font-semibold leading-[0.95] tracking-[-0.08em]">{card.title}</h3>
      </div>

      <div className="space-y-5 p-5 md:p-7">
        <div className="grid gap-3 md:grid-cols-2">
          <section className="rounded-[24px] bg-black/[0.035] p-4 dark:bg-black/25">
            <p className="text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-black/55 dark:text-white/65">
              {activeTab === 'recommended' ? 'Focus area' : activeTab === 'good' ? 'What is working' : 'What is happening'}
            </p>
            <p className="mt-3 text-sm leading-6 text-black/78 dark:text-white/88">{card.main_point}</p>
          </section>
          <section className="rounded-[24px] bg-[#FF5900]/8 p-4 dark:bg-[#FF5900]/12">
            <p className="text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-black/55 dark:text-white/65">
              {activeTab === 'recommended' ? 'Why this matters' : activeTab === 'good' ? 'Why it may be working' : 'Why it may be happening'}
            </p>
            <p className="mt-3 text-sm leading-6 text-black/78 dark:text-white/88">{card.why}</p>
          </section>
        </div>

        <EvidenceChips card={card} />

        <section className="rounded-[26px] border border-black/8 bg-black/[0.025] p-4 dark:border-white/8 dark:bg-black/25">
          <p className="text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-black/55 dark:text-white/75">Projected effect</p>
          <p className="mt-3 text-base leading-7 text-black/80 dark:text-white">{card.projected_effect}</p>
        </section>

        <div className={
          activeTab === 'bad' && (card.projection_groups || []).length === 2
            ? 'grid grid-cols-1 gap-4 md:grid-cols-2 max-h-[500px] overflow-y-auto'
            : 'max-h-[60vh] overflow-y-auto space-y-4'
        }>
          {(card.projection_groups || []).map((group) => <ProjectionGroupView key={`${card.id}-${group.key}`} group={group} />)}
        </div>

        <p className="text-xs text-black/55 dark:text-white/60">{confidenceLabel(card)}</p>
      </div>
    </article>
  );
}

function fallbackProjectionGroup(label: AIInsightProjectionGroup['key'], impact: number): AIInsightProjectionGroup {
  return {
    key: label,
    metrics: [
      {
        metric_key: 'impact_signal',
        label: 'Impact Signal',
        current_value: 'Current pattern',
        projected_value: `${impact}% signal`,
        delta_label: `${impact}% modeled`,
        direction: 'better',
        visual_type: 'metric',
        points: [impact],
        baseline_points: [0],
      },
    ],
  };
}

function findingToFallbackCard(finding: AIInsightFinding, mode: 'bad' | 'good'): AIInsightTabCard {
  const impact = Math.max(5, Math.min(100, Math.round((finding.impact_score || 0.25) * 100)));
  return {
    id: finding.id,
    title: finding.title,
    main_point: finding.explanation,
    why: finding.impact_description || 'This is based on the strongest available evidence for the selected account.',
    evidence_highlights: finding.evidence.slice(0, 3),
    projected_effect: mode === 'bad'
      ? 'If this continues, the pattern can keep adding pressure to performance. If fixed, the affected area should improve.'
      : 'If this continues, it can protect the positive edge signal shown by this evidence.',
    projection_groups: mode === 'bad' ? [fallbackProjectionGroup('continued', impact), fallbackProjectionGroup('fixed', impact)] : [fallbackProjectionGroup('continued', impact)],
    confidence: finding.confidence,
    sample_size: finding.sample_size,
    confidence_basis_label: 'closed trades',
    confidence_basis_count: finding.sample_size,
    severity: mode === 'bad' ? finding.severity : undefined,
  };
}

function recommendationToFallbackCard(recommendation: AIRecommendation): AIInsightTabCard {
  return {
    id: recommendation.id,
    title: recommendation.title,
    main_point: recommendation.action,
    why: recommendation.why,
    evidence_highlights: [],
    projected_effect: recommendation.expected_benefit || 'This focus area should improve long-term trading quality if the evidence remains stable.',
    projection_groups: [fallbackProjectionGroup('long_term', 25)],
    confidence: 'low',
    sample_size: 0,
    confidence_basis_label: 'closed trades',
    confidence_basis_count: 0,
    priority: recommendation.priority,
  };
}

function buildFallbackTabs(data: Awaited<ReturnType<typeof fetchAIInsightsSummary>>): AIInsightSummaryTabs {
  return {
    bad: data.summary.what_is_going_wrong.slice(0, 15).map((finding) => findingToFallbackCard(finding, 'bad')),
    good: data.summary.what_is_going_right.slice(0, 15).map((finding) => findingToFallbackCard(finding, 'good')),
    recommended: data.summary.what_to_do_next.slice(0, 15).map(recommendationToFallbackCard),
  };
}

export function AIInsightsScreen({ activeTab }: { activeTab: InsightTab; onTabChange: (tab: InsightTab) => void }) {
  const accountId = usePrototypeStore((state) => state.accountId);
  const { data, isLoading, error } = useQuery(
    ['prototype-ai-insights-summary', accountId],
    () => fetchAIInsightsSummary(accountId as string),
    { enabled: Boolean(accountId), staleTime: 60000 },
  );
  const [activeIndexes, setActiveIndexes] = useState<Record<InsightTab, number>>({ good: 0, bad: 0, recommended: 0 });

  const tabs = useMemo(() => {
    if (!data) return null;
    return data.summary_tabs || buildFallbackTabs(data);
  }, [data]);

  useEffect(() => {
    setActiveIndexes({ good: 0, bad: 0, recommended: 0 });
  }, [accountId, data?.created_at_epoch]);

  const activeCards = tabs?.[activeTab] || [];
  const activeIndex = clampIndex(activeIndexes[activeTab] || 0, activeCards.length);
  const activeCard = activeCards[activeIndex] || null;

  const setTabIndex = (nextIndex: number) => {
    setActiveIndexes((current) => ({
      ...current,
      [activeTab]: clampIndex(nextIndex, activeCards.length),
    }));
  };

  if (!accountId) {
    return (
      <section className="rounded-[26px] border border-black/10 bg-white p-6 text-black dark:border-white/10 dark:bg-[#222] dark:text-white">
        <h2 className="text-[1.9rem] font-semibold tracking-[-0.05em]">AI Insights</h2>
        <p className="mt-3 text-sm text-black/65 dark:text-white/70">
          Select an account to generate the full insight layer. We will use dashboard, journal, missed opportunity, and calendar data together to diagnose what is working, what is hurting, and what to focus on next.
        </p>
      </section>
    );
  }

  if (isLoading) {
    return (
      <div className="rounded-[24px] border border-black/10 bg-white px-5 py-8 text-sm text-black/65 dark:border-white/10 dark:bg-[#222] dark:text-white/70">
        Building your AI review across all sections...
      </div>
    );
  }

  if (error instanceof Error) {
    return (
      <div className="rounded-[24px] border border-rose-500/20 bg-rose-50 px-5 py-4 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">
        {error.message}
      </div>
    );
  }

  if (!tabs || !activeCard) {
    return <EmptyState message={TAB_EMPTY[activeTab]} />;
  }

  return (
    <section>
      <InsightNavigator
        index={activeIndex}
        total={activeCards.length}
        onPrev={() => setTabIndex(activeIndex - 1)}
        onNext={() => setTabIndex(activeIndex + 1)}
        onJump={setTabIndex}
      />
      <InsightTabCardView card={activeCard} activeTab={activeTab} />
    </section>
  );
}
