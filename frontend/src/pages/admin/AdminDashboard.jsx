import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Users, GraduationCap, Building2, Clock } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { fetchAdminStatistics } from "../../api/statsApi";
import { fetchExperiences } from "../../api/experienceApi";
import PageHeader from "../../components/common/PageHeader";

const dateFmt = (iso) => iso ? new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }) : "";

export default function AdminDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [pending, setPending] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAdminStatistics().then((res) => setStats(res.data));
    fetchExperiences({ status: "pending" }).then((res) => setPending(res.data.slice(0, 5))).finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <PageHeader title="Dashboard" subtitle={`Welcome, ${user?.name}`} />
      <div className="page-content">
        {stats && (
          <div className="stats-cards">
            <div className="stat-card">
              <div className="stat-card-text"><span className="stat-value">{stats.total_students}</span><span className="stat-label">Students</span></div>
              <span className="stat-card-icon"><Users size={18} /></span>
            </div>
            <div className="stat-card">
              <div className="stat-card-text"><span className="stat-value">{stats.total_alumni}</span><span className="stat-label">Alumni</span></div>
              <span className="stat-card-icon" style={{ background: "#e4f7ea", color: "#1f8a44" }}><GraduationCap size={18} /></span>
            </div>
            <div className="stat-card">
              <div className="stat-card-text"><span className="stat-value">{stats.total_companies}</span><span className="stat-label">Companies</span></div>
              <span className="stat-card-icon" style={{ background: "#fde8f3", color: "#b0348a" }}><Building2 size={18} /></span>
            </div>
            <div className="stat-card">
              <div className="stat-card-text"><span className="stat-value">{stats.pending_experiences}</span><span className="stat-label">Awaiting approval</span></div>
              <span className="stat-card-icon" style={{ background: "#fff4e0", color: "#a1670a" }}><Clock size={18} /></span>
            </div>
          </div>
        )}

        <div className="activity-card">
          <div className="activity-card-header">
            <span>Pending Approvals</span>
            <Link to="/admin/experiences">View all</Link>
          </div>
          {loading ? (
            <div className="activity-empty">Loading...</div>
          ) : pending.length === 0 ? (
            <div className="activity-empty">Nothing waiting on review right now.</div>
          ) : (
            pending.map((e) => (
              <Link to={`/experiences/${e.id}`} key={e.id} className="activity-row">
                <span className="activity-avatar">{e.company_name?.[0]}</span>
                <span className="activity-main">
                  <p className="activity-title">{e.company_name}</p>
                  <p className="activity-subtitle">{e.role_title} &middot; submitted by {e.user_name}</p>
                </span>
                <span className="activity-meta">
                  <span className="activity-badge pending">PENDING</span>
                  <span className="activity-date">{dateFmt(e.created_at)}</span>
                </span>
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
