import { useEffect, useRef, useState } from "react";
import maplibregl, { type Map as MapLibreMap } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { Eye, EyeOff, Layers3, MapPinned, RefreshCw, Trees } from "lucide-react";
import { api } from "@/lib/api";

type MapProperties = Record<string, string | number | boolean | null | undefined>;
type FeatureCollection = GeoJSON.FeatureCollection<GeoJSON.Geometry, MapProperties>;
type LayerKey = "cadastres" | "subparts" | "registry" | "notifications";
type LayerConfig = { key: LayerKey; label: string; endpoint: string; color: string; kind: "fill" | "line" | "point"; description: string };

const STYLE: maplibregl.StyleSpecification = { version: 8, sources: { openfreemap: { type: "raster", tiles: ["https://tiles.openfreemap.org/styles/liberty/{z}/{x}/{y}.png"], tileSize: 256, attribution: "© OpenFreeMap" } }, layers: [{ id: "base", type: "raster", source: "openfreemap" }] };
const LAYERS: LayerConfig[] = [
  { key: "cadastres", label: "Katastriüksused", endpoint: "/services/map/cadastres", color: "#13795b", kind: "fill", description: "Valideeritud katastripiirid" },
  { key: "subparts", label: "Metsaeraldised", endpoint: "/services/map/layers/subparts", color: "#e58e26", kind: "line", description: "GeoDjango eraldiste geomeetria" },
  { key: "registry", label: "Metsaregistri objektid", endpoint: "/services/map/layers/registry", color: "#805ad5", kind: "line", description: "Metsaregistri WFS-i objektid" },
  { key: "notifications", label: "Teatised", endpoint: "/services/map/layers/notifications", color: "#d53f5d", kind: "point", description: "Uute eraldiste teatiste markerid" },
];

function value(properties: MapProperties, key: string) { return String(properties[key] ?? "—"); }

