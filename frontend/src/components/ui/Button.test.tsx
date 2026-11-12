import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { Button } from "./Button";

describe("Button component", () => {
  it("renders with correct text and primary styling", () => {
    render(<Button>Submit Search</Button>);
    const btn = screen.getByRole("button", { name: "Submit Search" });
    expect(btn).toBeInTheDocument();
    expect(btn).toHaveClass("bg-neutral-900");
  });

  it("handles disabled state correctly", () => {
    render(<Button disabled>Disabled Action</Button>);
    const btn = screen.getByRole("button", { name: "Disabled Action" });
    expect(btn).toBeDisabled();
    expect(btn).toHaveClass("disabled:opacity-50");
  });
});
