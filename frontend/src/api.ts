import type { RiskReport, StateSummary } from "./types";

async function req<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const b = await res.json();
      if (b?.error?.message) msg = b.error.message;
    } catch {
      /* keep generic */
    }
    throw new Error(msg);
  }
  return res.json();
}

export const listStates = () => req<{ count: number; states: StateSummary[] }>("/api/states");

export const checkWater = (state: string, district: string) => {
  const qs = new URLSearchParams({ state });
  if (district.trim()) qs.set("district", district.trim());
  return req<RiskReport>(`/api/check?${qs}`);
};

export const getMeta = () => req<{ disclaimer: string }>("/api/meta");
