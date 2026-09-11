import React from 'react';
import { Car, ShieldCheck, Zap, Leaf, ArrowRight } from 'lucide-react';

export default function SplashPage({ onGetStarted }) {
  return (
    <div className="min-h-[85vh] flex flex-col items-center justify-center text-center px-4 py-12">
      {/* Decorative Glow */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Hero Badge */}
      <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-semibold uppercase tracking-wider mb-6">
        <Zap className="w-3.5 h-3.5" />
        <span>Enterprise Intelligent Carpooling</span>
      </div>

      {/* Hero Title */}
      <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-white max-w-3xl leading-tight mb-4">
        Ride Together <span className="bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-indigo-500">Save Together</span>
      </h1>

      <p className="text-slate-400 text-lg md:text-xl max-w-2xl mb-8 leading-relaxed">
        Smart organizational carpooling powered by geohash spatial matching, real-time route optimization, and seamless cost sharing.
      </p>

      {/* Splash Screen Illustration Card (Matching Wireframe) */}
      <div className="w-full max-w-xl glass-card rounded-2xl p-8 mb-10 border border-slate-700/60 shadow-2xl relative overflow-hidden group">
        <div className="flex items-center justify-center space-x-6 py-6">
          <div className="w-16 h-16 rounded-2xl bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-xl group-hover:scale-110 transition-transform">
            <Car className="w-10 h-10" />
          </div>
          <div className="text-left">
            <h3 className="text-2xl font-bold text-white">Ride Together Save Together</h3>
            <p className="text-sm text-slate-400">Shared & Sustainable Enterprise Commuting</p>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row items-center space-y-3 sm:space-y-0 sm:space-x-4">
        <button
          onClick={onGetStarted}
          className="w-full sm:w-auto px-8 py-3.5 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-slate-950 font-bold rounded-xl text-base shadow-xl shadow-cyan-500/25 flex items-center justify-center space-x-2 transition-all transform hover:-translate-y-0.5"
        >
          <span>Get Started</span>
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>

      {/* Feature Pills */}
      <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl text-left">
        <div className="glass-card p-5 rounded-xl border border-slate-800">
          <ShieldCheck className="w-6 h-6 text-cyan-400 mb-2" />
          <h4 className="font-semibold text-white">Verified Employees</h4>
          <p className="text-xs text-slate-400 mt-1">Exclusive to registered organization members for safety and security.</p>
        </div>
        <div className="glass-card p-5 rounded-xl border border-slate-800">
          <Zap className="w-6 h-6 text-indigo-400 mb-2" />
          <h4 className="font-semibold text-white">Geohash Ride Match</h4>
          <p className="text-xs text-slate-400 mt-1">Sub-15ms route matching algorithm for instant pickup discovery.</p>
        </div>
        <div className="glass-card p-5 rounded-xl border border-slate-800">
          <Leaf className="w-6 h-6 text-emerald-400 mb-2" />
          <h4 className="font-semibold text-white">Eco Analytics</h4>
          <p className="text-xs text-slate-400 mt-1">Track fuel saved, CO2 reduction, and expense sharing in real time.</p>
        </div>
      </div>
    </div>
  );
}
