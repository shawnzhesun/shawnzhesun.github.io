/** A decorative, non-interactive "command center" drawn onto the TV. Mirrors the baked
 *  terminal texture (scripts/comic_art.py) so the swap from render to live is seamless. */
const W = 960, H = 540;
const C = { bg:'#090d14', bar:'#161b22', green:'#7ee787', cyan:'#79c0ff', amber:'#f2cc60', pink:'#ff7b72', dim:'#465468', fg:'#c9d1d9', off:'#1c2430' };
const JOBS = [
  ['render', 'view 12/25  ok'], ['mix', 'bounce  journal_v3.wav'], ['sync', 'tide-of-echo/stems  ↑ 2.1 GB'],
  ['build', 'site  ✓ 412 ms'], ['deploy', 'shawnzhesun.github.io  ok'], ['agent', 'eval run 0419  pass 47/50'],
  ['tune', 'E standard  ✓'], ['backup', 'sessions → nas  ok'], ['track', 'echo of tide  take 7'], ['comp', '1176  -4.5 dB GR'],
  ['amp', 'vox  warmed up'], ['pedal', 'strymon  preset 12'], ['agent', 'plan → code → review  ✓'], ['cache', 'scene.json  hit'],
];
const pad = n => String(n).padStart(2, '0');
const clock = d => `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;

export class LiveTerminal {
  constructor(canvas, { still = false } = {}) {
    this.canvas = canvas; this.ctx = canvas.getContext('2d'); this.still = still;
    canvas.width = W * 2; canvas.height = H * 2; this.ctx.scale(2, 2);
    this.stats = [.62, .81, .47, .33, .56]; this.levels = Array.from({ length: 12 }, () => Math.random() * .7 + .2);
    this.traffic = Array.from({ length: 60 }, (_, i) => .5 + .35 * Math.sin(i * .17) * Math.sin(i * .05));
    this.log = []; this.job = 0; for (let i = 0; i < 8; i++) this.push();
    this.tick = 0; this.timer = null;
  }
  push() {
    const [kind, text] = JOBS[this.job++ % JOBS.length];
    this.log.push([clock(new Date()), kind, text]); if (this.log.length > 8) this.log.shift();
  }
  start() {
    this.draw();
    if (this.still || this.timer) return;
    this.timer = setInterval(() => { if (!document.hidden) { this.step(); this.draw(); } }, 110);
  }
  stop() { clearInterval(this.timer); this.timer = null; }
  step() {
    this.tick++;
    this.stats = this.stats.map(v => Math.min(.97, Math.max(.08, v + (Math.random() - .5) * .06)));
    this.levels = this.levels.map(v => Math.max(.05, Math.min(1, v * .78 + Math.random() * .32)));
    if (this.tick % 3 === 0) { this.traffic.shift(); this.traffic.push(Math.max(.05, Math.min(.95, this.traffic.at(-1) + (Math.random() - .5) * .25))); }
    if (this.tick % 12 === 0) this.push();
  }
  pane(x0, y0, x1, y1, title) {
    const c = this.ctx; c.strokeStyle = C.cyan; c.lineWidth = 1.5; c.strokeRect(x0, y0, x1 - x0, y1 - y0);
    c.fillStyle = C.bg; c.fillRect(x0 + 9, y0 - 7, 12 + title.length * 6.6, 14); c.fillStyle = C.cyan; c.fillText(title, x0 + 12, y0 + 4);
  }
  draw() {
    const c = this.ctx, now = new Date();
    c.fillStyle = C.bg; c.fillRect(0, 0, W, H); c.textBaseline = 'alphabetic';
    c.fillStyle = C.bar; c.fillRect(0, 0, W, 26);
    c.font = '13px Menlo, ui-monospace, monospace'; c.fillStyle = C.green; c.fillText('shawn@studio: ~/command-center', 12, 18);
    c.fillStyle = C.amber; c.fillText(clock(now), W - 100, 18);
    c.font = '11px Menlo, ui-monospace, monospace';
    this.pane(10, 36, 470, 280, 'SYSTEMS'); this.pane(480, 36, 950, 280, 'MIX BUS');
    this.pane(10, 290, 590, 500, 'LOG · tail -f studio.log'); this.pane(600, 290, 950, 500, 'TRAFFIC');
    c.font = '13px Menlo, ui-monospace, monospace';
    ['cpu', 'gpu', 'mem', 'disk', 'net'].forEach((k, i) => {
      const y = 60 + i * 42, v = this.stats[i], n = 36; c.fillStyle = C.fg; c.fillText(k, 25, y + 16);
      for (let j = 0; j < n; j++) { c.fillStyle = j < v * n ? (j / n < .6 ? C.green : j / n < .85 ? C.amber : C.pink) : C.off; c.fillRect(75 + j * 10, y + 2, 7, 15); }
      c.fillStyle = C.fg; c.fillText(`${Math.round(v * 100)}%`.padStart(4), 415, y + 16);
    });
    this.levels.forEach((lvl, k) => {
      const x = 500 + k * 36;
      for (let j = 0; j < 16; j++) { c.fillStyle = j < lvl * 16 ? (j < 10 ? C.green : j < 14 ? C.amber : C.pink) : C.off; c.fillRect(x, 260 - j * 13 - 10, 25, 10); }
    });
    c.font = '11px Menlo, ui-monospace, monospace';
    this.log.forEach(([t, kind, text], i) => {
      const y = 318 + i * 22; c.fillStyle = C.dim; c.fillText(`[${t}]`, 25, y);
      c.fillStyle = [C.green, C.cyan, C.fg, C.amber][i % 4]; c.fillText(kind.padEnd(8) + text, 140, y);
    });
    c.fillStyle = C.green; c.fillText('$', 25, 318 + 8 * 22);
    if (this.still || Math.floor(this.tick / 5) % 2 === 0) c.fillRect(37, 318 + 8 * 22 - 10, 7, 12);
    c.strokeStyle = C.dim; c.lineWidth = 1; c.beginPath(); c.moveTo(615, 480); c.lineTo(940, 480); c.stroke();
    c.strokeStyle = C.cyan; c.lineWidth = 2; c.beginPath();
    this.traffic.forEach((v, i) => { const x = 615 + i * 5.5, y = 480 - v * 160; i ? c.lineTo(x, y) : c.moveTo(x, y); }); c.stroke();
  }
}
export const TERMINAL_SIZE = { width: W, height: H };
