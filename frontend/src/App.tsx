import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { Moon, Sun, Search, History, Bookmark, CheckCircle, Sliders } from "lucide-react";
import { SearchPage } from "./pages/SearchPage";
import { RunPage } from "./pages/RunPage";

function ThemeToggle() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    setIsDark(document.documentElement.classList.contains("dark"));
  }, []);

  const toggleTheme = () => {
    const next = !isDark;
    setIsDark(next);
    if (next) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  };

  return (
    <button
      onClick={toggleTheme}
      className="p-1.5 border border-neutral-300 dark:border-neutral-700 rounded-sm hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
      aria-label="Toggle theme"
    >
      {isDark ? <Sun className="w-4 h-4 text-neutral-300" /> : <Moon className="w-4 h-4 text-neutral-700" />}
    </button>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-white dark:bg-neutral-950 text-neutral-900 dark:text-neutral-100 flex flex-col font-sans">
        <header className="border-b border-neutral-200 dark:border-neutral-800 px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/" className="font-mono text-sm font-semibold tracking-wider uppercase text-neutral-950 dark:text-neutral-50">
              Cart Detective
            </Link>
            <nav className="flex items-center gap-4 text-xs">
              <Link to="/" className="flex items-center gap-1.5 text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100">
                <Search className="w-3.5 h-3.5" />
                <span>Search</span>
              </Link>
              <Link to="/history" className="flex items-center gap-1.5 text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100">
                <History className="w-3.5 h-3.5" />
                <span>History</span>
              </Link>
              <Link to="/wishlist" className="flex items-center gap-1.5 text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100">
                <Bookmark className="w-3.5 h-3.5" />
                <span>Wishlist</span>
              </Link>
              <Link to="/bought" className="flex items-center gap-1.5 text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100">
                <CheckCircle className="w-3.5 h-3.5" />
                <span>Bought</span>
              </Link>
              <Link to="/settings" className="flex items-center gap-1.5 text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100">
                <Sliders className="w-3.5 h-3.5" />
                <span>Settings</span>
              </Link>
            </nav>
          </div>
          <ThemeToggle />
        </header>
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<SearchPage />} />
            <Route path="/runs/:runId" element={<RunPage />} />
            <Route path="/history" element={<div className="p-6 max-w-4xl mx-auto"><h2 className="text-lg font-medium">History</h2></div>} />
            <Route path="/wishlist" element={<div className="p-6 max-w-4xl mx-auto"><h2 className="text-lg font-medium">Wishlist</h2></div>} />
            <Route path="/bought" element={<div className="p-6 max-w-4xl mx-auto"><h2 className="text-lg font-medium">Bought</h2></div>} />
            <Route path="/settings" element={<div className="p-6 max-w-4xl mx-auto"><h2 className="text-lg font-medium">Settings</h2></div>} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
