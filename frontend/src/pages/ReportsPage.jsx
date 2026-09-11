import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Fuel, Leaf, DollarSign, Activity } from 'lucide-react';
import { api } from '../services/api';

export default function ReportsPage() {
  const [reports, setReports] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getReports().then(setReports).finally(() => setLoading(false));
  }, []);

  if (loading || !reports) {
    return <div className="p-8 text-center text-slate-400">Loading analytics & reporting dashboard...</div>;
  }

  const { summary, fuel_efficiency_trend, emission_reduction_by_dept } = reports;

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 space-y-6 text-left">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-2xl font-bold text-white flex items-center space-x-2">
          <BarChart3 className="w-6 h-6 text-cyan-400" />
          <span>Reports & Analytics Dashboard</span>
        </h2>
        <p className="text-xs text-slate-400">Organization travel activity, fuel savings, and emission reduction insights</p>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Total Completed Trips</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-2xl font-extrabold text-white">{summary.total_trips}</p>
          <p className="text-[10px] text-cyan-400">From {summary.total_rides_offered} offered rides</p>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Distance Travelled</span>
            <TrendingUp className="w-4 h-4 text-indigo-400" />
          </div>
          <p className="text-2xl font-extrabold text-white">{summary.total_distance_km} km</p>
          <p className="text-[10px] text-indigo-400">Average commute distance</p>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Fuel Saved</span>
            <Fuel className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl font-extrabold text-white">{summary.fuel_saved_liters} L</p>
          <p className="text-[10px] text-amber-400">Cost: ₹{summary.avg_cost_per_km}/km</p>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>CO2 Reduction</span>
            <Leaf className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-extrabold text-emerald-400">{summary.co2_reduction_kg} kg</p>
          <p className="text-[10px] text-emerald-400">Total Savings: ₹{summary.total_cost_savings}</p>
        </div>
      </div>

      {/* Visual Charts (Wireframe Matching) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Fuel Efficiency Trend */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3">
          <h3 className="text-sm font-bold text-white flex items-center space-x-2">
            <Fuel className="w-4 h-4 text-cyan-400" />
            <span>Fuel Efficiency Trend (km/L)</span>
          </h3>

          <div className="h-48 flex items-end justify-between px-4 pb-2 pt-6 bg-slate-900/60 rounded-xl border border-slate-800">
            {fuel_efficiency_trend.map((item, idx) => (
              <div key={idx} className="flex flex-col items-center space-y-2">
                <span className="text-[10px] font-bold text-cyan-400">{item.km_per_liter}</span>
                <div
                  className="w-10 bg-gradient-to-t from-cyan-500 to-indigo-600 rounded-t-lg transition-all hover:opacity-80"
                  style={{ height: `${item.km_per_liter * 10}px` }}
                />
                <span className="text-xs text-slate-400">{item.month}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Top 5 Emission Reduction by Dept */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3">
          <h3 className="text-sm font-bold text-white flex items-center space-x-2">
            <Leaf className="w-4 h-4 text-emerald-400" />
            <span>Emission Reduction by Department</span>
          </h3>

          <div className="space-y-3 pt-2">
            {emission_reduction_by_dept.map((item, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-300 font-semibold">{item.department}</span>
                  <span className="text-emerald-400 font-bold">{item.co2_saved_kg} kg CO2</span>
                </div>
                <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-emerald-500 to-cyan-400 h-2.5 rounded-full"
                    style={{ width: `${(item.co2_saved_kg / 150) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
