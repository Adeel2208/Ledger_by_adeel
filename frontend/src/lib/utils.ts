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

export const AXIS_META: Record<string, { label: string; color: string; bar: string }> = {
  founder: { label: "Founder", color: "text-founder", bar: "bg-founder" },
  market: { label: "Market", color: "text-market", bar: "bg-market" },
  idea: { label: "Idea vs Market", color: "text-idea", bar: "bg-idea" },
};

export const CONFIDENCE_META: Record<string, { label: string; cls: string }> = {
  verified: { label: "Verified", cls: "bg-verified/15 text-verified" },
  corroborated: { label: "Corroborated", cls: "bg-corroborated/15 text-corroborated" },
  claimed: { label: "Claimed", cls: "bg-claimed/15 text-claimed" },
  scraped: { label: "Scraped", cls: "bg-scraped/15 text-scraped" },
};
