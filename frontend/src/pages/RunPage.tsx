import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  CheckCircle2,
  Clock,
  ExternalLink,
  ShieldCheck,
  AlertCircle,
  Download,
  Bookmark,
  ShoppingBag,
} from "lucide-react";
import { getRun, getRunProducts, addToWishlist, recordPurchase } from "../api/client";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Progress } from "../components/ui/Progress";
import { downloadCSV, downloadJSON } from "../lib/export";

interface RunData {
  id: string;
  status: string;
  current_stage: number;
  stage_progress: number;
  error_message?: string;
  logs: Array<{ timestamp: string; stage: number; level: string; message: string }>;
}

interface ProductItem {
  id: string;
  canonical_brand: string;
  canonical_model: string;
  title: string;
  score: number;
  confidence: number;
  verdict: string;
  pros: string[];
  cons: string[];
  offers: Array<{ seller_name: string; price: number; currency: string; url: string; status: string }>;
  evidence: Array<{ claim: string; source_url: string; verification_status: string }>;
  videos: Array<{ title: string; url: string; transcript_summary: string; is_sponsored: boolean }>;
}

const STAGES = [
  { num: 1, name: "Understand Query" },
  { num: 2, name: "Discover Candidates" },
  { num: 3, name: "Brand Research" },
  { num: 4, name: "Crawl and Scrape" },
  { num: 5, name: "Review and YouTube" },
  { num: 6, name: "Cross-Verification" },
  { num: 7, name: "Score and Rank" },
  { num: 8, name: "Present and Persist" },
];

