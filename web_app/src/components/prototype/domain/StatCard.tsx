type StatCardProps = {
  label: string;
  value: string;
  helper?: string;
  tone?: 'default' | 'success' | 'accent';
};

const toneMap = {
  default:
    'border-[#7dd3fc]/70 bg-[#e0f2fe] text-[#082f49] shadow-[0_18px_44px_rgba(14,165,233,0.12)] dark:border-[#38bdf8]/40 dark:bg-[#082f49]/55 dark:text-[#e0f2fe]',
  success:
    'border-[#7dd3fc]/70 bg-[#e0f2fe] text-[#082f49] shadow-[0_18px_44px_rgba(14,165,233,0.12)] dark:border-[#38bdf8]/40 dark:bg-[#082f49]/55 dark:text-[#e0f2fe]',
  accent:
    'border-[#38bdf8]/80 bg-[#dbeafe] text-[#082f49] shadow-[0_18px_44px_rgba(14,165,233,0.16)] dark:border-[#38bdf8]/45 dark:bg-[#082f49]/60 dark:text-[#e0f2fe]',
};

export function StatCard({ label, value, helper, tone = 'default' }: StatCardProps) {
  return (
    <div className={`h-full min-h-[96px] rounded-[16px] border px-3 py-3 transition hover:border-[#ff5900] hover:shadow-[0_18px_44px_rgba(255,89,0,0.12)] dark:hover:border-[#ff5900] dark:hover:shadow-[0_18px_44px_rgba(255,89,0,0.12)] ${toneMap[tone]}`}>
      <div className="min-w-0">
        <p className="text-[0.6rem] font-semibold uppercase tracking-[0.13em] text-[#075985]/70 dark:text-[#bae6fd]/75">{label}</p>
        <p className="mt-1.5 text-[1.18rem] font-semibold tracking-[-0.03em] text-[#0c4a6e] dark:text-[#e0f2fe]">{value}</p>
      </div>
    </div>
  );
}
