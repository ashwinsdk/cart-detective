import { useEffect, useState, type FormEvent } from "react";
import { CheckCircle, Plus } from "lucide-react";
import { listPurchases, recordPurchase } from "../api/client";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";

interface PurchaseEntry {
  id: string;
  product_id: string;
  price_paid: number;
  currency: string;
  store: string;
  purchase_date: string;
  notes?: string;
  product_title: string;
}

export function BoughtPage() {
  const [purchases, setPurchases] = useState<PurchaseEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);

  const [title, setTitle] = useState("");
  const [price, setPrice] = useState("");
  const [store, setStore] = useState("");
  const [notes, setNotes] = useState("");

  const loadData = () => {
    listPurchases<PurchaseEntry[]>()
      .then(setPurchases)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAddPurchase = async (e: FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !price) return;

    await recordPurchase({
      product_id: `manual-${Date.now()}`,
      price_paid: parseFloat(price),
      currency: "INR",
      store: store.trim() || "Retail Store",
      notes: notes.trim() || undefined,
    });

    setTitle("");
    setPrice("");
    setStore("");
    setNotes("");
    setShowAddForm(false);
    loadData();
  };

  const totalSpent = purchases.reduce((acc, curr) => acc + (curr.price_paid || 0), 0);

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="border-b border-neutral-200 dark:border-neutral-800 pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">
            Purchased Products
          </h1>
          <p className="text-sm text-neutral-500 mt-1">
            Track actual acquisitions, price paid, and fulfillment records.
          </p>
        </div>
        <Button onClick={() => setShowAddForm(!showAddForm)} size="sm">
          <Plus className="w-3.5 h-3.5 mr-1.5" />
          <span>Record Purchase</span>
        </Button>
      </div>

      {/* Summary Banner */}
      <div className="border border-neutral-200 dark:border-neutral-800 rounded-sm p-4 bg-neutral-50 dark:bg-neutral-900/50 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 border border-neutral-300 dark:border-neutral-700 rounded-sm bg-white dark:bg-neutral-900">
            <CheckCircle className="w-4 h-4 text-neutral-700 dark:text-neutral-300" />
          </div>
          <div>
            <div className="text-xs font-mono uppercase tracking-wider text-neutral-500">
              Total Recorded Purchases
            </div>
            <div className="text-base font-mono font-semibold text-neutral-900 dark:text-neutral-100 mt-0.5">
              {purchases.length} Items
            </div>
          </div>
        </div>

        <div className="text-right">
          <div className="text-xs font-mono uppercase tracking-wider text-neutral-500">
            Total Expenditure
          </div>
          <div className="text-base font-mono font-semibold text-neutral-900 dark:text-neutral-100 mt-0.5">
            INR {totalSpent.toLocaleString()}
          </div>
        </div>
      </div>

      {showAddForm && (
        <form onSubmit={handleAddPurchase} className="border border-neutral-300 dark:border-neutral-700 rounded-sm p-4 bg-white dark:bg-neutral-900 space-y-4">
          <h3 className="text-sm font-semibold">Record Manual Purchase</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label htmlFor="input-bought-title" className="block text-xs font-mono text-neutral-500 mb-1">Product Title *</label>
              <Input
                id="input-bought-title"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Rynox Stealth Evo"
              />
            </div>
            <div>
              <label htmlFor="input-bought-price" className="block text-xs font-mono text-neutral-500 mb-1">Price Paid (INR) *</label>
              <Input
                id="input-bought-price"
                required
                type="number"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="e.g. 10750"
              />
            </div>
            <div>
              <label htmlFor="input-bought-store" className="block text-xs font-mono text-neutral-500 mb-1">Store / Retailer</label>
              <Input
                id="input-bought-store"
                value={store}
                onChange={(e) => setStore(e.target.value)}
                placeholder="e.g. Amazon.in"
              />
            </div>
          </div>
          <div>
            <label htmlFor="input-bought-notes" className="block text-xs font-mono text-neutral-500 mb-1">Notes</label>
            <Input
              id="input-bought-notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Ordered with CE Level 2 back protector"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" size="sm" onClick={() => setShowAddForm(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm">
              Save Record
            </Button>
          </div>
        </form>
      )}

      {loading ? (
        <div className="p-8 text-center text-xs text-neutral-400 font-mono">
          Loading purchase records...
        </div>
      ) : purchases.length === 0 ? (
        <div className="p-12 border border-neutral-200 dark:border-neutral-800 rounded-sm text-center">
          <p className="text-sm text-neutral-500">No purchases recorded yet.</p>
        </div>
      ) : (
        <div className="border border-neutral-200 dark:border-neutral-800 rounded-sm divide-y divide-neutral-200 dark:divide-neutral-800">
          {purchases.map((p) => (
            <div key={p.id} className="p-4 flex items-center justify-between">
              <div>
                <h4 className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                  {p.product_title || "Product Purchase"}
                </h4>
                {p.notes && <p className="text-xs text-neutral-500 mt-0.5">{p.notes}</p>}
                <div className="text-xs font-mono text-neutral-500 mt-1 flex items-center gap-3">
                  <span>Store: {p.store || "Direct"}</span>
                  <span>•</span>
                  <span>{new Date(p.purchase_date).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="text-right">
                <span className="font-mono text-sm font-semibold">
                  {p.currency} {p.price_paid.toLocaleString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
