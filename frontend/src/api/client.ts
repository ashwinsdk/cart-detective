const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function handleResponse<T>(res: Response, fallbackMessage: string): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText || `Status ${res.status}`;
    try {
      const data = await res.json();
      if (data && data.detail) {
        detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      // Fallback to HTTP status text
    }
    throw new Error(`${fallbackMessage}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export interface SearchPayload {
  product_type: string;
  budget_min?: number | null;
  budget_max?: number | null;
  currency?: string;
  color_preferences?: string[];
  size_fit_gender?: string | null;
  must_haves?: string | null;
  deal_breakers?: string | null;
  brands_included?: string[];
  brands_excluded?: string[];
  marketplaces?: string[];
}

export async function createSearch(payload: SearchPayload) {
  const res = await fetch(`${API_BASE}/api/searches`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<{ search_id: string; run_id: string; status: string; created_at: string }>(
    res,
    "Failed to create search"
  );
}

export async function listSearches<T = unknown[]>(limit = 20, offset = 0): Promise<T> {
  const res = await fetch(`${API_BASE}/api/searches?limit=${limit}&offset=${offset}`);
  return handleResponse<T>(res, "Failed to list searches");
}

export async function getRun<T = unknown>(runId: string): Promise<T> {
  const res = await fetch(`${API_BASE}/api/runs/${runId}`);
  return handleResponse<T>(res, "Failed to fetch run");
}

export async function getRunProducts<T = unknown[]>(runId: string): Promise<T> {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/products`);
  return handleResponse<T>(res, "Failed to fetch products");
}

export async function getWishlist<T = unknown[]>(): Promise<T> {
  const res = await fetch(`${API_BASE}/api/wishlist`);
  return handleResponse<T>(res, "Failed to fetch wishlist");
}

export async function addToWishlist<T = { id: string; status: string }>(productId: string, notes?: string): Promise<T> {
  const res = await fetch(`${API_BASE}/api/wishlist`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_id: productId, notes }),
  });
  return handleResponse<T>(res, "Failed to add to wishlist");
}

export async function removeFromWishlist<T = { status: string }>(itemId: string): Promise<T> {
  const res = await fetch(`${API_BASE}/api/wishlist/${itemId}`, {
    method: "DELETE",
  });
  return handleResponse<T>(res, "Failed to remove from wishlist");
}

export async function listPurchases<T = unknown[]>(): Promise<T> {
  const res = await fetch(`${API_BASE}/api/purchases`);
  return handleResponse<T>(res, "Failed to list purchases");
}

export async function recordPurchase<T = { id: string; status: string }>(payload: {
  product_id: string;
  price_paid: number;
  currency?: string;
  store?: string;
  notes?: string;
}): Promise<T> {
  const res = await fetch(`${API_BASE}/api/purchases`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<T>(res, "Failed to record purchase");
}

export async function getSettings<T = { scoring_weights?: Record<string, number>; provider_status?: Record<string, unknown> }>(): Promise<T> {
  const res = await fetch(`${API_BASE}/api/settings`);
  return handleResponse<T>(res, "Failed to fetch settings");
}

export async function updateSettings<T = { status: string }>(settingsData: Record<string, unknown>): Promise<T> {
  const res = await fetch(`${API_BASE}/api/settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ settings: settingsData }),
  });
  return handleResponse<T>(res, "Failed to update settings");
}
