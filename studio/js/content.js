// Resolved from this module, not the page URL, so images load wherever the site is served.
const art = name => new URL(`../assets/${name}`, import.meta.url).href;
export const RECORDS = [
  { key: 'modern-times', title: 'Modern Times', subtitle: 'SINGLE', art: art('albums/modern-times.webp'), href: 'https://open.spotify.com/track/1I2ffk4W1Rt6vi9Ht8p9Uw', body: 'Gold towers, a burning skyline and two glasses raised to it anyway.' },
  { key: 'echo-of-tide', title: 'Echo of Tide', subtitle: 'SINGLE', art: art('albums/echo-of-tide.webp'), href: 'https://open.spotify.com/track/4HbKy1HOeyikBuw9zeyz1a', body: 'Headphones on, floating under a breaking wave. The ocean on the poster starts here.' },
  { key: 'journal', title: 'Journal', subtitle: 'ALBUM · TIDE OF ECHO', art: art('albums/journal.webp'), href: 'https://open.spotify.com/album/2YukUrIciZZ9FmSAp3tRAm', body: 'The Tide of Echo album: static, a caged heart and a storm breaking out of the screen.' },
];
export const LINKEDIN = 'https://www.linkedin.com/in/sunzhe/';
export const PORTRAIT = art('shawn.webp');
export const POSTER = art('poster.webp');
export const ITEMS = {
  badge: { title: 'Shawn Sun', subtitle: 'SAY HELLO', action: 'Meet Shawn', hash: 'shawn' },
  guitar: { title: 'The Suhr', subtitle: 'Flame top. Charcoal burst.', action: 'See the guitar', hash: 'the-guitar' },
  amp: { title: 'The Vox', subtitle: 'Small amp. Big personality.', action: 'Meet the amp', hash: 'the-amp' },
  rack: { title: 'The signal chain', subtitle: '1073 · 1176 · LA-2A · BUS COMP', action: 'Look inside the rack', hash: 'the-signal-chain' },
  poster: { title: 'Tide of Echo', subtitle: 'THE BAND · COME ON IN', action: 'Meet the band', hash: 'tide-of-echo' },
  vinyl: { title: 'The records', subtitle: 'THREE ON THE WALL', action: 'Browse records', hash: 'records' },
  tv: { title: 'Command center', subtitle: 'ALWAYS RUNNING', action: 'Look at the command center', hash: 'command-center' },
  pedals: { title: 'The pedalboard', subtitle: 'COMP · DRIVE · OCD · DELAY · REVERB', action: 'See the pedalboard', hash: 'the-pedalboard' },
  ...Object.fromEntries(RECORDS.map(r => [r.key, { title: r.title, subtitle: r.subtitle, action: `Play ${r.title}`, hash: r.key, record: r }])),
};
export const SIGNAL_CHAIN = [
  { name: 'Neve 1073', role: 'MIC PREAMP & EQ', note: 'Class-A, transformer-coupled preamp with a three-band EQ and high-pass filter. Thick, forward mids; the first stop for guitars and vocals.' },
  { name: 'AudioScape 1176', role: 'FET COMPRESSOR', note: 'A hand-built take on the classic 1176 FET limiter: very fast attack and ratios from 4:1 to 20:1. Catches peaks and adds bite; all-buttons-in when it needs to be loud.' },
  { name: 'Teletronix LA-2A', role: 'OPTICAL LEVELER', note: 'Tube leveling amplifier with two knobs: gain and peak reduction. Smooth, program-dependent release that sits a vocal or bass right in the mix.' },
  { name: 'Bus compressor', role: 'STEREO VCA GLUE', note: 'Gentle 2:1 or 4:1 across the mix bus with auto release. A couple of dB of gain reduction to hold the whole song together.' },
];
export const PEDALBOARD = [
  { name: 'Keeley Compressor', role: 'DYNAMICS', note: 'First in line. Evens out picking, adds sustain, and keeps clean parts sitting still.' },
  { name: 'Precision Drive', role: 'TIGHT OVERDRIVE', note: 'Horizon Devices. Tightens the low end and sharpens the attack in front of a driven amp.' },
  { name: 'Fulltone OCD', role: 'OVERDRIVE', note: 'Amp-like drive that goes from edge-of-breakup crunch to full rhythm distortion.' },
  { name: 'Strymon delay', role: 'TIME', note: 'Stereo delay with tape and analog voicings for long, warm repeats.' },
  { name: 'Strymon reverb', role: 'SPACE', note: 'Last in the chain: rooms, plates and big ambient washes.' },
];
export const MOODS = [{ id:'golden-hour', name:'Sunset' }, { id:'late-night', name:'Late night' }, { id:'warm-tape', name:'Warm tape' }];
export const PANEL_COPY = {
  badge: { eyebrow:'SAY HELLO / 00', title:'Hi, I’m Shawn.', body:'This is my studio: a guitar, a few too many pedals, and the band on the wall. Come say hello.', note:'Opens LinkedIn in a new tab.' },
  poster: { eyebrow:'THE BAND / 01', title:'Tide of Echo', body:'Sound comes in waves. This one has a place on the wall.', note:'Journal, the band’s album, is on Spotify.' },
  vinyl: { eyebrow:'THE RECORDS / 02', title:'Three on the wall.', body:'Modern Times, Echo of Tide and Journal. Pick one and press play.', note:'Each record opens on Spotify in a new tab.' },
  record: { eyebrow:'ON THE WALL / 02', note:'Opens on Spotify in a new tab.' },
  rack: { eyebrow:'THE SIGNAL CHAIN / 03', title:'A little analog soul.', body:'Mic in, record out. Four classic boxes, in the order the signal meets them.', note:'Preamp, peak control, leveling, then glue.' },
  guitar: { eyebrow:'THE SIX-STRING / 04', title:'It starts with a string.', body:'A Suhr S-style: flame maple top in a charcoal burst, white pearloid pickguard, humbucker in the bridge and a roasted maple neck.', note:'Modeled from Shawn’s own guitar.' },
  amp: { eyebrow:'THE AMPLIFIER / 05', title:'A familiar kind of chime.', body:'Diamond grille cloth, a brass badge, and the warm glow of a little Vox in the corner. Ready for one more take.', note:'Small amp. Big personality.' },
  pedals: { eyebrow:'THE PEDALBOARD / 06', title:'Color outside the lines.', body:'Five pedals, in signal order.', note:'Compressor first, time and space last.' },
  tv: { eyebrow:'THE SCREEN / 07', title:'Command center.', body:'Systems, the mix bus, a log that never stops scrolling. Always running, even when nobody is playing.', note:'A live terminal rendered in your browser; nothing here is real or interactive.' },
};
