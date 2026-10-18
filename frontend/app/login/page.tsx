'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, saveAuthSession } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    try {
      const response = await api.post('/auth/login', { email, password });
      saveAuthSession(response.data.token, response.data.user_id, response.data.role);
      router.push('/');
    } catch (error: any) {
      setMessage(error.response?.data?.detail || 'Login failed');
    }
  };

  return (
    <main className="p-6 max-w-md mx-auto">
      <form className="card space-y-3" onSubmit={submit}>
        <h1 className="text-xl font-bold">Log in</h1>
        <input className="w-full bg-slate-800 border border-slate-700 p-2" type="email" placeholder="Email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        <input className="w-full bg-slate-800 border border-slate-700 p-2" type="password" placeholder="Password" value={password} onChange={(event) => setPassword(event.target.value)} required />
        <button className="bg-blue-600 px-3 py-2 rounded" type="submit">Log in</button>
        {message && <p className="text-red-400 text-sm">{message}</p>}
      </form>
    </main>
  );
}
