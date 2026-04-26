import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import DashboardPage from "./components/DashboardPage";
import FrameworksPage from "./components/FrameworksPage";
import ScoringPage from "./components/ScoringPage";
import ExceptionQueuePage from "./components/ExceptionQueuePage";
import FlightRecorderPage from "./components/FlightRecorderPage";
import ReceiptsPage from "./components/ReceiptsPage";
import TierConfigPage from "./components/TierConfigPage";
import HeaderBar from "./components/HeaderBar";

const NAV_ITEMS: Array<{ to: string; label: string }> = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/score", label: "Score Intent" },
  { to: "/exceptions", label: "Exceptions" },
  { to: "/receipts", label: "Receipts" },
  { to: "/flight-recorder", label: "Flight Recorder" },
  { to: "/frameworks", label: "Frameworks" },
  { to: "/tiers", label: "Tier Config" },
];

export default function App() {
  return (
    <div className="min-h-screen bg-adam-ink text-slate-100 flex flex-col">
      <HeaderBar />
      <div className="flex flex-1 min-h-0">
        <aside className="w-60 border-r border-slate-800/60 px-4 py-6 space-y-1 bg-adam-navy/60 hidden md:block">
          <nav className="flex flex-col gap-1">
            {NAV_ITEMS.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `nav-link ${isActive ? "nav-link-active" : ""}`
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
          <div className="mt-8 text-xs text-slate-500 leading-snug">
            <p className="uppercase tracking-widest mb-1">BOSS Engine</p>
            <p>v3.2.0 · ADAM reference v1.6</p>
            <p className="mt-1">All actions are written to the hash-chained Flight Recorder.</p>
          </div>
        </aside>
        <main className="flex-1 px-6 py-8 overflow-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/score" element={<ScoringPage />} />
            <Route path="/exceptions" element={<ExceptionQueuePage />} />
            <Route path="/receipts" element={<ReceiptsPage />} />
            <Route path="/flight-recorder" element={<FlightRecorderPage />} />
            <Route path="/frameworks" element={<FrameworksPage />} />
            <Route path="/tiers" element={<TierConfigPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
