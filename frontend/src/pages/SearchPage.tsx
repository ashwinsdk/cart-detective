import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Search as SearchIcon, ArrowRight } from "lucide-react";
import { createSearch } from "../api/client";

export function SearchPage() {
  const navigate = useNavigate();
  const [productType, setProductType] = useState("riding jacket");
  const [budgetMax, setBudgetMax] = useState("12000");
  const [budgetMin, setBudgetMin] = useState("5000");
  const [currency, setCurrency] = useState("INR");
  const [colors, setColors] = useState("black, grey");
  const [sizeFitGender, setSizeFitGender] = useState("men XL, touring fit");
  const [mustHaves, setMustHaves] = useState("CE Level 2 armor for elbows and shoulders");
  const [dealBreakers, setDealBreakers] = useState("no mesh only construction");
  const [brandsIncluded, setBrandsIncluded] = useState("Rynox, Royal Enfield, Viaterra");
  const [brandsExcluded, setBrandsExcluded] = useState("");
  const [marketplaces, setMarketplaces] = useState("Amazon.in, Flipkart, Brand sites");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!productType.trim()) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const payload = {
        product_type: productType.trim(),
        budget_min: budgetMin ? parseFloat(budgetMin) : null,
        budget_max: budgetMax ? parseFloat(budgetMax) : null,
        currency,
        color_preferences: colors ? colors.split(",").map((c) => c.trim()).filter(Boolean) : [],
        size_fit_gender: sizeFitGender.trim() || null,
        must_haves: mustHaves.trim() || null,
        deal_breakers: dealBreakers.trim() || null,
        brands_included: brandsIncluded ? brandsIncluded.split(",").map((b) => b.trim()).filter(Boolean) : [],
        brands_excluded: brandsExcluded ? brandsExcluded.split(",").map((b) => b.trim()).filter(Boolean) : [],
        marketplaces: marketplaces ? marketplaces.split(",").map((m) => m.trim()).filter(Boolean) : [],
      };

      const res = await createSearch(payload);
      navigate(`/runs/${res.run_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to initiate search run");
      setIsSubmitting(false);
    }
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="border-b border-neutral-200 dark:border-neutral-800 pb-4 mb-6">
        <h1 className="text-xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">
          New Product Investigation
        </h1>
        <p className="text-sm text-neutral-500 mt-1">
          Specify product requirements. The background pipeline crawls listings, analyzes reviews, checks video consensus, and corroborates evidence.
        </p>
      </div>

      {error && (
        <div className="mb-6 p-3 text-xs border border-neutral-300 dark:border-neutral-700 bg-neutral-100 dark:bg-neutral-900 text-neutral-800 dark:text-neutral-200 rounded-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label htmlFor="input-product-type" className="block text-xs uppercase tracking-wider font-mono text-neutral-600 dark:text-neutral-400 mb-1">
            Product Category / Query *
          </label>
          <input
            id="input-product-type"
            type="text"
            required
            value={productType}
            onChange={(e) => setProductType(e.target.value)}
            placeholder="e.g. riding jacket, running shoes, laptop backpack"
            className="w-full text-sm p-2.5 bg-white dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-700 rounded-sm focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-100"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label htmlFor="input-budget-min" className="block text-xs uppercase tracking-wider font-mono text-neutral-600 dark:text-neutral-400 mb-1">
              Min Budget
            </label>
            <input
              id="input-budget-min"
              type="number"
              value={budgetMin}
              onChange={(e) => setBudgetMin(e.target.value)}
              className="w-full text-sm p-2 bg-white dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-700 rounded-sm focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-100 font-mono"
            />
          </div>
          <div>
            <label htmlFor="input-budget-max" className="block text-xs uppercase tracking-wider font-mono text-neutral-600 dark:text-neutral-400 mb-1">
              Max Budget
            </label>
            <input
              id="input-budget-max"
              type="number"
              value={budgetMax}
              onChange={(e) => setBudgetMax(e.target.value)}
              className="w-full text-sm p-2 bg-white dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-700 rounded-sm focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-100 font-mono"
            />
          </div>
          <div>
            <label htmlFor="select-currency" className="block text-xs uppercase tracking-wider font-mono text-neutral-600 dark:text-neutral-400 mb-1">
              Currency
            </label>
            <select
              id="select-currency"
              aria-label="Currency"
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              className="w-full text-sm p-2 bg-white dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-700 rounded-sm focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-100 font-mono"
            >
              <option value="INR">INR</option>
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
              <option value="GBP">GBP</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label htmlFor="input-colors" className="block text-xs uppercase tracking-wider font-mono text-neutral-600 dark:text-neutral-400 mb-1">
              Color Preferences
            </label>
            <input
              id="input-colors"
              type="text"
              value={colors}
              onChange={(e) => setColors(e.target.value)}
              placeholder="e.g. black, dark grey, navy"
              className="w-full text-sm p-2 bg-white dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-700 rounded-sm focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-100"
            />
          </div>
          <div>
            <label htmlFor="input-size-fit" className="block text-xs uppercase tracking-wider font-mono text-neutral-600 dark:text-neutral-400 mb-1">
              Size / Fit / Gender
            </label>
            <input
              id="input-size-fit"
              type="text"
              value={sizeFitGender}
              onChange={(e) => setSizeFitGender(e.target.value)}
              placeholder="e.g. men size 10, slim fit, 28L"
              className="w-full text-sm p-2 bg-white dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-700 rounded-sm focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-100"
            />
          </div>
        </div>

        <div>
          <label htmlFor="input-must-haves" className="block text-xs uppercase tracking-wider font-mono text-neutral-600 dark:text-neutral-400 mb-1">
            Must-Have Features
          </label>
          <input
            id="input-must-haves"
            type="text"
            value={mustHaves}
            onChange={(e) => setMustHaves(e.target.value)}
            placeholder="e.g. CE Level 2 armor, Vibram outsole, padded laptop sleeve"
            className="w-full text-sm p-2 bg-white dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-700 rounded-sm focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-100"
          />
        </div>

        <div>
          <label htmlFor="input-deal-breakers" className="block text-xs uppercase tracking-wider font-mono text-neutral-600 dark:text-neutral-400 mb-1">
            Deal Breakers
          </label>
          <input
            id="input-deal-breakers"
            type="text"
            value={dealBreakers}
            onChange={(e) => setDealBreakers(e.target.value)}
            placeholder="e.g. non-breathable fabric, lack of rain cover, heavy weight"
            className="w-full text-sm p-2 bg-white dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-700 rounded-sm focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-100"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label htmlFor="input-brands-included" className="block text-xs uppercase tracking-wider font-mono text-neutral-600 dark:text-neutral-400 mb-1">
              Brands to Prioritize
            </label>
            <input
              id="input-brands-included"
              type="text"
              value={brandsIncluded}
              onChange={(e) => setBrandsIncluded(e.target.value)}
              placeholder="e.g. Rynox, Viaterra, Royal Enfield"
              className="w-full text-sm p-2 bg-white dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-700 rounded-sm focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-100"
            />
          </div>
          <div>
            <label htmlFor="input-brands-excluded" className="block text-xs uppercase tracking-wider font-mono text-neutral-600 dark:text-neutral-400 mb-1">
              Brands to Exclude
            </label>
            <input
              id="input-brands-excluded"
              type="text"
              value={brandsExcluded}
              onChange={(e) => setBrandsExcluded(e.target.value)}
              placeholder="e.g. unverified white-label brands"
              className="w-full text-sm p-2 bg-white dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-700 rounded-sm focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-100"
            />
          </div>
        </div>

        <div>
          <label htmlFor="input-marketplaces" className="block text-xs uppercase tracking-wider font-mono text-neutral-600 dark:text-neutral-400 mb-1">
            Target Marketplaces and Stores
          </label>
          <input
            id="input-marketplaces"
            type="text"
            value={marketplaces}
            onChange={(e) => setMarketplaces(e.target.value)}
            placeholder="e.g. Amazon.in, Flipkart, Brand Webstores"
            className="w-full text-sm p-2 bg-white dark:bg-neutral-900 border border-neutral-300 dark:border-neutral-700 rounded-sm focus:outline-none focus:border-neutral-900 dark:focus:border-neutral-100"
          />
        </div>

        <div className="pt-2">
          <button
            type="submit"
            disabled={isSubmitting}
            className="flex items-center justify-center gap-2 w-full py-2.5 px-4 bg-neutral-900 hover:bg-neutral-800 text-white dark:bg-neutral-100 dark:hover:bg-neutral-200 dark:text-neutral-950 font-medium text-sm rounded-sm transition-colors disabled:opacity-50"
          >
            {isSubmitting ? (
              <span>Initiating background run...</span>
            ) : (
              <>
                <SearchIcon className="w-4 h-4" />
                <span>Launch Research Investigation</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
