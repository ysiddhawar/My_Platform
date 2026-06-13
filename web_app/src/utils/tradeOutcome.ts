import type { TradeRecord } from '@/types/prototype';

export const TRADE_OUTCOME_TOLERANCE = 0.001;

export type TradeOutcome = 'win' | 'loss' | 'breakeven' | 'open';

export function tradeNetPnl(trade: Pick<TradeRecord, 'net_pnl'>): number {
  const value = Number(trade.net_pnl || 0);
  return Number.isFinite(value) ? value : 0;
}

export function classifyPnlOutcome(pnl: number, isClosed: boolean, tolerance = TRADE_OUTCOME_TOLERANCE): TradeOutcome {
  if (!isClosed) return 'open';
  if (pnl > tolerance) return 'win';
  if (pnl < -tolerance) return 'loss';
  return 'breakeven';
}

export function classifyTradeOutcome(trade: Pick<TradeRecord, 'is_closed' | 'net_pnl'>, tolerance = TRADE_OUTCOME_TOLERANCE): TradeOutcome {
  return classifyPnlOutcome(tradeNetPnl(trade), trade.is_closed, tolerance);
}

export function isWinningTrade(trade: Pick<TradeRecord, 'is_closed' | 'net_pnl'>): boolean {
  return classifyTradeOutcome(trade) === 'win';
}

export function isLosingTrade(trade: Pick<TradeRecord, 'is_closed' | 'net_pnl'>): boolean {
  return classifyTradeOutcome(trade) === 'loss';
}

export function isBreakevenTrade(trade: Pick<TradeRecord, 'is_closed' | 'net_pnl'>): boolean {
  return classifyTradeOutcome(trade) === 'breakeven';
}

export function summarizeTradeOutcomes(trades: TradeRecord[]) {
  const winTrades: TradeRecord[] = [];
  const lossTrades: TradeRecord[] = [];
  const breakevenTrades: TradeRecord[] = [];
  const openTrades: TradeRecord[] = [];

  trades.forEach((trade) => {
    const outcome = classifyTradeOutcome(trade);
    if (outcome === 'win') winTrades.push(trade);
    if (outcome === 'loss') lossTrades.push(trade);
    if (outcome === 'breakeven') breakevenTrades.push(trade);
    if (outcome === 'open') openTrades.push(trade);
  });

  const closedTrades = [...winTrades, ...lossTrades, ...breakevenTrades];
  return {
    closedTrades,
    winTrades,
    lossTrades,
    breakevenTrades,
    openTrades,
    closedCount: closedTrades.length,
    winCount: winTrades.length,
    lossCount: lossTrades.length,
    breakevenCount: breakevenTrades.length,
    openCount: openTrades.length,
    winRate: closedTrades.length ? winTrades.length / closedTrades.length : 0,
    lossRate: closedTrades.length ? lossTrades.length / closedTrades.length : 0,
    breakevenRate: closedTrades.length ? breakevenTrades.length / closedTrades.length : 0,
  };
}
