import React from 'react';
import { FaSearch, FaFilter, FaSortAmountDown } from 'react-icons/fa';

export default function ProjectToolbar({
  searchQuery,
  setSearchQuery,
  statusFilter,
  setStatusFilter,
  sortBy,
  setSortBy
}) {
  return (
    <div className="bg-slate-950 border border-slate-800/80 rounded-2xl p-4 shadow-xl flex flex-col md:flex-row items-center justify-between gap-4 font-sans">
      {/* Search Input */}
      <div className="relative w-full md:w-80">
        <FaSearch className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 w-3.5 h-3.5" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search projects by name, stack, description..."
          className="w-full pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-sans"
        />
      </div>

      {/* Filter & Sort Controls */}
      <div className="flex items-center gap-3 w-full md:w-auto justify-end">
        {/* Status Filter */}
        <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl text-xs text-slate-300">
          <FaFilter className="text-slate-500 w-3 h-3" />
          <span className="text-[11px] text-slate-400 font-medium">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer"
          >
            <option value="all" className="bg-slate-950 text-white">All Statuses</option>
            <option value="building" className="bg-slate-950 text-white">Building</option>
            <option value="completed" className="bg-slate-950 text-white">Completed</option>
            <option value="live" className="bg-slate-950 text-white">Deployed (Live)</option>
            <option value="failed" className="bg-slate-950 text-white">Failed</option>
            <option value="archived" className="bg-slate-950 text-white">Archived</option>
          </select>
        </div>

        {/* Sort */}
        <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl text-xs text-slate-300">
          <FaSortAmountDown className="text-slate-500 w-3 h-3" />
          <span className="text-[11px] text-slate-400 font-medium">Sort:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-transparent text-white font-semibold focus:outline-none cursor-pointer"
          >
            <option value="recently_updated" className="bg-slate-950 text-white">Recently Updated</option>
            <option value="recently_created" className="bg-slate-950 text-white">Recently Created</option>
            <option value="highest_quality" className="bg-slate-950 text-white">Highest Quality</option>
            <option value="lowest_quality" className="bg-slate-950 text-white">Lowest Quality</option>
            <option value="alphabetical" className="bg-slate-950 text-white">Alphabetical</option>
          </select>
        </div>
      </div>
    </div>
  );
}
