import { render, screen } from "@testing-library/react";
import { BrowserRouter, MemoryRouter } from "react-router-dom";
import { describe, it, expect } from "vitest";
import { SearchPage } from "./SearchPage";

describe("SearchPage component", () => {
  it("renders all core query input fields empty by default", () => {
    render(
      <BrowserRouter>
        <SearchPage />
      </BrowserRouter>
    );

    expect(screen.getByText("New Product Investigation")).toBeInTheDocument();
    const productInput = screen.getByPlaceholderText(/e\.g\. riding jacket/);
    expect(productInput).toBeInTheDocument();
    expect((productInput as HTMLInputElement).value).toBe("");
    expect(screen.getByRole("button", { name: /Launch Research Investigation/ })).toBeInTheDocument();
  });

  it("populates fields when reusing a past query from history", () => {
    const pastQuery = {
      product_type: "running shoes",
      budget_max: 5000,
      budget_min: 2000,
      currency: "INR",
      color_preferences: ["navy", "white"],
      brands_included: ["Asics", "Nike"],
    };

    render(
      <MemoryRouter initialEntries={[{ pathname: "/", state: { reuseQuery: pastQuery } }]}>
        <SearchPage />
      </MemoryRouter>
    );

    expect(screen.getByText(/Editing previous query from history/)).toBeInTheDocument();
    expect((screen.getByLabelText(/Product Category/i) as HTMLInputElement).value).toBe("running shoes");
    expect((screen.getByLabelText(/Max Budget/i) as HTMLInputElement).value).toBe("5000");
  });
});
