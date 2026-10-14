import { useState, useEffect } from "react";
import {
  fetchSuggestions, fetchDuplicates, approveCompany, approveRole, mergeCompanies,
} from "../../api/adminApi";

export default function Suggestions() {
  const [data, setData] = useState({ companies: [], roles: [] });
  const [pairs, setPairs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  function load() {
    setLoading(true);
    Promise.all([fetchSuggestions(), fetchDuplicates()])
      .then(([s, d]) => { setData(s.data); setPairs(d.data); })
      .catch(() => setError("Could not load suggestions."))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, []);

  async function run(action, success) {
    setError("");
    setMessage("");
    try {
      await action();
      setMessage(success);
      load();
    } catch (err) {
      setError(err.response?.data?.error || "Action failed.");
    }
  }

  function handleMerge(source, target) {
    if (!window.confirm(`Merge "${source.name}" into "${target.name}"? All its experiences, roles and bookmarks move to "${target.name}", and "${source.name}" is deleted.`)) return;
    run(() => mergeCompanies(source.id, target.id), `Merged ${source.name} into ${target.name}.`);
  }

  if (loading) return <div className="page"><p>Loading...</p></div>;

  return (
    <div className="page">
      <h2>Suggestions &amp; Duplicates</h2>
      {message && <p className="hint">{message}</p>}
      {error && <p className="form-error">{error}</p>}

      <h3>Companies awaiting review</h3>
      {data.companies.length === 0 ? <p>None.</p> : (
        <table className="admin-table">
          <thead><tr><th>Company</th><th>Suggested by</th><th>Looks like</th><th>Experiences</th><th>Actions</th></tr></thead>
          <tbody>
            {data.companies.map((c) => (
              <tr key={c.id}>
                <td>{c.name}</td>
                <td>{c.suggested_by || "—"}</td>
                <td>{c.similar_to ? c.similar_to.name : "—"}</td>
                <td>{c.experience_count}</td>
                <td style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
                  <button className="secondary-btn" onClick={() => run(() => approveCompany(c.id), `Approved ${c.name}.`)}>Approve</button>
                  {c.similar_to && (
                    <button className="danger-btn small" onClick={() => handleMerge(c, c.similar_to)}>
                      Merge into {c.similar_to.name}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h3 style={{ marginTop: "2rem" }}>Roles awaiting review</h3>
      {data.roles.length === 0 ? <p>None.</p> : (
        <table className="admin-table">
          <thead><tr><th>Role</th><th>Company</th><th>Suggested by</th><th>Actions</th></tr></thead>
          <tbody>
            {data.roles.map((r) => (
              <tr key={r.id}>
                <td>{r.title}</td>
                <td>{r.company_name}</td>
                <td>{r.suggested_by || "—"}</td>
                <td><button className="secondary-btn" onClick={() => run(() => approveRole(r.id), `Approved ${r.title}.`)}>Approve</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h3 style={{ marginTop: "2rem" }}>Possible duplicate companies</h3>
      {pairs.length === 0 ? <p>No similar company names found.</p> : (
        <table className="admin-table">
          <thead><tr><th>Similarity</th><th>Company A</th><th>Company B</th><th>Actions</th></tr></thead>
          <tbody>
            {pairs.map((p) => (
              <tr key={`${p.a.id}-${p.b.id}`}>
                <td>{p.score}%</td>
                <td>{p.a.name} <small>({p.a.experience_count} exp{p.a.status === "pending" ? ", pending" : ""})</small></td>
                <td>{p.b.name} <small>({p.b.experience_count} exp{p.b.status === "pending" ? ", pending" : ""})</small></td>
                <td style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
                  <button className="secondary-btn" onClick={() => handleMerge(p.b, p.a)}>Keep A, merge B</button>
                  <button className="secondary-btn" onClick={() => handleMerge(p.a, p.b)}>Keep B, merge A</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
