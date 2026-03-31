import { ReactNode } from 'react';

import { SectionLabel } from '@/components/foundation/SectionLabel';

type FeatureStoryProps = {
  label: string;
  title: string;
  description: string;
  points: string[];
  visual: ReactNode;
  reverse?: boolean;
};

export function FeatureStory({ label, title, description, points, visual, reverse = false }: FeatureStoryProps) {
  return (
    <section className={`grid gap-10 rounded-[2rem] border border-white/70 bg-white/80 p-8 shadow-[0_24px_80px_rgba(15,23,42,0.08)] backdrop-blur-xl lg:grid-cols-2 ${reverse ? 'lg:[&>*:first-child]:order-2' : ''}`}>
      <div className="flex flex-col justify-center">
        <SectionLabel>{label}</SectionLabel>
        <h3 className="mt-6 max-w-xl font-display text-4xl font-semibold leading-tight tracking-tight text-slate-950">{title}</h3>
        <p className="mt-5 max-w-xl text-base leading-8 text-slate-600">{description}</p>
        <ul className="mt-6 space-y-3 text-sm text-slate-700">
          {points.map((point) => (
            <li key={point} className="flex items-start gap-3">
              <span className="mt-1 inline-flex h-6 w-6 items-center justify-center rounded-full bg-teal-100 text-xs font-bold text-teal-700">+</span>
              <span className="leading-7">{point}</span>
            </li>
          ))}
        </ul>
      </div>
      <div>{visual}</div>
    </section>
  );
}
