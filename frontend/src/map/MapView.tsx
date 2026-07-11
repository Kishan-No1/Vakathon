import { useState } from "react";
import DeckGL from "@deck.gl/react";
import { Map } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import type { Plume } from "../api/client";
import { plumeLayer } from "./layers/plumeLayer";

const BASEMAP =
  "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";

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
  selectedId: string | null;
  onSelect: (p: Plume) => void;
}

export default function MapView({ plumes, selectedId, onSelect }: Props) {
  const [hovered, setHovered] = useState<Plume | null>(null);

  return (
    <div className="map-wrap">
      <DeckGL
        initialViewState={INITIAL_VIEW}
        controller
        layers={[plumeLayer(plumes, selectedId, onSelect)]}
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
        <span className="legend-hint">dot size = leak rate · click a plume to resolve it</span>
      </div>
    </div>
  );
}
