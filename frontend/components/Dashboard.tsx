'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useSessionStore } from '@/store/useSessionStore';

const userId = 1;

export default function Dashboard() {
  const { mode, sessionStarted, pnlVisible, toggleSession, environment, setEnvironment } = useSessionStore();

  const scoreQuery = useQuery({
    queryKey: ['score'],
    queryFn: async () => (await api.get(`/users/${userId}/score`)).data
  });
  const eventsQuery = useQuery({
    queryKey: ['events'],
    queryFn: async () => (await api.get(`/users/${userId}/events`)).data
  });

  return (
    <main className="p-6 space-y-4">
      <header className="card flex flex-wrap items-center gap-3 justify-between">
        <div className="space-x-2">
          <span className="px-2 py-1 rounded bg-indigo-700 text-xs uppercase">{mode} mode</span>
          <span className="px-2 py-1 rounded bg-emerald-700 text-xs">{sessionStarted ? 'Session Live' : 'Session Inactive'}</span>
        </div>
        <div className="text-sm">StabilityScore: <b>{scoreQuery.data?.score ?? '--'}</b></div>
        <div className="flex items-center gap-2">
          <select className="bg-slate-800 border border-slate-700 p-1" value={environment} onChange={(e) => setEnvironment(e.target.value as 'demo' | 'prod')}>
            <option value="demo">Demo</option>
            <option value="prod">Prod</option>
          </select>
          <button className="bg-blue-600 px-3 py-1 rounded" onClick={() => toggleSession(!sessionStarted)}>{sessionStarted ? 'Stop Session' : 'Start Session'}</button>
        </div>
      </header>

      <section className="grid md:grid-cols-2 gap-4">
        <div className="card">
          <h2 className="font-semibold mb-2">Risk Envelope</h2>
          <ul className="text-sm space-y-1">
            <li>Risk-at-stop %: 1.0%</li>
            <li>Max leverage: 3x</li>
            <li>Max adds remaining: 1</li>
            <li>Stop edit permissions: tighten only (widen blocked)</li>
          </ul>
        </div>
        <div className="card">
          <h2 className="font-semibold mb-2">Next Permitted Actions</h2>
          <div className="flex flex-wrap gap-2 text-sm">
            <button className="bg-emerald-700 px-2 py-1 rounded">Place Market</button>
            <button className="bg-emerald-700 px-2 py-1 rounded">Place Limit</button>
            <button className="bg-emerald-700 px-2 py-1 rounded">Place Stop</button>
            <button className="bg-slate-700 px-2 py-1 rounded" disabled title="Stop widening is blocked">Widen Stop (Blocked)</button>
          </div>
        </div>
      </section>

      <section className="grid md:grid-cols-2 gap-4">
        <div className="card">
          <h2 className="font-semibold mb-2">Rule Adherence Checklist</h2>
          <ul className="text-sm space-y-1">
            <li>✅ No over-leverage attempts</li>
            <li>✅ No stop widening</li>
            <li>✅ Add cooldown respected (10m)</li>
            <li>✅ Symbol allowlist respected (BTCUSD)</li>
          </ul>
        </div>
        <div className="card">
          <h2 className="font-semibold mb-2">Event Feed (Last 10)</h2>
          <div className="text-xs space-y-1">
            {(eventsQuery.data || []).map((e: any) => (
              <div key={e.id} className="border-b border-slate-800 pb-1">{e.action} — <span className={e.guard_result === 'block' ? 'text-red-400' : 'text-green-400'}>{e.guard_result}</span> {e.reason ? `(${e.reason})` : ''}</div>
            ))}
          </div>
        </div>
      </section>

      <section className="card">
        <h2 className="font-semibold mb-2">Post-trade Reveal</h2>
        {!pnlVisible ? (
          <p className="text-sm text-amber-300">PnL, ROE, equity delta, and % return are hidden while trade is open.</p>
        ) : (
          <p className="text-sm">Trade closed/session ended. PnL: <b>$120.50</b> | ROE: <b>+2.1%</b></p>
        )}
      </section>
    </main>
  );
}
