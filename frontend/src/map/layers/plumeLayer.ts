import { ScatterplotLayer } from "@deck.gl/layers";
import { stateAbbr, type Plume } from "../../api/client";

// NM = teal, TX = orange — the regulatory-gap color story used across the app
export const STATE_COLORS: Record<string, [number, number, number]> = {
  NM: [45, 212, 191],
  TX: [251, 146, 60],
};

// matches CSS --heading; deck.gl draws to canvas and can't read CSS vars, keep in sync manually
const SELECTED_STROKE: [number, number, number, number] = [32, 33, 36, 255];

export function plumeLayer(
  plumes: Plume[],
  selectedId: string | null,
  onClick: (p: Plume) => void,
) {
  return new ScatterplotLayer<Plume>({
    id: "carbon-mapper-plumes",
    data: plumes,
    getPosition: (d) => [d.lon, d.lat],
    // radius scales with leak rate so big emitters read at a glance
    getRadius: (d) => 800 + Math.sqrt(d.leak_rate_kg_hr) * 60,
    radiusUnits: "meters",
    radiusMinPixels: 6,
    radiusMaxPixels: 28,
    getFillColor: (d) => {
      const c = STATE_COLORS[stateAbbr(d.state)] ?? [200, 200, 200];
      return [...c, d.plume_id === selectedId ? 255 : 200] as [
        number, number, number, number,
      ];
    },
    getLineColor: (d) =>
      d.plume_id === selectedId ? SELECTED_STROKE : [0, 0, 0, 0],
    getLineWidth: 2.5,
    lineWidthUnits: "pixels",
    stroked: true,
    pickable: true,
    onClick: (info) => info.object && onClick(info.object),
    updateTriggers: { getFillColor: [selectedId], getLineColor: [selectedId] },
  });
}
