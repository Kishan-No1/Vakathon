// Fetches the CARTO Positron style and adjusts it for this app:
// bolder state boundaries and slightly darker roads, so the TX/NM/OK
// state lines and road network read clearly under the plume overlay.
import type { StyleSpecification } from "maplibre-gl";

export const BASEMAP_URL =
  "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";

// Positron's road/bridge/tunnel greys, each mapped to a slightly darker shade.
const ROAD_COLOR_DARKEN: Record<string, string> = {
  "#e6e6e6": "#d0d2d4",
  "#ddd": "#c8cacc",
  "#dddddd": "#c8cacc",
  "#d5d5d5": "#c1c3c5",
  "#eee": "#dcdee0",
  "#eeeeee": "#dcdee0",
  "rgba(238, 238, 238, 1)": "#dcdee0",
  "#fdfdfd": "#eff0f1",
  "#fff": "#f3f4f5",
  "#ffffff": "#f3f4f5",
};

type StopsColor = { stops: [number, string][] };
type LineColor = string | StopsColor;

function darkenColor(color: LineColor): LineColor {
  if (typeof color === "string") return ROAD_COLOR_DARKEN[color] ?? color;
  if (color && Array.isArray(color.stops)) {
    return {
      ...color,
      stops: color.stops.map(([zoom, c]) => [zoom, ROAD_COLOR_DARKEN[c] ?? c]),
    };
  }
  return color;
}

// MapLibre style layers are loosely typed here on purpose — we only touch
// well-known paint properties and pass everything else through untouched.
interface StyleLayer {
  id: string;
  type: string;
  "source-layer"?: string;
  paint?: Record<string, unknown>;
}

export async function loadBasemapStyle(): Promise<StyleSpecification | string> {
  try {
    const res = await fetch(BASEMAP_URL);
    if (!res.ok) throw new Error(`${res.status}`);
    const style = (await res.json()) as StyleSpecification;

    for (const layer of style.layers as unknown as StyleLayer[]) {
      if (layer.type !== "line" || !layer.paint) continue;

      if (layer.id === "boundary_state") {
        layer.paint["line-color"] = {
          stops: [
            [4, "#c9a3a7"],
            [5, "#c9a3a7"],
            [6, "#b8898e"],
          ],
        };
        layer.paint["line-width"] = {
          stops: [
            [4, 1.5],
            [7, 2.5],
            [8, 2.5],
            [9, 3],
          ],
        };
      } else if (layer["source-layer"] === "transportation") {
        layer.paint["line-color"] = darkenColor(
          layer.paint["line-color"] as LineColor,
        );
      }
    }
    return style;
  } catch {
    // Style fetch failed — fall back to the stock hosted style URL.
    return BASEMAP_URL;
  }
}
