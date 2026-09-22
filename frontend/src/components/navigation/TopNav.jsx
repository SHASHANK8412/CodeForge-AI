import React, { useState, useEffect, useRef } from "react";
import { 
  FaSearch, FaBell, FaCog, FaKey, FaSignOutAlt, 
  FaPlus, FaBolt, FaCheckCircle, FaTrash, FaBars, FaShieldAlt
} from "react-icons/fa";
import { useAuth } from "../../auth/useAuth";

export default function TopNav({ 
  onOpenCommandPalette, 
  currentView, 
  setView, 
  onToggleSidebar 
}) {
  const { user, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(3);
  
  const [notifications, setNotifications] = useState([
    {
      id: "n-1",
      title: "Empirical Test Suite Passed",
      desc: "48/48 unit & integration tests completed with 0 regressions.",
      time: "5m ago",
      type: "success",
      unread: true
    },
    {
      id: "n-2",
      title: "Security SAST Scan Clean",
      desc: "Zero high-severity CVEs detected in backend dependencies.",
      time: "25m ago",
      type: "security",
      unread: true
    },
    {
      id: "n-3",
      title: "Multi-Agent Orchestrator Ready",
      desc: "Claude 3.7 Sonnet & DeepSeek R1 models synced to workspace.",
      time: "1h ago",
      type: "info",
      unread: true
    }
  ]);

  const userMenuRef = useRef(null);
  const notificationRef = useRef(null);

  // Close dropdowns on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
      if (notificationRef.current && !notificationRef.current.contains(event.target)) {
        setShowNotifications(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, unread: false })));
    setUnreadCount(0);
  };

  const clearAllNotifications = () => {
    setNotifications([]);
    setUnreadCount(0);
  };

  const isMac = typeof window !== "undefined" && navigator.platform?.toUpperCase().indexOf("MAC") >= 0;

  return (
    <header className="h-14 bg-[#0F1117]/90 backdrop-blur-md border-b border-[#242833] text-[#F5F7FA] px-4 flex items-center justify-between z-30 shrink-0 select-none">
      {/* Left side: Mobile Toggle & Breadcrumb / Section Label */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="md:hidden p-2 rounded-lg bg-[#151821] hover:bg-[#1E2330] text-[#9AA1B2] hover:text-white transition active:scale-95"
          title="Toggle Navigation"
        >
          <FaBars size={14} />
        </button>

        <div className="hidden sm:flex items-center gap-2 text-xs font-semibold">
          <span className="text-[#9AA1B2]">AIForge OS</span>
          <span className="text-[#64748B]">/</span>
          <span className="text-white capitalize font-bold">
            {currentView === "dashboard" ? "Command Center" : currentView.replace(/-/g, " ")}
          </span>
        </div>

        {/* Live Agent Status Indicator */}
        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-[11px] font-medium text-emerald-400">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>Multi-Agent Engine Online</span>
        </div>
      </div>

      {/* Center: Global Search / Command Bar Trigger */}
      <div className="flex-1 max-w-xl mx-3 sm:mx-6">
        <button
          onClick={onOpenCommandPalette}
          className="w-full flex items-center justify-between bg-[#151821] hover:bg-[#1E2330] border border-[#242833] hover:border-[#8D5CF6]/50 rounded-xl px-3.5 py-1.5 text-xs text-[#9AA1B2] hover:text-[#F5F7FA] transition-all shadow-inner group cursor-pointer"
        >
          <div className="flex items-center gap-2.5 truncate">
            <FaSearch className="text-[#64748B] group-hover:text-[#8D5CF6] transition-colors shrink-0" size={12} />
            <span className="truncate text-[11px] sm:text-xs">Search projects, AI tools, saved snippets, actions...</span>
          </div>
          <div className="hidden sm:flex items-center gap-1 bg-[#08090D] border border-[#242833] rounded px-1.5 py-0.5 text-[10px] font-mono text-[#9AA1B2]">
            <span>{isMac ? "⌘" : "Ctrl"}</span>
            <span>K</span>
          </div>
        </button>
      </div>

      {/* Right side: Quick Action, Notifications, User Menu */}
      <div className="flex items-center gap-2 sm:gap-3">
        {/* Quick New Project Button */}
        <button
          onClick={() => setView("create")}
          className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 bg-[#8D5CF6] hover:bg-[#7c4ee4] text-white rounded-lg text-xs font-bold transition shadow-md shadow-violet-500/20 active:scale-95 cursor-pointer"
        >
          <FaPlus size={10} />
          <span>New</span>
        </button>

        {/* Notifications Popover */}
        <div className="relative" ref={notificationRef}>
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            className="p-2 rounded-xl bg-[#151821] hover:bg-[#1E2330] border border-[#242833] text-[#9AA1B2] hover:text-white transition relative active:scale-95 cursor-pointer"
            title="System Notifications"
          >
            <FaBell size={13} />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-cyan-500 text-black text-[9px] font-black rounded-full flex items-center justify-center animate-pulse">
                {unreadCount}
              </span>
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-[#0F1117] border border-[#242833] rounded-2xl shadow-2xl z-50 overflow-hidden text-xs animate-fade-in">
              <div className="p-3.5 border-b border-[#242833] flex items-center justify-between bg-[#151821]/50">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-white">System Feed</span>
                  {unreadCount > 0 && (
                    <span className="px-1.5 py-0.5 bg-cyan-500/20 text-cyan-400 text-[10px] rounded font-bold">
                      {unreadCount} new
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 text-[10px]">
                  {unreadCount > 0 && (
                    <button
                      onClick={markAllAsRead}
                      className="text-[#8D5CF6] hover:text-[#a78bfa] transition font-semibold cursor-pointer"
                    >
                      Mark read
                    </button>
                  )}
                  {notifications.length > 0 && (
                    <button
                      onClick={clearAllNotifications}
                      className="text-[#64748B] hover:text-rose-400 transition cursor-pointer"
                      title="Clear notifications"
                    >
                      <FaTrash size={9} />
                    </button>
                  )}
                </div>
              </div>

              <div className="max-h-72 overflow-y-auto divide-y divide-[#1E2330] custom-scrollbar">
                {notifications.length === 0 ? (
                  <div className="p-6 text-center text-[#64748B]">
                    <FaCheckCircle className="mx-auto mb-2 text-[#242833]" size={20} />
                    <span>All clear! No notifications.</span>
                  </div>
                ) : (
                  notifications.map((item) => (
                    <div 
                      key={item.id} 
                      className={`p-3 hover:bg-[#151821]/60 transition flex items-start gap-2.5 ${
                        item.unread ? "bg-violet-500/5" : ""
                      }`}
                    >
                      <span className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${
                        item.type === "success" ? "bg-emerald-400" :
                        item.type === "security" ? "bg-cyan-400" : "bg-violet-400"
                      }`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-1">
                          <span className="font-bold text-white truncate text-[11px]">{item.title}</span>
                          <span className="text-[9px] text-[#64748B] shrink-0">{item.time}</span>
                        </div>
                        <p className="text-[#9AA1B2] text-[11px] mt-0.5 line-clamp-2 leading-relaxed">{item.desc}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>

              <div className="p-2 border-t border-[#242833] bg-[#08090D] text-center">
                <button
                  onClick={() => {
                    setShowNotifications(false);
                    setView("history");
                  }}
                  className="text-[11px] text-[#8D5CF6] hover:text-white font-semibold transition cursor-pointer"
                >
                  View full activity log →
                </button>
              </div>
            </div>
          )}
        </div>

        {/* User Profile Menu */}
        <div className="relative" ref={userMenuRef}>
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2 p-1.5 sm:px-2.5 sm:py-1.5 bg-[#151821] hover:bg-[#1E2330] border border-[#242833] rounded-xl text-xs transition active:scale-95 cursor-pointer"
          >
            <div className="w-6 h-6 rounded-lg bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center font-bold text-[11px] text-white shadow">
              {(user?.name || "Dev").charAt(0).toUpperCase()}
            </div>
            <span className="hidden sm:inline font-semibold text-white max-w-[100px] truncate">
              {user?.name || "Developer"}
            </span>
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-[#0F1117] border border-[#242833] rounded-2xl p-1.5 shadow-2xl z-50 text-xs animate-fade-in">
              <div className="p-3 border-b border-[#242833]">
                <div className="font-bold text-white truncate">{user?.name || "Developer"}</div>
                <div className="text-[10px] text-[#9AA1B2] truncate font-mono">{user?.email || "dev@aiforge.io"}</div>
                <div className="mt-2 inline-flex items-center gap-1.5 px-2 py-0.5 bg-violet-500/10 border border-violet-500/20 text-violet-400 text-[10px] rounded-full font-semibold">
                  <FaBolt size={8} /> Pro AI Workspace
                </div>
              </div>

              <div className="py-1 space-y-0.5">
                <button
                  onClick={() => {
                    setShowUserMenu(false);
                    setView("settings");
                  }}
                  className="w-full text-left px-3 py-2 hover:bg-[#151821] text-[#9AA1B2] hover:text-white rounded-lg flex items-center gap-2.5 transition cursor-pointer"
                >
                  <FaCog className="text-[#64748B]" /> Workspace Settings
                </button>
                <button
                  onClick={() => {
                    setShowUserMenu(false);
                    setView("api-keys");
                  }}
                  className="w-full text-left px-3 py-2 hover:bg-[#151821] text-[#9AA1B2] hover:text-white rounded-lg flex items-center gap-2.5 transition cursor-pointer"
                >
                  <FaKey className="text-[#64748B]" /> API Keys & Models
                </button>
                <button
                  onClick={() => {
                    setShowUserMenu(false);
                    setView("security");
                  }}
                  className="w-full text-left px-3 py-2 hover:bg-[#151821] text-[#9AA1B2] hover:text-white rounded-lg flex items-center gap-2.5 transition cursor-pointer"
                >
                  <FaShieldAlt className="text-[#64748B]" /> Security Center
                </button>
              </div>

              <div className="pt-1 border-t border-[#242833]">
                <button
                  onClick={() => {
                    setShowUserMenu(false);
                    if (logout) logout();
                  }}
                  className="w-full text-left px-3 py-2 hover:bg-rose-500/10 text-rose-400 rounded-lg flex items-center gap-2.5 transition cursor-pointer"
                >
                  <FaSignOutAlt /> Sign Out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
