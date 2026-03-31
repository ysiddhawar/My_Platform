import { BehavioralDisciplinePanel } from '@/components/discipline/BehavioralDisciplinePanel';
import { StrategySetupManager } from '@/components/discipline/StrategySetupManager';

export function DisciplineDashboard() {
  return (
    <div className="space-y-6">
      <StrategySetupManager />
      <BehavioralDisciplinePanel />
    </div>
  );
}
