import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  LayoutDashboard,
  Files,
  FolderKanban,
  MessageSquare,
  LogOut,
  User,
  ShieldCheck,
  Menu,
  X,
  Sparkles
} from 'lucide-react';

export default function DashboardLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'Documents', path: '/documents', icon: Files },
    { name: 'Collections', path: '/collections', icon: FolderKanban },
    { name: 'Document Chat', path: '/chat', icon: MessageSquare },
  ];

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col md:flex-row text-slate-100">
      {/* Mobile Topbar */}
      <div className="md:hidden bg-slate-900 border-b border-slate-800 p-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="h-8 w-8 rounded-lg bg-sky-500/20 text-sky-400 flex items-center justify-center font-bold text-sm border border-sky-500/30">
            RF
          </div>
          <span className="font-bold text-white tracking-tight">RAGForge</span>
        </div>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="text-slate-400 hover:text-white"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Sidebar for Desktop & Mobile Toggle */}
      <aside
        className={`${
          mobileMenuOpen ? 'block' : 'hidden'
        } md:flex flex-col w-full md:w-64 bg-slate-900/90 border-r border-slate-800/80 p-5 shrink-0 justify-between backdrop-blur-md`}
      >
        <div className="space-y-6">
          {/* Logo / Brand */}
          <div className="hidden md:flex items-center space-x-3 px-2">
            <div className="h-9 w-9 rounded-xl bg-sky-500/20 text-sky-400 flex items-center justify-center font-bold text-lg border border-sky-500/30 shadow-md shadow-sky-500/10">
              RF
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-tight leading-none">RAGForge</h1>
              <span className="text-[11px] text-sky-400 font-medium">Document Intelligence</span>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition ${
                      isActive
                        ? 'bg-sky-500/15 text-sky-400 border border-sky-500/20'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* User Card & Logout */}
        <div className="border-t border-slate-800/80 pt-4 mt-6">
          <div className="flex items-center justify-between px-2 py-2">
            <div className="flex items-center space-x-3 overflow-hidden">
              <div className="h-8 w-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-semibold text-sky-400 uppercase shrink-0">
                {user?.name ? user.name[0] : 'U'}
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-semibold text-slate-200 truncate">{user?.name || 'User'}</p>
                <p className="text-[11px] text-slate-400 truncate">{user?.email}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Logout"
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-y-auto bg-slate-950">
        <Outlet />
      </main>
    </div>
  );
}
