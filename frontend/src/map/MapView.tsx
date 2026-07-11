import { useEffect, useState } from "react";
import DeckGL from "@deck.gl/react";
import { Map } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import type { StyleSpecification } from "maplibre-gl";
import type { Plume, ReportedPlume } from "../api/client";
import { plumeLayer, reportedPlumeLayer } from "./layers/plumeLayer";
import { loadBasemapStyle } from "./basemapStyle";

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
  // null until the customized style is ready — mounting <Map> once with the
  // final style avoids a mid-load setStyle swap that can strand tile loading.
  const [mapStyle, setMapStyle] = useState<StyleSpecification | string | null>(
    null,
  );

  useEffect(() => {
    let cancelled = false;
    loadBasemapStyle().then((style) => {
      if (!cancelled) setMapStyle(style);
    });
    return () => {
      cancelled = true;
    };
  }, []);

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
        {mapStyle && <Map mapStyle={mapStyle} />}
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
