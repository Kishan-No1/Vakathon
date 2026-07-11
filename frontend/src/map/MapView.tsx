import { useState } from "react";
import DeckGL from "@deck.gl/react";
import { Map } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import type { Plume, ReportedPlume } from "../api/client";
import { plumeLayer, reportedPlumeLayer } from "./layers/plumeLayer";

const BASEMAP =
  "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";

// Permian basin, straddling the TX/NM line
const INITIAL_VIEW = {
  longitude: -103.5,
  latitude: 32.0,
  zoom: 7.3,
  pitch: 0,
  bearing: 0,
};

interface Props {
  plumes: Plume[];
  reportedPlumes: ReportedPlume[];
  selectedId: string | null;
  onSelect: (p: Plume) => void;
  panelOpen: boolean;
  onTogglePanel: () => void;
}

export default function MapView({
  plumes,
  reportedPlumes,
  selectedId,
  onSelect,
  panelOpen,
  onTogglePanel,
}: Props) {
  const [hovered, setHovered] = useState<Plume | null>(null);

  return (
    <div className="map-wrap">
      <DeckGL
        initialViewState={INITIAL_VIEW}
        controller
        layers={[
          plumeLayer(plumes, selectedId, onSelect),
          reportedPlumeLayer(reportedPlumes),
        ]}
        onHover={(info) => setHovered((info.object as Plume) ?? null)}
        getCursor={({ isHovering }) => (isHovering ? "pointer" : "grab")}
      >
        <Map mapStyle={BASEMAP} />
      </DeckGL>

      {hovered && (
        <div className="map-tooltip">
          <strong>{hovered.plume_id}</strong>
          <div>
            {hovered.place}, {hovered.state} ·{" "}
            {Math.round(hovered.leak_rate_kg_hr)} kg/hr
          </div>
        </div>
      )}

      <div className="map-legend">
        <span>
          <i className="dot dot-nm" /> New Mexico plume
        </span>
        <span>
          <i className="dot dot-tx" /> Texas plume
        </span>
        <span>
          <i className="dot dot-ok" /> Oklahoma plume
        </span>
        <span>
          <i className="dot dot-reported" /> Potential new plume (reported)
        </span>
        <span className="legend-hint">dot size = leak rate · click a plume to resolve it</span>
      </div>

      <button
        className="panel-toggle"
        onClick={onTogglePanel}
        aria-label={panelOpen ? "Hide panel" : "Show panel"}
        title={panelOpen ? "Hide panel" : "Show panel"}
      >
        {panelOpen ? "›" : "‹"}
      </button>
    </div>
  );
}
