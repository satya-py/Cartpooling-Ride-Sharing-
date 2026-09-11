import React, { useState, useEffect } from 'react';
import { Clock, Car, MapPin, Phone, MessageSquare, CheckCircle, CreditCard, Navigation, Play, QrCode, Check, X, Users, AlertCircle } from 'lucide-react';
import MapView from '../components/MapView';
import { api } from '../services/api';

export default function MyTripsPage({ user, onPaySuccess }) {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTrackingTrip, setActiveTrackingTrip] = useState(null);
  const [livePos, setLivePos] = useState({ latitude: 22.584, longitude: 88.402 });
  const [chatModalOpen, setChatModalOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    { sender: 'Driver', text: 'Hi! I am reaching the pickup point in 5 mins.' },
    { sender: 'You', text: 'Great! I am waiting near Gate 2.' },
  ]);
  const [newMessage, setNewMessage] = useState('');
  const [payModalTrip, setPayModalTrip] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState('wallet');
  const [payLoading, setPayLoading] = useState(false);
  const [payMsg, setPayMsg] = useState('');
  const [ridersModalRideId, setRidersModalRideId] = useState(null);
  const [ridersList, setRidersList] = useState([]);
  const [actionMsg, setActionMsg] = useState('');

  const fetchTrips = async () => {
    if (!user?.id) return;
    setLoading(true);
    try {
      const data = await api.getUserTrips(user.id);
      setTrips(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrips();
  }, [user]);

  // Simulate animated vehicle movement when tracking trip is active
  useEffect(() => {
    if (!activeTrackingTrip) return;
    const interval = setInterval(() => {
      setLivePos((prev) => ({
        latitude: prev.latitude - 0.001,
        longitude: prev.longitude - 0.001,
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, [activeTrackingTrip]);

  const handleAcceptRequest = async (bookingId) => {
    setActionMsg('');
    try {
      await api.acceptBooking(bookingId, user.id);
      setActionMsg('Request accepted! Available seats updated.');
      fetchTrips();
    } catch (err) {
      setActionMsg(`Error: ${err.message}`);
    }
  };

  const handleRejectRequest = async (bookingId) => {
    setActionMsg('');
    try {
      await api.rejectBooking(bookingId, user.id);
      setActionMsg('Request declined.');
      fetchTrips();
    } catch (err) {
      setActionMsg(`Error: ${err.message}`);
    }
  };

  const handleUpdateStatus = async (tripId, status) => {
    try {
      await api.updateTripStatus(tripId, status);
      fetchTrips();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleShowRiders = async (rideId) => {
    setRidersModalRideId(rideId);
    try {
      const riders = await api.getShowRiders(rideId);
      setRidersList(riders);
    } catch (err) {
      console.error(err);
      setRidersList([]);
    }
  };

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;
    setChatMessages([...chatMessages, { sender: 'You', text: newMessage }]);
    setNewMessage('');
  };

  const handleProcessPayment = async () => {
    if (!payModalTrip) return;
    setPayLoading(true);
    setPayMsg('');
    try {
      const res = await api.payTrip(payModalTrip.id, paymentMethod, user.id);
      setPayMsg(res.message);
      setTimeout(() => {
        setPayModalTrip(null);
        fetchTrips();
        if (onPaySuccess) onPaySuccess();
      }, 1500);
    } catch (err) {
      setPayMsg(err.message || 'Payment failed.');
    } finally {
      setPayLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 space-y-6 text-left">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-2xl font-bold text-white">My Trips & Requests</h2>
          <p className="text-xs text-slate-400">View ride requests, driver accept/reject workflow, live trip tracking, and payments</p>
        </div>
        <button
          onClick={fetchTrips}
          className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-cyan-400 hover:bg-slate-800"
        >
          Refresh Trips
        </button>
      </div>

      {actionMsg && (
        <div className={`p-3 rounded-xl text-xs font-semibold ${actionMsg.startsWith('Error') ? 'bg-rose-500/10 border border-rose-500/30 text-rose-400' : 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'}`}>
          {actionMsg}
        </div>
      )}

      {loading ? (
        <div className="glass-panel p-8 text-center text-slate-400 text-sm">Loading trips...</div>
      ) : trips.length === 0 ? (
        <div className="glass-panel p-8 text-center text-slate-400 text-sm space-y-2">
          <p>No active or completed trips found.</p>
          <p className="text-xs text-slate-500">Go to "Find Ride" to discover and book a commute!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {trips.map((t) => {
            const isPassenger = t.passenger_id === user?.id;

            return (
              <div key={t.id} className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[10px] px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 font-mono">
                      Trip #{t.id}
                    </span>
                    <h3 className="font-bold text-white text-base mt-1">{t.pickup_name} → {t.drop_name}</h3>
                    <p className="text-xs text-slate-400">
                      {isPassenger ? 'You (Passenger)' : `Passenger: ${t.passenger_name}`} • {t.seats_booked} Seat(s)
                    </p>
                  </div>

                  <span className={`text-xs px-2.5 py-1 rounded-lg font-bold capitalize ${
                    t.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' :
                    t.status === 'accepted' || t.status === 'booked' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30' :
                    t.status === 'requested' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' :
                    t.status === 'rejected' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30' :
                    'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30'
                  }`}>
                    {t.status === 'requested' ? 'Pending Approval' : t.status}
                  </span>
                </div>

                <div className="bg-slate-900/60 p-3 rounded-xl space-y-1.5 text-xs text-slate-300">
                  <div className="flex justify-between"><span className="text-slate-400">Vehicle:</span><span className="font-semibold text-white">Honda City (WB-02-AB-1234)</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Fare:</span><span className="font-bold text-cyan-400">₹{t.total_fare.toFixed(2)}</span></div>
                  <div className="flex justify-between"><span className="text-slate-400">Payment Status:</span><span className="font-semibold text-white capitalize">{t.payment_status}</span></div>
                </div>

                {/* Driver Approval Workflow (Accept / Reject Controls) */}
                {!isPassenger && t.status === 'requested' && (
                  <div className="bg-amber-500/10 border border-amber-500/30 p-3 rounded-xl space-y-2">
                    <p className="text-xs font-semibold text-amber-300 flex items-center space-x-1">
                      <AlertCircle className="w-4 h-4" />
                      <span>Passenger Request Received from {t.passenger_name} ({t.seats_booked} seat)</span>
                    </p>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleAcceptRequest(t.id)}
                        className="flex-1 py-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-extrabold rounded-lg flex items-center justify-center space-x-1"
                      >
                        <Check className="w-4 h-4" />
                        <span>Accept Request</span>
                      </button>
                      <button
                        onClick={() => handleRejectRequest(t.id)}
                        className="flex-1 py-1.5 bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 text-xs font-bold rounded-lg flex items-center justify-center space-x-1"
                      >
                        <X className="w-4 h-4" />
                        <span>Decline</span>
                      </button>
                    </div>
                  </div>
                )}

                {/* Passenger Status Observation Pill */}
                {isPassenger && t.status === 'requested' && (
                  <div className="bg-slate-900/80 p-2.5 rounded-xl border border-slate-800 text-xs text-amber-400 flex items-center space-x-2">
                    <Clock className="w-4 h-4 animate-spin" />
                    <span>Waiting for Driver to accept your booking request...</span>
                  </div>
                )}

                {/* Actions */}
                <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-800">
                  <button
                    onClick={() => setActiveTrackingTrip(t)}
                    className="flex-1 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-cyan-400 text-xs font-semibold rounded-xl flex items-center justify-center space-x-1"
                  >
                    <Navigation className="w-3.5 h-3.5" />
                    <span>Live Tracking</span>
                  </button>

                  <button
                    onClick={() => setChatModalOpen(true)}
                    className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-indigo-400 text-xs font-semibold rounded-xl flex items-center space-x-1"
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span>Chat / Call</span>
                  </button>

                  {!isPassenger && (
                    <button
                      onClick={() => handleShowRiders(t.ride_id)}
                      className="px-3 py-2 bg-purple-900/40 hover:bg-purple-800/60 text-purple-300 text-xs font-semibold rounded-xl flex items-center space-x-1 border border-purple-500/30"
                    >
                      <Users className="w-3.5 h-3.5" />
                      <span>Show Riders</span>
                    </button>
                  )}

                  {(t.status === 'accepted' || t.status === 'booked') && (
                    <button
                      onClick={() => handleUpdateStatus(t.id, 'started')}
                      className="px-3 py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold rounded-xl flex items-center space-x-1"
                    >
                      <Play className="w-3.5 h-3.5" />
                      <span>Start Trip</span>
                    </button>
                  )}

                  {(t.status === 'started' || t.status === 'in_progress') && (
                    <button
                      onClick={() => handleUpdateStatus(t.id, 'completed')}
                      className="px-3 py-2 bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold rounded-xl flex items-center space-x-1"
                    >
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>Complete Trip</span>
                    </button>
                  )}

                  {isPassenger && t.payment_status === 'pending' && t.status === 'completed' && (
                    <button
                      onClick={() => setPayModalTrip(t)}
                      className="w-full mt-2 py-2.5 bg-gradient-to-r from-emerald-400 to-cyan-500 text-slate-950 text-xs font-black rounded-xl shadow-lg flex items-center justify-center space-x-2"
                    >
                      <CreditCard className="w-4 h-4" />
                      <span>Pay ₹{t.total_fare.toFixed(2)} Now</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Show Riders Modal */}
      {ridersModalRideId && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-md w-full glass-panel p-6 rounded-2xl border border-slate-700 space-y-4 text-left shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                <Users className="w-5 h-5 text-purple-400" />
                <span>Riders on Ride #{ridersModalRideId}</span>
              </h3>
              <button
                onClick={() => setRidersModalRideId(null)}
                className="px-3 py-1 bg-slate-800 text-slate-300 rounded-lg text-xs"
              >
                Close
              </button>
            </div>

            {ridersList.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-4">No passengers registered yet for this ride.</p>
            ) : (
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {ridersList.map((r, idx) => (
                  <div key={idx} className="p-3 bg-slate-900/80 rounded-xl border border-slate-800 flex items-center justify-between text-xs">
                    <div>
                      <p className="font-semibold text-white">{r.passenger_name}</p>
                      <p className="text-[10px] text-slate-400">{r.pickup_name} → {r.drop_name}</p>
                    </div>
                    <div className="text-right">
                      <span className="font-bold text-cyan-400">{r.seats_booked} Seat(s)</span>
                      <p className="text-[10px] text-emerald-400 capitalize">{r.status}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Live Trip Tracking Modal */}
      {activeTrackingTrip && (
        <div className="fixed inset-0 z-50 bg-slate-950/85 backdrop-blur-md flex items-center justify-center p-4">
          <div className="max-w-2xl w-full glass-panel p-6 rounded-2xl border border-slate-700 space-y-4 text-left shadow-2xl">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                  <Navigation className="w-5 h-5 text-cyan-400 animate-pulse" />
                  <span>Live Trip Tracking — Trip #{activeTrackingTrip.id}</span>
                </h3>
                <p className="text-xs text-slate-400">Real-time driver location updates & route status</p>
              </div>
              <button
                onClick={() => setActiveTrackingTrip(null)}
                className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs"
              >
                Close
              </button>
            </div>

            <MapView
              pickup={{ latitude: 22.584, longitude: 88.402, name: activeTrackingTrip.pickup_name }}
              destination={{ latitude: 22.570, longitude: 88.435, name: activeTrackingTrip.drop_name }}
              liveLocation={livePos}
              height="350px"
            />

            <div className="grid grid-cols-3 gap-3 text-xs bg-slate-900/80 p-3 rounded-xl">
              <div><span className="text-slate-400 block">Status:</span><span className="font-bold text-cyan-400 capitalize">{activeTrackingTrip.status}</span></div>
              <div><span className="text-slate-400 block">Est. Arrival:</span><span className="font-bold text-white">8 Mins</span></div>
              <div><span className="text-slate-400 block">Speed:</span><span className="font-bold text-white">42 km/h</span></div>
            </div>
          </div>
        </div>
      )}

      {/* Chat Simulation Modal */}
      {chatModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-md w-full glass-panel p-6 rounded-2xl border border-slate-700 space-y-4 text-left shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center space-x-2">
                <MessageSquare className="w-5 h-5 text-indigo-400" />
                <span>Trip Communication</span>
              </h3>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => alert('Simulating voice call to driver (+91 9876543210)...')}
                  className="p-2 bg-emerald-500/20 text-emerald-400 rounded-lg hover:bg-emerald-500/30"
                  title="Voice Call"
                >
                  <Phone className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setChatModalOpen(false)}
                  className="px-3 py-1 bg-slate-800 text-slate-300 rounded-lg text-xs"
                >
                  Close
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="h-48 overflow-y-auto space-y-2 bg-slate-900/80 p-3 rounded-xl text-xs">
              {chatMessages.map((m, idx) => (
                <div key={idx} className={`p-2 rounded-lg max-w-[80%] ${m.sender === 'You' ? 'bg-cyan-500/20 text-cyan-300 ml-auto' : 'bg-slate-800 text-slate-200'}`}>
                  <span className="font-semibold block text-[10px] text-slate-400">{m.sender}</span>
                  <span>{m.text}</span>
                </div>
              ))}
            </div>

            <form onSubmit={handleSendMessage} className="flex space-x-2">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Type a message..."
                className="flex-1 px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white"
              />
              <button type="submit" className="px-4 py-2 bg-indigo-600 text-white font-bold rounded-xl text-xs">
                Send
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Payment Modal */}
      {payModalTrip && (
        <div className="fixed inset-0 z-50 bg-slate-950/85 backdrop-blur-md flex items-center justify-center p-4">
          <div className="max-w-md w-full glass-panel p-6 rounded-2xl border border-slate-700 space-y-4 text-left shadow-2xl">
            <h3 className="text-lg font-bold text-white">Complete Trip Payment</h3>
            <p className="text-xs text-slate-400">Total Fare: <span className="text-emerald-400 font-extrabold text-base">₹{payModalTrip.total_fare.toFixed(2)}</span></p>

            {payMsg && (
              <div className="p-3 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs">
                {payMsg}
              </div>
            )}

            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-300">Select Payment Method:</label>
              <div className="grid grid-cols-2 gap-2">
                {['wallet', 'upi', 'card', 'cash'].map((method) => (
                  <button
                    key={method}
                    type="button"
                    onClick={() => setPaymentMethod(method)}
                    className={`p-3 rounded-xl border text-xs font-bold uppercase transition-all ${
                      paymentMethod === method
                        ? 'bg-cyan-500/20 text-cyan-400 border-cyan-500/50'
                        : 'bg-slate-900/60 text-slate-400 border-slate-800'
                    }`}
                  >
                    {method}
                  </button>
                ))}
              </div>
            </div>

            {paymentMethod === 'upi' && (
              <div className="bg-slate-900/80 p-4 rounded-xl text-center space-y-2">
                <QrCode className="w-16 h-16 text-cyan-400 mx-auto" />
                <p className="text-[11px] text-slate-400">Scan QR Code using Razorpay / UPI App</p>
              </div>
            )}

            <div className="flex space-x-3 pt-2">
              <button
                onClick={() => setPayModalTrip(null)}
                className="flex-1 py-2.5 bg-slate-800 text-slate-300 font-medium rounded-xl text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleProcessPayment}
                disabled={payLoading}
                className="flex-1 py-2.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold rounded-xl text-xs shadow-lg disabled:opacity-50"
              >
                {payLoading ? 'Processing...' : 'Pay Now'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
