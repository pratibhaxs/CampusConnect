import { Link } from "react-router-dom";
import { Search, Building2, HelpCircle, Bookmark } from "lucide-react";
import { useAuth } from "../../hooks/useAuth";
import PageHeader from "../../components/common/PageHeader";

export default function StudentDashboard() {
  const { user } = useAuth();

  return (
    <div>
      <PageHeader
        title="Dashboard"
        subtitle={`${user?.college_name || ""}${user?.branch ? ` · ${user.branch}` : ""}`}
      />
      <div className="page-content">
        <div className="dashboard-cards">
          <Link to="/search" className="dashboard-card">
            <span className="stat-card-icon" style={{ marginBottom: "0.6rem" }}><Search size={18} /></span>
            <h3>Search Experiences</h3>
            <p>Filter by company, college, role, year, branch, difficulty, or topic.</p>
          </Link>
          <Link to="/companies" className="dashboard-card">
            <span className="stat-card-icon" style={{ marginBottom: "0.6rem" }}><Building2 size={18} /></span>
            <h3>Browse Companies</h3>
            <p>See placement stats, recommended prep, and shared experiences.</p>
          </Link>
          <Link to="/questions" className="dashboard-card">
            <span className="stat-card-icon" style={{ marginBottom: "0.6rem" }}><HelpCircle size={18} /></span>
            <h3>Question Repository</h3>
            <p>Browse interview questions with frequency and difficulty.</p>
          </Link>
          <Link to="/student/saved" className="dashboard-card">
            <span className="stat-card-icon" style={{ marginBottom: "0.6rem" }}><Bookmark size={18} /></span>
            <h3>Saved Items</h3>
            <p>Everything you've bookmarked, in one place.</p>
          </Link>
        </div>
      </div>
    </div>
  );
}
