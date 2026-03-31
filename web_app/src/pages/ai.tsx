import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { AIDashboard } from '@/dashboards/ai/AIDashboard';

export default function AIPage() {
  return (
    <DashboardLayout>
      <AIDashboard />
    </DashboardLayout>
  );
}
