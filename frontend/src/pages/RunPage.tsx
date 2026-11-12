import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { CheckCircle2, Clock, ExternalLink, ShieldCheck, AlertCircle } from "lucide-react";
import { getRun, getRunProducts } from "../api/client";
import { Badge } from "../components/ui/Badge";
import { Progress } from "../components/ui/Progress";

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
  offers: Array<{ seller_name: string; price: number; currency: string; url: string; status: string }>;
  evidence: Array<{ claim: string; source_url: string; verification_status: string }>;
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

  useEffect(() => {
    if (!runId) return;

    getRun(runId)
      .then((data) => {
        setRun(data);
        if (data.status === "completed") {
          setIsCompleted(true);
          getRunProducts(runId).then(setProducts);
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
      getRunProducts(runId).then(setProducts);
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
        <div>
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
        <div className="max-h-40 overflow-y-auto space-y-1">
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
              return (
                <div
                  key={p.id}
                  className="p-5 border border-neutral-200 dark:border-neutral-800 rounded-sm bg-white dark:bg-neutral-900 flex flex-col justify-between"
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

                  <div className="mt-4 pt-3 border-t border-neutral-100 dark:border-neutral-800 flex items-center justify-between text-xs font-mono">
                    <div className="flex items-center gap-1.5 text-neutral-600 dark:text-neutral-400">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      <span>{p.evidence.length} verified claims</span>
                    </div>
                    {bestOffer.url && (
                      <a
                        href={bestOffer.url}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 text-neutral-800 dark:text-neutral-200 hover:underline"
                      >
                        <span>View Source Offer</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
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
