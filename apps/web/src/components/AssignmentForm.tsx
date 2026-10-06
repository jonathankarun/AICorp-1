import { FormEvent, useMemo, useState } from "react";
import { ApiValidationError, createAssignment } from "../api";
import type { AssignmentCreate, AssignmentResponse } from "../types";

const EMPTY_FORM = {
  problem: "",
  department_id: "dept-fixture-001",
  intended_result: "",
  required_sections: "problem_summary, findings, recommendation, implementation_steps",
  audience: "",
  constraints: "",
};

type Props = {
  onCreated: (assignment: AssignmentResponse) => void;
};

export function AssignmentForm({ onCreated }: Props) {
  const [form, setForm] = useState(EMPTY_FORM);
  const [pending, setPending] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [generalError, setGeneralError] = useState("");

  const clientErrors = useMemo(() => {
    const next: Record<string, string> = {};
    if (!form.problem.trim()) next.problem = "Problem is required.";
    if (!form.department_id.trim()) next.department_id = "Department is required.";
    if (!form.intended_result.trim()) next.intended_result = "Required output is required.";
    if (!form.required_sections.trim()) next.required_sections = "At least one report section is required.";
    if (!form.audience.trim()) next.audience = "Audience is required.";
    return next;
  }, [form]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setGeneralError("");

    if (Object.keys(clientErrors).length > 0) {
      setErrors(clientErrors);
      return;
    }

    const payload: AssignmentCreate = {
      problem: form.problem,
      department_id: form.department_id,
      intended_result: form.intended_result,
      required_sections: form.required_sections
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      audience: form.audience,
      constraints: form.constraints
        .split("\n")
        .map((item) => item.trim())
        .filter(Boolean),
      selected_document_version_ids: ["doc-fixture-v1"],
      request_type: "problem",
    };

    setPending(true);
    setErrors({});

    try {
      const created = await createAssignment(payload);
      onCreated(created);
      setForm(EMPTY_FORM);
    } catch (error) {
      if (error instanceof ApiValidationError) {
        const serverErrors: Record<string, string> = {};
        error.fields.forEach((field) => {
          serverErrors[field.field] = field.message;
        });
        setErrors(serverErrors);
      } else {
        setGeneralError("Could not reach the API. Check that FastAPI is running.");
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card" aria-label="assignment form">
      <h2>1. Create an assignment</h2>
      <p className="muted">Week 1 synthetic demo — not a real City record.</p>

      <label>
        Problem
        <textarea
          value={form.problem}
          onChange={(e) => setForm({ ...form, problem: e.target.value })}
          placeholder="Describe the consulting need"
          rows={4}
        />
      </label>
      {errors.problem && <div className="field-error">{errors.problem}</div>}

      <label>
        Department ID
        <input
          value={form.department_id}
          onChange={(e) => setForm({ ...form, department_id: e.target.value })}
        />
      </label>
      {errors.department_id && <div className="field-error">{errors.department_id}</div>}

      <label>
        Required output / intended result
        <textarea
          value={form.intended_result}
          onChange={(e) => setForm({ ...form, intended_result: e.target.value })}
          placeholder="Describe what the finished consulting deliverable should accomplish"
          rows={2}
        />
      </label>
      {errors.intended_result && <div className="field-error">{errors.intended_result}</div>}

      <label>
        Required report sections (comma-separated)
        <input
          value={form.required_sections}
          onChange={(e) => setForm({ ...form, required_sections: e.target.value })}
        />
      </label>
      {errors.required_sections && <div className="field-error">{errors.required_sections}</div>}

      <label>
        Audience
        <input
          value={form.audience}
          onChange={(e) => setForm({ ...form, audience: e.target.value })}
          placeholder="City department manager"
        />
      </label>
      {errors.audience && <div className="field-error">{errors.audience}</div>}

      <label>
        Constraints (one per line)
        <textarea
          value={form.constraints}
          onChange={(e) => setForm({ ...form, constraints: e.target.value })}
          placeholder={"Use a six-week implementation horizon\nUse only the synthetic fixture evidence"}
          rows={3}
        />
      </label>

      {generalError && <div className="field-error">{generalError}</div>}

      <button type="submit" disabled={pending}>
        {pending ? "Submitting…" : "Submit assignment"}
      </button>
    </form>
  );
}
