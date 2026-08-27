import { useEffect, useRef, useState } from "react";
import maplibregl, { type Map as MapLibreMap } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import {
  Eye,
  EyeOff,
  Layers3,
  MapPinned,
  RefreshCw,
  SlidersHorizontal,
  Trees,
} from "lucide-react";

import { CadastreWorkspaceDialog, type CadastreWorkspace } from "@/components/CadastreWorkspaceDialog";
import { api } from "@/lib/api";

type MapProperties = Record<string, string | number | boolean | null | undefined>;
type FeatureCollection = GeoJSON.FeatureCollection<GeoJSON.Geometry, MapProperties>;
type LayerKey = "cadastres" | "subparts" | "newSubparts" | "registry" | "notifications";
type SourceKind = "vector" | "geojson";
type LayerConfig = {
  key: LayerKey;
  label: string;
  color: string;
  kind: "fill" | "line" | "point";
  description: string;
  minZoom: number;
  sourceKind: SourceKind;
  endpoint?: string;
  tileEndpoint?: string;
};
type MapFilters = {
  customer: boolean;
  activeDeal: boolean;
  activityDays: string;
  dealStage: string;
};

const ESTONIA_BOUNDS: [number, number, number, number] = [21.7, 57.5, 28.3, 59.9];
const EMPTY: FeatureCollection = { type: "FeatureCollection", features: [] };
const DEFAULT_FILTERS: MapFilters = {
  customer: false,
  activeDeal: false,
  activityDays: "",
  dealStage: "",
};
const STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {
    openfreemap: {
      type: "raster",
      tiles: ["https://tiles.openfreemap.org/styles/liberty/{z}/{x}/{y}.png"],
      tileSize: 256,
      attribution: "© OpenFreeMap",
    },
  },
  layers: [{ id: "base", type: "raster", source: "openfreemap" }],
};
const LAYERS: LayerConfig[] = [
  {
    key: "cadastres",
    label: "Katastriüksused",
    color: "#13795b",
    kind: "fill",
    description: "MVT-vektorplaadid nähtaval kaardialal",
    minZoom: 8,
    sourceKind: "vector",
    tileEndpoint: "/api/services/map/tiles/cadastres/{z}/{x}/{y}.pbf",
  },
  {
    key: "subparts",
    label: "Metsaeraldised",
    color: "#e58e26",
    kind: "line",
    description: "MVT-vektorplaadid alates suumist 10",
    minZoom: 10,
    sourceKind: "vector",
    tileEndpoint: "/api/services/map/tiles/subparts/{z}/{x}/{y}.pbf",
  },
  {
    key: "registry",
    label: "Metsaregistri objektid",
    color: "#805ad5",
    kind: "line",
    description: "MVT-vektorplaadid alates suumist 10",
    minZoom: 10,
    sourceKind: "vector",
    tileEndpoint: "/api/services/map/tiles/registry/{z}/{x}/{y}.pbf",
  },
  {
    key: "newSubparts",
    label: "Uued eraldised",
    color: "#21a366",
    kind: "fill",
    description: "CQL-avastused nähtaval alal",
    minZoom: 8,
    sourceKind: "geojson",
    endpoint: "/services/map/layers/new-subparts",
  },
  {
    key: "notifications",
    label: "Teatised",
    color: "#d53f5d",
    kind: "point",
    description: "Teatised nähtaval kaardialal",
    minZoom: 9,
    sourceKind: "geojson",
    endpoint: "/services/map/layers/notifications",
  },
];

function value(properties: MapProperties, key: string) {
  return String(properties[key] ?? "—");
}

function normaliseProperties(properties: MapProperties): MapProperties {
  return {
    ...properties,
    cadastreId: properties.cadastreId ?? properties.cadastre_id,
    subpartCode: properties.subpartCode ?? properties.subpart_code,
    treeType: properties.treeType ?? properties.tree_type_code,
    workCode: properties.workCode ?? properties.work_code,
  };
}

