type StatCardProps = {
  label: string;
  value: string;
  helper?: string;
  tone?: 'default' | 'success' | 'accent';
};

const toneMap = {
  default:
    'border-black/8 bg-white text-black dark:border-white/10 dark:bg-[#111318] dark:text-white',
  success:
    'border-black/8 bg-white text-black dark:border-white/10 dark:bg-[#111318] dark:text-white',
  accent:
    'border-black/8 bg-white text-black dark:border-white/10 dark:bg-[#111318] dark:text-white',
};

export function StatCard({ label, value, helper, tone = 'default' }: StatCardProps) {
  return (
    <div className={`h-full min-h-[96px] rounded-[16px] border px-3 py-3 shadow-[0_18px_44px_rgba(15,23,42,0.06)] transition hover:border-[#ff5900] hover:shadow-[0_18px_44px_rgba(255,89,0,0.12)] dark:hover:border-[#ff5900] dark:hover:shadow-[0_18px_44px_rgba(255,89,0,0.12)] dark:shadow-[0_24px_70px_rgba(0,0,0,0.26)] ${toneMap[tone]}`}>
      <div className="min-w-0">
        <p className="text-[0.6rem] font-semibold uppercase tracking-[0.13em] text-black/55 dark:text-white/55">{label}</p>
        <p className="mt-1.5 text-[1.18rem] font-semibold tracking-[-0.03em] text-black dark:text-white">{value}</p>
      </div>
    </div>
  );
}
