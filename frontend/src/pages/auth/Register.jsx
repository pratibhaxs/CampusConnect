import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import SearchableSelect from "../../components/common/SearchableSelect";
import { fetchColleges } from "../../api/collegeApi";

const initialForm = {
  name: "",
  email: "",
  password: "",
  role: "student",
  college_id: "",
  branch: "",
  graduation_year: "",
};

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [colleges, setColleges] = useState([]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchColleges()
      .then((res) => setColleges(res.data))
      .catch(() => setError("Could not load colleges list. Is the backend running?"));
  }, []);

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (!form.college_id) { setError("Please pick your college from the list."); return; }
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        college_id: Number(form.college_id),
        graduation_year: form.graduation_year ? Number(form.graduation_year) : undefined,
      };
      const user = await register(payload);
      navigate(user.role === "alumni" ? "/alumni" : "/student");
    } catch (err) {
      const details = err.response?.data?.details;
      const message = details
        ? Object.entries(details).map(([field, msgs]) => `${field}: ${msgs.join(", ")}`).join(" | ")
        : err.response?.data?.error || "Registration failed. Please try again.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <form onSubmit={handleSubmit} className="auth-form">
        <h2>Create an account</h2>
        {error && <p className="form-error">{error}</p>}

        <label>
          I am a
          <select name="role" value={form.role} onChange={handleChange}>
            <option value="student">Student</option>
            <option value="alumni">Alumni</option>
          </select>
        </label>

        <label>
          Full name
          <input type="text" name="name" value={form.name} onChange={handleChange} required />
        </label>

        <label>
          Email
          <input type="email" name="email" value={form.email} onChange={handleChange} required />
        </label>

        <label>
          Password
          <input type="password" name="password" value={form.password} onChange={handleChange} required minLength={6} />
        </label>

        <label>
          College
          <SearchableSelect
            name="college_id"
            options={colleges.map((c) => ({ value: c.id, label: c.name }))}
            value={form.college_id}
            onChange={(v) => setForm({ ...form, college_id: v })}
            placeholder="Type to search your college..."
            required
          />
        </label>

        <label>
          Branch
          <input type="text" name="branch" value={form.branch} onChange={handleChange} placeholder="e.g. CSE" />
        </label>

        <label>
          Graduation year
          <input type="number" name="graduation_year" value={form.graduation_year} onChange={handleChange} placeholder="e.g. 2027" />
        </label>

        <button type="submit" disabled={submitting}>
          {submitting ? "Creating account..." : "Register"}
        </button>

        <p>
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </form>
    </div>
  );
}