export function RunPage() {
  const { runId } = useParams<{ runId: string }>();
  const [run, setRun] = useState<RunData | null>(null);
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [events, setEvents] = useState<string[]>([]);
  const [isCompleted, setIsCompleted] = useState(false);
  const [filterLevel, setFilterLevel] = useState<string>("ALL");
  const [actionNotices, setActionNotices] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!runId) return;

    getRun<RunData>(runId)
      .then((data) => {
        setRun(data);
        if (data.status === "completed") {
          setIsCompleted(true);
          getRunProducts<ProductItem[]>(runId).then(setProducts);
        }
      })
      .catch((err) => {
        setEvents((prev) => [...prev, `Failed to load run: ${err.message}`]);
      });

    const apiBase = import.meta.env.VITE_API_BASE_URL || "";
    const eventSource = new EventSource(`${apiBase}/api/runs/${runId}/stream`);

    eventSource.addEventListener("stage_start", (e) => {
      const data = JSON.parse(e.data);
      setEvents((prev) => [...prev, `[Stage ${data.stage}] Started: ${data.name}`]);
      setRun((prev) => (prev ? { ...prev, current_stage: data.stage } : null));
    });

    eventSource.addEventListener("stage_complete", (e) => {
      const data = JSON.parse(e.data);
      setEvents((prev) => [...prev, `[Stage ${data.stage}] Completed: ${data.name}`]);
      setRun((prev) => (prev ? { ...prev, stage_progress: data.progress } : null));
    });

    eventSource.addEventListener("complete", (_e) => {
      setIsCompleted(true);
      eventSource.close();
      getRunProducts<ProductItem[]>(runId).then(setProducts);
    });

    eventSource.addEventListener("error", (e: Event) => {
      const msg = (e as MessageEvent).data;
      if (msg) {
        try {
          const data = JSON.parse(msg);
          setEvents((prev) => [...prev, `[ERROR] ${data.message}`]);
        } catch {
          // Stream error
        }
      }
    });

    return () => {
      eventSource.close();
    };
  }, [runId]);

  const handleSaveWishlist = async (productId: string) => {
    await addToWishlist(productId, "Shortlisted from investigation");
    setActionNotices((prev) => ({ ...prev, [productId]: "Saved to Wishlist" }));
    setTimeout(() => {
      setActionNotices((prev) => {
        const next = { ...prev };
        delete next[productId];
        return next;
      });
    }, 2500);
  };

  const handleMarkBought = async (product: ProductItem) => {
    const offer = product.offers[0];
    await recordPurchase({
      product_id: product.id,
      price_paid: offer ? offer.price : 0,
      currency: offer ? offer.currency : "INR",
      store: offer ? offer.seller_name : "Direct",
      notes: "Acquired via Cart Detective shortlist",
    });
    setActionNotices((prev) => ({ ...prev, [product.id]: "Recorded as Bought" }));
    setTimeout(() => {
      setActionNotices((prev) => {
        const next = { ...prev };
        delete next[product.id];
        return next;
      });
    }, 2500);
  };

  const handleExportJSON = () => {
    downloadJSON(products, `cart-detective-${runId}.json`);
  };

  const handleExportCSV = () => {
    const rows = products.map((p, idx) => ({
      Rank: idx + 1,
      Brand: p.canonical_brand,
      Model: p.canonical_model,
      Title: p.title,
      Price: p.offers[0]?.price || 0,
      Currency: p.offers[0]?.currency || "INR",
      Seller: p.offers[0]?.seller_name || "Direct",
      Score: p.score,
      Confidence: p.confidence,
      Verdict: p.verdict,
    }));
    downloadCSV(rows, `cart-detective-${runId}.csv`);
  };

  const filteredLogs = events.filter((e) => {
    if (filterLevel === "WARNING") return e.includes("WARNING") || e.includes("ERROR");
    if (filterLevel === "ERROR") return e.includes("ERROR");
    return true;
  });

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-8">
      {/* Run Header */}
      <div className="border-b border-neutral-200 dark:border-neutral-800 pb-4 flex items-center justify-between">
        <div>
          <div className="text-xs font-mono uppercase tracking-wider text-neutral-500">
            Investigation Run
          </div>
          <h1 className="text-lg font-mono font-medium text-neutral-900 dark:text-neutral-100 mt-0.5">
            {runId}
          </h1>
        </div>
        <div className="flex items-center gap-2">
          {isCompleted && products.length > 0 && (
            <>
              <Button onClick={handleExportCSV} variant="outline" size="sm">
                <Download className="w-3.5 h-3.5 mr-1" />
                <span>CSV</span>
              </Button>
              <Button onClick={handleExportJSON} variant="outline" size="sm">
                <Download className="w-3.5 h-3.5 mr-1" />
                <span>JSON</span>
              </Button>
            </>
          )}
          <Badge variant={isCompleted ? "success" : "default"}>
            {isCompleted ? "Completed" : run?.status || "Running"}
          </Badge>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-mono text-neutral-600 dark:text-neutral-400">
          <span>Pipeline Progress</span>
          <span>{isCompleted ? "100%" : `${Math.round(run?.stage_progress || 0)}%`}</span>
        </div>
        <Progress value={isCompleted ? 100 : run?.stage_progress || 0} />
      </div>

      {/* Stage Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {STAGES.map((s) => {
          const current = run?.current_stage || 1;
          const isDone = isCompleted || s.num < current;
          const isActive = !isCompleted && s.num === current;

          return (
            <div
              key={s.num}
              className={`p-3 border rounded-sm text-xs transition-colors ${
                isDone
                  ? "border-neutral-300 bg-neutral-50 dark:border-neutral-700 dark:bg-neutral-900"
                  : isActive
                  ? "border-neutral-900 dark:border-neutral-100 bg-white dark:bg-neutral-950 font-medium"
                  : "border-neutral-200 dark:border-neutral-800 opacity-40"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono text-neutral-500">0{s.num}</span>
                {isDone ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-neutral-900 dark:text-neutral-100" />
                ) : (
                  <Clock className="w-3.5 h-3.5 text-neutral-400" />
                )}
              </div>
              <div className="truncate">{s.name}</div>
            </div>
          );
        })}
      </div>

      {/* Live Event Console */}
      <div className="border border-neutral-200 dark:border-neutral-800 rounded-sm bg-neutral-50 dark:bg-neutral-900/50 p-4 font-mono text-xs">
        <div className="flex items-center justify-between mb-2">
          <span className="text-neutral-500 uppercase tracking-wider">Live Pipeline Telemetry</span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setFilterLevel("ALL")}
              className={`px-1.5 py-0.5 rounded-sm ${
                filterLevel === "ALL" ? "bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-950" : "text-neutral-500"
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilterLevel("WARNING")}
              className={`px-1.5 py-0.5 rounded-sm ${
                filterLevel === "WARNING" ? "bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-950" : "text-neutral-500"
              }`}
            >
              Warnings
            </button>
          </div>
        </div>
        <div className="max-h-36 overflow-y-auto space-y-1">
          {filteredLogs.length === 0 ? (
            <div className="text-neutral-400">Connecting to telemetry stream...</div>
          ) : (
            filteredLogs.map((evt, idx) => (
              <div key={idx} className="text-neutral-700 dark:text-neutral-300">
                &gt; {evt}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Decision Rationale */}
      {isCompleted && products.length > 0 && (
        <div className="p-4 border border-neutral-200 dark:border-neutral-800 rounded-sm bg-neutral-50 dark:bg-neutral-900/40">
          <div className="text-xs font-mono uppercase tracking-wider text-neutral-500">
            How We Decided
          </div>
          <p className="text-sm text-neutral-800 dark:text-neutral-200 mt-1">
            Ranked {products.length} products using multi-source corroboration. The top recommendation is{" "}
            <span className="font-semibold">{products[0].title}</span> (Score: {products[0].score}/100, {products[0].confidence}% evidence confidence).
          </p>
        </div>
      )}

      {/* Comparison Table for Top Products */}
      {isCompleted && products.length >= 2 && (
        <div className="space-y-3">
          <div className="text-xs font-mono uppercase tracking-wider text-neutral-500">
            Top Contenders Comparison Matrix
          </div>
          <div className="border border-neutral-200 dark:border-neutral-800 rounded-sm overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-neutral-100 dark:bg-neutral-800 border-b border-neutral-200 dark:border-neutral-800">
                <tr>
                  <th className="p-2.5">Attribute</th>
                  {products.slice(0, 4).map((p) => (
                    <th key={p.id} className="p-2.5 font-semibold">
                      {p.canonical_brand} {p.canonical_model}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200 dark:divide-neutral-800">
                <tr>
                  <td className="p-2.5 text-neutral-500">Score / Conf</td>
                  {products.slice(0, 4).map((p) => (
                    <td key={p.id} className="p-2.5 font-semibold">
                      {p.score}/100 ({p.confidence}%)
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-2.5 text-neutral-500">Best Price</td>
                  {products.slice(0, 4).map((p) => {
                    const off = p.offers[0];
                    return (
                      <td key={p.id} className="p-2.5">
                        {off?.price ? `${off.currency} ${off.price.toLocaleString()}` : "Unverified"}
                      </td>
                    );
                  })}
                </tr>
                <tr>
                  <td className="p-2.5 text-neutral-500">Seller / Store</td>
                  {products.slice(0, 4).map((p) => (
                    <td key={p.id} className="p-2.5">
                      {p.offers[0]?.seller_name || "Direct"}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="p-2.5 text-neutral-500">Verified Evidence</td>
                  {products.slice(0, 4).map((p) => (
                    <td key={p.id} className="p-2.5">
                      {p.evidence.length} sources
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Shortlisted Products View */}
      {isCompleted && products.length > 0 && (
        <div className="space-y-4">
          <div className="border-b border-neutral-200 dark:border-neutral-800 pb-2 flex items-baseline justify-between">
            <h2 className="text-base font-medium">Ranked Product Shortlist</h2>
            <span className="font-mono text-xs text-neutral-500">
              {products.length} Products Verified
            </span>
          </div>

          <div className="grid grid-cols-1 gap-4">
            {products.map((p, idx) => {
              const bestOffer = p.offers[0] || {};
              const notice = actionNotices[p.id];

              return (
                <div
                  key={p.id}
                  className="p-5 border border-neutral-200 dark:border-neutral-800 rounded-sm bg-white dark:bg-neutral-900 flex flex-col justify-between space-y-4"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-semibold px-1.5 py-0.5 border border-neutral-300 dark:border-neutral-700 rounded-sm">
                          #{idx + 1}
                        </span>
                        <span className="text-xs font-mono uppercase tracking-wider text-neutral-500">
                          {p.canonical_brand}
                        </span>
                      </div>
                      <h3 className="text-sm font-medium mt-1 text-neutral-900 dark:text-neutral-100">
                        {p.title}
                      </h3>
                      <p className="text-xs text-neutral-600 dark:text-neutral-400 mt-2">
                        {p.verdict}
                      </p>
                    </div>

                    <div className="text-right shrink-0">
                      <div className="font-mono text-base font-semibold">
                        {bestOffer.price ? `${bestOffer.currency} ${bestOffer.price.toLocaleString()}` : "Price unverified"}
                      </div>
                      <div className="text-xs font-mono text-neutral-500 mt-0.5">
                        Seller: {bestOffer.seller_name || "Direct"}
                      </div>
                      <div className="mt-2 text-xs font-mono text-neutral-700 dark:text-neutral-300">
                        Score: {p.score}/100 ({p.confidence}% conf)
                      </div>
                    </div>
                  </div>

                  {/* Evidence & Video Summary */}
                  {p.videos && p.videos.length > 0 && (
                    <div className="p-3 border border-neutral-200 dark:border-neutral-800 rounded-sm bg-neutral-50 dark:bg-neutral-900/50 text-xs">
                      <div className="font-mono text-neutral-500 uppercase tracking-wider text-xs mb-1">
                        Video Review Consensus
                      </div>
                      <p className="text-neutral-700 dark:text-neutral-300">
                        {p.videos[0].transcript_summary || "Independent review consensus synthesized from reviewer transcript."}
                      </p>
                    </div>
                  )}

                  {/* Actions and Footer */}
                  <div className="pt-3 border-t border-neutral-100 dark:border-neutral-800 flex items-center justify-between text-xs font-mono">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-1.5 text-neutral-600 dark:text-neutral-400">
                        <ShieldCheck className="w-3.5 h-3.5" />
                        <span>{p.evidence.length} claims verified</span>
                      </div>
                      {notice && (
                        <span className="text-neutral-900 dark:text-neutral-100 font-semibold">{notice}</span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      <Button onClick={() => handleSaveWishlist(p.id)} variant="outline" size="sm">
                        <Bookmark className="w-3.5 h-3.5 mr-1" />
                        <span>Wishlist</span>
                      </Button>
                      <Button onClick={() => handleMarkBought(p)} variant="outline" size="sm">
                        <ShoppingBag className="w-3.5 h-3.5 mr-1" />
                        <span>Bought</span>
                      </Button>
                      {bestOffer.url && (
                        <a
                          href={bestOffer.url}
                          target="_blank"
                          rel="noreferrer"
                          className="flex items-center gap-1 px-2.5 py-1 border border-neutral-300 dark:border-neutral-700 rounded-sm hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-800 dark:text-neutral-200"
                        >
                          <span>Store</span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {isCompleted && products.length === 0 && (
        <div className="p-8 border border-neutral-200 dark:border-neutral-800 rounded-sm text-center text-xs text-neutral-500 flex flex-col items-center gap-2">
          <AlertCircle className="w-5 h-5 text-neutral-400" />
          <span>No candidates met the minimum criteria or all candidates were disqualified based on brand reliability.</span>
        </div>
      )}
    </div>
  );
}
