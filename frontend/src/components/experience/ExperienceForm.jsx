import { useState, useEffect } from "react";
import SearchableSelect from "../common/SearchableSelect";
import { fetchCompanies, fetchCompanyDetail, submitCompany, submitRole } from "../../api/companyApi";
import { fetchColleges } from "../../api/collegeApi";

const CATEGORIES = ["Aptitude", "Coding", "DSA", "OOP", "DBMS", "Operating Systems",
  "Computer Networks", "Python", "Java", "JavaScript", "HR", "Behavioral", "Other"];
const DIFFICULTIES = ["easy", "medium", "hard"];

const emptyQuestion = () => ({ question_text: "", category: "", topic: "", difficulty: "medium" });
const emptyRound = (n) => ({ round_number: n, round_type: "", description: "", difficulty: "medium", questions: [emptyQuestion()] });

function blankForm(defaultCollegeId) {
  return {
    company_id: "",
    role_id: "",
    college_id: defaultCollegeId || "",
    branch: "",
    graduation_year: "",
    placement_year: "",
    package: "",
    rounds: [emptyRound(1)],
    overall_experience: "",
    preparation_tips: "",
    additional_advice: "",
    selected: false,
  };
}

/**
 * Reusable structured form for both "submit new experience" and "edit experience".
 * Pass `initialData` (already in the payload shape) to pre-fill for editing.
 */