export default function MapWorkspace() {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<MapLibreMap | null>(null);
  const [status, setStatus] = useState("Kaardiandmeid laaditakse…");
  const [visible, setVisible] = useState<Record<LayerKey, boolean>>({ cadastres: true, subparts: true, registry: true, notifications: true });
  const [counts, setCounts] = useState<Record<LayerKey, number>>({ cadastres: 0, subparts: 0, registry: 0, notifications: 0 });
  const [selected, setSelected] = useState<{ layer: string; properties: MapProperties } | null>(null);

  useEffect(() => {
    if (!container.current || map.current) return;
    const instance = new maplibregl.Map({ container: container.current, style: STYLE, center: [25.6, 58.7], zoom: 6.4 });
    instance.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
    instance.on("load", async () => {
      try {
        const collections = await Promise.all(LAYERS.map(async layer => ({ layer, collection: await api.get<FeatureCollection>(layer.endpoint) })));
        const nextCounts = { cadastres: 0, subparts: 0, registry: 0, notifications: 0 };
        for (const { layer, collection } of collections) {
          nextCounts[layer.key] = collection.features.length;
          instance.addSource(layer.key, { type: "geojson", data: collection });
          if (layer.kind === "fill") {
            instance.addLayer({ id: `${layer.key}-fill`, type: "fill", source: layer.key, paint: { "fill-color": layer.color, "fill-opacity": 0.2 } });
            instance.addLayer({ id: `${layer.key}-outline`, type: "line", source: layer.key, paint: { "line-color": "#0d4b38", "line-width": 1.5 } });
          } else if (layer.kind === "point") {
            instance.addLayer({ id: `${layer.key}-point`, type: "circle", source: layer.key, paint: { "circle-radius": 6, "circle-color": layer.color, "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.5 } });
          } else {
            instance.addLayer({ id: `${layer.key}-line`, type: "line", source: layer.key, paint: { "line-color": layer.color, "line-width": 2.2, "line-opacity": 0.88 } });
          }
          const interactionLayer = `${layer.key}-${layer.kind === "fill" ? "fill" : layer.kind === "point" ? "point" : "line"}`;
          instance.on("mouseenter", interactionLayer, () => { instance.getCanvas().style.cursor = "pointer"; });
          instance.on("mouseleave", interactionLayer, () => { instance.getCanvas().style.cursor = ""; });
          instance.on("click", interactionLayer, event => { const properties = event.features?.[0]?.properties; if (properties) setSelected({ layer: layer.label, properties }); });
        }
        setCounts(nextCounts);
        setStatus(`${Object.values(nextCounts).reduce((sum, count) => sum + count, 0)} GeoDjango objekti neljal kaardikihil`);
      } catch (error) { setStatus(error instanceof Error ? error.message : "Kaardiandmete laadimine ebaõnnestus."); }
    });
    map.current = instance;
    return () => { instance.remove(); map.current = null; };
  }, []);

  const toggle = (key: LayerKey) => {
    const next = !visible[key];
    setVisible(current => ({ ...current, [key]: next }));
    const instance = map.current;
    if (!instance) return;
    const config = LAYERS.find(item => item.key === key)!;
    const ids = config.kind === "fill" ? [`${key}-fill`, `${key}-outline`] : [config.kind === "point" ? `${key}-point` : `${key}-line`];
    ids.forEach(id => { if (instance.getLayer(id)) instance.setLayoutProperty(id, "visibility", next ? "visible" : "none"); });
  };

  return <main className="min-h-screen bg-[#f5f7f2] p-4 text-[#17342a] md:p-7"><section className="mx-auto max-w-7xl overflow-hidden rounded-[2rem] border border-[#d7e1d5] bg-white shadow-[0_24px_80px_rgba(22,54,42,0.12)]"><header className="flex flex-col gap-4 border-b border-[#e7eee5] px-6 py-5 md:flex-row md:items-center md:justify-between"><div><div className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-[0.18em] text-[#31705a]"><Trees className="h-4 w-4" /> Ruumiandmete töölaud</div><h1 className="font-serif text-3xl font-semibold tracking-tight">Metsa- ja katastrivaade</h1><p className="mt-1 text-sm text-[#627469]">GeoDjango WFS/GeoJSON kihid, PostGIS-i valideeritud geomeetria ja MapLibre’i kaarditööriistad.</p></div><div className="flex items-center gap-2 rounded-full bg-[#edf5ed] px-4 py-2 text-sm font-medium text-[#1f5d47]"><RefreshCw className="h-4 w-4" /> {status}</div></header><div className="grid min-h-[610px] lg:grid-cols-[1fr_330px]"><div ref={container} className="min-h-[500px] lg:min-h-[610px]" aria-label="Interaktiivne ForestIQ GeoDjango kaart" /><aside className="border-t border-[#e7eee5] bg-[#fbfdf9] p-6 lg:border-l lg:border-t-0"><div className="flex items-center gap-2 text-sm font-bold text-[#28624d]"><Layers3 className="h-4 w-4" /> GeoDjango kihid</div><div className="mt-4 space-y-2">{LAYERS.map(layer => <button key={layer.key} onClick={() => toggle(layer.key)} className="flex w-full items-center justify-between rounded-xl border border-[#e2eae0] bg-white px-3 py-3 text-left transition hover:border-[#9bc3a9]"><span><span className="block text-sm font-semibold">{layer.label} <span className="text-[#63766a]">({counts[layer.key]})</span></span><span className="mt-0.5 block text-xs text-[#708177]">{layer.description}</span></span>{visible[layer.key] ? <Eye className="h-4 w-4 text-[#28704f]" /> : <EyeOff className="h-4 w-4 text-[#9aa89f]" />}</button>)}</div><div className="mt-7 border-t border-[#e3ebe1] pt-5"><div className="flex items-center gap-2 text-sm font-bold text-[#28624d]"><MapPinned className="h-4 w-4" /> Valitud objekt</div>{selected ? <div className="mt-4 space-y-3"><p className="text-xs font-bold uppercase tracking-wider text-[#718176]">{selected.layer}</p>{Object.entries(selected.properties).filter(([, item]) => item !== "" && item != null).map(([key, item]) => <div key={key}><p className="text-xs uppercase tracking-wider text-[#738277]">{key}</p><p className="break-words text-sm font-medium">{value(selected.properties, key)}</p></div>)}</div> : <p className="mt-4 text-sm leading-6 text-[#65756b]">Kasuta kihipaneeli nähtavuse muutmiseks ning vali kaardilt objekt selle GeoDjango atribuutide vaatamiseks.</p>}</div></aside></div></section></main>;
}
