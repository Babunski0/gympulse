export type Coords = { latitude: number; longitude: number };

export type GymMapProps = {
  /** Gym centre; null shows the default area with no pin yet. */
  value: Coords | null;
  radiusM: number;
  /** When set, tapping the map (or dragging the pin on phones) moves the gym centre. */
  onChange?: (coords: Coords) => void;
  /** Move the view without placing a pin (e.g. to a searched city). New object = new move. */
  focus?: MapFocus | null;
  height?: number;
};

export type MapFocus = { coords: Coords; zoom: "city" | "street" };

// Podgorica, used until the gym has a location.
export const DEFAULT_CENTER: Coords = { latitude: 42.4411, longitude: 19.2627 };
