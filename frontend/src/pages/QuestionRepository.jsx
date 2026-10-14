import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import FilterBar from "../components/common/FilterBar";
import FrequentTopicsList from "../components/common/FrequentTopicsList";
import BookmarkButton from "../components/common/BookmarkButton";
import { fetchQuestions } from "../api/questionApi";
import { fetchCompanies } from "../api/companyApi";

const CATEGORIES = ["Aptitude", "Coding", "DSA", "OOP", "DBMS", "Operating Systems",
  "Computer Networks", "Python", "Java", "JavaScript", "HR", "Behavioral", "Other"];
const DIFFICULTIES = [{ value: "easy", label: "Easy" }, { value: "medium", label: "Medium" }, { value: "hard", label: "Hard" }];

export default function QuestionRepository() {
  const [companies, setCompanies] = useState([]);
  const [filters, setFilters] = useState({ category: "", topic: "", company_id: "", difficulty: "" });
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCompanies().then((res) => setCompanies(res.data));
  }, []);

  useEffect(() => {
    setLoading(true);
    const timer = setTimeout(() => {
      fetchQuestions(filters).then((res) => setQuestions(res.data)).finally(() => setLoading(false));
    }, 300);
    return () => clearTimeout(timer);
  }, [filters]);

  function handleChange(name, value) {
    setFilters({ ...filters, [name]: value });
  }
  function handleClear() {
    setFilters({ category: "", topic: "", company_id: "", difficulty: "" });
  }

  const fields = [
    { name: "category", label: "Category", type: "select", options: CATEGORIES.map((c) => ({ value: c, label: c })) },
    { name: "topic", label: "Topic", type: "text", placeholder: "e.g. SQL" },
    { name: "company_id", label: "Company", type: "searchable", options: companies.map((c) => ({ value: c.id, label: c.name })) },
    { name: "difficulty", label: "Difficulty", type: "select", options: DIFFICULTIES },
  ];

  return (
    <div className="page">
      <h2>Question Repository</h2>

      <div className="repo-layout">
        <div className="repo-main">
          <FilterBar fields={fields} values={filters} onChange={handleChange} onClear={handleClear} />

          {loading ? (
            <p>Loading...</p>
          ) : questions.length === 0 ? (
            <p>No questions match these filters.</p>
          ) : (
            <ul className="question-list">
              {questions.map((q) => (
                <li key={q.id} className="question-item">
                  <p className="question-text">{q.question_text} <BookmarkButton targetType="question" targetId={q.id} /></p>
                  <p className="company-meta">
                    {q.company_name} &middot; {q.role_title} &middot; {q.category || "Uncategorized"}
                    {q.topic && <> &middot; {q.topic}</>}
                    {q.difficulty && <> &middot; {q.difficulty}</>}
                    {" · "}reported {q.report_count} time{q.report_count !== 1 ? "s" : ""}
                  </p>
                  <Link to={`/experiences/${q.experience_id}`}>View full experience &rarr;</Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="repo-sidebar">
          <h3>🔥 Top Topics Overall</h3>
          <FrequentTopicsList limit={10} />
        </div>
      </div>
    </div>
  );
}
