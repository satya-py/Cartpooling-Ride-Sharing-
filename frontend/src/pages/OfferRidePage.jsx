import React, { useState, useEffect } from 'react';
import { MapPin, Navigation, Calendar, Clock, Users, DollarSign, PlusCircle, Car, CheckCircle2, ShieldAlert } from 'lucide-react';
import MapView from '../components/MapView';
import { api } from '../services/api';

const PRESET_LOCATIONS = [
  { name: 'Home (New Town)', address: 'Action Area 1, Kolkata', lat: 22.584, lon: 88.402 },
  { name: 'Office (Sector V)', address: 'Salt Lake, Kolkata', lat: 22.570, lon: 88.435 },
  { name: 'Salt Lake Gate 1', address: 'Bidhannagar, Kolkata', lat: 22.590, lon: 88.410 },
  { name: 'Kolkata Airport', address: 'CCU, Dumdum, Kolkata', lat: 22.650, lon: 88.440 },
  { name: 'Park Street', address: 'Central Kolkata', lat: 22.550, lon: 88.350 },
];

export default function OfferRidePage({ user, onSwitchToFind, onRideCreated }) {
  const [pickup, setPickup] = useState(PRESET_LOCATIONS[0]);
  const [destination, setDestination] = useState(PRESET_LOCATIONS[1]);
  const [travelDate, setTravelDate] = useState('2026-08-10');
  const [travelHour, setTravelHour] = useState(18.0);
  const [availableSeats, setAvailableSeats] = useState(3);
  const [farePerSeat, setFarePerSeat] = useState(60.0);
  const [vehicles, setVehicles] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (user?.id) {
      api.getVehicles(user.id).then((vehs) => {
        setVehicles(vehs);
        if (vehs.length > 0) setSelectedVehicle(vehs[0].id);
      }).catch(console.error);
    }
  }, [user]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!user?.id) {
      setError('Please log in before publishing a ride.');
      return;
    }
    setError('');
    setLoading(true);

    try {
      const rideData = {
        pickup_name: pickup.name,
        pickup_lat: pickup.lat,
        pickup_lon: pickup.lon,
        drop_name: destination.name,
        drop_lat: destination.lat,
        drop_lon: destination.lon,
        travel_date: travelDate,
        departure_hour: parseFloat(travelHour),
        available_seats: parseInt(availableSeats),
        fare_per_seat: parseFloat(farePerSeat),
        vehicle_id: selectedVehicle || null,
      };

      const newRide = await api.createRide(rideData, user.id);
      setSuccess(true);
      setTimeout(() => {
        onRideCreated(newRide);
      }, 1200);
    } catch (err) {
      setError(err.message || 'Failed to publish ride.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-2">
          <button
            onClick={onSwitchToFind}
            className="px-5 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors flex items-center space-x-2"
          >
            <Navigation className="w-4 h-4" />
            <span>Find Ride</span>
          </button>
          <button
            className="px-5 py-2.5 rounded-xl text-sm font-bold bg-cyan-500 text-slate-950 shadow-lg shadow-cyan-500/20 flex items-center space-x-2"
          >
            <Navigation className="w-4 h-4 rotate-90" />
            <span>Offer Ride</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Form */}
        <div className="lg:col-span-5 glass-panel p-6 rounded-2xl border border-slate-800 space-y-5 text-left">
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <PlusCircle className="w-5 h-5 text-cyan-400" />
            <span>Publish New Ride</span>
          </h2>

          {error && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs flex items-center space-x-2">
              <ShieldAlert className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="p-4 rounded-xl bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs flex items-center space-x-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
              <span>Ride published successfully! Geohash index updated.</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Vehicle Selection */}
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Select Registered Vehicle</label>
              <div className="relative">
                <Car className="w-4 h-4 text-cyan-400 absolute left-3 top-3" />
                <select
                  value={selectedVehicle}
                  onChange={(e) => setSelectedVehicle(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-xl text-sm text-white focus:outline-none focus:border-cyan-500"
                >
                  {vehicles.length > 0 ? (
                    vehicles.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.model} ({v.registration_number}) - Cap: {v.seating_capacity}
                      </option>
                    ))
                  ) : (
                    <option value="">Honda City (WB-02-AB-1234) - Approved</option>
                  )}
                </select>
              </div>
            </div>

            {/* Locations */}
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Pickup Point</label>
                <div className="relative">
                  <MapPin className="w-4 h-4 text-emerald-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    required
                    value={pickup.name}
                    onChange={(e) => setPickup({ ...pickup, name: e.target.value })}
                    className="w-full pl-9 pr-3 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-xl text-sm text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Destination Point</label>
                <div className="relative">
                  <MapPin className="w-4 h-4 text-rose-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    required
                    value={destination.name}
                    onChange={(e) => setDestination({ ...destination, name: e.target.value })}
                    className="w-full pl-9 pr-3 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-xl text-sm text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>
            </div>

            {/* Date & Time */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Travel Date</label>
                <input
                  type="date"
                  required
                  value={travelDate}
                  onChange={(e) => setTravelDate(e.target.value)}
                  className="w-full px-3 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-xl text-sm text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Departure Hour</label>
                <select
                  value={travelHour}
                  onChange={(e) => setTravelHour(e.target.value)}
                  className="w-full px-3 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-xl text-sm text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value={9.0}>09:00 AM</option>
                  <option value={10.0}>10:00 AM</option>
                  <option value={18.0}>06:00 PM (18:00)</option>
                  <option value={19.0}>07:00 PM (19:00)</option>
                </select>
              </div>
            </div>

            {/* Seats & Fare */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Seats Available</label>
                <input
                  type="number"
                  min="1"
                  max="6"
                  required
                  value={availableSeats}
                  onChange={(e) => setAvailableSeats(e.target.value)}
                  className="w-full px-3 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-xl text-sm text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Fare Per Seat (₹)</label>
                <input
                  type="number"
                  required
                  value={farePerSeat}
                  onChange={(e) => setFarePerSeat(e.target.value)}
                  className="w-full px-3 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-xl text-sm text-white focus:outline-none focus:border-cyan-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-slate-950 font-bold rounded-xl text-sm transition-all shadow-lg shadow-cyan-500/25 disabled:opacity-50"
            >
              {loading ? 'Publishing Ride...' : 'Publish Ride'}
            </button>
          </form>
        </div>

        {/* Map Preview */}
        <div className="lg:col-span-7 glass-panel p-4 rounded-2xl border border-slate-800 space-y-3 text-left">
          <h3 className="text-sm font-semibold text-slate-200">Route Geometry Preview</h3>
          <MapView pickup={pickup} destination={destination} height="400px" />
        </div>
      </div>
    </div>
  );
}
