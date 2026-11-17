// Original palettes. Negative / neutral / positive always share the legend's order.
export const palettes = {
  accessible: { label: 'Blue / orange', negative: '#a45612', positive: '#155da6', stops: ['#a45612','#e4b480','#f7f7f2','#91bde2','#155da6'] },
  classic: { label: 'Blue / red', negative: '#b1333b', positive: '#155da6', stops: ['#b1333b','#e6a0a4','#f7f7f2','#91bde2','#155da6'] },
};
export const defaults = { palette: 'accessible', scale: 'focused', borders: 'subtle' };

export function colorSettings(value) {
  return {
    palette: Object.hasOwn(palettes, value?.palette) ? value.palette : defaults.palette,
    scale: ['focused','fixed'].includes(value?.scale) ? value.scale : defaults.scale,
    borders: ['subtle','strong','none'].includes(value?.borders) ? value.borders : defaults.borders,
  };
}

// Symmetric domains preserve zero; rounding never clips a focused view's values.
export function colorLimit(mode, scale, values, units = false) {
  if (mode === 'district') return null;
  if (units) return 100; // Voting units retain a comparable full-range scale.
  if (scale === 'fixed' && mode !== 'population') return mode === 'gap' ? 200 : 100;
  const extent = Math.max(1, ...values.filter(Number.isFinite).map(Math.abs));
  if (mode === 'population') return Math.ceil(extent);
  return [2,5,10,15,20,30,40,50,75,100,150,200].find(n => n >= extent) ?? Math.ceil(extent);
}

export function colorExpression(property, limit, palette) {
  const stops = palettes[palette].stops;
  return ['case',['==',['get',property],null],'#a9b5bf',
    ['interpolate',['linear'],['coalesce',['get',property],0],
      -limit,stops[0],-limit/2,stops[1],0,stops[2],limit/2,stops[3],limit,stops[4]]];
}
