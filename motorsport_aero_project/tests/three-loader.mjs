// Node-only import-map equivalent for testing procedural geometry without a browser.
export function resolve(specifier,context,nextResolve){
  if(specifier==='three')return {url:new URL('../reports/vendor/three/three.module.js',import.meta.url).href,shortCircuit:true};
  return nextResolve(specifier,context);
}
