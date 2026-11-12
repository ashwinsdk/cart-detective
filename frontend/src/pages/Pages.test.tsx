import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect, vi } from "vitest";
import axe from "axe-core";
import { HistoryPage } from "./HistoryPage";
import { WishlistPage } from "./WishlistPage";
import { BoughtPage } from "./BoughtPage";
import { SettingsPage } from "./SettingsPage";

// Mock the API client
vi.mock("../api/client", () => ({
  listSearches: vi.fn().mockResolvedValue([]),
  getWishlist: vi.fn().mockResolvedValue([]),
  listPurchases: vi.fn().mockResolvedValue([]),
  getSettings: vi.fn().mockResolvedValue({
    scoring_weights: { budget_fit: 0.2 },
    provider_status: { groq_configured: false },
  }),
}));

describe("Application Views and Empty States", () => {
  it("renders HistoryPage empty state when no searches exist", async () => {
    const { container } = render(
      <BrowserRouter>
        <HistoryPage />
      </BrowserRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("No past searches found.")).toBeInTheDocument();
    });
    const results = await axe.run(container);
    expect(results.violations).toEqual([]);
  });

  it("renders WishlistPage empty state when no items saved", async () => {
    const { container } = render(
      <BrowserRouter>
        <WishlistPage />
      </BrowserRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("Your wishlist is currently empty.")).toBeInTheDocument();
    });
    const results = await axe.run(container);
    expect(results.violations).toEqual([]);
  });

  it("renders BoughtPage empty state when no items recorded", async () => {
    const { container } = render(
      <BrowserRouter>
        <BoughtPage />
      </BrowserRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("No purchases recorded yet.")).toBeInTheDocument();
    });
    const results = await axe.run(container);
    expect(results.violations).toEqual([]);
  });

  it("renders SettingsPage and passes axe audit", async () => {
    const { container } = render(
      <BrowserRouter>
        <SettingsPage />
      </BrowserRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("Application Settings")).toBeInTheDocument();
    });
    const results = await axe.run(container);
    expect(results.violations).toEqual([]);
  });
});

