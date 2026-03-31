export function HeroProductStage() {
  return (
    <section
      id="next-section"
      className="relative overflow-hidden rounded-[2.4rem] border border-[var(--theme-border)] bg-[var(--theme-surface)] px-8 py-10 shadow-[0_24px_80px_var(--stage-shell-shadow)] backdrop-blur-xl sm:px-10 lg:px-12 lg:py-12"
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,var(--stage-glow-a),transparent_34%),radial-gradient(circle_at_bottom_right,var(--stage-glow-b),transparent_28%)]" />

      <div className="relative">
        <div className="max-w-3xl">
          <p className="text-[0.72rem] font-semibold uppercase tracking-[0.3em] text-[var(--hero-accent)]">Hero product stage</p>
          <h2 className="mt-4 text-3xl font-semibold tracking-[-0.05em] text-[var(--color-ink)] sm:text-4xl lg:text-[3.4rem]">
            The product needs to feel as premium as the promise.
          </h2>
          <p className="mt-5 max-w-2xl text-base leading-8 text-[var(--color-muted)] sm:text-lg">
            This stage previews the full workflow: trade planning, structured discipline capture, screenshot evidence, and AI diagnosis, without turning the landing page into a crowded dashboard.
          </p>
        </div>

        <div className="mt-10 grid gap-8 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
          <div className="relative rounded-[2rem] border border-[var(--stage-border)] bg-[var(--stage-core-bg)] p-5 shadow-[0_28px_80px_var(--stage-core-shadow)]">
            <div className="flex items-center justify-between border-b border-[var(--stage-border)] pb-4">
              <div>
                <p className="text-[0.68rem] font-semibold uppercase tracking-[0.24em] text-[var(--color-muted)]">My Platform</p>
                <p className="mt-2 text-xl font-semibold tracking-[-0.03em] text-[var(--color-ink)]">Execution intelligence workspace</p>
              </div>
              <div className="rounded-full bg-[var(--stage-pill-bg)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--stage-pill-text)]">
                Live discipline mode
              </div>
            </div>

            <div className="mt-5 grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
              <div className="rounded-[1.6rem] border border-[var(--stage-border)] bg-[var(--stage-panel-bg)] p-5">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[0.68rem] uppercase tracking-[0.22em] text-[var(--color-muted)]">Position sizer</p>
                    <p className="mt-2 text-lg font-semibold tracking-[-0.03em] text-[var(--color-ink)]">Pre-trade capture stays inside execution</p>
                  </div>
                  <div className="rounded-2xl bg-[var(--stage-mini-bg)] px-3 py-2 text-sm font-semibold text-[var(--hero-accent)]">Preview</div>
                </div>

                <div className="mt-5 rounded-[1.4rem] bg-[var(--stage-inner-bg)] p-4">
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-[1.1rem] bg-[var(--stage-chip-bg)] px-4 py-3">
                      <p className="text-[0.62rem] uppercase tracking-[0.2em] text-[var(--color-muted)]">Strategy</p>
                      <p className="mt-2 text-sm font-semibold text-[var(--color-ink)]">London Breakout</p>
                    </div>
                    <div className="rounded-[1.1rem] bg-[var(--stage-chip-bg)] px-4 py-3">
                      <p className="text-[0.62rem] uppercase tracking-[0.2em] text-[var(--color-muted)]">Probability</p>
                      <p className="mt-2 text-sm font-semibold text-[var(--color-ink)]">60%</p>
                    </div>
                  </div>

                  <div className="relative mt-4 overflow-hidden rounded-[1.3rem] border border-[var(--stage-border)] bg-[var(--stage-chart-bg)] p-4">
                    <div className="absolute left-5 right-5 top-[24%] h-[2px] bg-cyan-400/70" />
                    <div className="absolute left-5 right-5 top-[52%] h-[2px] bg-emerald-400/70" />
                    <div className="absolute left-5 right-5 top-[78%] h-[2px] bg-rose-400/70" />
                    <div className="relative flex min-h-[12rem] items-end justify-between gap-3">
                      <div className="rounded-full bg-cyan-500/12 px-3 py-1 text-[0.62rem] font-semibold uppercase tracking-[0.2em] text-cyan-600">Entry</div>
                      <div className="rounded-full bg-emerald-500/12 px-3 py-1 text-[0.62rem] font-semibold uppercase tracking-[0.2em] text-emerald-600">Target</div>
                      <div className="rounded-full bg-rose-500/12 px-3 py-1 text-[0.62rem] font-semibold uppercase tracking-[0.2em] text-rose-600">Stop</div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="grid gap-4">
                <div className="rounded-[1.6rem] border border-[var(--stage-border)] bg-[var(--stage-panel-bg)] p-5">
                  <p className="text-[0.68rem] uppercase tracking-[0.22em] text-[var(--color-muted)]">Evidence bundle</p>
                  <p className="mt-2 text-lg font-semibold tracking-[-0.03em] text-[var(--color-ink)]">Markers, notes, tags, and ratings stay attached.</p>
                  <div className="mt-4 rounded-[1.3rem] bg-[var(--stage-inner-bg)] p-4">
                    <div className="flex items-center justify-between text-sm text-[var(--color-muted)]">
                      <span>Screenshot markers</span>
                      <span>4 linked</span>
                    </div>
                    <div className="mt-4 grid grid-cols-2 gap-3">
                      <div className="rounded-[1rem] bg-[var(--stage-chip-bg)] px-3 py-3 text-sm font-semibold text-[var(--color-ink)]">Entry</div>
                      <div className="rounded-[1rem] bg-[var(--stage-chip-bg)] px-3 py-3 text-sm font-semibold text-[var(--color-ink)]">Close</div>
                      <div className="rounded-[1rem] bg-[var(--stage-chip-bg)] px-3 py-3 text-sm font-semibold text-[var(--color-ink)]">Stop</div>
                      <div className="rounded-[1rem] bg-[var(--stage-chip-bg)] px-3 py-3 text-sm font-semibold text-[var(--color-ink)]">Target</div>
                    </div>
                  </div>
                </div>

                <div className="rounded-[1.6rem] border border-[var(--stage-border)] bg-[var(--stage-panel-bg)] p-5">
                  <p className="text-[0.68rem] uppercase tracking-[0.22em] text-[var(--color-muted)]">AI diagnosis</p>
                  <p className="mt-2 text-lg font-semibold tracking-[-0.03em] text-[var(--color-ink)]">Behavior becomes measurable instead of anecdotal.</p>
                  <div className="mt-4 rounded-[1.3rem] bg-[var(--stage-inner-bg)] p-4">
                    <p className="text-[0.62rem] uppercase tracking-[0.2em] text-[var(--color-muted)]">Current signal</p>
                    <p className="mt-3 text-base font-semibold text-[var(--color-ink)]">Checklist incompletion + early exit tendency</p>
                    <p className="mt-3 text-sm leading-7 text-[var(--color-muted)]">Pre-trade conviction and post-trade behavior can be reviewed in the same chain of evidence.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="grid gap-4">
            <div className="rounded-[1.8rem] border border-[var(--stage-border)] bg-[var(--stage-panel-bg)] px-6 py-6 shadow-[0_18px_44px_var(--stage-float-shadow)]">
              <p className="text-[0.68rem] uppercase tracking-[0.22em] text-[var(--color-muted)]">Why this stage exists</p>
              <p className="mt-3 text-base leading-8 text-[var(--color-ink)]">
                The visitor should feel the product before they scroll into the deeper story. This is where the page starts earning trust.
              </p>
            </div>
            <div className="rounded-[1.8rem] border border-[var(--stage-border)] bg-[var(--stage-panel-bg)] px-6 py-6 shadow-[0_18px_44px_var(--stage-float-shadow)]">
              <p className="text-[0.68rem] uppercase tracking-[0.22em] text-[var(--color-muted)]">What comes next</p>
              <p className="mt-3 text-base leading-8 text-[var(--color-ink)]">
                After this section, we build the autoplay walkthrough so the product journey becomes explicit instead of only implied.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
