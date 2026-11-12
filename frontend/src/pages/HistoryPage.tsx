import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Search, ArrowRight, RotateCcw } from "lucide-react";
import { listSearches } from "../api/client";
import { Input } from "../components/ui/Input";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";

interface SearchRecord {
  id: string;
  created_at: string;
  product_type: string;
  budget_min?: number | null;
  budget_max?: number | null;
  currency: string;
  color_preferences: string[];
  latest_run_id?: string | null;
  latest_status?: string | null;
}

export function HistoryPage() {
  const navigate = useNavigate();
  const [searches, setSearches] = useState<SearchRecord[]>([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listSearches()
      .then(setSearches)
      .finally(() => setLoading(false));
  }, []);

  const filtered = searches.filter((s) =>
    s.product_type.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="border-b border-neutral-200 dark:border-neutral-800 pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">
            Search History
          </h1>
          <p className="text-sm text-neutral-500 mt-1">
            Previous product research queries and investigation runs.
          </p>
        </div>
        <Button onClick={() => navigate("/")} size="sm">
          <Search className="w-3.5 h-3.5 mr-1.5" />
          <span>New Search</span>
        </Button>
      </div>

      <div className="flex items-center gap-3">
        <Input
          type="text"
          placeholder="Filter by query..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="max-w-sm"
        />
      </div>

      {loading ? (
        <div className="p-8 text-center text-xs text-neutral-400 font-mono">
          Loading investigation logs...
        </div>
      ) : filtered.length === 0 ? (
        <div className="p-12 border border-neutral-200 dark:border-neutral-800 rounded-sm text-center">
          <p className="text-sm text-neutral-500">No past searches found.</p>
          <Button onClick={() => navigate("/")} variant="outline" size="sm" className="mt-4">
            Start your first search
          </Button>
        </div>
      ) : (
        <div className="border border-neutral-200 dark:border-neutral-800 rounded-sm divide-y divide-neutral-200 dark:divide-neutral-800">
          {filtered.map((item) => (
            <div
              key={item.id}
              className="p-4 flex items-center justify-between hover:bg-neutral-50 dark:hover:bg-neutral-900/50 transition-colors"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
                    {item.product_type}
                  </span>
                  {item.latest_status && (
                    <Badge variant={item.latest_status === "completed" ? "success" : "neutral"}>
                      {item.latest_status}
                    </Badge>
                  )}
                </div>
                <div className="text-xs font-mono text-neutral-500 mt-1 flex items-center gap-3">
                  <span>
                    Budget: {item.budget_max ? `Up to ${item.currency} ${item.budget_max.toLocaleString()}` : "Flexible"}
                  </span>
                  <span>•</span>
                  <span>{new Date(item.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {item.latest_run_id ? (
                  <Link to={`/runs/${item.latest_run_id}`}>
                    <Button variant="outline" size="sm">
                      <span>View Results</span>
                      <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
                    </Button>
                  </Link>
                ) : (
                  <Button variant="ghost" size="sm" onClick={() => navigate("/")}>
                    <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
                    <span>Re-run</span>
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
