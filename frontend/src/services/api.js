const API_BASE = 'http://localhost:8000';

async function fetchJSON(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Network error' }));
    throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

export const api = {
  // Health
  health: () => fetchJSON('/health'),

  // Auth
  login: (email, password) =>
    fetchJSON('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  register: (data) =>
    fetchJSON('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getCurrentUser: (userId) => fetchJSON(`/api/auth/me?user_id=${userId}`),

  // Rides & Matching
  matchRides: (matchReq) =>
    fetchJSON('/rides/match', {
      method: 'POST',
      body: JSON.stringify(matchReq),
    }),

  listRides: (statusFilter) =>
    fetchJSON(`/api/rides${statusFilter ? `?status_filter=${statusFilter}` : ''}`),

  getRideDetail: (rideId) => fetchJSON(`/api/rides/${rideId}`),

  createRide: (rideData, userId) =>
    fetchJSON(`/api/rides?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify(rideData),
    }),

  // Bookings & Trips
  bookRide: (rideId, bookingData, userId) =>
    fetchJSON(`/api/rides/${rideId}/book?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify(bookingData),
    }),

  acceptBooking: (bookingId, driverId) =>
    fetchJSON(`/api/bookings/${bookingId}/accept?driver_id=${driverId}`, {
      method: 'POST',
    }),

  rejectBooking: (bookingId, driverId) =>
    fetchJSON(`/api/bookings/${bookingId}/reject?driver_id=${driverId}`, {
      method: 'POST',
    }),

  getShowRiders: (rideId) => fetchJSON(`/api/rides/${rideId}/riders`),

  getUserTrips: (userId) => fetchJSON(`/api/trips?user_id=${userId}`),

  getTripDetail: (bookingId) => fetchJSON(`/api/trips/${bookingId}`),

  updateTripStatus: (bookingId, newStatus) =>
    fetchJSON(`/api/trips/${bookingId}/status?new_status=${newStatus}`, {
      method: 'PATCH',
    }),

  payTrip: (bookingId, paymentMethod, userId) =>
    fetchJSON(`/api/trips/${bookingId}/pay?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify({ payment_method: paymentMethod }),
    }),

  // Wallet
  getWallet: (userId) => fetchJSON(`/api/wallet?user_id=${userId}`),

  rechargeWallet: (amount, userId) =>
    fetchJSON(`/api/wallet/recharge?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify({ amount: parseFloat(amount) }),
    }),

  // Vehicles
  getVehicles: (userId) => fetchJSON(`/api/vehicles?user_id=${userId}`),

  registerVehicle: (vehData, userId) =>
    fetchJSON(`/api/vehicles?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify(vehData),
    }),

  // Saved Places
  getSavedPlaces: (userId) => fetchJSON(`/api/saved-places?user_id=${userId}`),

  addSavedPlace: (placeData, userId) =>
    fetchJSON(`/api/saved-places?user_id=${userId}`, {
      method: 'POST',
      body: JSON.stringify(placeData),
    }),

  // Admin
  getAdminEmployees: () => fetchJSON('/api/admin/employees'),

  updateEmployeeAccess: (userId, platformAccess) =>
    fetchJSON(`/api/admin/employees/${userId}`, {
      method: 'PATCH',
      body: JSON.stringify({ platform_access: platformAccess }),
    }),

  getAdminVehicles: () => fetchJSON('/api/admin/vehicles'),

  updateVehicleStatus: (vehicleId, status) =>
    fetchJSON(`/api/admin/vehicles/${vehicleId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),

  getAdminSettings: () => fetchJSON('/api/admin/settings'),

  updateAdminSettings: (data) =>
    fetchJSON('/api/admin/settings', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Reports
  getReports: () => fetchJSON('/api/reports'),
};
