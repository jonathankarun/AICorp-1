import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { MOCK_EVIDENCE, MOCK_REPORT } from "../mockReport";
import { ReportView } from "./ReportView";

describe("ReportView", () => {
  it("renders Jai-compatible report fields and opens source details", async () => {
    const user = userEvent.setup();
    render(<ReportView report={MOCK_REPORT} evidence={MOCK_EVIDENCE} />);

    expect(screen.getByText("Problem Summary")).toBeInTheDocument();
    expect(screen.getByText("Findings")).toBeInTheDocument();
    expect(screen.getByText("Recommendation")).toBeInTheDocument();
    expect(screen.getByText("Implementation Steps")).toBeInTheDocument();
    expect(screen.getByText("Assumptions")).toBeInTheDocument();
    expect(screen.getByText("Missing information")).toBeInTheDocument();
    expect(screen.getByText("DRAFT")).toBeInTheDocument();

    await user.click(screen.getAllByRole("button", { name: /cite-001/ })[0]);
    expect(screen.getByLabelText("source details")).toHaveTextContent(
      "Fictional Process Improvement Project",
    );
  });
});
