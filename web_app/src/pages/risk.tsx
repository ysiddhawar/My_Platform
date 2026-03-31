import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { RiskDashboard } from '@/dashboards/risk/RiskDashboard';

export default function RiskPage() {
  return (
    <DashboardLayout>
      <RiskDashboard />
    </DashboardLayout>
  );
}
