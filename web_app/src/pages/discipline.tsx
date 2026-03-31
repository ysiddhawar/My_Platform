import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { DisciplineDashboard } from '@/dashboards/discipline/DisciplineDashboard';

export default function DisciplinePage() {
  return (
    <DashboardLayout>
      <DisciplineDashboard />
    </DashboardLayout>
  );
}
