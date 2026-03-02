'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export default function AdminPage() {
  const policies = useQuery({ queryKey: ['policies'], queryFn: async () => (await api.get('/admin/policies')).data });
  const logs = useQuery({ queryKey: ['logs'], queryFn: async () => (await api.get('/admin/audit-logs')).data });

  return (
    <main className="p-6 space-y-4">
      <h1 className="text-xl font-bold">Back Office Admin</h1>
      <section className="card">
        <h2 className="font-semibold mb-2">Policies</h2>
        {(policies.data || []).map((p: any) => <div key={p.id} className="text-sm">#{p.id} {p.name} (max lev {p.max_leverage}x)</div>)}
      </section>
      <section className="card">
        <h2 className="font-semibold mb-2">Audit Logs</h2>
        {(logs.data || []).map((l: any) => <div key={l.id} className="text-xs border-b border-slate-800 py-1">{l.entity}:{l.action}</div>)}
      </section>
    </main>
  );
}
