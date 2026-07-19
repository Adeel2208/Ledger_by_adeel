import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind classes safely. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Score band -> semantic color (0-100). */
export function scoreColor(v: number | null | undefined): string {
  if (v == null) return "text-faint";
  if (v >= 70) return "text-success";
  if (v >= 45) return "text-claimed";
  return "text-danger";
}

export const AXIS_META: Record<
  string,
  { label: string; color: string; hex: string; hexLight: string }
> = {
  founder: { label: "Founder", color: "text-founder", hex: "#6366f1", hexLight: "#a5b4fc" },
  market: { label: "Market", color: "text-market", hex: "#10b981", hexLight: "#6ee7b7" },
  idea: { label: "Idea vs Market", color: "text-idea", hex: "#f59e0b", hexLight: "#fcd34d" },
};

export const CONFIDENCE_META: Record<string, { label: string; cls: string }> = {
  verified: { label: "Verified", cls: "bg-verified/12 text-verified ring-1 ring-verified/20" },
  corroborated: { label: "Corroborated", cls: "bg-corroborated/12 text-corroborated ring-1 ring-corroborated/20" },
  claimed: { label: "Claimed", cls: "bg-claimed/12 text-claimed ring-1 ring-claimed/20" },
  scraped: { label: "Scraped", cls: "bg-scraped/12 text-scraped ring-1 ring-scraped/20" },
};
