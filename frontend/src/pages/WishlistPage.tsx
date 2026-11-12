import { useEffect, useState } from "react";
import { Trash2, ShoppingBag } from "lucide-react";
import { getWishlist, removeFromWishlist, recordPurchase } from "../api/client";
import { Button } from "../components/ui/Button";

interface WishlistEntry {
  id: string;
  product_id: string;
  notes?: string;
  added_at: string;
  product?: {
    title: string;
    brand: string;
    score: number;
    price: number;
    currency: string;
  };
}

export function WishlistPage() {
  const [items, setItems] = useState<WishlistEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = () => {
    getWishlist<WishlistEntry[]>()
      .then(setItems)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRemove = async (id: string) => {
    await removeFromWishlist(id);
    loadData();
  };

  const handleMarkBought = async (item: WishlistEntry) => {
    if (!item.product) return;
    await recordPurchase({
      product_id: item.product_id,
      price_paid: item.product.price,
      currency: item.product.currency,
      store: "Online",
      notes: "Acquired from Wishlist",
    });
    await removeFromWishlist(item.id);
    loadData();
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="border-b border-neutral-200 dark:border-neutral-800 pb-4">
        <h1 className="text-xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">
          Saved Wishlist
        </h1>
        <p className="text-sm text-neutral-500 mt-1">
          Candidate products shortlisted for future purchase decisions.
        </p>
      </div>

      {loading ? (
        <div className="p-8 text-center text-xs text-neutral-400 font-mono">
          Loading saved items...
        </div>
      ) : items.length === 0 ? (
        <div className="p-12 border border-neutral-200 dark:border-neutral-800 rounded-sm text-center">
          <p className="text-sm text-neutral-500">Your wishlist is currently empty.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {items.map((item) => {
            const p = item.product;
            return (
              <div
                key={item.id}
                className="p-4 border border-neutral-200 dark:border-neutral-800 rounded-sm bg-white dark:bg-neutral-900 flex items-center justify-between"
              >
                <div>
                  <div className="text-xs font-mono uppercase tracking-wider text-neutral-500">
                    {p?.brand || "Brand"}
                  </div>
                  <h3 className="text-sm font-medium text-neutral-900 dark:text-neutral-100 mt-0.5">
                    {p?.title || "Product"}
                  </h3>
                  {item.notes && (
                    <p className="text-xs text-neutral-500 mt-1">Note: {item.notes}</p>
                  )}
                  <div className="text-xs font-mono text-neutral-600 dark:text-neutral-400 mt-2 flex items-center gap-3">
                    <span>
                      {p?.price ? `${p.currency} ${p.price.toLocaleString()}` : "Price unverified"}
                    </span>
                    <span>•</span>
                    <span>Score: {p?.score ?? 0}/100</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    onClick={() => handleMarkBought(item)}
                    size="sm"
                    variant="outline"
                    title="Mark as bought"
                  >
                    <ShoppingBag className="w-3.5 h-3.5 mr-1" />
                    <span>Bought</span>
                  </Button>
                  <Button
                    onClick={() => handleRemove(item.id)}
                    size="sm"
                    variant="ghost"
                    title="Remove from wishlist"
                  >
                    <Trash2 className="w-3.5 h-3.5 text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100" />
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
