import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import SplashPage from './pages/SplashPage';
import LoginPage from './pages/LoginPage';
import SignUpPage from './pages/SignUpPage';
import FindRidePage from './pages/FindRidePage';
import OfferRidePage from './pages/OfferRidePage';
import MyTripsPage from './pages/MyTripsPage';
import VehiclesPage from './pages/VehiclesPage';
import WalletPage from './pages/WalletPage';
import RideHistoryPage from './pages/RideHistoryPage';
import ReportsPage from './pages/ReportsPage';
import SavedPlacesPage from './pages/SavedPlacesPage';
import AdminDashboardPage from './pages/AdminDashboardPage';
import { api } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('splash');
  const [currentUser, setCurrentUser] = useState(null);

  // Initialize with demo user on startup for instant demo flow
  useEffect(() => {
    api.login('amit@org.com', 'user123').then(setCurrentUser).catch(console.error);
  }, []);

  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
    setActiveTab('find-ride');
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setActiveTab('login');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        user={currentUser}
        onLogout={handleLogout}
      />

      <main className="flex-1 pb-12">
        {activeTab === 'splash' && (
          <SplashPage onGetStarted={() => setActiveTab(currentUser ? 'find-ride' : 'login')} />
        )}

        {activeTab === 'login' && (
          <LoginPage
            onLoginSuccess={handleLoginSuccess}
            onGoToRegister={() => setActiveTab('register')}
          />
        )}

        {activeTab === 'register' && (
          <SignUpPage
            onRegisterSuccess={handleLoginSuccess}
            onGoToLogin={() => setActiveTab('login')}
          />
        )}

        {activeTab === 'find-ride' && (
          <FindRidePage
            user={currentUser}
            onSwitchToOffer={() => setActiveTab('offer-ride')}
            onBookingSuccess={() => setActiveTab('my-trips')}
          />
        )}

        {activeTab === 'offer-ride' && (
          <OfferRidePage
            user={currentUser}
            onSwitchToFind={() => setActiveTab('find-ride')}
            onRideCreated={() => setActiveTab('find-ride')}
          />
        )}

        {activeTab === 'my-trips' && (
          <MyTripsPage
            user={currentUser}
            onPaySuccess={() => setActiveTab('history')}
          />
        )}

        {activeTab === 'vehicles' && <VehiclesPage user={currentUser} />}

        {activeTab === 'wallet' && <WalletPage user={currentUser} />}

        {activeTab === 'history' && <RideHistoryPage user={currentUser} />}

        {activeTab === 'reports' && <ReportsPage />}

        {activeTab === 'saved-places' && <SavedPlacesPage user={currentUser} />}

        {activeTab === 'admin' && <AdminDashboardPage />}
      </main>

      {/* Persistent Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <p>© 2026 Enterprise Carpooling Platform • Built for Hackathon</p>
          <div className="flex space-x-4">
            <button onClick={() => setActiveTab('saved-places')} className="hover:text-slate-300">Saved Places</button>
            <button onClick={() => setActiveTab('reports')} className="hover:text-slate-300">Analytics</button>
            <button onClick={() => setActiveTab('admin')} className="hover:text-slate-300">Admin Portal</button>
          </div>
        </div>
      </footer>
    </div>
  );
}
