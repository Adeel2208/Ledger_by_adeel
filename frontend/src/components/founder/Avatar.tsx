import { mediaUrl } from "@/api/client";
import type { AvatarBlock } from "@/api/types";
import { cn } from "@/lib/utils";
import { useState } from "react";

const SIZES = {
  sm: { box: "h-8 w-8", text: "text-[11px]", ring: "ring-1" },
  md: { box: "h-12 w-12", text: "text-sm", ring: "ring-1" },
  lg: { box: "h-20 w-20", text: "text-xl", ring: "ring-2" },
  xl: { box: "h-28 w-28", text: "text-3xl", ring: "ring-4" },
} as const;

/**
 * Founder avatar — photo when the founder supplied one, otherwise a designed
 * initials monogram.
 *
 * Outbound-discovered founders have no photo by design (we never scrape one),
 * so the monogram is a first-class state rather than a broken-image fallback:
 * it carries a deterministic per-founder colour from the backend so the profile
 * still reads as finished. A photo that fails to load degrades to the same
 * monogram instead of an empty box.
 */
export function Avatar({
  profile,
  name,
  size = "md",
  className,
}: {
  /** Full FounderProfile works too — only photo_url + monogram are read. */
  profile: AvatarBlock;
  name: string;
  size?: keyof typeof SIZES;
  className?: string;
}) {
  const [failed, setFailed] = useState(false);
  const src = mediaUrl(profile.photo_url);
  const s = SIZES[size];

  const shell = cn(
    "shrink-0 overflow-hidden rounded-full ring-white/80 shadow-soft",
    s.box,
    s.ring,
    className,
  );

  if (src && !failed) {
    return (
      <img
        src={src}
        alt={name}
        loading="lazy"
        onError={() => setFailed(true)}
        className={cn(shell, "object-cover")}
      />
    );
  }

  return (
    <div
      className={cn(shell, "flex items-center justify-center font-display font-semibold text-white")}
      style={{ backgroundColor: profile.monogram.color }}
      // The initials are decorative; the accessible name comes from surrounding
      // context, so don't have a screen reader announce "MU".
      role="img"
      aria-label={name}
    >
      <span aria-hidden className={s.text}>
        {profile.monogram.initials}
      </span>
    </div>
  );
}
