import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { FileText, CheckCircle2, Clock, PlusCircle, Building2 } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import { fetchMyExperiences } from "../../api/experienceApi";
import PageHeader from "../../components/common/PageHeader";

const dateFmt = (iso) => iso ? new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" }) : "";

export default function AlumniDashboard() {
  const { user } = useAuth();
  const [experiences, setExperiences] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMyExperiences().then((res) => setExperiences(res.data)).finally(() => setLoading(false));
  }, []);

  const pendingCount = experiences.filter((e) => e.status === "pending").length;
  const approvedCount = experiences.filter((e) => e.status === "approved").length;
  const recent = [...experiences]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 5);

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle={`${user?.college_name || ""}${user?.branch ? ` · ${user.branch}` : ""}`}
        actions={<Link to="/alumni/submit-experience" className="btn-primary"><PlusCircle size={16} /> Submit Experience</Link>}
      />
      <div className="page-content">
        <div className="stats-cards">
          <div className="stat-card">
            <div className="stat-card-text"><span className="stat-value">{experiences.length}</span><span className="stat-label">Total submitted</span></div>
            <span className="stat-card-icon"><FileText size={18} /></span>
          </div>
          <div className="stat-card">
            <div className="stat-card-text"><span className="stat-value">{approvedCount}</span><span className="stat-label">Approved</span></div>
            <span className="stat-card-icon" style={{ background: "#e4f7ea", color: "#1f8a44" }}><CheckCircle2 size={18} /></span>
          </div>
          <div className="stat-card">
            <div className="stat-card-text"><span className="stat-value">{pendingCount}</span><span className="stat-label">Pending review</span></div>
            <span className="stat-card-icon" style={{ background: "#fff4e0", color: "#a1670a" }}><Clock size={18} /></span>
          </div>
        </div>

        <div className="activity-card">
          <div className="activity-card-header">
            <span>Recent Submissions</span>
            <Link to="/alumni/my-experiences">View all</Link>
          </div>
          {loading ? (
            <div className="activity-empty">Loading...</div>
          ) : recent.length === 0 ? (
            <div className="activity-empty">
              You haven't submitted any experiences yet. <Link to="/alumni/submit-experience">Submit your first one &rarr;</Link>
            </div>
          ) : (
            recent.map((e) => (
              <Link to={`/experiences/${e.id}`} key={e.id} className="activity-row">
                <span className="activity-avatar"><Building2 size={16} /></span>
                <span className="activity-main">
                  <p className="activity-title">{e.company_name}</p>
                  <p className="activity-subtitle">{e.role_title} &middot; {e.college_name}</p>
                </span>
                <span className="activity-meta">
                  <span className={`activity-badge ${e.status}`}>{e.status.toUpperCase()}</span>
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
