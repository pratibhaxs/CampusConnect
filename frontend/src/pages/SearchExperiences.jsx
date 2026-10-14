import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import FilterBar from "../components/common/FilterBar";
import { fetchExperiences } from "../api/experienceApi";
import { fetchCompanies } from "../api/companyApi";
import { fetchColleges } from "../api/collegeApi";

const DIFFICULTIES = [
  { value: "easy", label: "Easy" },
  { value: "medium", label: "Medium" },
  { value: "hard", label: "Hard" },
];

export default function SearchExperiences() {
  const [companies, setCompanies] = useState([]);
  const [colleges, setColleges] = useState([]);
  const [filters, setFilters] = useState({
    company_id: "", college_id: "", year: "", branch: "", difficulty: "", round_type: "", topic: "",
  });
  const [experiences, setExperiences] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCompanies().then((res) => setCompanies(res.data));
    fetchColleges().then((res) => setColleges(res.data));
  }, []);

  useEffect(() => {
    setLoading(true);
    const timer = setTimeout(() => {
      fetchExperiences(filters).then((res) => setExperiences(res.data)).finally(() => setLoading(false));
    }, 300);
    return () => clearTimeout(timer);
  }, [filters]);

  function handleChange(name, value) {
    setFilters({ ...filters, [name]: value });
  }

  function handleClear() {
    setFilters({ company_id: "", college_id: "", year: "", branch: "", difficulty: "", round_type: "", topic: "" });
  }

  const fields = [
    { name: "company_id", label: "Company", type: "searchable", options: companies.map((c) => ({ value: c.id, label: c.name })) },
    { name: "college_id", label: "College", type: "searchable", options: colleges.map((c) => ({ value: c.id, label: c.name })) },
    { name: "year", label: "Placement Year", type: "number", placeholder: "e.g. 2026" },
    { name: "branch", label: "Branch", type: "text", placeholder: "e.g. CSE" },
    { name: "difficulty", label: "Round Difficulty", type: "select", options: DIFFICULTIES },
    { name: "round_type", label: "Round Type", type: "text", placeholder: "e.g. Technical" },
    { name: "topic", label: "Topic", type: "text", placeholder: "e.g. SQL" },
  ];

  return (
    <div className="page">
      <h2>Search Placement Experiences</h2>
      <FilterBar fields={fields} values={filters} onChange={handleChange} onClear={handleClear} />

      {loading ? (
        <p>Loading...</p>
      ) : experiences.length === 0 ? (
        <p>No experiences match these filters.</p>
      ) : (
        <div className="card-grid">
          {experiences.map((e) => (
            <Link to={`/experiences/${e.id}`} key={e.id} className="company-card">
              <h3>{e.company_name} — {e.role_title}</h3>
              <p className="company-desc">{e.college_name} &middot; {e.branch} &middot; {e.placement_year}</p>
              <p className="company-meta">{e.selected ? "Selected" : "Not selected"}{e.package ? ` · ${e.package}` : ""}</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
