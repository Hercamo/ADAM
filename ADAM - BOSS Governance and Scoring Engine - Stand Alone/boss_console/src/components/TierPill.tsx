import type { EscalationTier } from "../types";
import { TIER_META } from "../types";

interface Props {
  tier: EscalationTier;
  showDescription?: boolean;
}

export default function TierPill({ tier, showDescription }: Props) {
  const meta = TIER_META[tier];
  return (
    <div className="flex items-center gap-2">
      <span
        className={`pill border uppercase tracking-wider ${meta.color}`}
        title={meta.description}
      >
        {meta.label}
      </span>
      {showDescription && (
        <span className="text-xs text-slate-400">{meta.description}</span>
      )}
    </div>
  );
}