export default function ExperienceForm({ initialData, defaultCollegeId, onSubmit, submitLabel = "Submit Experience" }) {
  const [step, setStep] = useState(1);
  const [form, setForm] = useState(initialData || blankForm(defaultCollegeId));
  const [companies, setCompanies] = useState([]);
  const [roles, setRoles] = useState([]);
  const [colleges, setColleges] = useState([]);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchCompanies().then((res) => setCompanies(res.data));
    fetchColleges().then((res) => setColleges(res.data));
  }, []);

  // load roles whenever the selected company changes
  useEffect(() => {
    if (!form.company_id) { setRoles([]); return; }
    fetchCompanyDetail(form.company_id).then((res) => setRoles(res.data.roles));
  }, [form.company_id]);

  // "Add new" flow for a company/role that isn't listed. The server fuzzy-matches
  // the name; if something similar exists we ask "Did you mean ...?" first.
  const [suggestion, setSuggestion] = useState(null); // { kind, typed, matches }

  async function reloadCompanies() {
    const res = await fetchCompanies();
    setCompanies(res.data);
  }

  async function addCompany(name, confirmNew = false) {
    setError("");
    try {
      const res = await submitCompany(name, confirmNew);
      if (res.data.needs_confirmation) {
        setSuggestion({ kind: "company", typed: name, matches: res.data.matches });
        return;
      }
      setSuggestion(null);
      await reloadCompanies();
      setForm((f) => ({ ...f, company_id: String(res.data.company.id), role_id: "" }));
    } catch (err) {
      setError(err.response?.data?.error || "Could not add that company.");
    }
  }

  async function addRole(title, confirmNew = false) {
    setError("");
    try {
      const res = await submitRole(form.company_id, title, confirmNew);
      if (res.data.needs_confirmation) {
        setSuggestion({ kind: "role", typed: title, matches: res.data.matches });
        return;
      }
      setSuggestion(null);
      const detail = await fetchCompanyDetail(form.company_id);
      setRoles(detail.data.roles);
      setForm((f) => ({ ...f, role_id: String(res.data.role.id) }));
    } catch (err) {
      setError(err.response?.data?.error || "Could not add that role.");
    }
  }

  function useExisting(match) {
    if (suggestion.kind === "company") {
      setForm((f) => ({ ...f, company_id: String(match.id), role_id: "" }));
    } else {
      setForm((f) => ({ ...f, role_id: String(match.id) }));
    }
    setSuggestion(null);
  }

  function updateField(field, value) {
    setForm({ ...form, [field]: value });
  }

  function updateRound(index, field, value) {
    const rounds = [...form.rounds];
    rounds[index] = { ...rounds[index], [field]: value };
    setForm({ ...form, rounds });
  }

  function addRound() {
    setForm({ ...form, rounds: [...form.rounds, emptyRound(form.rounds.length + 1)] });
  }

  function removeRound(index) {
    const rounds = form.rounds.filter((_, i) => i !== index)
      .map((r, i) => ({ ...r, round_number: i + 1 }));
    setForm({ ...form, rounds });
  }

  function updateQuestion(roundIndex, qIndex, field, value) {
    const rounds = [...form.rounds];
    const questions = [...rounds[roundIndex].questions];
    questions[qIndex] = { ...questions[qIndex], [field]: value };
    rounds[roundIndex] = { ...rounds[roundIndex], questions };
    setForm({ ...form, rounds });
  }

  function addQuestion(roundIndex) {
    const rounds = [...form.rounds];
    rounds[roundIndex] = { ...rounds[roundIndex], questions: [...rounds[roundIndex].questions, emptyQuestion()] };
    setForm({ ...form, rounds });
  }

  function removeQuestion(roundIndex, qIndex) {
    const rounds = [...form.rounds];
    rounds[roundIndex] = { ...rounds[roundIndex], questions: rounds[roundIndex].questions.filter((_, i) => i !== qIndex) };
    setForm({ ...form, rounds });
  }

  function validateStep1() {
    return form.company_id && form.role_id && form.college_id && form.placement_year;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (!form.company_id || !form.role_id || !form.college_id) {
      setError("Please pick the company, role and college from the suggestion lists.");
      setStep(1);
      return;
    }
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        company_id: Number(form.company_id),
        role_id: Number(form.role_id),
        college_id: Number(form.college_id),
        graduation_year: form.graduation_year ? Number(form.graduation_year) : undefined,
        placement_year: Number(form.placement_year),
        rounds: form.rounds.map((r) => ({
          ...r,
          questions: r.questions.filter((q) => q.question_text.trim() !== ""),
        })),
      };
      await onSubmit(payload);
    } catch (err) {
      const details = err.response?.data?.details;
      setError(details ? JSON.stringify(details) : err.response?.data?.error || "Something went wrong.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="experience-form">
      {error && <p className="form-error">{error}</p>}

      <div className="step-indicator">
        <span className={step === 1 ? "active" : ""}>1. Basic Info</span>
        <span className={step === 2 ? "active" : ""}>2. Recruitment Process</span>
        <span className={step === 3 ? "active" : ""}>3. Final Experience</span>
      </div>

      {step === 1 && (
        <fieldset>
          <legend>Basic Information</legend>
          <label>Company
            <SearchableSelect
              options={companies.map((c) => ({ value: c.id, label: c.name }))}
              value={String(form.company_id ?? "")}
              onChange={(v) => setForm((f) => ({ ...f, company_id: v, role_id: "" }))}
              placeholder="Type to search company..."
              onAddNew={(name) => addCompany(name)}
              required
            />
          </label>
          <label>Job Role
            <SearchableSelect
              options={roles.map((r) => ({ value: r.id, label: r.title }))}
              value={String(form.role_id ?? "")}
              onChange={(v) => updateField("role_id", v)}
              placeholder="Type to search role..."
              disabled={!form.company_id}
              onAddNew={(title) => addRole(title)}
              required
            />
          </label>
          {form.company_id && roles.length === 0 && (
            <p className="hint">No roles listed for this company yet — type one above and choose “Add new”.</p>
          )}
          {(companies.find((c) => String(c.id) === String(form.company_id))?.status === "pending"
            || roles.find((r) => String(r.id) === String(form.role_id))?.status === "pending") && (
            <p className="hint"><span className="badge-pending">Pending review</span> Your new company/role is awaiting admin approval. You can submit your experience now; it goes live once they approve.</p>
          )}
          {suggestion && (
            <div className="suggestion-box">
              <p>
                Did you mean{" "}
                {suggestion.matches.map((m, i) => (
                  <strong key={m.id}>{i > 0 ? ", " : ""}{m.name}</strong>
                ))}
                ? You typed “{suggestion.typed}”.
              </p>
              <div className="suggestion-actions">
                {suggestion.matches.map((m) => (
                  <button type="button" key={m.id} className="secondary-btn" onClick={() => useExisting(m)}>
                    Yes, use {m.name}
                  </button>
                ))}
                <button
                  type="button"
                  className="secondary-btn"
                  onClick={() => (suggestion.kind === "company"
                    ? addCompany(suggestion.typed, true)
                    : addRole(suggestion.typed, true))}
                >
                  No, add “{suggestion.typed}” as new
                </button>
                <button type="button" className="secondary-btn" onClick={() => setSuggestion(null)}>Cancel</button>
              </div>
            </div>
          )}
          <label>College
            <SearchableSelect
              options={colleges.map((c) => ({ value: c.id, label: c.name }))}
              value={String(form.college_id ?? "")}
              onChange={(v) => updateField("college_id", v)}
              placeholder="Type to search college..."
              required
            />
          </label>
          <label>Branch
            <input type="text" value={form.branch} onChange={(e) => updateField("branch", e.target.value)} placeholder="e.g. CSE" />
          </label>
          <label>Graduation Year
            <input type="number" value={form.graduation_year} onChange={(e) => updateField("graduation_year", e.target.value)} placeholder="e.g. 2026" />
          </label>
          <label>Placement Year
            <input type="number" value={form.placement_year} onChange={(e) => updateField("placement_year", e.target.value)} required placeholder="e.g. 2026" />
          </label>
          <label>Package (optional)
            <input type="text" value={form.package} onChange={(e) => updateField("package", e.target.value)} placeholder="e.g. 12 LPA" />
          </label>
          <div className="step-nav">
            <button type="button" onClick={() => setStep(2)} disabled={!validateStep1()}>Next: Recruitment Process</button>
          </div>
        </fieldset>
      )}

      {step === 2 && (
        <fieldset>
          <legend>Recruitment Process</legend>
          {form.rounds.map((round, ri) => (
            <div key={ri} className="round-block">
              <div className="round-header">
                <h4>Round {round.round_number}</h4>
                {form.rounds.length > 1 && (
                  <button type="button" onClick={() => removeRound(ri)} className="danger-btn small">Remove round</button>
                )}
              </div>
              <label>Round Type
                <input type="text" value={round.round_type} onChange={(e) => updateRound(ri, "round_type", e.target.value)}
                  placeholder="e.g. Aptitude, Coding, Technical, HR" required />
              </label>
              <label>Round Description
                <textarea value={round.description} onChange={(e) => updateRound(ri, "description", e.target.value)}
                  placeholder="What happened in this round?" rows={2} />
              </label>
              <label>Difficulty
                <select value={round.difficulty} onChange={(e) => updateRound(ri, "difficulty", e.target.value)}>
                  {DIFFICULTIES.map((d) => <option key={d} value={d}>{d}</option>)}
                </select>
              </label>

              <h5>Questions asked in this round</h5>
              {round.questions.map((q, qi) => (
                <div key={qi} className="question-block">
                  <input type="text" value={q.question_text}
                    onChange={(e) => updateQuestion(ri, qi, "question_text", e.target.value)}
                    placeholder="Question text" />
                  <select value={q.category} onChange={(e) => updateQuestion(ri, qi, "category", e.target.value)}>
                    <option value="">Category</option>
                    {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
                  </select>
                  <input type="text" value={q.topic} onChange={(e) => updateQuestion(ri, qi, "topic", e.target.value)}
                    placeholder="Topic (e.g. SQL JOIN)" />
                  <select value={q.difficulty} onChange={(e) => updateQuestion(ri, qi, "difficulty", e.target.value)}>
                    {DIFFICULTIES.map((d) => <option key={d} value={d}>{d}</option>)}
                  </select>
                  {round.questions.length > 1 && (
                    <button type="button" onClick={() => removeQuestion(ri, qi)} className="danger-btn small">&times;</button>
                  )}
                </div>
              ))}
              <button type="button" onClick={() => addQuestion(ri)} className="secondary-btn">+ Add question</button>
            </div>
          ))}
          <button type="button" onClick={addRound} className="secondary-btn">+ Add another round</button>

          <div className="step-nav">
            <button type="button" onClick={() => setStep(1)}>Back</button>
            <button type="button" onClick={() => setStep(3)}>Next: Final Experience</button>
          </div>
        </fieldset>
      )}

      {step === 3 && (
        <fieldset>
          <legend>Final Experience</legend>
          <label>Overall Experience
            <textarea value={form.overall_experience} onChange={(e) => updateField("overall_experience", e.target.value)} rows={4} />
          </label>
          <label>Preparation Tips
            <textarea value={form.preparation_tips} onChange={(e) => updateField("preparation_tips", e.target.value)} rows={3} />
          </label>
          <label>Additional Advice
            <textarea value={form.additional_advice} onChange={(e) => updateField("additional_advice", e.target.value)} rows={3} />
          </label>
          <label className="checkbox-label">
            <input type="checkbox" checked={form.selected} onChange={(e) => updateField("selected", e.target.checked)} />
            I was selected
          </label>

          <div className="step-nav">
            <button type="button" onClick={() => setStep(2)}>Back</button>
            <button type="submit" disabled={submitting}>{submitting ? "Submitting..." : submitLabel}</button>
          </div>
        </fieldset>
      )}
    </form>
  );
}
