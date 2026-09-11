import React, { useState, useEffect } from 'react';
import { Users, Car, Settings, Shield, CheckCircle2, XCircle, Save, Building } from 'lucide-react';
import { api } from '../services/api';

export default function AdminDashboardPage() {
  const [activeSubTab, setActiveSubTab] = useState('employees'); // 'employees' | 'vehicles' | 'settings'
  const [employees, setEmployees] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [settings, setSettings] = useState({
    company_name: 'Acme Corp Kolkata',
    registered_office: 'Sector V, Salt Lake, Kolkata',
    industry: 'Technology',
    admin_contact: 'admin@acmecorp.com',
    fuel_cost_per_liter: 102.50,
    travel_cost_per_km: 12.00,
    default_policy: 'Standard Enterprise Carpooling Policy',
  });
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState('');

  const fetchAdminData = async () => {
    setLoading(true);
    try {
      const [empRes, vehRes, setRes] = await Promise.all([
        api.getAdminEmployees(),
        api.getAdminVehicles(),
        api.getAdminSettings(),
      ]);
      setEmployees(empRes);
      setVehicles(vehRes);
      if (setRes) setSettings(setRes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminData();
  }, []);

  const handleToggleAccess = async (userId, currentAccess) => {
    const nextAccess = currentAccess === 'active' ? 'revoked' : 'active';
    try {
      await api.updateEmployeeAccess(userId, nextAccess);
      fetchAdminData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleToggleVehicleStatus = async (vehId, currentStatus) => {
    const nextStatus = currentStatus === 'approved' ? 'inactive' : 'approved';
    try {
      await api.updateVehicleStatus(vehId, nextStatus);
      fetchAdminData();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleSaveSettings = async (e) => {
    e.preventDefault();
    setMsg('');
    try {
      await api.updateAdminSettings(settings);
      setMsg('Organization carpooling configuration saved!');
    } catch (err) {
      setMsg(err.message || 'Failed to save settings.');
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 space-y-6 text-left">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-2xl font-bold text-white flex items-center space-x-2">
          <Shield className="w-6 h-6 text-purple-400" />
          <span>Company Administration Dashboard</span>
        </h2>
        <p className="text-xs text-slate-400">Manage employee platform access, vehicle approvals, and organization policy settings</p>
      </div>

      {/* Top Overview KPI Stat Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-1">
          <span className="text-xs font-semibold text-slate-400">Total Employees</span>
          <p className="text-3xl font-black text-white">{employees.length}</p>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-1">
          <span className="text-xs font-semibold text-slate-400">Registered Vehicles</span>
          <p className="text-3xl font-black text-cyan-400">{vehicles.length}</p>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-1">
          <span className="text-xs font-semibold text-slate-400">Trips This Month</span>
          <p className="text-3xl font-black text-emerald-400">163</p>
        </div>
      </div>

      {/* Sub Tabs */}
      <div className="flex space-x-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveSubTab('employees')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 ${
            activeSubTab === 'employees'
              ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>Employees Tab</span>
        </button>

        <button
          onClick={() => setActiveSubTab('vehicles')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 ${
            activeSubTab === 'vehicles'
              ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <Car className="w-4 h-4" />
          <span>Vehicles Tab</span>
        </button>

        <button
          onClick={() => setActiveSubTab('settings')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center space-x-2 ${
            activeSubTab === 'settings'
              ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <Settings className="w-4 h-4" />
          <span>Settings Tab</span>
        </button>
      </div>

      {/* Subtab Content */}
      {loading ? (
        <div className="glass-panel p-8 text-center text-xs text-slate-400">Loading admin records...</div>
      ) : activeSubTab === 'employees' ? (
        /* Employees Tab */
        <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="p-3">Employee Name</th>
                <th className="p-3">Email</th>
                <th className="p-3">Department</th>
                <th className="p-3">Manager</th>
                <th className="p-3">Office Location</th>
                <th className="p-3">Platform Access</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {employees.map((emp) => (
                <tr key={emp.id} className="hover:bg-slate-900/40">
                  <td className="p-3 font-semibold text-white">{emp.name}</td>
                  <td className="p-3 text-slate-400">{emp.email}</td>
                  <td className="p-3">{emp.department || 'N/A'}</td>
                  <td className="p-3">{emp.manager || 'N/A'}</td>
                  <td className="p-3">{emp.office_location || 'Kolkata HQ'}</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold capitalize ${
                      emp.platform_access === 'active' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                    }`}>
                      {emp.platform_access}
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    <button
                      onClick={() => handleToggleAccess(emp.id, emp.platform_access)}
                      className={`px-3 py-1 rounded-lg text-[10px] font-bold ${
                        emp.platform_access === 'active'
                          ? 'bg-rose-500/20 text-rose-300 hover:bg-rose-500/30'
                          : 'bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30'
                      }`}
                    >
                      {emp.platform_access === 'active' ? 'Revoke Access' : 'Approve Access'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : activeSubTab === 'vehicles' ? (
        /* Vehicles Tab */
        <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 font-semibold border-b border-slate-800">
              <tr>
                <th className="p-3">Registration Number</th>
                <th className="p-3">Driver / Owner</th>
                <th className="p-3">Vehicle Model</th>
                <th className="p-3">Seating Capacity</th>
                <th className="p-3">Approval Status</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {vehicles.map((v) => (
                <tr key={v.id} className="hover:bg-slate-900/40">
                  <td className="p-3 font-mono font-bold text-white">{v.registration_number}</td>
                  <td className="p-3">{v.driver_name}</td>
                  <td className="p-3">{v.model}</td>
                  <td className="p-3">{v.seating_capacity} Seats</td>
                  <td className="p-3">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold capitalize ${
                      v.status === 'approved' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                    }`}>
                      {v.status}
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    <button
                      onClick={() => handleToggleVehicleStatus(v.id, v.status)}
                      className={`px-3 py-1 rounded-lg text-[10px] font-bold ${
                        v.status === 'approved'
                          ? 'bg-amber-500/20 text-amber-300 hover:bg-amber-500/30'
                          : 'bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30'
                      }`}
                    >
                      {v.status === 'approved' ? 'Set Inactive' : 'Approve Vehicle'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        /* Settings Tab */
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-6">
          <h3 className="text-lg font-bold text-white flex items-center space-x-2">
            <Building className="w-5 h-5 text-purple-400" />
            <span>Organization & Carpooling Configuration</span>
          </h3>

          {msg && <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs">{msg}</div>}

          <form onSubmit={handleSaveSettings} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Company Name</label>
                <input
                  type="text"
                  required
                  value={settings.company_name}
                  onChange={(e) => setSettings({ ...settings, company_name: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Industry</label>
                <input
                  type="text"
                  required
                  value={settings.industry}
                  onChange={(e) => setSettings({ ...settings, industry: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Registered Office Address</label>
              <input
                type="text"
                required
                value={settings.registered_office}
                onChange={(e) => setSettings({ ...settings, registered_office: e.target.value })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Fuel Cost Per Liter (₹)</label>
                <input
                  type="number"
                  step="0.1"
                  required
                  value={settings.fuel_cost_per_liter}
                  onChange={(e) => setSettings({ ...settings, fuel_cost_per_liter: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Travel Cost Per Km (₹)</label>
                <input
                  type="number"
                  step="0.1"
                  required
                  value={settings.travel_cost_per_km}
                  onChange={(e) => setSettings({ ...settings, travel_cost_per_km: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Default Carpooling Policy</label>
              <textarea
                rows={2}
                value={settings.default_policy}
                onChange={(e) => setSettings({ ...settings, default_policy: e.target.value })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-xs text-white"
              />
            </div>

            <button
              type="submit"
              className="px-6 py-2.5 bg-gradient-to-r from-purple-500 to-indigo-600 text-white font-bold rounded-xl text-xs shadow-lg flex items-center space-x-2"
            >
              <Save className="w-4 h-4" />
              <span>Save Organization Settings</span>
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
