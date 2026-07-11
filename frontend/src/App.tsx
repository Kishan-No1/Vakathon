import { useEffect, useState } from "react";
import { api, type Plume } from "./api/client";
import MapView from "./map/MapView";
import ClickResolvePanel from "./components/ClickResolvePanel";
import CitizenReportPanel from "./components/CitizenReportPanel";
import "./App.css";

type PanelMode = "detection" | "citizen";

export default function App() {
  const [plumes, setPlumes] = useState<Plume[]>([]);
  const [selected, setSelected] = useState<Plume | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [panelOpen, setPanelOpen] = useState(() => window.innerWidth > 768);
  const [mode, setMode] = useState<PanelMode>("detection");

  const selectPlume = (p: Plume) => {
    setSelected(p);
    setPanelOpen(true);
  };

  useEffect(() => {
    api
      .events()
      .then((r) => setPlumes(r.events))
      .catch(() =>
        setLoadError(
          "Could not reach the backend at http://localhost:8000 — start it with: uvicorn backend.main:app",
        ),
      );
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <h1>Plume Finder</h1>
          <span className="tagline">
            methane detection → attribution → community action
          </span>
        </div>
        <div className="mode-toggle" role="group" aria-label="Sidebar mode">
          <button
            className={mode === "detection" ? "active" : ""}
            onClick={() => setMode("detection")}
          >
            Detection
          </button>
          <button
            className={mode === "citizen" ? "active" : ""}
            onClick={() => setMode("citizen")}
          >
            Citizen Report
          </button>
        </div>
      </header>

      {loadError && <div className="load-error">{loadError}</div>}

      <main className="app-main">
        <MapView
          plumes={plumes}
          selectedId={selected?.plume_id ?? null}
          onSelect={selectPlume}
          panelOpen={panelOpen}
          onTogglePanel={() => setPanelOpen(!panelOpen)}
        />
        <aside className={`side-panel${panelOpen ? "" : " collapsed"}`}>
          {selected ? (
            mode === "detection" ? (
              <ClickResolvePanel plume={selected} />
            ) : (
              <CitizenReportPanel plume={selected} />
            )
          ) : (
            <div className="panel-placeholder">
              <h2>Click a plume</h2>
              <p>
                {mode === "detection"
                  ? "Each dot is a real methane plume detected from orbit. Click one to see who it belongs to, which rule applies, and what your community can do about it."
                  : "Click the plume nearest to what you saw, then describe your own observations — your report becomes the basis of a complaint letter."}
              </p>
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}