function escapeHtml(input: unknown) {
  return String(input ?? "—").replace(
    /[&<>'"]/g,
    (character) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[
        character
      ] ?? character,
  );
}

function simplePopup(layer: LayerConfig, properties: MapProperties) {
  return `<div style="min-width:190px"><b style="font-size:16px;color:#17342a">${escapeHtml(
    layer.label,
  )}</b><p style="margin:7px 0 0;font-size:13px">Katastritunnus: <b>${escapeHtml(
    properties.cadastreId,
  )}</b></p><p style="margin:4px 0;font-size:13px">Eraldis: ${escapeHtml(
    properties.subpartCode,
  )}</p><p style="margin:4px 0;font-size:13px">${escapeHtml(
    properties.workCode ?? properties.treeType ?? properties.title ?? "",
  )}</p></div>`;
}

function bbox(map: MapLibreMap) {
  const bounds = map.getBounds();
  return [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()]
    .map((number) => number.toFixed(6))
    .join(",");
}

function filterQuery(filters: MapFilters) {
  const query = new URLSearchParams();
  if (filters.customer) query.set("customer", "true");
  if (filters.activeDeal) query.set("activeDeal", "true");
  if (filters.activityDays) query.set("activityDays", filters.activityDays);
  if (filters.dealStage) query.set("dealStage", filters.dealStage);
  return query.toString();
}

function mapQuery(viewport: string, filters: MapFilters) {
  const query = new URLSearchParams({ bbox: viewport });
  if (filters.customer) query.set("customer", "true");
  if (filters.activeDeal) query.set("activeDeal", "true");
  if (filters.activityDays) query.set("activityDays", filters.activityDays);
  if (filters.dealStage) query.set("dealStage", filters.dealStage);
  return query.toString();
}

function vectorTileUrl(layer: LayerConfig, filters: MapFilters) {
  const query = filterQuery(filters);
  return `${layer.tileEndpoint}${query ? `?${query}` : ""}`;
}

function layerIds(layer: LayerConfig) {
  if (layer.kind === "fill") return [`${layer.key}-fill`, `${layer.key}-outline`];
  return [layer.kind === "point" ? `${layer.key}-point` : `${layer.key}-line`];
}

export default function MapWorkspace() {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<MapLibreMap | null>(null);
  const popup = useRef<maplibregl.Popup | null>(null);
  const refreshTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const requestId = useRef(0);
  const visibleRef = useRef<Record<LayerKey, boolean>>({
    cadastres: true,
    subparts: true,
    newSubparts: true,
    registry: true,
    notifications: true,
  });
  const filtersRef = useRef<MapFilters>(DEFAULT_FILTERS);
  const refreshMap = useRef<() => void>(() => undefined);
  const [status, setStatus] = useState("Suumige sisse, et laadida nähtava kaardiala andmed.");
  const [visible, setVisible] = useState(visibleRef.current);
  const [filters, setFilters] = useState<MapFilters>(DEFAULT_FILTERS);
  const [counts, setCounts] = useState<Record<LayerKey, number | null>>({
    cadastres: null,
    subparts: null,
    newSubparts: 0,
    registry: null,
    notifications: 0,
  });
  const [selected, setSelected] = useState<{ layer: string; properties: MapProperties } | null>(null);
  const [workspaceId, setWorkspaceId] = useState<string | null>(null);
  const [workspace, setWorkspace] = useState<CadastreWorkspace | null>(null);
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);

  useEffect(() => {
    if (!container.current || map.current) return;

    const instance = new maplibregl.Map({
      container: container.current,
      style: STYLE,
      center: [25.6, 58.7],
      zoom: 7.2,
      fadeDuration: 0,
    });
    instance.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");

    const updateLayerData = async () => {
      const currentRequest = ++requestId.current;
      const zoom = instance.getZoom();
      const viewport = bbox(instance);
      const nextCounts: Record<LayerKey, number | null> = {
        cadastres: null,
        subparts: null,
        newSubparts: 0,
        registry: null,
        notifications: 0,
      };

      await Promise.all(
        LAYERS.map(async (layer) => {
          if (!visibleRef.current[layer.key] || zoom < layer.minZoom) {
            if (layer.sourceKind === "geojson") {
              const source = instance.getSource(layer.key) as maplibregl.GeoJSONSource | undefined;
              source?.setData(EMPTY);
            }
            return;
          }
          if (layer.sourceKind === "vector") {
            const source = instance.getSource(layer.key) as maplibregl.VectorTileSource | undefined;
            source?.setTiles([vectorTileUrl(layer, filtersRef.current)]);
            return;
          }
          const source = instance.getSource(layer.key) as maplibregl.GeoJSONSource | undefined;
          if (!source || !layer.endpoint) return;
          try {
            const collection = await api.get<FeatureCollection>(
              `${layer.endpoint}?${mapQuery(viewport, filtersRef.current)}`,
            );
            if (currentRequest !== requestId.current) return;
            nextCounts[layer.key] = collection.features.length;
            source.setData(collection);
          } catch {
            if (currentRequest === requestId.current) source.setData(EMPTY);
          }
        }),
      );

      if (currentRequest !== requestId.current) return;
      setCounts(nextCounts);
      const activeVectors = LAYERS.filter(
        (layer) =>
          layer.sourceKind === "vector" &&
          visibleRef.current[layer.key] &&
          zoom >= layer.minZoom,
      );
      const legacyFeatures = Object.values(nextCounts).reduce<number>(
        (sum, count) => sum + (count ?? 0),
        0,
      );
      const vectorMessage = activeVectors.length
        ? `${activeVectors.map((layer) => layer.label).join(", ")} MVT-paanid`
        : "";
      const legacyMessage = legacyFeatures ? `${legacyFeatures} väikest GeoJSON objekti` : "";
      setStatus(
        [vectorMessage, legacyMessage].filter(Boolean).join(" · ") ||
          `Suum ${zoom.toFixed(1)} — suumige sisse, et laadida detailkihid.`,
      );
    };

    refreshMap.current = () => {
      if (refreshTimer.current) clearTimeout(refreshTimer.current);
      refreshTimer.current = setTimeout(() => {
        void updateLayerData();
      }, 220);
    };

    instance.on("load", () => {
      for (const layer of LAYERS) {
        if (layer.sourceKind === "vector") {
          instance.addSource(layer.key, {
            type: "vector",
            tiles: [vectorTileUrl(layer, filtersRef.current)],
            minzoom: layer.minZoom,
            maxzoom: 22,
            bounds: ESTONIA_BOUNDS,
            promoteId: "id",
          });
        } else {
          instance.addSource(layer.key, { type: "geojson", data: EMPTY });
        }

        const sourceLayer = layer.sourceKind === "vector" ? layer.key : undefined;
        if (layer.kind === "fill") {
          instance.addLayer({
            id: `${layer.key}-fill`,
            type: "fill",
            source: layer.key,
            ...(sourceLayer ? { "source-layer": sourceLayer } : {}),
            minzoom: layer.minZoom,
            paint: {
              "fill-color": layer.color,
              "fill-opacity": layer.key === "newSubparts" ? 0.36 : 0.2,
            },
          });
          instance.addLayer({
            id: `${layer.key}-outline`,
            type: "line",
            source: layer.key,
            ...(sourceLayer ? { "source-layer": sourceLayer } : {}),
            minzoom: layer.minZoom,
            paint: {
              "line-color": layer.color,
              "line-width": layer.key === "newSubparts" ? 2.4 : 1.2,
            },
          });
        } else if (layer.kind === "point") {
          instance.addLayer({
            id: `${layer.key}-point`,
            type: "circle",
            source: layer.key,
            minzoom: layer.minZoom,
            paint: {
              "circle-radius": 6,
              "circle-color": layer.color,
              "circle-stroke-color": "#fff",
              "circle-stroke-width": 1.5,
            },
          });
        } else {
          instance.addLayer({
            id: `${layer.key}-line`,
            type: "line",
            source: layer.key,
            ...(sourceLayer ? { "source-layer": sourceLayer } : {}),
            minzoom: layer.minZoom,
            paint: {
              "line-color": layer.color,
              "line-width": 2,
              "line-opacity": 0.86,
            },
          });
        }

        const interactionLayer = layerIds(layer)[0];
        instance.on("mouseenter", interactionLayer, () => {
          instance.getCanvas().style.cursor = "pointer";
        });
        instance.on("mouseleave", interactionLayer, () => {
          instance.getCanvas().style.cursor = "";
        });
        instance.on("click", interactionLayer, (event) => {
          const rawProperties = event.features?.[0]?.properties as MapProperties | undefined;
          if (!rawProperties) return;
          const properties = normaliseProperties(rawProperties);
          setSelected({ layer: layer.label, properties });
          if (layer.key === "cadastres") {
            const id = String(properties.id || properties.cadastreId || "");
            if (!id) return;
            setWorkspaceId(id);
            setWorkspace(null);
            setWorkspaceError(null);
            void api
              .get<CadastreWorkspace>(`/services/cadastres/${encodeURIComponent(id)}/workspace`)
              .then(setWorkspace)
              .catch((error: unknown) =>
                setWorkspaceError(
                  error instanceof Error
                    ? error.message
                    : "Katastri detailandmete laadimine ebaõnnestus.",
                ),
              );
            return;
          }
          popup.current?.remove();
          popup.current = new maplibregl.Popup({ closeButton: true, maxWidth: "290px", offset: 12 })
            .setLngLat(event.lngLat)
            .setHTML(simplePopup(layer, properties))
            .addTo(instance);
        });
      }
      refreshMap.current();
    });
    instance.on("moveend", refreshMap.current);
    map.current = instance;

    return () => {
      if (refreshTimer.current) clearTimeout(refreshTimer.current);
      popup.current?.remove();
      instance.remove();
      map.current = null;
    };
  }, []);

  const toggle = (key: LayerKey) => {
    const next = !visibleRef.current[key];
    visibleRef.current = { ...visibleRef.current, [key]: next };
    setVisible(visibleRef.current);
    const instance = map.current;
    const config = LAYERS.find((item) => item.key === key);
    if (instance && config) {
      layerIds(config).forEach((id) => {
        if (instance.getLayer(id)) {
          instance.setLayoutProperty(id, "visibility", next ? "visible" : "none");
        }
      });
    }
    refreshMap.current();
  };

  const updateFilters = (patch: Partial<MapFilters>) => {
    const next = { ...filtersRef.current, ...patch };
    filtersRef.current = next;
    setFilters(next);
    refreshMap.current();
  };

  return (
    <main className="min-h-screen bg-[#f5f7f2] p-4 text-[#17342a] md:p-7">
      <section className="mx-auto max-w-7xl overflow-hidden rounded-[2rem] border border-[#d7e1d5] bg-white shadow-[0_24px_80px_rgba(22,54,42,0.12)]">
        <header className="flex flex-col gap-4 border-b border-[#e7eee5] px-6 py-5 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-[.18em] text-[#31705a]">
              <Trees className="h-4 w-4" /> Keskne ruumiandmete töölaud
            </div>
            <h1 className="font-serif text-3xl font-semibold tracking-tight">Metsa- ja katastrivaade</h1>
            <p className="mt-1 text-sm text-[#627469]">
              Suured katastri- ja registrikihid laetakse MVT-paanidena; klõpsa katastriüksusel tervikvaate avamiseks.
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-full bg-[#edf5ed] px-4 py-2 text-sm font-medium text-[#1f5d47]">
            <RefreshCw className="h-4 w-4" /> {status}
          </div>
        </header>
        <div className="grid min-h-[610px] lg:grid-cols-[1fr_330px]">
          <div
            ref={container}
            className="min-h-[500px] lg:min-h-[610px]"
            aria-label="Interaktiivne ForestIQ GeoDjango kaart"
          />
          <aside className="border-t border-[#e7eee5] bg-[#fbfdf9] p-6 lg:border-l lg:border-t-0">
            <div className="flex items-center gap-2 text-sm font-bold text-[#28624d]">
              <SlidersHorizontal className="h-4 w-4" /> Kaardifiltrid
            </div>
            <div className="mt-3 space-y-3 rounded-xl border border-[#e2eae0] bg-white p-3 text-sm">
              <label className="flex cursor-pointer items-center justify-between gap-2">
                <span>Klient või võidetud tehing</span>
                <input
                  type="checkbox"
                  checked={filters.customer}
                  onChange={(event) => updateFilters({ customer: event.target.checked })}
                />
              </label>
              <label className="flex cursor-pointer items-center justify-between gap-2">
                <span>Aktiivne tehing</span>
                <input
                  type="checkbox"
                  checked={filters.activeDeal}
                  onChange={(event) => updateFilters({ activeDeal: event.target.checked })}
                />
              </label>
              <label className="block text-xs font-semibold text-[#587065]">
                Tehinguetapp
                <select
                  value={filters.dealStage}
                  onChange={(event) => updateFilters({ dealStage: event.target.value })}
                  className="mt-1 w-full rounded-lg border border-[#dbe8d8] bg-white px-2 py-1.5 text-sm"
                >
                  <option value="">Kõik etapid</option>
                  <option value="QUALIFICATION">Kvalifitseerimine</option>
                  <option value="EVALUATION">Hindamine</option>
                  <option value="NEGOTIATION">Läbirääkimine</option>
                  <option value="WON">Võidetud</option>
                  <option value="LOST">Kaotatud</option>
                </select>
              </label>
              <label className="block text-xs font-semibold text-[#587065]">
                Tegevusajalugu
                <select
                  value={filters.activityDays}
                  onChange={(event) => updateFilters({ activityDays: event.target.value })}
                  className="mt-1 w-full rounded-lg border border-[#dbe8d8] bg-white px-2 py-1.5 text-sm"
                >
                  <option value="">Kõik ajad</option>
                  <option value="7">Viimased 7 päeva</option>
                  <option value="30">Viimased 30 päeva</option>
                  <option value="90">Viimased 90 päeva</option>
                  <option value="365">Viimased 12 kuud</option>
                </select>
              </label>
              <button
                onClick={() => updateFilters(DEFAULT_FILTERS)}
                className="text-xs font-bold text-[#2b7455] hover:underline"
              >
                Lähtesta filtrid
              </button>
            </div>
            <div className="mt-7 flex items-center gap-2 text-sm font-bold text-[#28624d]">
              <Layers3 className="h-4 w-4" /> GeoDjango kihid
            </div>
            <div className="mt-4 space-y-2">
              {LAYERS.map((layer) => (
                <button
                  key={layer.key}
                  onClick={() => toggle(layer.key)}
                  className="flex w-full items-center justify-between rounded-xl border border-[#e2eae0] bg-white px-3 py-3 text-left transition hover:border-[#9bc3a9]"
                >
                  <span>
                    <span className="block text-sm font-semibold">
                      {layer.label}{" "}
                      <span className="text-[#63766a]">
                        ({counts[layer.key] === null ? "MVT" : counts[layer.key]})
                      </span>
                    </span>
                    <span className="mt-0.5 block text-xs text-[#708177]">{layer.description}</span>
                  </span>
                  {visible[layer.key] ? (
                    <Eye className="h-4 w-4 text-[#28704f]" />
                  ) : (
                    <EyeOff className="h-4 w-4 text-[#9aa89f]" />
                  )}
                </button>
              ))}
            </div>
            <div className="mt-7 border-t border-[#e3ebe1] pt-5">
              <div className="flex items-center gap-2 text-sm font-bold text-[#28624d]">
                <MapPinned className="h-4 w-4" /> Valitud objekt
              </div>
              {selected ? (
                <div className="mt-4 space-y-3">
                  <p className="text-xs font-bold uppercase tracking-wider text-[#718176]">{selected.layer}</p>
                  {Object.entries(selected.properties)
                    .filter(([, item]) => item !== "" && item != null)
                    .map(([key, item]) => (
                      <div key={key}>
                        <p className="text-xs uppercase tracking-wider text-[#738277]">{key}</p>
                        <p className="break-words text-sm font-medium">{value(selected.properties, key)}</p>
                      </div>
                    ))}
                </div>
              ) : (
                <p className="mt-4 text-sm leading-6 text-[#65756b]">
                  Suumige sisse ning klõpsake katastriüksusel, et avada selle terviklik detailaken.
                </p>
              )}
            </div>
          </aside>
        </div>
      </section>
      <CadastreWorkspaceDialog
        cadastreId={workspaceId}
        data={workspace}
        loading={Boolean(workspaceId && !workspace && !workspaceError)}
        error={workspaceError}
        onClose={() => {
          setWorkspaceId(null);
          setWorkspace(null);
          setWorkspaceError(null);
        }}
      />
    </main>
  );
}
