import "leaflet/dist/leaflet.css";

import { useEffect } from "react";
import { View } from "react-native";
import { Circle, CircleMarker, MapContainer, TileLayer, useMap, useMapEvents } from "react-leaflet";

import { colors } from "../theme";
import { DEFAULT_CENTER, type Coords, type GymMapProps, type MapFocus } from "./types";

function ClickToPlace({ onChange }: { onChange: (c: Coords) => void }) {
  useMapEvents({ click: (e) => onChange({ latitude: e.latlng.lat, longitude: e.latlng.lng }) });
  return null;
}

function FollowPin({ value }: { value: Coords | null }) {
  const map = useMap();
  useEffect(() => {
    if (value) map.setView([value.latitude, value.longitude], Math.max(map.getZoom(), 17));
  }, [map, value?.latitude, value?.longitude]); // eslint-disable-line react-hooks/exhaustive-deps
  return null;
}

function FollowFocus({ focus }: { focus: MapFocus | null | undefined }) {
  const map = useMap();
  useEffect(() => {
    if (focus) map.setView([focus.coords.latitude, focus.coords.longitude], focus.zoom === "city" ? 13 : 17);
  }, [map, focus]);
  return null;
}

/** Web version (browser preview) using Leaflet with OpenStreetMap tiles. */
export function GymMap({ value, radiusM, onChange, focus, height = 260 }: GymMapProps) {
  const center = value ?? DEFAULT_CENTER;
  return (
    <View
      style={{ height, borderRadius: 12, overflow: "hidden", borderWidth: 1, borderColor: colors.border }}
    >
      <MapContainer
        center={[center.latitude, center.longitude]}
        zoom={value ? 17 : 13}
        style={{ height: "100%", width: "100%", cursor: onChange ? "crosshair" : undefined }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />
        {onChange && <ClickToPlace onChange={onChange} />}
        <FollowPin value={value} />
        <FollowFocus focus={focus} />
        {value && (
          <>
            <Circle
              center={[value.latitude, value.longitude]}
              radius={radiusM}
              pathOptions={{ color: colors.primary, weight: 2, fillOpacity: 0.15 }}
            />
            <CircleMarker
              center={[value.latitude, value.longitude]}
              radius={7}
              pathOptions={{ color: "#fff", weight: 2, fillColor: colors.primary, fillOpacity: 1 }}
            />
          </>
        )}
      </MapContainer>
    </View>
  );
}
