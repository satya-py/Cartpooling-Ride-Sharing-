import React, { useState, useEffect } from 'react';
import { Car, PlusCircle, CheckCircle, ShieldCheck } from 'lucide-react';
import { api } from '../services/api';

export default function VehiclesPage({ user }) {
  const [vehicles, setVehicles] = useState([]);
  const [model, setModel] = useState('');
  const [regNo, setRegNo] = useState('');
  const [seats, setSeats] = useState(4);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');

  const fetchVehicles = async () => {
    if (!user?.id) return;
    try {
      const data = await api.getVehicles(user.id);
      setVehicles(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchVehicles();
  }, [user]);

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!user?.id) {
      setMsg('Please log in before registering a vehicle.');
      return;
    }
    setLoading(true);
    setMsg('');
    try {
      await api.registerVehicle({ model, registration_number: regNo, seating_capacity: parseInt(seats) }, user.id);
      setMsg('Vehicle registered successfully and approved!');
      setModel('');
      setRegNo('');
      fetchVehicles();
    } catch (err) {
      setMsg(err.message || 'Vehicle registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6 text-left">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-2xl font-bold text-white">Vehicle Management</h2>
        <p className="text-xs text-slate-400">Register and manage your vehicles for ride publishing</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Register Vehicle Form */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <h3 className="text-lg font-bold text-white flex items-center space-x-2">
            <PlusCircle className="w-5 h-5 text-cyan-400" />
            <span>Register New Vehicle</span>
          </h3>

          {msg && <div className="p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs">{msg}</div>}

          <form onSubmit={handleRegister} className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Vehicle Model</label>
              <input
                type="text"
                required
                value={model}
                onChange={(e) => setModel(e.target.value)}
                placeholder="e.g. Honda City / Hyundai i20"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Registration Number</label>
              <input
                type="text"
                required
                value={regNo}
                onChange={(e) => setRegNo(e.target.value)}
                placeholder="e.g. WB-02-AB-1234"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Seating Capacity</label>
              <input
                type="number"
                min="1"
                max="8"
                required
                value={seats}
                onChange={(e) => setSeats(e.target.value)}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-gradient-to-r from-cyan-500 to-indigo-600 text-slate-950 font-bold rounded-xl text-xs shadow-md disabled:opacity-50"
            >
              {loading ? 'Registering...' : 'Register Vehicle'}
            </button>
          </form>
        </div>

        {/* Registered Vehicles List */}
        <div className="space-y-3">
          <h3 className="text-lg font-bold text-white">Registered Vehicles</h3>
          {vehicles.length === 0 ? (
            <div className="glass-panel p-6 rounded-2xl text-center text-xs text-slate-400">
              No vehicles registered yet. Register your vehicle to publish rides!
            </div>
          ) : (
            vehicles.map((v) => (
              <div key={v.id} className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center">
                    <Car className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="font-bold text-white text-sm">{v.model}</h4>
                    <p className="text-xs text-slate-400 font-mono">{v.registration_number}</p>
                    <p className="text-[10px] text-slate-500">Seating Capacity: {v.seating_capacity}</p>
                  </div>
                </div>

                <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 capitalize">
                  {v.status}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
