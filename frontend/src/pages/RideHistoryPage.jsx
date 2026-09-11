import React, { useState, useEffect } from 'react';
import { Clock, MapPin, CheckCircle } from 'lucide-react';
import { api } from '../services/api';

export default function RideHistoryPage({ user }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.id) {
      api.getUserTrips(user.id).then((data) => {
        setHistory(data.filter((t) => t.status === 'completed' || t.payment_status === 'completed'));
      }).finally(() => setLoading(false));
    }
  }, [user]);

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6 text-left">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-2xl font-bold text-white">Ride History</h2>
        <p className="text-xs text-slate-400">Record of all completed journeys and travel history</p>
      </div>

      {loading ? (
        <div className="glass-panel p-6 rounded-2xl text-center text-xs text-slate-400">Loading history...</div>
      ) : history.length === 0 ? (
        <div className="glass-panel p-6 rounded-2xl text-center text-xs text-slate-400">
          No completed rides recorded yet. Complete a trip to see history!
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((h) => (
            <div key={h.id} className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center justify-between">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  <span className="font-bold text-white text-sm">{h.pickup_name} → {h.drop_name}</span>
                </div>
                <p className="text-xs text-slate-400">Passenger: {h.passenger_name} • Seats: {h.seats_booked}</p>
                <p className="text-[10px] text-slate-500 font-mono">Trip #{h.id} • {h.created_at}</p>
              </div>

              <div className="text-right">
                <span className="font-extrabold text-cyan-400 text-sm">₹{h.total_fare.toFixed(2)}</span>
                <p className="text-[10px] text-emerald-400 capitalize">{h.payment_method} Payment Paid</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
