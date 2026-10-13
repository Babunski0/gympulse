import { useFocusEffect } from "expo-router";
import { useCallback, useRef, useState } from "react";

import { errorMessage } from "@/i18n/sr";

/** Loads data whenever the screen comes into focus, so lists stay fresh after edits. */
export function useFocusData<T>(load: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const loadRef = useRef(load);
  loadRef.current = load;

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      setData(await loadRef.current());
      setError(null);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useFocusEffect(useCallback(() => void reload(), [reload, ...deps]));

  return { data, error, loading, reload, setData };
}
