import { useFocusEffect } from "expo-router";
import { useCallback, useRef, useState } from "react";

import { errorMessage } from "@/i18n/sr";

/**
 * Loads data whenever the screen comes into focus, so lists stay fresh after edits.
 * With refreshMs it also reloads on that interval while the screen stays open (live occupancy).
 */
export function useFocusData<T>(load: () => Promise<T>, deps: unknown[] = [], refreshMs?: number) {
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

  useFocusEffect(
    // eslint-disable-next-line react-hooks/exhaustive-deps
    useCallback(() => {
      void reload();
      if (!refreshMs) return;
      const timer = setInterval(() => void reload(), refreshMs);
      return () => clearInterval(timer);
    }, [reload, refreshMs, ...deps]),
  );

  return { data, error, loading, reload, setData };
}
