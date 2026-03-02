'use client';

import { useState } from 'react';
import { api } from '@/lib/api';

export default function TradePage() {
  const [message, setMessage] = useState('');
  const [size, setSize] = useState('1');

  const place = async (type: 'mkt' | 'lmt' | 'stp') => {
    try {
      const payload = { orderType: type, symbol: 'PI_XBTUSD', size: Number(size), leverage: 2, type, risk_at_stop_pct: 0.8 };
      const res = await api.post('/kraken/1/order?environment=demo', payload);
      setMessage(`Order sent: ${JSON.stringify(res.data)}`);
    } catch (err: any) {
      setMessage(`Blocked/Error: ${JSON.stringify(err.response?.data || err.message)}`);
    }
  };

  return (
    <main className="p-6 space-y-3">
      <h1 className="text-xl font-bold">Execution Proxy Ticket</h1>
      <div className="card space-y-2">
        <label className="text-sm block">Size</label>
        <input className="bg-slate-800 border border-slate-700 p-1" value={size} onChange={(e) => setSize(e.target.value)} />
        <div className="flex gap-2">
          <button className="bg-emerald-700 px-3 py-1 rounded" onClick={() => place('mkt')}>Market</button>
          <button className="bg-blue-700 px-3 py-1 rounded" onClick={() => place('lmt')}>Limit</button>
          <button className="bg-purple-700 px-3 py-1 rounded" onClick={() => place('stp')}>Stop</button>
        </div>
      </div>
      <pre className="card text-xs whitespace-pre-wrap">{message}</pre>
    </main>
  );
}
