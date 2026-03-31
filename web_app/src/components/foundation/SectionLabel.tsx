import { PropsWithChildren } from 'react';

export function SectionLabel({ children }: PropsWithChildren) {
  return (
    <span className="inline-flex rounded-full border border-teal-200 bg-white/90 px-4 py-1.5 text-[0.7rem] font-semibold uppercase tracking-[0.24em] text-teal-700 shadow-[0_10px_24px_rgba(15,23,42,0.06)]">
      {children}
    </span>
  );
}
