import { DashboardLayout } from '@/components/layout/DashboardLayout';
import { PortfolioDashboard } from '@/dashboards/portfolio/PortfolioDashboard';

export default function PortfolioPage() {
  return (
    <DashboardLayout>
      <PortfolioDashboard />
    </DashboardLayout>
  );
}
