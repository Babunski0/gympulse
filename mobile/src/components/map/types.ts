export type Coords = { latitude: number; longitude: number };

export type GymMapProps = {
  /** Gym centre; null shows the default area with no pin yet. */
  value: Coords | null;
  radiusM: number;
  /** When set, tapping the map (or dragging the pin on phones) moves the gym centre. */
  onChange?: (coords: Coords) => void;
  height?: number;
};

// Podgorica, used until the gym has a location.
export const DEFAULT_CENTER: Coords = { latitude: 42.4411, longitude: 19.2627 };
