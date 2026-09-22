// Display-only conversion. API values and replay calculations remain in seconds.
globalThis.AeroTime = Object.freeze({format(seconds, signed=false) {
  if (!Number.isFinite(seconds)) return '—';
  const milliseconds=Math.round(Math.abs(seconds)*1000);
  const minutes=Math.floor(milliseconds/60000);
  const remainder=milliseconds%60000;
  const sign=milliseconds===0?'':seconds<0?'−':signed?'+':'';
  return sign+minutes+':'+String(Math.floor(remainder/1000)).padStart(2,'0')+'.'+String(remainder%1000).padStart(3,'0');
}});
