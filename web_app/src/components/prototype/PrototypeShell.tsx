import { useEffect, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from 'react-query';

import { connectMt5FileBridge, createConnectedAccount, fetchAccountIntegrations, fetchAccounts, fetchWorkspaceLayout, saveWorkspaceLayout, seedInvestorDemoPack, validateMt5FileBridge } from '@/api/prototype';
import { AccountPickerModal } from '@/components/prototype/AccountPickerModal';
import { PrototypeSidebar } from '@/components/prototype/PrototypeSidebar';
import { PrototypeTopbar } from '@/components/prototype/PrototypeTopbar';
import { AIInsightsScreen } from '@/components/prototype/screens/AIInsightsScreen';
import { CalendarScreen } from '@/components/prototype/screens/CalendarScreen';
import { DashboardScreen } from '@/components/prototype/screens/DashboardScreen';
import { DemoDataScreen } from '@/components/prototype/screens/DemoDataScreen';
import { JournalScreen } from '@/components/prototype/screens/JournalScreen';
import { MissedOpportunitiesScreen } from '@/components/prototype/screens/MissedOpportunitiesScreen';
import { PositionSizerScreen } from '@/components/prototype/screens/PositionSizerScreen';
import { TradeDetailScreen } from '@/components/prototype/screens/TradeDetailScreen';
import type { PrototypeView } from '@/types/prototype';
import { usePrototypeStore } from '@/state/prototypeStore';

export function PrototypeShell() {
  const queryClient = useQueryClient();
  const activeView = usePrototypeStore((state) => state.activeView);
  const accountId = usePrototypeStore((state) => state.accountId);
  const hydrateFromStorage = usePrototypeStore((state) => state.hydrateFromStorage);
  const sidebarOrder = usePrototypeStore((state) => state.sidebarOrder);
  const sidebarCollapsed = usePrototypeStore((state) => state.sidebarCollapsed);
  const setSidebarOrder = usePrototypeStore((state) => state.setSidebarOrder);
  const toggleSidebarCollapsed = usePrototypeStore((state) => state.toggleSidebarCollapsed);
  const resetSidebarOrder = usePrototypeStore((state) => state.resetSidebarOrder);
  const dashboardGroupOrder = usePrototypeStore((state) => state.dashboardGroupOrder);
  const dashboardMetricGroup = usePrototypeStore((state) => state.dashboardMetricGroup);
  const dashboardMetricSize = usePrototypeStore((state) => state.dashboardMetricSize);
  const setActiveView = usePrototypeStore((state) => state.setActiveView);
  const setAccountId = usePrototypeStore((state) => state.setAccountId);
  const hydrateWorkspaceLayout = usePrototypeStore((state) => state.hydrateWorkspaceLayout);
  const exportWorkspaceLayout = usePrototypeStore((state) => state.exportWorkspaceLayout);
  const [accountPickerOpen, setAccountPickerOpen] = useState(false);
  const { data: accounts = [] } = useQuery(['prototype-accounts'], fetchAccounts);
  const { data: integrations = [] } = useQuery(['prototype-account-integrations'], fetchAccountIntegrations);
  const { data: savedLayout, isFetched: layoutFetched } = useQuery(
    ['prototype-workspace-layout', accountId],
    () => fetchWorkspaceLayout(accountId as string),
    { enabled: Boolean(accountId) },
  );
  const layoutFingerprint = useMemo(
    () => JSON.stringify(exportWorkspaceLayout()),
    [exportWorkspaceLayout, sidebarOrder, sidebarCollapsed, dashboardGroupOrder, dashboardMetricGroup, dashboardMetricSize],
  );
  const lastPersistedRef = useRef<string>('');

  useEffect(() => {
    hydrateFromStorage();
  }, [hydrateFromStorage]);

  useEffect(() => {
    if (!accountId) return;
    hydrateWorkspaceLayout(savedLayout || null);
    lastPersistedRef.current = JSON.stringify(savedLayout || exportWorkspaceLayout());
  }, [accountId, savedLayout, hydrateWorkspaceLayout]);

  useEffect(() => {
    if (!accountId) return;
    if (!layoutFetched) return;
    if (layoutFingerprint === lastPersistedRef.current) return;
    const timer = window.setTimeout(async () => {
      const nextLayout = exportWorkspaceLayout();
      const serialized = JSON.stringify(nextLayout);
      if (serialized === lastPersistedRef.current) return;
      await saveWorkspaceLayout(accountId, nextLayout);
      lastPersistedRef.current = serialized;
    }, 350);
    return () => window.clearTimeout(timer);
  }, [accountId, exportWorkspaceLayout, layoutFingerprint, layoutFetched]);

  const refreshAccounts = async () => {
    await Promise.all([
      queryClient.invalidateQueries(['prototype-accounts']),
      queryClient.invalidateQueries(['prototype-account-integrations']),
    ]);
  };

  const createAccountMutation = useMutation(createConnectedAccount, {
    onSuccess: async (account) => {
      await refreshAccounts();
      setAccountId(account.account_id);
      setAccountPickerOpen(false);
    },
  });

  const seedDemoMutation = useMutation(
    ({ account_id, broker_id, account_name }: { account_id: string; broker_id: string; account_name: string }) =>
      seedInvestorDemoPack(account_id, { broker_id, account_name, trade_count: 300, timezone_name: 'Asia/Kolkata' }),
    {
      onSuccess: async (_result, variables) => {
        await refreshAccounts();
        await Promise.all([
          queryClient.invalidateQueries(['prototype-overview', variables.account_id]),
          queryClient.invalidateQueries(['prototype-trades', variables.account_id]),
          queryClient.invalidateQueries(['prototype-missed-opportunities', variables.account_id]),
          queryClient.invalidateQueries(['prototype-calendar-summaries', variables.account_id]),
        ]);
        setAccountId(variables.account_id);
        setAccountPickerOpen(false);
      },
    },
  );

  const handleSidebarSelect = (view: PrototypeView) => {
    setActiveView(view);
    if (!accountId && view !== 'ai-insights') {
      setAccountPickerOpen(true);
    }
  };

  const shouldGateData = !accountId && activeView !== 'ai-insights';

  return (
    <div className="h-screen overflow-hidden bg-[var(--page-bg)] text-[var(--color-ink)]">
      <div className="flex h-screen">
        <PrototypeSidebar
          activeView={activeView}
          order={sidebarOrder}
          collapsed={sidebarCollapsed}
          onSelect={handleSidebarSelect}
          onReorder={setSidebarOrder}
          onReset={resetSidebarOrder}
          onToggleCollapse={toggleSidebarCollapsed}
        />
        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
          <PrototypeTopbar
            activeView={activeView}
            accountId={accountId}
            accounts={accounts}
            onChooseAccount={(nextAccountId) => setAccountId(nextAccountId)}
            onOpenAccountPicker={() => setAccountPickerOpen(true)}
          />
          <main
            className={`flex-1 overflow-x-hidden overflow-y-auto ${
              activeView === 'dashboard'
                ? 'px-2 pb-6 pt-0 md:px-3 md:pb-8 md:pt-0 xl:px-4 xl:pb-10 xl:pt-0'
                : 'px-2 py-6 md:px-3 md:py-8 xl:px-4 xl:py-10'
            }`}
          >
            {shouldGateData ? (
              <AccountRequiredState
                view={activeView}
                accounts={accounts}
                onOpenAccounts={() => setAccountPickerOpen(true)}
                onCreateDemo={() => seedDemoMutation.mutate({ account_id: 'DEFAULT', broker_id: 'BROKER', account_name: 'Prototype Workspace' })}
                isCreatingDemo={seedDemoMutation.isLoading}
              />
            ) : (
              <>
                {activeView === 'dashboard' ? <DashboardScreen /> : null}
                {activeView === 'journal' ? <JournalScreen /> : null}
                {activeView === 'trade-detail' ? <TradeDetailScreen /> : null}
                {activeView === 'ai-insights' ? <AIInsightsScreen /> : null}
                {activeView === 'missed-opportunities' ? <MissedOpportunitiesScreen /> : null}
                {activeView === 'calendar' ? <CalendarScreen /> : null}
                {activeView === 'position-sizer' ? <PositionSizerScreen /> : null}
                {activeView === 'demo-data' ? <DemoDataScreen /> : null}
              </>
            )}
          </main>
        </div>
      </div>
      <AccountPickerModal
        accounts={accounts}
        selectedAccountId={accountId}
        integrations={integrations}
        onSelect={(nextAccountId) => {
          setAccountId(nextAccountId);
          setAccountPickerOpen(false);
        }}
        onCreateAccount={async (payload) => {
          return await createAccountMutation.mutateAsync(payload);
        }}
        onConnectMt5={async (payload) => {
          await connectMt5FileBridge(payload);
          await refreshAccounts();
        }}
        onValidateMt5={validateMt5FileBridge}
        onCreateDemoAccount={async (payload) => {
          await seedDemoMutation.mutateAsync(payload);
        }}
        onClose={() => setAccountPickerOpen(false)}
        open={accountPickerOpen}
      />
    </div>
  );
}

function AccountRequiredState({
  view,
  accounts,
  onOpenAccounts,
  onCreateDemo,
  isCreatingDemo,
}: {
  view: PrototypeView;
  accounts: { account_id: string; account_name?: string | null }[];
  onOpenAccounts: () => void;
  onCreateDemo: () => void;
  isCreatingDemo: boolean;
}) {
  return (
    <section className="rounded-[28px] border border-dashed border-black/12 bg-white px-6 py-8 dark:border-white/10 dark:bg-[#060606]">
      <p className="text-[0.72rem] font-semibold uppercase tracking-[0.22em] text-black/50 dark:text-white/50">Account Needed</p>
      <h2 className="mt-3 text-[1.8rem] font-semibold tracking-[-0.04em] text-black dark:text-white">
        {view === 'dashboard' ? 'Select an account to load the dashboard' : 'Select an account to load this section'}
      </h2>
      <p className="mt-3 max-w-2xl text-sm leading-6 text-black/70 dark:text-white/70">
        The workspace itself stays open so you can inspect the interface. Data-heavy sections attach to a connected account. If you do not have one yet, create a demo account with sample trades or add a live account connection.
      </p>
      <div className="mt-6 flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onOpenAccounts}
          className="rounded-full bg-black px-5 py-3 text-sm font-semibold text-white dark:bg-white dark:text-black"
        >
          {accounts.length ? 'Select or Add Account' : 'Add Account'}
        </button>
        <button
          type="button"
          onClick={onCreateDemo}
          className="rounded-full border border-black/10 px-5 py-3 text-sm font-semibold text-black dark:border-white/10 dark:text-white"
        >
          {isCreatingDemo ? 'Creating Demo…' : 'Create Demo Account'}
        </button>
      </div>
    </section>
  );
}
