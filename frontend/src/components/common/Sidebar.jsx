import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  LayoutDashboard, Search, HelpCircle, Building2, Bookmark,
  FileText, PlusCircle, CheckSquare, Flag, BarChart3, Menu, X, LogOut, Briefcase,
} from "lucide-react";
import { useAuth } from "../../hooks/useAuth";

// Same links and labels as before — only the layout changed.
const LINKS = {
  student: [
    { to: "/student", label: "Dashboard", icon: LayoutDashboard },
    { to: "/search", label: "Search", icon: Search },
    { to: "/questions", label: "Questions", icon: HelpCircle },
    { to: "/companies", label: "Companies", icon: Building2 },
    { to: "/student/saved", label: "Saved", icon: Bookmark },
  ],
  alumni: [
    { to: "/alumni", label: "Dashboard", icon: LayoutDashboard },
    { to: "/alumni/my-experiences", label: "My Experiences", icon: FileText },
    { to: "/alumni/submit-experience", label: "Submit", icon: PlusCircle },
    { to: "/companies", label: "Companies", icon: Building2 },
  ],
  admin: [
    { to: "/admin", label: "Dashboard", icon: LayoutDashboard },
    { to: "/admin/experiences", label: "Approvals", icon: CheckSquare },
    { to: "/admin/reports", label: "Reports", icon: Flag },
    { to: "/admin/companies", label: "Companies", icon: Building2 },
    { to: "/admin/statistics", label: "Statistics", icon: BarChart3 },
  ],
};

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  if (!user) return null; // Login/Register pages render without a sidebar

  const links = LINKS[user.role] || [];

  function handleLogout() {
    logout();
    navigate("/login");
  }

  function isActive(to) {
    return location.pathname === to;
  }

  return (
    <>
      <button className="sidebar-mobile-toggle" onClick={() => setMobileOpen(true)} aria-label="Open menu">
        <Menu size={20} />
      </button>

      {mobileOpen && <div className="sidebar-backdrop" onClick={() => setMobileOpen(false)} />}

      <aside className={mobileOpen ? "sidebar open" : "sidebar"}>
        <div className="sidebar-brand-row">
          <Link to={`/${user.role}`} className="sidebar-brand" onClick={() => setMobileOpen(false)}>
            <span className="sidebar-brand-icon"><Briefcase size={18} /></span>
            <span>
              <span className="sidebar-brand-title">Placement Hub</span>
              <span className="sidebar-brand-subtitle">Campus Experience Hub</span>
            </span>
          </Link>
          <button className="sidebar-mobile-close" onClick={() => setMobileOpen(false)} aria-label="Close menu">
            <X size={20} />
          </button>
        </div>

        <nav className="sidebar-nav">
          {links.map((l) => {
            const Icon = l.icon;
            return (
              <Link
                key={l.to}
                to={l.to}
                onClick={() => setMobileOpen(false)}
                className={isActive(l.to) ? "sidebar-link active" : "sidebar-link"}
              >
                <Icon size={18} />
                <span>{l.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <span className="sidebar-user-avatar">{user.name?.[0]?.toUpperCase()}</span>
            <span className="sidebar-user-info">
              <span className="sidebar-user-name">{user.name}</span>
              <span className="sidebar-user-role">{user.role}</span>
            </span>
          </div>
          <button onClick={handleLogout} className="sidebar-logout" aria-label="Log out">
            <LogOut size={16} />
          </button>
        </div>
      </aside>
    </>
  );
}
