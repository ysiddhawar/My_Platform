import { FormEvent, useMemo, useState } from 'react';

import { endpoints } from '@/api/endpoints';
import { useAuthStore } from '@/state/authStore';

type AuthMode = 'signup' | 'signin';

type FormState = {
  fullName: string;
  email: string;
  password: string;
};

const defaultState: FormState = {
  fullName: '',
  email: '',
  password: ''
};

export function AuthCard() {
  const { mode, setMode, setToken, statusMessage, setStatusMessage } = useAuthStore();
  const [form, setForm] = useState<FormState>(defaultState);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const title = useMemo(() => {
    return mode === 'signup' ? 'Create your secure workspace' : 'Sign in to continue';
  }, [mode]);

  const subtitle = useMemo(() => {
    return mode === 'signup'
      ? 'Start with the owner account for this deployment. You can invite and manage additional users after setup.'
      : 'Use your existing credentials to enter the platform.';
  }, [mode]);

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setStatusMessage(null);

    try {
      if (mode === 'signup') {
        await endpoints.bootstrapAdmin({
          username: form.email.trim(),
          password: form.password,
          account_ids: ['*']
        });
        setStatusMessage('Workspace owner created. Sign in now with the same credentials.');
        setMode('signin');
        return;
      }

      const response = await endpoints.login({
        username: form.email.trim(),
        password: form.password
      });
      const token = response.data?.session?.session_token || response.data?.token || null;
      if (token) {
        setToken(token);
      }
      setStatusMessage('Session created. The workspace is ready.');
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Unable to complete the request.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="rounded-[2rem] border border-slate-200/80 bg-white/90 p-8 shadow-[0_24px_70px_rgba(15,23,42,0.1)] backdrop-blur-xl">
      <div className="flex gap-2 rounded-full border border-slate-200 bg-[#f4efe6] p-1">
        {(['signup', 'signin'] as AuthMode[]).map((item) => {
          const active = item === mode;
          return (
            <button
              type="button"
              key={item}
              onClick={() => {
                setMode(item);
                setError(null);
                setStatusMessage(null);
              }}
              className={`flex-1 rounded-full px-4 py-3 text-sm font-semibold transition ${
                active ? 'bg-slate-950 text-white shadow-[0_10px_24px_rgba(15,23,42,0.16)]' : 'text-slate-500'
              }`}
            >
              {item === 'signup' ? 'Sign up' : 'Sign in'}
            </button>
          );
        })}
      </div>

      <div className="mt-8">
        <p className="text-[0.72rem] font-semibold uppercase tracking-[0.28em] text-cyan-700">Workspace access</p>
        <h2 className="mt-4 text-3xl font-semibold tracking-[-0.05em] text-slate-950 sm:text-[2.15rem]">{title}</h2>
        <p className="mt-4 max-w-lg text-[0.95rem] leading-8 text-slate-600">{subtitle}</p>
      </div>

      <form className="mt-10 space-y-5" onSubmit={onSubmit}>
        {mode === 'signup' ? (
          <label className="block">
            <span className="mb-2.5 block text-sm font-medium text-slate-700">Full name</span>
            <input
              value={form.fullName}
              onChange={(event) => setForm((current) => ({ ...current, fullName: event.target.value }))}
              className="h-14 w-full rounded-2xl border border-slate-200 bg-[#fbfaf6] px-4 text-sm text-slate-950 outline-none transition focus:border-cyan-500 focus:bg-white"
              placeholder="Aman Sharma"
            />
          </label>
        ) : null}

        <label className="block">
          <span className="mb-2.5 block text-sm font-medium text-slate-700">Email</span>
          <input
            type="email"
            required
            value={form.email}
            onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
            className="h-14 w-full rounded-2xl border border-slate-200 bg-[#fbfaf6] px-4 text-sm text-slate-950 outline-none transition focus:border-cyan-500 focus:bg-white"
            placeholder="founder@myplatform.trade"
          />
        </label>

        <label className="block">
          <span className="mb-2.5 block text-sm font-medium text-slate-700">Password</span>
          <input
            type="password"
            required
            value={form.password}
            onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
            className="h-14 w-full rounded-2xl border border-slate-200 bg-[#fbfaf6] px-4 text-sm text-slate-950 outline-none transition focus:border-cyan-500 focus:bg-white"
            placeholder="Minimum 8 characters"
          />
        </label>

        <button
          type="submit"
          disabled={isSubmitting}
          className="inline-flex h-14 w-full items-center justify-center rounded-2xl bg-slate-950 px-5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {isSubmitting ? 'Processing...' : mode === 'signup' ? 'Create workspace' : 'Sign in'}
        </button>
      </form>

      {error ? <p className="mt-5 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p> : null}
      {statusMessage ? <p className="mt-5 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">{statusMessage}</p> : null}

      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        <div className="rounded-[1.4rem] bg-[#f7f5ef] px-4 py-4">
          <p className="text-[0.65rem] uppercase tracking-[0.22em] text-slate-400">Pre-trade</p>
          <p className="mt-3 text-sm font-medium leading-7 text-slate-700">Record setup, probability, and checklist at entry.</p>
        </div>
        <div className="rounded-[1.4rem] bg-[#f7f5ef] px-4 py-4">
          <p className="text-[0.65rem] uppercase tracking-[0.22em] text-slate-400">Evidence</p>
          <p className="mt-3 text-sm font-medium leading-7 text-slate-700">Attach screenshots, notes, ratings, and tags to one trade bundle.</p>
        </div>
        <div className="rounded-[1.4rem] bg-[#f7f5ef] px-4 py-4">
          <p className="text-[0.65rem] uppercase tracking-[0.22em] text-slate-400">AI review</p>
          <p className="mt-3 text-sm font-medium leading-7 text-slate-700">See what broke, why it happened, and how to correct it.</p>
        </div>
      </div>
    </div>
  );
}
