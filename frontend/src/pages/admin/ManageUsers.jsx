import { useState, useEffect } from "react";
import { fetchUsers, deleteUser } from "../../api/adminApi";

export default function ManageUsers() {
  const [users, setUsers] = useState([]);
  const [role, setRole] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  function load() {
    setLoading(true);
    fetchUsers({ role: role || undefined, q: search || undefined })
      .then((res) => setUsers(res.data))
      .catch(() => setError("Could not load users."))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [role]);

  async function handleDelete(u) {
    const note = u.experience_count > 0
      ? ` Their ${u.experience_count} experience(s) will stay on the platform as "Anonymous alumnus".`
      : "";
    if (!window.confirm(`Delete ${u.name} (${u.email})? This cannot be undone.${note}`)) return;
    setError("");
    setMessage("");
    try {
      await deleteUser(u.id);
      setMessage(`Deleted ${u.name}.`);
      load();
    } catch (err) {
      setError(err.response?.data?.error || "Could not delete user.");
    }
  }

  return (
    <div className="page">
      <h2>Manage Users</h2>
      {message && <p className="hint">{message}</p>}
      {error && <p className="form-error">{error}</p>}

      <form className="filter-bar" onSubmit={(e) => { e.preventDefault(); load(); }}>
        <label className="filter-field">
          <span>Role</span>
          <select value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="">All</option>
            <option value="student">Student</option>
            <option value="alumni">Alumni</option>
            <option value="admin">Admin</option>
          </select>
        </label>
        <label className="filter-field">
          <span>Search</span>
          <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Name or email" />
        </label>
        <button type="submit" className="secondary-btn">Search</button>
      </form>

      {loading ? (
        <p>Loading...</p>
      ) : users.length === 0 ? (
        <p>No users found.</p>
      ) : (
        <table className="admin-table">
          <thead>
            <tr><th>Name</th><th>Email</th><th>Role</th><th>College</th><th>Experiences</th><th>Actions</th></tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.name}</td>
                <td>{u.email}</td>
                <td>{u.role}</td>
                <td>{u.college_name || "—"}</td>
                <td>{u.experience_count}</td>
                <td>
                  {u.role !== "admin" && (
                    <button onClick={() => handleDelete(u)} className="danger-btn small">Delete</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
