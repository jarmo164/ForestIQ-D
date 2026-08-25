import { useEffect, useRef, useState } from "react";
import maplibregl, { type Map as MapLibreMap } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { MapPinned, RefreshCw, Trees } from "lucide-react";
import { api } from "@/lib/api";

type FeatureCollection = GeoJSON.FeatureCollection<GeoJSON.Geometry, { id: string; name: string; county: string; area: string }>;

const STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: { openfreemap: { type: "raster", tiles: ["https://tiles.openfreemap.org/styles/liberty/{z}/{x}/{y}.png"], tileSize: 256, attribution: "© OpenFreeMap" } },
  layers: [{ id: "base", type: "raster", source: "openfreemap" }],
};

export default function MapWorkspace() {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<MapLibreMap | null>(null);
  const [status, setStatus] = useState("Kaardiandmeid laaditakse…");
  const [selected, setSelected] = useState<{ id: string; name: string; county: string; area: string } | null>(null);

  useEffect(() => {
    if (!container.current || map.current) return;
    const instance = new maplibregl.Map({ container: container.current, style: STYLE, center: [25.6, 58.7], zoom: 6.4 });
    instance.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
    instance.on("load", async () => {
      try {
        const collection = await api.get<FeatureCollection>("/services/map/cadastres");
        instance.addSource("cadastres", { type: "geojson", data: collection });
        instance.addLayer({ id: "cadastre-fill", type: "fill", source: "cadastres", paint: { "fill-color": "#13795b", "fill-opacity": 0.22 } });
        instance.addLayer({ id: "cadastre-outline", type: "line", source: "cadastres", paint: { "line-color": "#0d4b38", "line-width": 1.5 } });
        instance.on("mouseenter", "cadastre-fill", () => { instance.getCanvas().style.cursor = "pointer"; });
        instance.on("mouseleave", "cadastre-fill", () => { instance.getCanvas().style.cursor = ""; });
        instance.on("click", "cadastre-fill", (event) => {
          const properties = event.features?.[0]?.properties;
          if (properties) setSelected({ id: String(properties.id || ""), name: String(properties.name || "Nimetu katastriüksus"), county: String(properties.county || ""), area: String(properties.area || "") });
        });
        setStatus(collection.features.length ? `${collection.features.length} katastriüksust kaardil` : "Selles vaates pole veel valideeritud geomeetriaid.");
      } catch (error) {
        setStatus(error instanceof Error ? error.message : "Kaardiandmete laadimine ebaõnnestus.");
      }
    });
    map.current = instance;
    return () => { instance.remove(); map.current = null; };
  }, []);

  return <main className="min-h-screen bg-[#f5f7f2] text-[#17342a] p-4 md:p-7"><section className="mx-auto max-w-7xl overflow-hidden rounded-[2rem] border border-[#d7e1d5] bg-white shadow-[0_24px_80px_rgba(22,54,42,0.12)]"><header className="flex flex-col gap-4 border-b border-[#e7eee5] px-6 py-5 md:flex-row md:items-center md:justify-between"><div><div className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-[0.18em] text-[#31705a]"><Trees className="h-4 w-4" /> Ruumiandmete töölaud</div><h1 className="font-serif text-3xl font-semibold tracking-tight">Metsa- ja katastrivaade</h1><p className="mt-1 text-sm text-[#627469]">PostGIS-i valideeritud geomeetria, MapLibre’i kaardikiht ja olemasolevad ForestIQ andmevood.</p></div><div className="flex items-center gap-2 rounded-full bg-[#edf5ed] px-4 py-2 text-sm font-medium text-[#1f5d47]"><RefreshCw className="h-4 w-4" /> {status}</div></header><div className="grid min-h-[610px] lg:grid-cols-[1fr_300px]"><div ref={container} className="min-h-[500px] lg:min-h-[610px]" aria-label="Interaktiivne ForestIQ kaart" /><aside className="border-t border-[#e7eee5] bg-[#fbfdf9] p-6 lg:border-l lg:border-t-0"><div className="flex items-center gap-2 text-sm font-bold text-[#28624d]"><MapPinned className="h-4 w-4" /> Valitud üksus</div>{selected ? <div className="mt-5 space-y-4"><div><p className="text-xs uppercase tracking-wider text-[#738277]">Katastritunnus</p><p className="font-mono text-sm font-semibold">{selected.id}</p></div><div><p className="text-xs uppercase tracking-wider text-[#738277]">Nimetus</p><p className="font-medium">{selected.name}</p></div><div><p className="text-xs uppercase tracking-wider text-[#738277]">Maakond</p><p>{selected.county || "—"}</p></div><div><p className="text-xs uppercase tracking-wider text-[#738277]">Pindala</p><p>{selected.area ? `${selected.area} ha` : "—"}</p></div></div> : <p className="mt-5 text-sm leading-6 text-[#65756b]">Vali kaardilt roheline katastriüksus, et näha selle andmeid. Kiht sisaldab ainult kontrollitud geomeetriaga objekte.</p>}</aside></div></section></main>;
}
