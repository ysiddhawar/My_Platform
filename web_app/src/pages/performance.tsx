import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { PerformanceDashboard } from '@/dashboards/performance/PerformanceDashboard';

export default function PerformancePage() {
  return (
    <DashboardLayout>
      <PerformanceDashboard />
    </DashboardLayout>
  );
}
