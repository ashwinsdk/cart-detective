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
