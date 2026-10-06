import type { FormEvent } from "react";
import type { Assignment, Document } from "../App";

type Props = {
  form: Assignment;
  docs: Document[];
  busy: boolean;
  onChange: (form: Assignment) => void;
  onSubmit: (event: FormEvent) => void;
};

export function AssignmentForm({ form, docs, busy, onChange, onSubmit }: Props) {
  return (
            <form onSubmit={onSubmit} aria-label="assignment form">
              <fieldset disabled={busy} className="assignment-fields">
              <label>
                Problem
                <textarea
                  aria-label="Problem"
                  required
                  value={form.problem}
                  onChange={(e) =>
                    onChange({ ...form, problem: e.target.value })
                  }
                />
              </label>
              <label>
                Intended result
                <input
                  required
                  value={form.intended_result}
                  onChange={(e) =>
                    onChange({ ...form, intended_result: e.target.value })
                  }
                />
              </label>
              <label>
                Audience
                <input
                  value={form.audience}
                  onChange={(e) =>
                    onChange({ ...form, audience: e.target.value })
                  }
                />
              </label>
              <label>
                Constraints (one per line)
                <textarea
                  aria-label="Constraints (one per line)"
                  value={form.constraints.join("\n")}
                  onChange={(e) =>
                    onChange({
                      ...form,
                      constraints: e.target.value.split("\n"),
                    })
                  }
                />
              </label>
              <label>
                Required report sections (comma-separated)
                <input required value={form.required_sections.join(",")}
                  onChange={(e) => onChange({ ...form, required_sections: e.target.value.split(",") })} />
              </label>
              <label>
                Request type
                <select value={form.request_type} onChange={(e) => onChange({ ...form, request_type: e.target.value as Assignment["request_type"] })}>
                  <option value="problem">Problem</option><option value="RFP">RFP</option><option value="RFQ">RFQ</option>
                </select>
              </label>
              <p className="muted">
                Department: Fictional department. Choose ready sources below
                before saving.
              </p>
              <fieldset>
                <legend>Ready sources</legend>
                {docs.length === 0 ? (
                  <p>No ready sources yet.</p>
                ) : (
                  docs.map((d) => (
                    <label className="check" key={d.document_version_id}>
                      <input
                        type="checkbox"
                        checked={form.selected_document_version_ids.includes(
                          d.document_version_id,
                        )}
                        onChange={(e) =>
                          onChange({
                            ...form,
                            selected_document_version_ids: e.target.checked
                              ? [
                                  ...form.selected_document_version_ids,
                                  d.document_version_id,
                                ]
                              : form.selected_document_version_ids.filter(
                                  (id) => id !== d.document_version_id,
                                ),
                          })
                        }
                      />
                      <span>
                        {d.title} · v{d.version}
                        <small>
                          {d.external_model_allowed
                            ? "Eligible for model context"
                            : "Read-only evidence; external model use not approved"}
                        </small>
                      </span>
                    </label>
                  ))
                )}
              </fieldset>
              <button disabled={busy}>
                {busy ? "Working…" : "Save assignment"}
              </button>
              {form.assignment_id && (
                <p className="muted">Saved ID: {form.assignment_id}</p>
              )}
              </fieldset>
            </form>
  );
}
