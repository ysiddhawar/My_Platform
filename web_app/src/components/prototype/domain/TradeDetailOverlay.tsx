import { useCallback, useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from 'react-query';

import { fetchTradeBundle, fetchTrades, updateTrade } from '@/api/prototype';
import { TradeBundlePanel } from '@/components/prototype/domain/TradeBundlePanel';
import { usePrototypeStore } from '@/state/prototypeStore';
import type { TradeBundle, TradeRecord } from '@/types/prototype';

type TradeDetailOverlayProps = {
  tradeId: string;
  onClose: () => void;
};

export function TradeDetailOverlay({ tradeId, onClose }: TradeDetailOverlayProps) {
  const accountId = usePrototypeStore((state) => state.accountId);
  const queryClient = useQueryClient();

  const { data: trades } = useQuery<TradeRecord[]>(
    ['prototype-trades', accountId],
    () => fetchTrades(accountId as string),
    {
      enabled: Boolean(accountId),
      staleTime: 60_000,
    },
  );

  const { data, isLoading, error } = useQuery<TradeBundle>(
    ['prototype-trade-bundle', tradeId],
    () => fetchTradeBundle(tradeId),
    { enabled: Boolean(tradeId) },
  );

  const tradeFromList = useMemo(
    () => (trades ?? []).find((trade) => trade.trade_id === tradeId) ?? null,
    [trades, tradeId],
  );

  // Body scroll lock
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

  // Escape key handler
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [onClose]);

  const saveMutation = useMutation(
    (payload: { strategy_tag?: string | null; probability_bucket?: string | null; confidence_score?: number | null; notes?: string | null; tags?: string[] }) =>
      updateTrade(tradeId, payload),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['prototype-trade-bundle', tradeId]);
        queryClient.invalidateQueries(['prototype-trades', accountId]);
      },
    },
  );

  const handleSave = useCallback(async (updates: Record<string, unknown>) => {
    await saveMutation.mutateAsync(updates as Parameters<typeof saveMutation.mutateAsync>[0]);
  }, [saveMutation]);

  const mergedBundle: TradeBundle | null = useMemo(() => {
    if (!data?.trade && !tradeFromList) return null;
    return {
      ...data!,
      trade: tradeFromList ?? data?.trade ?? null,
    };
  }, [data, tradeFromList]);

  return (
    <div
      className="fixed inset-0 z-[99999] flex items-start justify-center overflow-y-auto bg-black/30 backdrop-blur-md pt-10 pb-10"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="relative w-full max-w-5xl mx-4 rounded-[28px] border border-black/10 bg-white p-8 shadow-2xl dark:border-white/10 dark:bg-[#121212]">
        <button
          onClick={onClose}
          className="absolute right-6 top-6 z-10 flex h-8 w-8 items-center justify-center rounded-full border border-black/10 bg-white text-sm font-semibold text-black transition hover:bg-gray-100 dark:border-white/10 dark:bg-[#1a1a1a] dark:text-white dark:hover:bg-white/10"
          aria-label="Close trade detail"
        >
          ✕
        </button>

        {isLoading ? (
          <p className="text-sm text-gray-600 dark:text-slate-400">Loading trade detail…</p>
        ) : error instanceof Error ? (
          <p className="rounded-[20px] border border-rose-500/20 bg-rose-50 px-5 py-4 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-300">{error.message}</p>
        ) : !mergedBundle?.trade ? (
          <p className="text-sm text-gray-600 dark:text-slate-400">No trade data available.</p>
        ) : (
          <TradeBundlePanel
            bundle={mergedBundle}
            onSave={handleSave}
            isSaving={saveMutation.isLoading}
          />
        )}
      </div>
    </div>
  );
}