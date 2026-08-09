import React, { useState } from 'react';
import { FaTrophy, FaStopwatch, FaFlagCheckered, FaFire, FaChartLine, FaChevronRight, FaPlay, FaShieldAlt } from 'react-icons/fa';

export default function F1Website() {
  const [selectedTab, setSelectedTab] = useState('standings');

  const drivers = [
    { rank: 1, name: 'Max Verstappen', team: 'Red Bull Racing', points: 312, wins: 8, color: 'border-blue-600 bg-blue-950/40 text-blue-400' },
    { rank: 2, name: 'Charles Leclerc', team: 'Scuderia Ferrari', points: 275, wins: 5, color: 'border-red-600 bg-red-950/40 text-red-400' },
    { rank: 3, name: 'Lando Norris', team: 'McLaren F1 Team', points: 268, wins: 4, color: 'border-amber-500 bg-amber-950/40 text-amber-400' },
    { rank: 4, name: 'Lewis Hamilton', team: 'Scuderia Ferrari', points: 210, wins: 3, color: 'border-red-600 bg-red-950/40 text-red-400' },
    { rank: 5, name: 'George Russell', team: 'Mercedes-AMG PETRONAS', points: 195, wins: 2, color: 'border-cyan-500 bg-cyan-950/40 text-cyan-400' },
    { rank: 6, name: 'Oscar Piastri', team: 'McLaren F1 Team', points: 188, wins: 2, color: 'border-amber-500 bg-amber-950/40 text-amber-400' }
  ];

  const circuits = [
    { name: 'Monaco Grand Prix', location: 'Circuit de Monaco', date: 'MAY 24 - 26', laps: 78, distance: '260.28 km', image: '/f1_hero_car.png' },
    { name: 'British Grand Prix', location: 'Silverstone Circuit', date: 'JUL 05 - 07', laps: 52, distance: '306.19 km', image: '/f1_pitstop_action.png' },
    { name: 'Belgian Grand Prix', location: 'Circuit de Spa-Francorchamps', date: 'JUL 26 - 28', laps: 44, distance: '308.05 km', image: '/f1_hero_car.png' },
    { name: 'Italian Grand Prix', location: 'Autodromo Nazionale Monza', date: 'AUG 30 - SEP 01', laps: 53, distance: '306.72 km', image: '/f1_pitstop_action.png' }
  ];

  return (
    <div className="bg-slate-950 text-slate-100 min-h-screen font-sans border border-slate-800 rounded-xl overflow-hidden shadow-2xl mb-8">
      {/* Top Motorsport Announcement Bar */}
      <div className="bg-gradient-to-r from-red-700 via-red-600 to-slate-900 px-6 py-2 flex items-center justify-between text-xs font-mono tracking-widest uppercase">
        <div className="flex items-center gap-2">
          <FaFire className="text-amber-300 animate-bounce" />
          <span className="font-extrabold text-white">FORMULA 1 WORLD CHAMPIONSHIP 2026</span>
        </div>
        <span className="hidden sm:block text-red-200">LIVE TELEMETRY & SPEED ANALYTICS ACTIVE</span>
      </div>

      {/* Hero Section with AI Generated High-Octane F1 Car Image */}
      <div className="relative min-h-[420px] flex items-center p-8 bg-slate-900 overflow-hidden">
        {/* Background Image Container */}
        <div className="absolute inset-0 z-0">
          <img
            src="/f1_hero_car.png"
            alt="F1 High Speed Race Car"
            className="w-full h-full object-cover object-center opacity-40 filter brightness-90 contrast-125"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-slate-950 via-slate-950/80 to-transparent"></div>
        </div>

        {/* Hero Content Overlay */}
        <div className="relative z-10 max-w-2xl space-y-4">
          <div className="inline-flex items-center gap-2 bg-red-600/90 text-white px-3 py-1 rounded-full text-xs font-mono font-bold uppercase tracking-wider shadow-lg">
            <FaFlagCheckered /> NEXT GRAND PRIX: MONACO 2026
          </div>

          <h1 className="text-4xl sm:text-6xl font-black italic tracking-tighter uppercase text-white leading-none">
            PUSH THE LIMITS <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-500 via-amber-400 to-red-600">
              OF PURE SPEED
            </span>
          </h1>

          <p className="text-slate-300 text-sm leading-relaxed font-sans">
            Experience next-generation Formula 1 aerodynamics, hybrid turbo power units, telemetry analytics, and lightning-fast pit stop engineering.
          </p>

          <div className="flex items-center gap-4 pt-2 font-mono text-xs">
            <button className="bg-red-600 hover:bg-red-500 text-white font-bold px-6 py-3 rounded-lg uppercase tracking-wider transition flex items-center gap-2 shadow-xl cursor-pointer">
              <FaPlay className="text-xs" /> Watch Live Telemetry
            </button>

            <button className="border border-slate-700 hover:border-slate-500 bg-slate-900/80 text-slate-200 font-bold px-6 py-3 rounded-lg uppercase tracking-wider transition cursor-pointer">
              View Race Schedule
            </button>
          </div>
        </div>
      </div>

      {/* Telemetry Stats Bar */}
      <div className="bg-slate-900 border-y border-slate-800 grid grid-cols-2 sm:grid-cols-4 font-mono text-xs">
        <div className="p-4 border-r border-slate-800 text-center">
          <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Max Speed</span>
          <span className="text-2xl font-black text-red-500">362.4 km/h</span>
        </div>
        <div className="p-4 border-r border-slate-800 text-center">
          <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Record Pitstop</span>
          <span className="text-2xl font-black text-amber-400">1.82 sec</span>
        </div>
        <div className="p-4 border-r border-slate-800 text-center">
          <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Power Output</span>
          <span className="text-2xl font-black text-cyan-400">1,050+ HP</span>
        </div>
        <div className="p-4 text-center">
          <span className="text-[10px] text-slate-400 uppercase font-bold block mb-1">Cornering Force</span>
          <span className="text-2xl font-black text-purple-400">5.8 G</span>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="p-6">
        <div className="flex border-b border-slate-800 mb-6 gap-6 font-mono text-xs font-bold uppercase">
          <button
            onClick={() => setSelectedTab('standings')}
            className={`pb-3 transition border-b-2 cursor-pointer flex items-center gap-2 ${
              selectedTab === 'standings' ? 'border-red-500 text-red-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FaTrophy /> Driver Standings 2026
          </button>
          <button
            onClick={() => setSelectedTab('pitstop')}
            className={`pb-3 transition border-b-2 cursor-pointer flex items-center gap-2 ${
              selectedTab === 'pitstop' ? 'border-red-500 text-red-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FaStopwatch /> Pit Stop Engineering
          </button>
          <button
            onClick={() => setSelectedTab('circuits')}
            className={`pb-3 transition border-b-2 cursor-pointer flex items-center gap-2 ${
              selectedTab === 'circuits' ? 'border-red-500 text-red-400' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FaFlagCheckered /> Grand Prix Circuits
          </button>
        </div>

        {/* Tab 1: Driver Standings */}
        {selectedTab === 'standings' && (
          <div className="space-y-3 font-mono text-xs">
            <div className="grid grid-cols-12 px-4 py-2 text-[10px] text-slate-400 uppercase font-bold border-b border-slate-800">
              <span className="col-span-1">Rank</span>
              <span className="col-span-5">Driver Name</span>
              <span className="col-span-4">Constructor Team</span>
              <span className="col-span-1 text-center">Wins</span>
              <span className="col-span-1 text-right">Points</span>
            </div>

            {drivers.map((d) => (
              <div
                key={d.rank}
                className={`grid grid-cols-12 items-center px-4 py-3 rounded-lg border transition hover:border-slate-600 ${d.color}`}
              >
                <span className="col-span-1 font-black text-white text-sm">#{d.rank}</span>
                <span className="col-span-5 font-bold text-white text-sm">{d.name}</span>
                <span className="col-span-4 text-slate-300 font-semibold">{d.team}</span>
                <span className="col-span-1 text-center font-bold text-amber-300">{d.wins}</span>
                <span className="col-span-1 text-right font-black text-red-400 text-sm">{d.points} PTS</span>
              </div>
            ))}
          </div>
        )}

        {/* Tab 2: Pit Stop Tech Feature */}
        {selectedTab === 'pitstop' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
            <div className="space-y-4">
              <span className="text-xs font-mono text-amber-400 uppercase tracking-widest font-bold block">
                SUB-2 SECOND PRECISION
              </span>
              <h3 className="text-2xl font-black text-white italic uppercase">
                20 CREW MEMBERS. 4 WHEELS. 1.8 SECONDS.
              </h3>
              <p className="text-slate-300 text-xs leading-relaxed font-sans">
                A Formula 1 pit stop is the ultimate synchronization of human performance and pneumatic technology. During a pit stop, 20 specialized mechanics change all four wheels in under two seconds under high-pressure race conditions.
              </p>

              <div className="grid grid-cols-2 gap-3 font-mono text-xs">
                <div className="bg-slate-900 p-3 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Wheel Nut Torque</span>
                  <strong className="text-red-400 text-base">500 Nm @ 10,000 RPM</strong>
                </div>
                <div className="bg-slate-900 p-3 rounded border border-slate-800">
                  <span className="text-[10px] text-slate-400 block">Jack Release Reaction</span>
                  <strong className="text-emerald-400 text-base">0.12 Seconds</strong>
                </div>
              </div>
            </div>

            <div className="rounded-xl overflow-hidden border border-slate-800 shadow-2xl relative">
              <img
                src="/f1_pitstop_action.png"
                alt="F1 Pitstop Action"
                className="w-full h-64 object-cover filter brightness-105 contrast-110"
              />
              <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-slate-950 p-4 text-xs font-mono text-slate-200">
                <span>📍 Garage Telemetry: Live Pneumatic Wheel Gun Diagnostics</span>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Circuits */}
        {selectedTab === 'circuits' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 font-mono text-xs">
            {circuits.map((c, idx) => (
              <div key={idx} className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <span className="text-[10px] text-red-500 uppercase font-bold block">{c.date}</span>
                    <h4 className="text-base font-bold text-white">{c.name}</h4>
                    <span className="text-[11px] text-slate-400">{c.location}</span>
                  </div>
                  <span className="bg-slate-800 text-slate-300 text-[10px] px-2 py-1 rounded uppercase font-bold">
                    {c.laps} LAPS
                  </span>
                </div>

                <div className="pt-3 border-t border-slate-800/80 flex justify-between items-center text-[10px] text-slate-400">
                  <span>Race Distance: <strong className="text-white">{c.distance}</strong></span>
                  <span className="text-red-400 font-bold flex items-center gap-1 cursor-pointer hover:underline">
                    Circuit Layout <FaChevronRight className="text-[8px]" />
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
