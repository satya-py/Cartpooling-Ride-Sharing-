import React, { useState, useEffect } from 'react';
import { MapPin, PlusCircle } from 'lucide-react';
import { api } from '../services/api';

export default function SavedPlacesPage({ user }) {
  const [places, setPlaces] = useState([]);
  const [name, setName] = useState('');
  const [address, setAddress] = useState('');
  const [lat, setLat] = useState('22.584');
  const [lon, setLon] = useState('88.402');
  const [loading, setLoading] = useState(false);

  const fetchPlaces = async () => {
    if (!user?.id) return;
    try {
      const data = await api.getSavedPlaces(user.id);
      setPlaces(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchPlaces();
  }, [user]);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!user?.id) {
      alert('Please log in before saving locations.');
      return;
    }
    setLoading(true);
    try {
      await api.addSavedPlace({ name, address, latitude: parseFloat(lat), longitude: parseFloat(lon) }, user.id);
      setName('');
      setAddress('');
      fetchPlaces();
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6 text-left">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-2xl font-bold text-white">Saved Places</h2>
        <p className="text-xs text-slate-400">Save frequent pickup and destination locations for faster bookings</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <h3 className="text-lg font-bold text-white flex items-center space-x-2">
            <PlusCircle className="w-5 h-5 text-cyan-400" />
            <span>Add New Saved Place</span>
          </h3>

          <form onSubmit={handleAdd} className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Place Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Home, Office, Gym"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Address</label>
              <input
                type="text"
                required
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="e.g. New Town Action Area 1"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Latitude</label>
                <input
                  type="number"
                  step="0.0001"
                  required
                  value={lat}
                  onChange={(e) => setLat(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Longitude</label>
                <input
                  type="number"
                  step="0.0001"
                  required
                  value={lon}
                  onChange={(e) => setLon(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-cyan-500 text-slate-950 font-bold rounded-xl text-xs shadow-md disabled:opacity-50"
            >
              Save Location
            </button>
          </form>
        </div>

        <div className="space-y-3">
          <h3 className="text-lg font-bold text-white">Your Saved Places</h3>
          {places.length === 0 ? (
            <div className="glass-panel p-6 rounded-2xl text-center text-xs text-slate-400">No saved places yet.</div>
          ) : (
            places.map((p) => (
              <div key={p.id} className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center">
                  <MapPin className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-bold text-white text-sm">{p.name}</h4>
                  <p className="text-xs text-slate-400">{p.address}</p>
                  <p className="text-[10px] text-slate-500 font-mono">({p.latitude}, {p.longitude})</p>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
