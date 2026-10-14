import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { deleteMyAccount } from "../api/authApi";
import PageHeader from "../components/common/PageHeader";

export default function Account() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [confirming, setConfirming] = useState(false);
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleDelete(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await deleteMyAccount(password);
      logout();
      navigate("/login");
    } catch (err) {
      setError(err.response?.data?.error || "Could not delete your account.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <PageHeader title="My Account" subtitle="Your profile and account settings" />

      <div className="stats-panel">
        <p><strong>Name:</strong> {user.name}</p>
        <p><strong>Email:</strong> {user.email}</p>
        <p><strong>Role:</strong> {user.role}</p>
        <p><strong>College:</strong> {user.college_name || "—"}</p>
      </div>

      <div className="stats-panel" style={{ marginTop: "1.5rem" }}>
        <h3>Delete account</h3>
        <p className="hint">
          This permanently deletes your account, bookmarks and helpful votes.
          {user.role === "alumni" && " Experiences you shared will stay on the platform, shown as “Anonymous alumnus”."}
        </p>

        {!confirming ? (
          <button type="button" className="danger-btn" onClick={() => setConfirming(true)}>Delete my account</button>
        ) : (
          <form onSubmit={handleDelete}>
            {error && <p className="form-error">{error}</p>}
            <label>
              Enter your password to confirm
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </label>
            <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.75rem" }}>
              <button type="submit" className="danger-btn" disabled={busy}>{busy ? "Deleting..." : "Permanently delete"}</button>
              <button type="button" className="secondary-btn" onClick={() => { setConfirming(false); setPassword(""); setError(""); }}>Cancel</button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
