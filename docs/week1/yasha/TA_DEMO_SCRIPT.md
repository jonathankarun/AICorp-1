# Yasha Week 1 — short TA demo script

“My subsystem is the application and integration boundary. For Week 1 I built the React/TypeScript client and FastAPI API. The browser submits a typed assignment to `/api/v1/assignments`, FastAPI validates it again with Pydantic, generates the assignment ID, and stores it through a replaceable in-memory repository.”

“The frontend and backend both validate input. Browser validation is for usability; server validation is the real enforcement point because a caller can bypass the UI.”

“The mock report uses the same Week 1 field shape as Jai's engine: report sections use `name`, `content`, and citation IDs; citations point to evidence chunk IDs. The UI resolves those IDs to the same synthetic source details Jai currently uses.”

“For the success case, a complete assignment returns HTTP 201 and a generated ID. For the failure case, a whitespace-only problem returns HTTP 422 and creates nothing. I can prove both with `pytest`.”

“The main limitation is persistence. Restarting FastAPI clears assignments. Week 2 replaces this repository with Jonny's persistence boundary. Jonny currently uses UUID department IDs while Jai uses fixture source-key strings, and the repository documents that mapping as an unresolved team contract decision rather than silently converting it.”
