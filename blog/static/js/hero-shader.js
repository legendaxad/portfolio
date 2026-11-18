/**
 * Hero shader — raw WebGL, no dependencies.
 *
 * A domain-warped fBm "liquid light" field in the brand palette, lit by the
 * cursor. Performance guards:
 *  - device-pixel-ratio capped (1.5 desktop / 1 on small or low-power screens)
 *  - renders at a reduced internal resolution and lets CSS upscale (it's soft)
 *  - pauses when the hero is off-screen or the tab is hidden
 *  - renders one still frame for prefers-reduced-motion
 *  - context-loss handling + full resource disposal on pagehide
 * If WebGL is unavailable the CSS gradient fallback underneath stays visible.
 */
(function () {
  'use strict';

  var canvas = document.querySelector('[data-shader]');
  if (!canvas) return;

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var small = window.matchMedia('(max-width: 760px)').matches;

  var gl = canvas.getContext('webgl', {
    antialias: false, alpha: false, depth: false, stencil: false,
    premultipliedAlpha: false, powerPreference: 'low-power', preserveDrawingBuffer: false
  });
  if (!gl) return; // CSS fallback remains

  var VERT = [
    'attribute vec2 a_pos;',
    'void main(){ gl_Position = vec4(a_pos, 0.0, 1.0); }'
  ].join('\n');

  var FRAG = [
    'precision mediump float;',
    'uniform vec2  u_res;',
    'uniform float u_time;',
    'uniform vec2  u_mouse;',     // 0..1, smoothed
    'uniform float u_scroll;',    // 0..1 as hero scrolls away
    '',
    'float hash(vec2 p){ p = fract(p*vec2(123.34, 456.21)); p += dot(p, p+45.32); return fract(p.x*p.y); }',
    'float noise(vec2 p){',
    '  vec2 i = floor(p); vec2 f = fract(p);',
    '  vec2 u = f*f*(3.0-2.0*f);',
    '  return mix(mix(hash(i), hash(i+vec2(1.,0.)), u.x), mix(hash(i+vec2(0.,1.)), hash(i+vec2(1.,1.)), u.x), u.y);',
    '}',
    'float fbm(vec2 p){',
    '  float v = 0.0; float a = 0.5;',
    '  mat2 r = mat2(0.8, -0.6, 0.6, 0.8);',
    '  for (int i = 0; i < 5; i++){ v += a*noise(p); p = r*p*2.02 + 3.1; a *= 0.5; }',
    '  return v;',
    '}',
    '',
    'void main(){',
    '  vec2 uv = gl_FragCoord.xy / u_res;',
    '  float aspect = u_res.x / u_res.y;',
    '  vec2 p = (uv - 0.5) * vec2(aspect, 1.0);',
    '  vec2 m = (u_mouse - 0.5) * vec2(aspect, 1.0);',
    '  float t = u_time * 0.045;',
    '',
    // cursor gently bends the flow field
    '  vec2 toM = p - m; float md = length(toM);',
    '  p += 0.10 * normalize(toM + 1e-4) * exp(-md*2.4);',
    '',
    // two-level domain warping (Inigo Quilez style)
    '  vec2 q = vec2(fbm(p*1.35 + vec2(0.0, t)), fbm(p*1.35 + vec2(5.2, -t*0.8)));',
    '  vec2 r = vec2(fbm(p*1.6 + 3.0*q + vec2(1.7, 9.2) + t*0.6), fbm(p*1.6 + 3.0*q + vec2(8.3, 2.8) - t*0.5));',
    '  float f = fbm(p*1.2 + 3.2*r);',
    '',
    // palette: near-black → deep indigo → electric blue → cyan, a hint of violet
    '  vec3 base   = vec3(0.027, 0.031, 0.043);',
    '  vec3 indigo = vec3(0.10, 0.14, 0.38);',
    '  vec3 blue   = vec3(0.30, 0.49, 1.00);',
    '  vec3 cyan   = vec3(0.23, 0.88, 0.82);',
    '  vec3 violet = vec3(0.55, 0.48, 1.00);',
    '  vec3 col = mix(base, indigo, smoothstep(0.15, 0.75, f));',
    '  col = mix(col, blue,   smoothstep(0.55, 0.95, f) * 0.85);',
    '  col = mix(col, cyan,   smoothstep(0.62, 1.0, length(q)) * 0.38 * smoothstep(0.5, 0.9, f));',
    '  col = mix(col, violet, smoothstep(0.7, 1.0, r.x) * 0.22);',
    '',
    // light ribbons: thin bright iso-lines of the warped field
    '  float band = abs(sin(f*18.0 + t*6.0));',
    '  col += vec3(0.35, 0.55, 1.0) * pow(1.0 - band, 22.0) * 0.20 * smoothstep(0.4, 0.8, f);',
    '',
    // cursor light
    '  col += vec3(0.30, 0.45, 1.0) * 0.20 * exp(-md*md*7.0);',
    '',
    // keep the left (text) side calmer and darker for readability
    '  float textMask = smoothstep(0.15, 0.85, uv.x) * 0.65 + 0.35;',
    '  col = mix(base, col, textMask);',
    '',
    // vignette + scroll fade
    '  float vig = smoothstep(1.25, 0.25, length((uv - vec2(0.62, 0.55)) * vec2(aspect*0.85, 1.1)));',
    '  col = mix(base, col, vig);',
    '  col = mix(col, base, u_scroll*0.85);',
    '',
    // fine grain (dithers banding)
    '  col += (hash(gl_FragCoord.xy + fract(u_time)) - 0.5) * 0.025;',
    '  gl_FragColor = vec4(col, 1.0);',
    '}'
  ].join('\n');

  var program, buffer, uRes, uTime, uMouse, uScroll;
  var raf = 0, running = false, visible = true, disposed = false;
  var start = performance.now(), last = 0;
  var mouse = { x: 0.7, y: 0.6, tx: 0.7, ty: 0.6 };
  var scroll = 0;
  var dprCap = small ? 1 : 1.5;
  var scale = small ? 0.5 : 0.65; // internal resolution factor

  function compile(type, src) {
    var s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      console.warn('[hero-shader]', gl.getShaderInfoLog(s));
      gl.deleteShader(s);
      return null;
    }
    return s;
  }

  function init() {
    var vs = compile(gl.VERTEX_SHADER, VERT);
    var fs = compile(gl.FRAGMENT_SHADER, FRAG);
    if (!vs || !fs) return false;
    program = gl.createProgram();
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);
    gl.deleteShader(vs);
    gl.deleteShader(fs);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return false;
    gl.useProgram(program);

    buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(program, 'a_pos');
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

    uRes = gl.getUniformLocation(program, 'u_res');
    uTime = gl.getUniformLocation(program, 'u_time');
    uMouse = gl.getUniformLocation(program, 'u_mouse');
    uScroll = gl.getUniformLocation(program, 'u_scroll');
    return true;
  }

  function resize() {
    var dpr = Math.min(window.devicePixelRatio || 1, dprCap) * scale;
    var w = Math.max(1, Math.floor(canvas.clientWidth * dpr));
    var h = Math.max(1, Math.floor(canvas.clientHeight * dpr));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
      gl.viewport(0, 0, w, h);
    }
    gl.uniform2f(uRes, w, h);
  }

  function draw(now) {
    var t = (now - start) / 1000;
    mouse.x += (mouse.tx - mouse.x) * 0.045;
    mouse.y += (mouse.ty - mouse.y) * 0.045;
    gl.uniform1f(uTime, reduceMotion ? 12.0 : t);
    gl.uniform2f(uMouse, mouse.x, mouse.y);
    gl.uniform1f(uScroll, scroll);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }

  function frame(now) {
    if (!running) return;
    raf = requestAnimationFrame(frame);
    // ~40fps is plenty for a slow-moving field and saves battery
    if (now - last < 24) return;
    last = now;
    draw(now);
  }

  function play() {
    if (running || disposed || reduceMotion || !visible || document.hidden) return;
    running = true;
    raf = requestAnimationFrame(frame);
  }
  function pause() { running = false; cancelAnimationFrame(raf); }

  function dispose() {
    disposed = true;
    pause();
    if (program) gl.deleteProgram(program);
    if (buffer) gl.deleteBuffer(buffer);
    var ext = gl.getExtension('WEBGL_lose_context');
    if (ext) ext.loseContext();
  }

  if (!init()) return;
  resize();
  draw(performance.now());
  canvas.classList.add('is-ready');

  // Interaction
  if (!reduceMotion && window.matchMedia('(pointer: fine)').matches) {
    window.addEventListener('pointermove', function (e) {
      mouse.tx = e.clientX / window.innerWidth;
      mouse.ty = 1 - e.clientY / window.innerHeight;
    }, { passive: true });
  }

  var hero = canvas.closest('[data-hero]') || canvas;
  window.addEventListener('scroll', function () {
    scroll = Math.min(1, Math.max(0, window.scrollY / (hero.offsetHeight || 1)));
    if (!running && visible) draw(performance.now());
  }, { passive: true });

  var ro = 'ResizeObserver' in window ? new ResizeObserver(function () { resize(); if (!running) draw(performance.now()); }) : null;
  if (ro) ro.observe(canvas); else window.addEventListener('resize', resize);

  new IntersectionObserver(function (entries) {
    visible = entries[0].isIntersecting;
    visible ? play() : pause();
  }).observe(hero);

  document.addEventListener('visibilitychange', function () { document.hidden ? pause() : play(); });

  canvas.addEventListener('webglcontextlost', function (e) { e.preventDefault(); pause(); canvas.classList.remove('is-ready'); });
  canvas.addEventListener('webglcontextrestored', function () { if (init()) { resize(); canvas.classList.add('is-ready'); play(); } });

  window.addEventListener('pagehide', function (e) { if (!e.persisted) { if (ro) ro.disconnect(); dispose(); } });
  window.addEventListener('pageshow', function (e) { if (e.persisted && !disposed) play(); });

  play();
})();
