// Fixed 0-100 scale so a flat line really means a flat risk, not a zoomed-in wobble.
export default function Sparkline({ values, width = 84, height = 24 }: { values: number[]; width?: number; height?: number }) {
  if (values.length < 2) return <svg width={width} height={height} aria-hidden="true" />;
  const xy = values.map((v, i) => [(i / (values.length - 1)) * width, height - 1 - (v / 100) * (height - 2)]);
  const [lastX, lastY] = xy[xy.length - 1];

  return (
    <svg width={width} height={height} className="sparkline" aria-hidden="true">
      <polyline points={xy.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ")} />
      <circle cx={lastX} cy={lastY} r="2" />
    </svg>
  );
}
