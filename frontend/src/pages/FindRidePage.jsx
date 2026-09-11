import React, { useState } from 'react';
import { MapPin, Navigation, Calendar, Clock, Users, DollarSign, ArrowRightLeft, Sparkles, CheckCircle2, ShieldCheck, ChevronRight } from 'lucide-react';
import MapView from '../components/MapView';
import { api } from '../services/api';

const PRESET_LOCATIONS = [
  { name: 'Home (New Town)', address: 'Action Area 1, Kolkata', lat: 22.584, lon: 88.402 },
  { name: 'Office (Sector V)', address: 'Salt Lake, Kolkata', lat: 22.570, lon: 88.435 },
  { name: 'Salt Lake Gate 1', address: 'Bidhannagar, Kolkata', lat: 22.590, lon: 88.410 },
  { name: 'Kolkata Airport', address: 'CCU, Dumdum, Kolkata', lat: 22.650, lon: 88.440 },
  { name: 'Park Street', address: 'Central Kolkata', lat: 22.550, lon: 88.350 },
];

export default function FindRidePage({ user, onSwitchToOffer, onBookingSuccess }) {
  const [pickup, setPickup] = useState(PRESET_LOCATIONS[0]);
  const [destination, setDestination] = useState(PRESET_LOCATIONS[1]);
  const [travelDate, setTravelDate] = useState('2026-08-10');
  const [travelHour, setTravelHour] = useState(18.0);
  const [requestedSeats, setRequestedSeats] = useState(1);
  const [maxFare, setMaxFare] = useState(70);

  const [step, setStep] = useState('form'); // 'form' | 'confirm-route' | 'results'
  const [loading, setLoading] = useState(false);
  const [matchResults, setMatchResults] = useState(null);
  const [selectedRide, setSelectedRide] = useState(null);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState('');

  const handleSwap = () => {
    const temp = pickup;
    setPickup(destination);
    setDestination(temp);
  };

  const handleProceedToRouteConfirm = (e) => {
    e.preventDefault();
    setStep('confirm-route');
  };

  const handleExecuteMatching = async () => {
    setLoading(true);
    setStep('results');
    try {
      const matchReq = {
        org_id: user?.org_id || 'ORG_KOL_001',
        pickup: { latitude: pickup.lat, longitude: pickup.lon },
        destination: { latitude: destination.lat, longitude: destination.lon },
        travel_date: travelDate,
        requested_hour: parseFloat(travelHour),
        seats: parseInt(requestedSeats),
        max_fare: maxFare ? parseFloat(maxFare) : null,
      };

      const res = await api.matchRides(matchReq);
      setMatchResults(res);
    } catch (err) {
      console.error('Matching failed:', err);
      setMatchResults({ results: [], candidatesConsidered: 0, totalRidesInSystem: 0 });
    } finally {
      setLoading(false);
    }
  };

  const handleBookRide = async (ride) => {
    if (!user?.id) {
      setBookingError('Please log in before booking a ride.');
      return;
    }
    setBookingLoading(true);
    setBookingError('');
    try {
      const booking = await api.bookRide(
        ride.rideId,
        {
          seats_booked: requestedSeats,
          pickup_name: pickup.name,
          drop_name: destination.name,
        },
        user.id
      );
      setSelectedRide(null);
      onBookingSuccess(booking);
    } catch (err) {
      setBookingError(err.message || 'Booking failed.');
    } finally {
      setBookingLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
      {/* Mode Switch Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-2">
          <button
            className="px-5 py-2.5 rounded-xl text-sm font-bold bg-cyan-500 text-slate-950 shadow-lg shadow-cyan-500/20 flex items-center space-x-2"
          >
            <Navigation className="w-4 h-4" />
            <span>Find Ride</span>
          </button>
          <button
            onClick={onSwitchToOffer}
            className="px-5 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors flex items-center space-x-2"
          >
            <Navigation className="w-4 h-4 rotate-90" />
            <span>Offer Ride</span>
          </button>
        </div>

        <div className="hidden sm:flex items-center space-x-2 text-xs text-slate-400">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Tenant Verified ({user?.department || 'Enterprise Employee'})</span>
        </div>
      </div>

      {/* Main Flow Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Form Column */}
        <div className="lg:col-span-5 glass-panel p-6 rounded-2xl border border-slate-800 space-y-5">
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-cyan-400" />
            <span>Search Intelligent Matches</span>
          </h2>

          {/* Location Presets */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Quick Select Preset Locations
            </label>
            <div className="flex flex-wrap gap-1.5">
              {PRESET_LOCATIONS.map((loc, idx) => (
                <button
                  key={idx}
                  onClick={() => setPickup(loc)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                    pickup.name === loc.name
                      ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                      : 'bg-slate-900/60 text-slate-300 hover:bg-slate-800 border border-slate-800'
                  }`}
                >
                  {loc.name}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleProceedToRouteConfirm} className="space-y-4 text-left">
            {/* Pickup & Destination Inputs */}
            <div className="space-y-3 relative">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Start / Pickup Location</label>
                <div className="relative">
                  <MapPin className="w-4 h-4 text-emerald-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    required
                    value={pickup.name}
                    onChange={(e) => setPickup({ ...pickup, name: e.target.value })}
                    className="w-full pl-9 pr-3 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-xl text-sm text-white focus:outline-none focus:border-cyan-500"
                    placeholder="Enter pickup address"
                  />
                </div>
              </div>

              {/* Swap Button */}
              <button
                type="button"
                onClick={handleSwap}
                title="Swap Pickup & Destination"
                className="absolute right-3 top-[52px] z-20 w-8 h-8 rounded-full bg-slate-800 border border-slate-600 text-cyan-400 flex items-center justify-center hover:bg-cyan-500 hover:text-slate-950 transition-all shadow-md"
              >
                <ArrowRightLeft className="w-4 h-4" />
              </button>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Destination Location</label>
                <div className="relative">
                  <MapPin className="w-4 h-4 text-rose-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    required
                    value={destination.name}
                    onChange={(e) => setDestination({ ...destination, name: e.target.value })}
                    className="w-full pl-9 pr-3 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-xl text-sm text-white focus:outline-none focus:border-cyan-500"
                    placeholder="Enter destination address"
                  />
                </div>
              </div>
            </div>

            {/* Travel Date & Time */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Travel Date</label>
                <div className="relative">
                  <Calendar className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="date"
                    required
                    value={travelDate}
                    onChange={(e) => setTravelDate(e.target.value)}
                    className="w-full pl-9 pr-3 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-xl text-sm text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Departure Hour</label>
                <div className="relative">
                  <Clock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <select
                    value={travelHour}
                    onChange={(e) => setTravelHour(e.target.value)}
                    className="w-full pl-9 pr-3 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-xl text-sm text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value={9.0}>09:00 AM</option>
                    <option value={10.0}>10:00 AM</option>
                    <option value={14.0}>02:00 PM</option>
                    <option value={18.0}>06:00 PM (18:00)</option>
                    <option value={19.0}>07:00 PM (19:00)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Seats & Max Fare */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Seats Needed</label>
                <div className="relative">
                  <Users className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <select
                    value={requestedSeats}
                    onChange={(e) => setRequestedSeats(e.target.value)}
                    className="w-full pl-9 pr-3 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-xl text-sm text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value={1}>1 Seat</option>
                    <option value={2}>2 Seats</option>
                    <option value={3}>3 Seats</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Max Budget (₹/seat)</label>
                <div className="relative">
                  <DollarSign className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="number"
                    value={maxFare}
                    onChange={(e) => setMaxFare(e.target.value)}
                    className="w-full pl-9 pr-3 py-2.5 bg-slate-900/80 border border-slate-700/80 rounded-xl text-sm text-white focus:outline-none focus:border-cyan-500"
                    placeholder="e.g. 70"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              className="w-full py-3.5 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-slate-950 font-bold rounded-xl text-sm transition-all shadow-lg shadow-cyan-500/25 flex items-center justify-center space-x-2"
            >
              <span>Confirm Route & Match Rides</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </form>
        </div>

        {/* Right Map & Results Column */}
        <div className="lg:col-span-7 space-y-6">
          {/* Interactive Map */}
          <div className="glass-panel p-4 rounded-2xl border border-slate-800 space-y-3 text-left">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-200">Route Geometry Preview</h3>
              <span className="text-xs text-cyan-400 font-mono">Geohash Precision 6 (~1.2km)</span>
            </div>
            <MapView pickup={pickup} destination={destination} height="320px" />
          </div>

          {/* Route Confirmation & Matching Trigger */}
          {step === 'confirm-route' && (
            <div className="glass-card p-6 rounded-2xl border border-cyan-500/30 text-left space-y-4">
              <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                <CheckCircle2 className="w-5 h-5 text-cyan-400" />
                <span>Confirm Route Details Before Matching</span>
              </h3>
              <div className="grid grid-cols-2 gap-4 text-xs bg-slate-900/60 p-4 rounded-xl">
                <div>
                  <p className="text-slate-400">Pickup Location:</p>
                  <p className="font-semibold text-white">{pickup.name}</p>
                </div>
                <div>
                  <p className="text-slate-400">Destination:</p>
                  <p className="font-semibold text-white">{destination.name}</p>
                </div>
                <div>
                  <p className="text-slate-400">Travel Schedule:</p>
                  <p className="font-semibold text-white">{travelDate} @ {travelHour}:00</p>
                </div>
                <div>
                  <p className="text-slate-400">Requested Seats / Budget:</p>
                  <p className="font-semibold text-white">{requestedSeats} Seat(s) • ₹{maxFare || 'Any'}</p>
                </div>
              </div>

              <button
                onClick={handleExecuteMatching}
                disabled={loading}
                className="w-full py-3.5 bg-gradient-to-r from-emerald-400 to-cyan-500 hover:from-emerald-300 hover:to-cyan-400 text-slate-950 font-extrabold rounded-xl text-sm transition-all shadow-xl shadow-emerald-500/20 flex items-center justify-center space-x-2 disabled:opacity-50"
              >
                <Sparkles className="w-5 h-5" />
                <span>{loading ? 'Running Geohash Matcher...' : 'Find Matching Rides Now'}</span>
              </button>
            </div>
          )}

          {/* Match Results Display */}
          {step === 'results' && (
            <div className="space-y-4 text-left">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-white">Available Matching Rides</h3>
                {matchResults && (
                  <span className="text-xs text-slate-400 bg-slate-900/80 px-3 py-1 rounded-full border border-slate-800">
                    Evaluated <span className="text-cyan-400 font-semibold">{matchResults.candidatesConsidered} candidates</span> from {matchResults.totalRidesInSystem} system rides
                  </span>
                )}
              </div>

              {loading ? (
                <div className="glass-panel p-12 rounded-2xl text-center space-y-3">
                  <Sparkles className="w-8 h-8 text-cyan-400 animate-spin mx-auto" />
                  <p className="text-sm font-semibold text-white">Running 2-Stage Intelligent Matching Algorithm...</p>
                  <p className="text-xs text-slate-400">Filtering candidates via geohash spatial cells & multi-attribute scoring.</p>
                </div>
              ) : matchResults?.results.length === 0 ? (
                <div className="glass-panel p-8 rounded-2xl text-center space-y-2">
                  <p className="text-slate-300 font-semibold">No rides found matching your exact route & schedule.</p>
                  <p className="text-xs text-slate-500">Try adjusting your travel time or pickup budget.</p>
                </div>
              ) : (
                matchResults?.results.map((ride, idx) => {
                  const scoreColor =
                    ride.matchScore >= 85 ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' :
                    ride.matchScore >= 65 ? 'text-amber-400 bg-amber-500/10 border-amber-500/30' :
                    'text-cyan-400 bg-cyan-500/10 border-cyan-500/30';

                  return (
                    <div
                      key={idx}
                      className="glass-panel p-5 rounded-2xl border border-slate-800 hover:border-cyan-500/40 transition-all space-y-3"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-white text-base">{ride.driverName}</span>
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
                              Ride #{ride.rideId}
                            </span>
                          </div>
                          <p className="text-xs text-slate-400 mt-0.5">Verified Corporate Driver • Honda City</p>
                        </div>

                        {/* Match Score Badge */}
                        <div className={`px-3 py-1.5 rounded-xl border text-sm font-black flex items-center space-x-1 ${scoreColor}`}>
                          <Sparkles className="w-4 h-4" />
                          <span>{ride.matchScore.toFixed(1)}% Match</span>
                        </div>
                      </div>

                      {/* Reasons & Attributes */}
                      <div className="flex flex-wrap gap-1.5">
                        {ride.reasons.map((r, rIdx) => (
                          <span key={rIdx} className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-300">
                            {r}
                          </span>
                        ))}
                      </div>

                      {/* Breakdown Pills */}
                      <div className="grid grid-cols-5 gap-2 pt-2 border-t border-slate-800/80 text-[10px] text-center">
                        <div className="bg-slate-900/60 p-1.5 rounded-lg">
                          <span className="text-slate-400 block">Pickup</span>
                          <span className="font-bold text-cyan-400">{ride.breakdown.pickupScore.toFixed(0)}</span>
                        </div>
                        <div className="bg-slate-900/60 p-1.5 rounded-lg">
                          <span className="text-slate-400 block">Dropoff</span>
                          <span className="font-bold text-cyan-400">{ride.breakdown.destinationScore.toFixed(0)}</span>
                        </div>
                        <div className="bg-slate-900/60 p-1.5 rounded-lg">
                          <span className="text-slate-400 block">Detour</span>
                          <span className="font-bold text-cyan-400">{ride.breakdown.detourScore.toFixed(0)}</span>
                        </div>
                        <div className="bg-slate-900/60 p-1.5 rounded-lg">
                          <span className="text-slate-400 block">Time</span>
                          <span className="font-bold text-cyan-400">{ride.breakdown.timeScore.toFixed(0)}</span>
                        </div>
                        <div className="bg-slate-900/60 p-1.5 rounded-lg">
                          <span className="text-slate-400 block">Fare</span>
                          <span className="font-bold text-cyan-400">{ride.breakdown.fareScore.toFixed(0)}</span>
                        </div>
                      </div>

                      {/* Action */}
                      <div className="pt-2 flex items-center justify-between">
                        <div className="text-xs">
                          <span className="text-slate-400">Total Fare: </span>
                          <span className="font-bold text-white text-sm">₹60.00 / seat</span>
                        </div>

                        <button
                          onClick={() => setSelectedRide(ride)}
                          className="px-5 py-2 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-slate-950 font-extrabold rounded-xl text-xs shadow-lg transition-transform transform hover:scale-105"
                        >
                          Select & Join Ride
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}
        </div>
      </div>

      {/* Booking Modal */}
      {selectedRide && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-md w-full glass-panel p-6 rounded-2xl border border-slate-700 space-y-4 text-left shadow-2xl">
            <h3 className="text-lg font-bold text-white">Confirm Ride Booking</h3>
            <p className="text-xs text-slate-400">You are booking {requestedSeats} seat(s) with driver <span className="text-cyan-400 font-semibold">{selectedRide.driverName}</span>.</p>

            {bookingError && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                {bookingError}
              </div>
            )}

            <div className="bg-slate-900/80 p-4 rounded-xl space-y-2 text-xs">
              <div className="flex justify-between"><span className="text-slate-400">Pickup:</span><span className="font-semibold text-white">{pickup.name}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Destination:</span><span className="font-semibold text-white">{destination.name}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Travel Date:</span><span className="font-semibold text-white">{travelDate}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Fare per Seat:</span><span className="font-semibold text-white">₹60.00</span></div>
              <div className="flex justify-between pt-2 border-t border-slate-800 font-bold text-sm"><span className="text-white">Total Amount:</span><span className="text-cyan-400">₹{(60 * requestedSeats).toFixed(2)}</span></div>
            </div>

            <div className="flex space-x-3 pt-2">
              <button
                onClick={() => setSelectedRide(null)}
                className="flex-1 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium rounded-xl text-xs"
              >
                Cancel
              </button>
              <button
                onClick={() => handleBookRide(selectedRide)}
                disabled={bookingLoading}
                className="flex-1 py-2.5 bg-gradient-to-r from-cyan-500 to-indigo-600 text-slate-950 font-bold rounded-xl text-xs shadow-lg disabled:opacity-50"
              >
                {bookingLoading ? 'Booking...' : 'Confirm & Book'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
