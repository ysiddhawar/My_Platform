import { apiClient } from './client';

export const endpoints = {
  bootstrapAdmin: (payload: Record<string, unknown>) => apiClient.post('/auth/bootstrap-admin', payload),
  login: (payload: Record<string, unknown>) => apiClient.post('/auth/login', payload),
  me: () => apiClient.get('/auth/me'),
  logout: () => apiClient.post('/auth/logout'),
  runMetrics: (payload: Record<string, unknown>) => apiClient.post('/metrics/run', payload),
  runDiagnostic: (payload: Record<string, unknown>) => apiClient.post('/ai-diagnostic/run', payload),
  runDecision: (payload: Record<string, unknown>) => apiClient.post('/decisions/evaluate', payload),
  executeTrade: (payload: Record<string, unknown>) => apiClient.post('/execution-tools/execute-trade', payload),
  previewTrade: (payload: Record<string, unknown>) => apiClient.post('/execution-tools/preview-trade', payload),
  recordFilledTrade: (payload: Record<string, unknown>) => apiClient.post('/execution-tools/record-filled-trade', payload),
  closeTrade: (payload: Record<string, unknown>) => apiClient.post('/execution-tools/close-trade', payload),
  updateExecutionConfig: (payload: Record<string, unknown>) => apiClient.post('/execution-tools/update-config', payload),
  runRiskModeling: (payload: Record<string, unknown>) => apiClient.post('/risk-modeling/analyze', payload),
  getMonitoringSnapshot: () => apiClient.get('/monitoring/snapshot'),
  listStrategies: () => apiClient.get('/strategy-setup/list'),
  createStrategy: (payload: Record<string, unknown>) => apiClient.post('/strategy-setup/create', payload),
  appendChecklist: (strategyName: string, payload: Record<string, unknown>) =>
    apiClient.post(`/strategy-setup/${encodeURIComponent(strategyName)}/checklist`, payload),
  getJournalTrades: (accountId = 'DEFAULT') => apiClient.get('/journal/trades', { params: { account_id: accountId } }),
  getBehavioralSnapshot: (accountId = 'DEFAULT') => apiClient.get('/journal/behavior', { params: { account_id: accountId } })
};
