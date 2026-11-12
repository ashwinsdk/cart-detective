import { render, screen, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { describe, it, expect, vi } from "vitest";
import { HistoryPage } from "./HistoryPage";
import { WishlistPage } from "./WishlistPage";
import { BoughtPage } from "./BoughtPage";
import { SettingsPage } from "./SettingsPage";

// Mock the API client
vi.mock("../api/client", () => ({
  listSearches: vi.fn().mockResolvedValue([
    {
      id: "search-1",
      created_at: "2026-11-12T00:00:00Z",
      product_type: "riding jacket",
      currency: "INR",
      color_preferences: ["black"],
      latest_status: "completed",
    },
  ]),
  getWishlist: vi.fn().mockResolvedValue([]),
  listPurchases: vi.fn().mockResolvedValue([]),
  getSettings: vi.fn().mockResolvedValue({
    scoring_weights: { budget_fit: 0.2 },
    provider_status: { groq_configured: false },
  }),
}));

describe("Application Views", () => {
  it("renders HistoryPage title", async () => {
    render(
      <BrowserRouter>
        <HistoryPage />
      </BrowserRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("Search History")).toBeInTheDocument();
    });
  });

  it("renders WishlistPage title", async () => {
    render(
      <BrowserRouter>
        <WishlistPage />
      </BrowserRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("Saved Wishlist")).toBeInTheDocument();
    });
  });

  it("renders BoughtPage title", async () => {
    render(
      <BrowserRouter>
        <BoughtPage />
      </BrowserRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("Purchased Products")).toBeInTheDocument();
    });
  });

  it("renders SettingsPage title", async () => {
    render(
      <BrowserRouter>
        <SettingsPage />
      </BrowserRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("Application Settings")).toBeInTheDocument();
    });
  });
});

