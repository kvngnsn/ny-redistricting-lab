export const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));
export function voteShare(counts, swing = 0) {
  const total = counts[0] + counts[1];
  return total > 0 ? clamp(counts[0] / total + swing / 100, 0, 1) : null;
}
export function margin(counts, swing = 0) {
  const share = voteShare(counts, swing);
  return share === null ? null : 100 * (2 * share - 1);
}
export function seatCounts(districts, election, swing = 0) {
  return districts.reduce((out, d) => {
    const m = margin(d.votes[election], swing);
    out[m === null || Math.abs(m) < 1e-10 ? 'tie' : m > 0 ? 'dem' : 'rep']++;
    return out;
  }, { dem: 0, rep: 0, tie: 0 });
}
export function marginLabel(value, digits = 1) {
  if (value === null) return 'No votes';
  if (Math.abs(value) < 0.000001) return 'Even';
  return `${value > 0 ? 'D' : 'R'} +${Math.abs(value).toFixed(digits)}`;
}
export function robustMargin(district) {
  const values = district.votes.map(v => margin(v)).filter(v => v !== null);
  return values.length ? Math.min(...values) : null;
}
export function csvForPlan(plan, elections) {
  const quote = x => `"${String(x).replaceAll('"', '""')}"`;
  const header = ['district', 'population', 'connected_components_excluding_island_exceptions'];
  elections.forEach(e => header.push(`${e.id}_dem`, `${e.id}_rep`, `${e.id}_other`, `${e.id}_two_party_dem_share`));
  header.push('source_credits_and_terms');
  return [header, ...plan.districts.map(d => [d.id, d.population, d.components, ...d.votes.flatMap(v => [...v, voteShare(v) ?? '']), 'Census; NY LATFOR; DRA and original contributors; The New York Times / Benjamin J. Rosenblatt. DRA BY-SA + no-sale; NYT C-UDA noncommercial. https://github.com/kvngnsn/ny-redistricting-lab/blob/main/docs/SOURCES.md'])]
    .map(row => row.map(quote).join(',')).join('\r\n') + '\r\n';
}

export function marginFit(districts, election, statewideCounts, swing = 0) {
  const target = margin(statewideCounts, swing);
  const values = districts.map(d => margin(d.votes[election], swing)).filter(m => m !== null);
  if (target === null || !values.length) return null;
  const gaps = values.map(m => m - target);
  return { target, min: Math.min(...values), max: Math.max(...values),
    maxGap: Math.max(...gaps.map(Math.abs)), rmsGap: Math.sqrt(gaps.reduce((s,g)=>s+g*g,0)/gaps.length) };
}
