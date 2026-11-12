import { useEffect, useState } from "react";
import { RotateCcw, Save } from "lucide-react";
import { getSettings, updateSettings } from "../api/client";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";

const DEFAULT_WEIGHTS: Record<string, number> = {
  budget_fit: 0.2,
  spec_match: 0.2,
  review_sentiment: 0.2,
  brand_reliability: 0.15,
  youtube_consensus: 0.15,
  stock_seller_trust: 0.1,
};

export function SettingsPage() {
  const [weights, setWeights] = useState<Record<string, number>>(DEFAULT_WEIGHTS);
  const [providerStatus, setProviderStatus] = useState<Record<string, unknown>>({});
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSettings()
      .then((data) => {
        if (data.scoring_weights) setWeights(data.scoring_weights);
        if (data.provider_status) setProviderStatus(data.provider_status);
      })
      .finally(() => setLoading(false));
  }, []);

  const handleSliderChange = (key: string, val: number) => {
    setWeights((prev) => ({
      ...prev,
      [key]: val,
    }));
    setSaved(false);
  };

  const handleSave = async () => {
    await updateSettings({ scoring_weights: weights });
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleReset = () => {
    setWeights(DEFAULT_WEIGHTS);
    setSaved(false);
  };

  if (loading) {
    return <div className="p-8 text-center text-xs text-neutral-400 font-mono">Loading configuration...</div>;
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-8">
      <div className="border-b border-neutral-200 dark:border-neutral-800 pb-4">
        <h1 className="text-xl font-semibold tracking-tight text-neutral-900 dark:text-neutral-100">
          Application Settings
        </h1>
        <p className="text-sm text-neutral-500 mt-1">
          Scoring engine weights, API credentials connectivity, and system preferences.
        </p>
      </div>

      {/* Provider Connectivity Status */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold tracking-tight uppercase font-mono text-neutral-600 dark:text-neutral-400">
          Provider Connectivity Status
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="p-3 border border-neutral-200 dark:border-neutral-800 rounded-sm bg-neutral-50 dark:bg-neutral-900/50 flex items-center justify-between">
            <div>
              <div className="text-xs font-medium">Groq LLM</div>
              <div className="text-xs text-neutral-500 font-mono mt-0.5">
                {String(providerStatus.llm_model || "llama-3.3-70b")}
              </div>
            </div>
            {providerStatus.groq_configured ? (
              <Badge variant="success">Active</Badge>
            ) : (
              <Badge variant="neutral">Offline</Badge>
            )}
          </div>

          <div className="p-3 border border-neutral-200 dark:border-neutral-800 rounded-sm bg-neutral-50 dark:bg-neutral-900/50 flex items-center justify-between">
            <div>
              <div className="text-xs font-medium">YouTube API</div>
              <div className="text-xs text-neutral-500 font-mono mt-0.5">Data API v3</div>
            </div>
            {providerStatus.youtube_configured ? (
              <Badge variant="success">Active</Badge>
            ) : (
              <Badge variant="neutral">Fallback</Badge>
            )}
          </div>

          <div className="p-3 border border-neutral-200 dark:border-neutral-800 rounded-sm bg-neutral-50 dark:bg-neutral-900/50 flex items-center justify-between">
            <div>
              <div className="text-xs font-medium">Brave Search</div>
              <div className="text-xs text-neutral-500 font-mono mt-0.5">Web Search API</div>
            </div>
            {providerStatus.brave_configured ? (
              <Badge variant="success">Active</Badge>
            ) : (
              <Badge variant="neutral">Offline</Badge>
            )}
          </div>
        </div>
      </div>

      {/* Scoring Weights */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold tracking-tight uppercase font-mono text-neutral-600 dark:text-neutral-400">
              Scoring Dimension Weights
            </h2>
            <p className="text-xs text-neutral-500 mt-0.5">
              Adjust how different evidence factors influence overall product ranking.
            </p>
          </div>
          <div className="flex gap-2">
            <Button onClick={handleReset} variant="outline" size="sm">
              <RotateCcw className="w-3.5 h-3.5 mr-1" />
              <span>Defaults</span>
            </Button>
            <Button onClick={handleSave} size="sm">
              <Save className="w-3.5 h-3.5 mr-1" />
              <span>{saved ? "Saved" : "Save Weights"}</span>
            </Button>
          </div>
        </div>

        <div className="border border-neutral-200 dark:border-neutral-800 rounded-sm p-4 space-y-4 bg-white dark:bg-neutral-900">
          {Object.entries(weights).map(([key, val]) => (
            <div key={key} className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono">
                <span className="capitalize">{key.replace(/_/g, " ")}</span>
                <span>{Math.round(val * 100)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={val}
                onChange={(e) => handleSliderChange(key, parseFloat(e.target.value))}
                className="w-full accent-neutral-900 dark:accent-neutral-100 cursor-pointer"
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
