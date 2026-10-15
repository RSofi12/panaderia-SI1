import React, { useCallback, useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';

export const DashboardLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(min-width: 1024px)').matches,
  );
  const cerrarMenu = useCallback(() => setSidebarOpen(false), []);
  const alternarMenu = useCallback(() => setSidebarOpen((abierto) => !abierto), []);

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar open={sidebarOpen} onNavigate={cerrarMenu} />

      <div
        className={`flex min-h-screen flex-col transition-[padding] duration-300 ease-out motion-reduce:transition-none ${
          sidebarOpen ? 'lg:pl-72' : 'lg:pl-[4.5rem]'
        }`}
      >
        <Topbar title="Panel de Control" menuAbierto={sidebarOpen} onAlternarMenu={alternarMenu} />

        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>

        <footer className="border-t border-slate-200 bg-white px-4 py-3 text-center text-[11px] text-slate-400">
          Sistema de Información Web • Panadería Santiago © 2026
        </footer>
      </div>
    </div>
  );
};

export default DashboardLayout;
