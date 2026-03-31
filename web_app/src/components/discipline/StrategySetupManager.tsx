import { FormEvent, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from 'react-query';

import { endpoints } from '@/api/endpoints';
import { Panel } from '@/components/ui/Panel';

type StrategyRecord = {
  name: string;
  checklist_items: string[];
  mandatory_checklist_items: string[];
};

export function StrategySetupManager() {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [marketTypes, setMarketTypes] = useState('stock, forex, crypto');
  const [checklistItems, setChecklistItems] = useState('');
  const [mandatoryItems, setMandatoryItems] = useState('');
  const [appendTarget, setAppendTarget] = useState('');
  const [appendItems, setAppendItems] = useState('');

  const { data } = useQuery('strategies', async () => {
    const response = await endpoints.listStrategies();
    return (response.data?.strategies || []) as StrategyRecord[];
  });

  const createMutation = useMutation(async () => {
    return endpoints.createStrategy({
      name,
      description,
      market_types: splitValues(marketTypes),
      checklist_items: splitValues(checklistItems),
      mandatory_checklist_items: splitValues(mandatoryItems),
    });
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries('strategies');
      setName('');
      setDescription('');
      setChecklistItems('');
      setMandatoryItems('');
    }
  });

  const appendMutation = useMutation(async () => {
    return endpoints.appendChecklist(appendTarget, {
      checklist_items: splitValues(appendItems),
      mandatory_checklist_items: [],
    });
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries('strategies');
      setAppendItems('');
    }
  });

  const strategies = useMemo(() => data || [], [data]);

  const handleCreate = (event: FormEvent) => {
    event.preventDefault();
    createMutation.mutate();
  };

  return (
    <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
      <Panel title="Strategy / Setup Builder" subtitle="Create the setup catalog and checklist library used by the position sizer">
        <form className="space-y-4" onSubmit={handleCreate}>
          <label className="block text-sm text-slate-300">
            Strategy / Setup Name
            <input className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={name} onChange={(event) => setName(event.target.value)} />
          </label>
          <label className="block text-sm text-slate-300">
            Description
            <textarea className="mt-2 h-24 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={description} onChange={(event) => setDescription(event.target.value)} />
          </label>
          <label className="block text-sm text-slate-300">
            Supported Markets
            <input className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={marketTypes} onChange={(event) => setMarketTypes(event.target.value)} />
          </label>
          <label className="block text-sm text-slate-300">
            Checklist / Criteria
            <textarea className="mt-2 h-28 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" placeholder="One item per line" value={checklistItems} onChange={(event) => setChecklistItems(event.target.value)} />
          </label>
          <label className="block text-sm text-slate-300">
            Mandatory Checklist Items
            <textarea className="mt-2 h-24 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" placeholder="One item per line" value={mandatoryItems} onChange={(event) => setMandatoryItems(event.target.value)} />
          </label>
          <button className="rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-white" type="submit">
            {createMutation.isLoading ? 'Saving...' : 'Create Setup'}
          </button>
        </form>
      </Panel>

      <div className="space-y-6">
        <Panel title="Existing Setup Catalog" subtitle="Strategies already available to the position sizer">
          <div className="space-y-3">
            {strategies.map((strategy) => (
              <div key={strategy.name} className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold text-white">{strategy.name}</p>
                  <span className="text-xs text-slate-500">{strategy.checklist_items.length} criteria</span>
                </div>
                <p className="mt-2 text-xs text-slate-400">Mandatory: {strategy.mandatory_checklist_items.join(', ') || 'None'}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Append Checklist Items" subtitle="Add criteria to any existing strategy/setup">
          <label className="block text-sm text-slate-300">
            Target Setup
            <select className="mt-2 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" value={appendTarget} onChange={(event) => setAppendTarget(event.target.value)}>
              <option value="">Select setup</option>
              {strategies.map((strategy) => <option key={strategy.name} value={strategy.name}>{strategy.name}</option>)}
            </select>
          </label>
          <label className="mt-4 block text-sm text-slate-300">
            New Criteria
            <textarea className="mt-2 h-24 w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" placeholder="One item per line" value={appendItems} onChange={(event) => setAppendItems(event.target.value)} />
          </label>
          <button className="mt-4 rounded-xl border border-teal-700 bg-teal-950/50 px-4 py-2 text-sm font-semibold text-teal-200" onClick={() => appendMutation.mutate()}>
            {appendMutation.isLoading ? 'Appending...' : 'Append Criteria'}
          </button>
        </Panel>
      </div>
    </div>
  );
}

function splitValues(value: string) {
  return value
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}
