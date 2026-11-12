import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect } from "vitest";
import { SearchPage } from "./SearchPage";

describe("SearchPage component", () => {
  it("renders all core query input fields", () => {
    render(
      <BrowserRouter>
        <SearchPage />
      </BrowserRouter>
    );

    expect(screen.getByText("New Product Investigation")).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/e\.g\. riding jacket/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Launch Research Investigation/ })).toBeInTheDocument();
  });
});
