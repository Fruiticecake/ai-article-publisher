'use client';

import { Outlet, Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderOpen,
  FileText,
  Settings,
  LogOut,
  User,
  Sparkles,
  Send,
} from 'lucide-react';

export default function Layout() {
  const location = useLocation();

  const navItems = [
    { path: '/', label: '仪表盘', icon: LayoutDashboard },
    { path: '/projects', label: '项目', icon: FolderOpen },
    { path: '/reports', label: '报告', icon: FileText },
    { path: '/publish', label: '发布', icon: Send },
    { path: '/settings', label: '设置', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-cyan-50/20">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 z-40 h-screen w-72 border-r border-slate-200/60 bg-white/80 backdrop-blur-xl shadow-2xl shadow-slate-200/30">
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="border-b border-slate-200/60 px-6 py-7">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 via-cyan-500 to-blue-600 shadow-lg shadow-blue-500/30">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                  Auto Publisher
                </h1>
                <p className="text-xs text-slate-500">GitHub 项目分析与发布</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 space-y-1.5 px-4 py-6">
            {navItems.map((item, index) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`group flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg shadow-blue-500/30'
                      : 'text-slate-600 hover:bg-slate-100/80 hover:text-slate-900'
                  }`}
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <Icon size={18} className={isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-600'} />
                  {item.label}
                  {isActive && (
                    <div className="ml-auto w-1.5 h-1.5 rounded-full bg-white shadow-sm" />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* User */}
          <div className="border-t border-slate-200/60 px-4 py-4">
            <div className="flex items-center justify-between rounded-xl bg-slate-50/80 p-3">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-slate-100 to-slate-200 text-slate-600 shadow-sm">
                  <User size={16} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-700">Admin</p>
                  <p className="text-xs text-slate-500">管理员</p>
                </div>
              </div>
              <button
                className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600 transition-all duration-200"
                onClick={() => {
                  localStorage.removeItem('token');
                  window.location.href = '/login';
                }}
                title="退出登录"
              >
                <LogOut size={16} />
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="pl-72">
        <div className="min-h-screen p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
