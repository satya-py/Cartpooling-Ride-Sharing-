import React, { useState, useEffect } from 'react';
import { CreditCard, PlusCircle, ArrowUpRight, ArrowDownLeft, Wallet } from 'lucide-react';
import { api } from '../services/api';

export default function WalletPage({ user }) {
  const [balance, setBalance] = useState(500.0);
  const [amount, setAmount] = useState('200');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');

  const fetchWallet = async () => {
    if (!user?.id) return;
    try {
      const res = await api.getWallet(user.id);
      setBalance(res.wallet_balance);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchWallet();
  }, [user]);

  const handleRecharge = async (e) => {
    e.preventDefault();
    if (!user?.id) {
      setMsg('Please log in before recharging your wallet.');
      return;
    }
    setLoading(true);
    setMsg('');
    try {
      const res = await api.rechargeWallet(amount, user.id);
      setBalance(res.wallet_balance);
      setMsg(`Recharged ₹${amount} successfully!`);
    } catch (err) {
      setMsg(err.message || 'Recharge failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6 text-left">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-2xl font-bold text-white">Wallet & Payments</h2>
        <p className="text-xs text-slate-400">Manage wallet balance and view ride payments</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Wallet Balance Card */}
        <div className="glass-panel p-6 rounded-2xl border border-cyan-500/30 bg-gradient-to-br from-slate-900 via-slate-900 to-cyan-950/40 space-y-4 shadow-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">Available Balance</span>
            <Wallet className="w-6 h-6 text-cyan-400" />
          </div>
          <div className="text-4xl font-extrabold text-white">
            ₹{balance.toFixed(2)}
          </div>
          <p className="text-xs text-slate-400">Instant cashless payments for carpooling rides</p>
        </div>

        {/* Recharge Form */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <h3 className="text-lg font-bold text-white flex items-center space-x-2">
            <PlusCircle className="w-5 h-5 text-emerald-400" />
            <span>Recharge Wallet</span>
          </h3>

          {msg && <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs">{msg}</div>}

          <form onSubmit={handleRecharge} className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Amount (₹)</label>
              <input
                type="number"
                min="10"
                required
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-sm text-white"
              />
            </div>

            <div className="flex space-x-2">
              {[100, 200, 500, 1000].map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => setAmount(val.toString())}
                  className="px-3 py-1 bg-slate-800 text-xs font-medium text-slate-300 rounded-lg hover:bg-slate-700"
                >
                  +₹{val}
                </button>
              ))}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-gradient-to-r from-emerald-400 to-cyan-500 text-slate-950 font-bold rounded-xl text-xs shadow-md disabled:opacity-50"
            >
              {loading ? 'Processing...' : 'Add Money to Wallet'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
