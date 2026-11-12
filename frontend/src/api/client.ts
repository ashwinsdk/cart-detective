const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

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
  if (!res.ok) {
    throw new Error(`Failed to create search: ${res.statusText}`);
  }
  return res.json();
}

export async function listSearches(limit = 20, offset = 0) {
  const res = await fetch(`${API_BASE}/api/searches?limit=${limit}&offset=${offset}`);
  if (!res.ok) {
    throw new Error(`Failed to list searches: ${res.statusText}`);
  }
  return res.json();
}

export async function getRun(runId: string) {
  const res = await fetch(`${API_BASE}/api/runs/${runId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch run: ${res.statusText}`);
  }
  return res.json();
}

export async function getRunProducts(runId: string) {
  const res = await fetch(`${API_BASE}/api/runs/${runId}/products`);
  if (!res.ok) {
    throw new Error(`Failed to fetch products: ${res.statusText}`);
  }
  return res.json();
}

export async function getWishlist() {
  const res = await fetch(`${API_BASE}/api/wishlist`);
  if (!res.ok) {
    throw new Error(`Failed to fetch wishlist: ${res.statusText}`);
  }
  return res.json();
}

export async function addToWishlist(productId: string, notes?: string) {
  const res = await fetch(`${API_BASE}/api/wishlist`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ product_id: productId, notes }),
  });
  if (!res.ok) {
    throw new Error(`Failed to add to wishlist: ${res.statusText}`);
  }
  return res.json();
}

export async function removeFromWishlist(itemId: string) {
  const res = await fetch(`${API_BASE}/api/wishlist/${itemId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    throw new Error(`Failed to remove from wishlist: ${res.statusText}`);
  }
  return res.json();
}

export async function listPurchases() {
  const res = await fetch(`${API_BASE}/api/purchases`);
  if (!res.ok) {
    throw new Error(`Failed to list purchases: ${res.statusText}`);
  }
  return res.json();
}

export async function recordPurchase(payload: {
  product_id: string;
  price_paid: number;
  currency?: string;
  store?: string;
  notes?: string;
}) {
  const res = await fetch(`${API_BASE}/api/purchases`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(`Failed to record purchase: ${res.statusText}`);
  }
  return res.json();
}

export async function getSettings() {
  const res = await fetch(`${API_BASE}/api/settings`);
  if (!res.ok) {
    throw new Error(`Failed to fetch settings: ${res.statusText}`);
  }
  return res.json();
}

export async function updateSettings(settingsData: Record<string, unknown>) {
  const res = await fetch(`${API_BASE}/api/settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ settings: settingsData }),
  });
  if (!res.ok) {
    throw new Error(`Failed to update settings: ${res.statusText}`);
  }
  return res.json();
}
