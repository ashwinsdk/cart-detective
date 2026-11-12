import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "./App";

describe("App smoke test", () => {
  it("renders Cart Detective navigation header", () => {
    render(<App />);
    expect(screen.getByText("Cart Detective")).toBeInTheDocument();
    expect(screen.getByText("Search")).toBeInTheDocument();
    expect(screen.getByText("History")).toBeInTheDocument();
  });
});
