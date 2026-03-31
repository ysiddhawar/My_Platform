import { useEffect, useState } from 'react';

const frames = [
  {
    title: 'The trade is structured before execution.',
    body: 'The platform records strategy, probability, checklist, and line-based position planning before the order is allowed through.',
    stat: 'Pre-trade capture',
    accent: 'bg-cyan-400'
  },
  {
    title: 'The journal preserves evidence, not memory.',
    body: 'Screenshot markers, notes, tags, ratings, and trade outcomes stay linked inside a single review record.',
    stat: 'Evidence bundle',
    accent: 'bg-amber-400'
  },
  {
    title: 'AI explains the behavior behind the outcome.',
    body: 'Pre-trade intent, post-trade changes, and execution drift become concrete diagnosis instead of vague reflection.',
    stat: 'Behavioral diagnosis',
    accent: 'bg-emerald-400'
  }
];

export function ExplainerReel() {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setActive((current) => (current + 1) % frames.length);
    }, 3600);

    return () => window.clearInterval(interval);
  }, []);

  return (
    <section className="relative overflow-hidden rounded-[2.2rem] border border-slate-200 bg-white p-5 shadow-[0_28px_80px_rgba(15,23,42,0.12)]">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <div>
          <p className="text-[0.68rem] font-semibold uppercase tracking-[0.26em] text-cyan-700">Product walkthrough</p>
          <h3 className="mt-2 text-2xl font-semibold tracking-[-0.04em] text-slate-950">Autoplay explainer</h3>
        </div>
        <div className="inline-flex items-center gap-2 rounded-full bg-slate-950 px-3 py-1.5 text-[0.68rem] font-semibold uppercase tracking-[0.22em] text-white">
          <span className="h-2 w-2 rounded-full bg-rose-400 animate-pulse" />
          Playing
        </div>
      </div>

      <div className="mt-5 overflow-hidden rounded-[1.8rem] bg-[linear-gradient(145deg,#0b1320_0%,#12263a_58%,#173753_100%)] p-6 text-white">
        <div className="flex items-center justify-between text-[0.68rem] uppercase tracking-[0.22em] text-white/50">
          <span>Walkthrough</span>
          <span>{String(active + 1).padStart(2, '0')} / {String(frames.length).padStart(2, '0')}</span>
        </div>

        <div className="relative mt-6 min-h-[26rem]">
          {frames.map((frame, index) => {
            const isActive = index === active;
            return (
              <div
                key={frame.title}
                className={`absolute inset-0 grid gap-6 transition-all duration-700 lg:grid-cols-[1.1fr_0.9fr] ${
                  isActive ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'
                }`}
              >
                <div className="flex flex-col justify-between">
                  <div>
                    <span className={`inline-flex rounded-full ${frame.accent} px-4 py-1.5 text-[0.68rem] font-semibold uppercase tracking-[0.24em] text-slate-950`}>
                      {frame.stat}
                    </span>
                    <h4 className="mt-6 max-w-xl text-4xl font-semibold leading-tight tracking-[-0.05em] text-white lg:text-[2.7rem]">{frame.title}</h4>
                    <p className="mt-5 max-w-xl text-base leading-8 text-slate-300">{frame.body}</p>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-3">
                    <div className="rounded-[1.4rem] border border-white/10 bg-white/5 px-4 py-4">
                      <p className="text-[0.65rem] uppercase tracking-[0.22em] text-white/45">Step 1</p>
                      <p className="mt-3 text-sm font-medium leading-7 text-white">Plan the trade with entry, stop, target, and minimum target.</p>
                    </div>
                    <div className="rounded-[1.4rem] border border-white/10 bg-white/5 px-4 py-4">
                      <p className="text-[0.65rem] uppercase tracking-[0.22em] text-white/45">Step 2</p>
                      <p className="mt-3 text-sm font-medium leading-7 text-white">Capture discipline fields before execution and after close.</p>
                    </div>
                    <div className="rounded-[1.4rem] border border-white/10 bg-white/5 px-4 py-4">
                      <p className="text-[0.65rem] uppercase tracking-[0.22em] text-white/45">Step 3</p>
                      <p className="mt-3 text-sm font-medium leading-7 text-white">Review evidence, diagnostics, and corrective signals.</p>
                    </div>
                  </div>
                </div>

                <div className="rounded-[1.6rem] border border-white/10 bg-white/5 p-4 backdrop-blur-sm">
                  <div className="flex gap-2 pb-4">
                    <span className="h-2.5 w-2.5 rounded-full bg-rose-300" />
                    <span className="h-2.5 w-2.5 rounded-full bg-amber-300" />
                    <span className="h-2.5 w-2.5 rounded-full bg-emerald-300" />
                  </div>
                  <div className="relative h-full min-h-[18rem] overflow-hidden rounded-[1.2rem] border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.06),rgba(255,255,255,0.02))] p-4">
                    <div className="absolute left-6 right-6 top-[20%] h-[2px] bg-cyan-300/70" />
                    <div className="absolute left-6 right-6 top-[42%] h-[2px] bg-emerald-300/70" />
                    <div className="absolute left-6 right-6 top-[72%] h-[2px] bg-rose-300/70" />
                    <div className="absolute left-[18%] top-[18%] rounded-full border border-cyan-300/60 bg-cyan-300/10 px-3 py-1 text-[0.65rem] uppercase tracking-[0.2em] text-cyan-100">Entry</div>
                    <div className="absolute left-[52%] top-[40%] rounded-full border border-emerald-300/60 bg-emerald-300/10 px-3 py-1 text-[0.65rem] uppercase tracking-[0.2em] text-emerald-100">Target</div>
                    <div className="absolute left-[30%] top-[70%] rounded-full border border-rose-300/60 bg-rose-300/10 px-3 py-1 text-[0.65rem] uppercase tracking-[0.2em] text-rose-100">Stop</div>
                    <div className="absolute right-5 top-5 rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-right">
                      <p className="text-[0.62rem] uppercase tracking-[0.22em] text-white/45">AI note</p>
                      <p className="mt-2 max-w-[12rem] text-sm leading-6 text-white/90">Checklist incompletion and early exit are visible in the same trade evidence.</p>
                    </div>
                    <div className="absolute bottom-5 left-5 right-5 rounded-[1rem] border border-white/10 bg-black/20 px-4 py-3">
                      <div className="flex items-center justify-between text-xs uppercase tracking-[0.2em] text-white/45">
                        <span>Strategy</span>
                        <span>Probability</span>
                      </div>
                      <div className="mt-3 flex items-center justify-between text-sm font-medium text-white">
                        <span>London Breakout</span>
                        <span>60%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-5 flex items-center justify-between">
        <div className="flex gap-2">
          {frames.map((frame, index) => (
            <button
              type="button"
              key={frame.title}
              onClick={() => setActive(index)}
              className={`h-1.5 rounded-full transition-all ${index === active ? 'w-16 bg-slate-950' : 'w-10 bg-slate-300'}`}
              aria-label={`Show reel frame ${index + 1}`}
            />
          ))}
        </div>
        <p className="text-sm leading-7 text-slate-500">A guided overview of how the workflow captures the trade before, during, and after execution.</p>
      </div>
    </section>
  );
}
