import React, { useState } from 'react';
import { Mail, Lock, LogIn, ShieldAlert, Sparkles } from 'lucide-react';
import { api } from '../services/api';

export default function LoginPage({ onLoginSuccess, onGoToRegister }) {
  const [email, setEmail] = useState('amit@org.com');
  const [password, setPassword] = useState('user123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const user = await api.login(email, password);
      onLoginSuccess(user);
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemo = async (demoEmail, demoPass) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError('');
    setLoading(true);
    try {
      const user = await api.login(demoEmail, demoPass);
      onLoginSuccess(user);
    } catch (err) {
      setError(err.message || 'Login failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto my-12 p-6 glass-panel rounded-2xl border border-slate-800 shadow-2xl">
      <div className="text-center mb-6">
        <div className="w-12 h-12 rounded-xl bg-cyan-500/20 text-cyan-400 mx-auto flex items-center justify-center mb-3">
          <LogIn className="w-6 h-6" />
        </div>
        <h2 className="text-2xl font-bold text-white">Employee Login</h2>
        <p className="text-xs text-slate-400 mt-1">Sign in with your organization email</p>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4 text-left">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Email / Mobile</label>
          <div className="relative">
            <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full pl-9 pr-3 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-cyan-500"
              placeholder="name@organization.com"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
          <div className="relative">
            <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full pl-9 pr-3 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white focus:outline-none focus:border-cyan-500"
              placeholder="••••••••"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-slate-950 font-bold rounded-xl text-sm transition-all shadow-lg shadow-cyan-500/20 disabled:opacity-50"
        >
          {loading ? 'Authenticating...' : 'Login'}
        </button>
      </form>

      {/* Quick Demo Credentials */}
      <div className="mt-6 pt-4 border-t border-slate-800 text-left">
        <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center space-x-1">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span>One-Click Quick Login:</span>
        </p>
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => handleQuickDemo('amit@org.com', 'user123')}
            className="p-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-700/80 rounded-xl text-left transition-colors"
          >
            <p className="font-bold text-cyan-400 text-xs">Amit Sharma (Driver)</p>
            <p className="text-[10px] text-slate-400">amit@org.com</p>
          </button>

          <button
            type="button"
            onClick={() => handleQuickDemo('chanchal@org.com', 'user123')}
            className="p-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-700/80 rounded-xl text-left transition-colors"
          >
            <p className="font-bold text-indigo-400 text-xs">Chanchal (Passenger)</p>
            <p className="text-[10px] text-slate-400">chanchal@org.com</p>
          </button>

          <button
            type="button"
            onClick={() => handleQuickDemo('admin@org.com', 'admin123')}
            className="col-span-2 p-2.5 bg-purple-950/40 hover:bg-purple-900/50 border border-purple-700/50 rounded-xl text-left transition-colors"
          >
            <p className="font-bold text-purple-300 text-xs">Admin User (Company Admin)</p>
            <p className="text-[10px] text-slate-400">admin@org.com</p>
          </button>
        </div>
      </div>

      <div className="mt-6 text-center">
        <button
          onClick={onGoToRegister}
          className="text-xs text-slate-400 hover:text-cyan-400 transition-colors"
        >
          Don't have an account? <span className="text-cyan-400 font-semibold underline">Create Account</span>
        </button>
      </div>
    </div>
  );
}
