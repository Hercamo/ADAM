import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";
import type { DimensionScore } from "../types";
import { DIMENSION_ORDER } from "../types";

interface Props {
  scores: Record<string, DimensionScore> | null;
  height?: number;
}

export default function DimensionRadar({ scores, height = 280 }: Props) {
  if (!scores) {
    return (
      <div className="text-sm text-slate-500 italic">
        Run a scoring to populate the radar.
      </div>
    );
  }
  const data = DIMENSION_ORDER.map((dim) => ({
    dimension: dim,
    score: scores[dim]?.raw_score ?? 0,
  }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart data={data} outerRadius="75%">
        <PolarGrid stroke="#1f2937" />
        <PolarAngleAxis
          dataKey="dimension"
          stroke="#94a3b8"
          tick={{ fontSize: 11, fill: "#cbd5e1" }}
        />
        <PolarRadiusAxis
          angle={30}
          domain={[0, 100]}
          tick={{ fontSize: 10, fill: "#64748b" }}
          stroke="#1f2937"
        />
        <Radar
          dataKey="score"
          stroke="#60a5fa"
          fill="#60a5fa"
          fillOpacity={0.35}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
