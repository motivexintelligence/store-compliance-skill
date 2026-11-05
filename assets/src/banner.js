// README banner for store-compliance: banner(mode) -> SVG string, 1280x420.
// Render with banner.html in Chrome and screenshot at 2x (see assets/src/README.md).
(function (global) {
  const W = 1280, H = 420;
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  /* ---------- Concept C: lens over the manifest ---------- */
  const C_PAL = {
    light: { bg: '#F4F5F8', card: '#FFFFFF', border: '#D8DCE4', tab: '#EEF0F4', code: '#272D3B', muted: '#8A91A2', key: '#4746C8', str: '#1B7F5C', red: '#D3383B', ring: '#151925', glass: '#4746C8', chip: '#151925', chipT: '#FFFFFF', shadow: '#1B2236' },
    dark:  { bg: '#0D1016', card: '#161A23', border: '#2A303D', tab: '#1C212C', code: '#D7DCE7', muted: '#6E7689', key: '#9A98FF', str: '#5FD3A5', red: '#FF6D6D', ring: '#E6E9F2', glass: '#9A98FF', chip: '#E6E9F2', chipT: '#0D1016', shadow: '#000000' },
  };
  // Store icons, original colours, from Wikimedia Commons (Google_Play_2022_icon.svg, App_Store_(iOS).svg,
  // Huawei_AppGallery.svg). The marks are trademarks of Apple, Google and Huawei.
  const STORE_ICON = {
    appstore: (u) => `<svg viewBox="0 0 800 800"><linearGradient id="${u}as" gradientUnits="userSpaceOnUse" x1="400.05" y1="798.7717" x2="400.05" y2="-1.2283" gradientTransform="matrix(1 0 0 -1 0 798.7717)"><stop offset="0" stop-color="#18BFFB"/><stop offset="1" stop-color="#2072F3"/></linearGradient><path fill="url(#${u}as)" d="M638.4,0H161.6C72.3,0,0,72.3,0,161.6v476.9C0,727.7,72.3,800,161.6,800h476.9c89.2,0,161.6-72.3,161.6-161.6V161.6C800,72.3,727.7,0,638.4,0z"/><path fill="#FFFFFF" d="M396.6,183.8l16.2-28c10-17.5,32.3-23.4,49.8-13.4s23.4,32.3,13.4,49.8L319.9,462.4h112.9c36.6,0,57.1,43,41.2,72.8H143c-20.2,0-36.4-16.2-36.4-36.4c0-20.2,16.2-36.4,36.4-36.4h92.8l118.8-205.9l-37.1-64.4c-10-17.5-4.1-39.6,13.4-49.8c17.5-10,39.6-4.1,49.8,13.4L396.6,183.8L396.6,183.8z M256.2,572.7l-35,60.7c-10,17.5-32.3,23.4-49.8,13.4S148,614.5,158,597l26-45C213.4,542.9,237.3,549.9,256.2,572.7L256.2,572.7z M557.6,462.6h94.7c20.2,0,36.4,16.2,36.4,36.4c0,20.2-16.2,36.4-36.4,36.4h-52.6l35.5,61.6c10,17.5,4.1,39.6-13.4,49.8c-17.5,10-39.6,4.1-49.8-13.4c-59.8-103.7-104.7-181.3-134.5-233c-30.5-52.6-8.7-105.4,12.8-123.3C474.2,318.1,509.9,380,557.6,462.6L557.6,462.6z"/></svg>`,
    googleplay: () => `<svg viewBox="0 0 28.99 31.99"><path d="M13.54 15.28.12 29.34a3.66 3.66 0 0 0 5.33 2.16l15.1-8.6Z" fill="#ea4335"/><path d="m27.11 12.89-6.53-3.74-7.35 6.45 7.38 7.28 6.48-3.7a3.54 3.54 0 0 0 1.5-4.79 3.62 3.62 0 0 0-1.5-1.5z" fill="#fbbc04"/><path d="M.12 2.66a3.57 3.57 0 0 0-.12.92v24.84a3.57 3.57 0 0 0 .12.92L14 15.64Z" fill="#4285f4"/><path d="m13.64 16 6.94-6.85L5.5.51A3.73 3.73 0 0 0 3.63 0 3.64 3.64 0 0 0 .12 2.65Z" fill="#34a853"/></svg>`,
    appgallery: (u) => `<svg viewBox="0 0 36 36"><linearGradient id="${u}ag" x1="18" y1="0" x2="18" y2="36" gradientUnits="userSpaceOnUse"><stop stop-color="#FB6361" offset="0"/><stop stop-color="#ED3E45" offset="1"/></linearGradient><path fill="url(#${u}ag)" d="M10.101,0C2.705,0,0,2.705,0,10.099V25.901C0,33.295,2.705,36,10.101,36H25.894C33.29,36,36,33.295,36,25.901V10.099C36,2.705,33.295,0,25.899,0Z"/><path fill="#fff" d="m15.703052,20.879251h1.445267l-0.725093,-1.68629z m-0.355892,0.8498-0.428806,0.981162h-0.976243l2.076035,-4.709924h0.843724l2.067644,4.709924H17.92723l-0.423308,-0.981162z m15.709293,0.97769H32V18h-0.943547z m-3.755381,-2.021928h1.73924v-0.858191h-1.73924v-0.96467h2.524806v-0.85848h-3.468064v4.706451h3.558917v-0.85848H27.301072Z M23.552056,21.24093 22.482355,18h-0.780647l-1.069701,3.24093-1.041055,-3.238326h-1.017908l1.642888,4.710213h0.791353l1.071437,-3.093944 1.071437,3.093944h0.798297l1.638548,-4.710213H24.595426Z M12.501762,20.697833c0,0.76618-0.380486,1.1756-1.071437,1.1756-0.694712,0-1.077223,-0.421283-1.077223,-1.208296V18.003183H9.3968234v2.69465c0,1.32548 0.7366666,2.085584 2.0204816,2.085584 1.296545,0 2.039867,-0.774571 2.039867,-2.124935v-2.658193h-0.95541z M7.1153548,18.000289h0.9556995v4.712817H7.1153548V20.799103H4.9562782v1.914003H4v-4.712817h0.9562782v1.900983h2.1590766z"/><path fill="#fff" d="M18,12C14.691262,12 12,9.3084491 12,6h0.847512c0,2.8408565 2.311632,5.152199 5.152488,5.152199 2.840856,0 5.152488,-2.3113425 5.152488,-5.152199H24c0,3.3084491-2.691551,6-6,6"/></svg>`,
  };
  const STORES = [['appstore', 'App Store', 72], ['googleplay', 'Google Play', 232], ['appgallery', 'AppGallery', 412]];
  const C_TYPE = {
    inter: { family: "Inter, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif", body: "Inter, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif", weight: 700, size: 62, ls: -1.5 },
  };
  function conceptC(mode, uid, type) {
    const p = C_PAL[mode], u = 'c' + uid, T = C_TYPE[type || 'inter'];
    const mono = "'Geist Mono', ui-monospace, monospace";
    const tok = (parts) => parts.map(([t, c]) => `<tspan fill="${c}">${esc(t)}</tspan>`).join('');
    const K = p.key, Sg = p.str, D = p.code, M = p.muted;
    const card = (name, lines, errLine) => {
      let body = `<rect x="0" y="0" width="400" height="236" rx="14" fill="${p.card}" stroke="${p.border}"/>
        <path d="M0 14 A14 14 0 0 1 14 0 H386 A14 14 0 0 1 400 14 V40 H0 Z" fill="${p.tab}"/>
        <circle cx="20" cy="20" r="4.5" fill="${p.border}"/><circle cx="35" cy="20" r="4.5" fill="${p.border}"/><circle cx="50" cy="20" r="4.5" fill="${p.border}"/>
        <text x="70" y="25" font-family="${mono}" font-size="12.5" fill="${p.muted}">${esc(name)}</text>`;
      lines.forEach((ln, i) => {
        const y = 70 + i * 24;
        body += `<text x="18" y="${y}" font-family="${mono}" font-size="11" fill="${p.muted}" text-anchor="end" transform="translate(14 0)">${i + 1}</text>`;
        body += `<text x="42" y="${y}" font-family="${mono}" font-size="13" xml:space="preserve">${tok(ln)}</text>`;
        if (i === errLine) {
          let d = 'M108 ' + (y + 5);
          for (let x = 108; x < 340; x += 4) d += ` L${x + 2} ${y + (x / 4 % 2 ? 5 : 8)}`;
          body += `<path d="${d}" fill="none" stroke="${p.red}" stroke-width="1.6" stroke-linejoin="round"/>`;
        }
      });
      return body;
    };
    const plist = card('ios/Runner/Info.plist', [
      [['<key>', M], ['NSCameraUsageDescription', K], ['</key>', M]],
      [['<string>', M], ['This app needs the camera', Sg], ['</string>', M]],
      [['<key>', M], ['NSUserTrackingUsageDescription', K], ['</key>', M]],
      [['<string>', M], ['Allow tracking to earn coins', Sg], ['</string>', M]],
      [['<key>', M], ['UIBackgroundModes', K], ['</key>', M]],
      [['<array><string>', M], ['audio', Sg], ['</string></array>', M]],
    ], -1);
    const manifest = card('android/app/src/main/AndroidManifest.xml', [
      [['<uses-permission', M]],
      [['  android:name=', M], ['"READ_MEDIA_IMAGES"', Sg], [' />', M]],
      [['<uses-permission', M]],
      [['  android:name=', M], ['"QUERY_ALL_PACKAGES"', Sg], [' />', M]],
      [['<uses-sdk ', M], ['android:targetSdkVersion', K], ['="34"', Sg], [' />', M]],
      [['<service android:foregroundServiceType=', M], ['"location"', Sg]],
    ], -1);
    const json5 = card('entry/src/main/module.json5', [
      [['"requestPermissions"', K], [': [{', D]],
      [['  "name"', K], [': ', D], ['"ohos.permission.READ_IMAGEVIDEO"', Sg]],
      [['  "reason"', K], [': ', D], ['"$string:reason_photos"', Sg], [',', D]],
      [['  "usedScene"', K], [': { ', D], ['"when"', K], [': ', D], ['"always"', Sg], [' }', D]],
      [['}]', D]],
      [['"compatibleSdkVersion"', K], [': ', D], ['"5.0.0(12)"', Sg]],
    ], 1);
    const cx = 1040, cy = 236, r = 86;
    const front = `<g transform="translate(838 138) rotate(4)">${json5}</g>`;
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="store-compliance">
  <defs>
    <filter id="${u}sh" x="-20%" y="-20%" width="140%" height="160%"><feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="${p.shadow}" flood-opacity="${mode === 'dark' ? 0.55 : 0.10}"/></filter>
    <clipPath id="${u}lens"><circle cx="${cx}" cy="${cy}" r="${r}"/></clipPath>
  </defs>
  <rect width="${W}" height="${H}" fill="${p.bg}"/>
  <text x="68" y="180" font-family="${T.family}" font-weight="${T.weight}" font-size="${T.size}" letter-spacing="${T.ls}" fill="${p.code}">store-compliance</text>
  ${STORES.map(([kind, label, x]) => STORE_ICON[kind](u).replace('<svg ', `<svg x="${x}" y="205" width="24" height="24" `) + `<text x="${x + 32}" y="227" font-family="${T.body}" font-weight="500" font-size="21" fill="${p.code}">${label}</text>`).join('\n  ')}
  <text x="72" y="264" font-family="${T.body}" font-size="17" fill="${p.muted}">Reads your manifests and code the way a reviewer would,</text>
  <text x="72" y="289" font-family="${T.body}" font-size="17" fill="${p.muted}">then tells you the file, the line, the rule and the fix.</text>
  <g filter="url(#${u}sh)">
    <g transform="translate(760 40) rotate(-7)">${plist}</g>
    <g transform="translate(806 86) rotate(-1.5)">${manifest}</g>
    ${front}
  </g>
  <g clip-path="url(#${u}lens)">
    <rect x="${cx - r}" y="${cy - r}" width="${2 * r}" height="${2 * r}" fill="${p.card}"/>
    <g transform="translate(${cx} ${cy}) scale(1.75) translate(${-cx} ${-cy})">${front}</g>
    <circle cx="${cx}" cy="${cy}" r="${r}" fill="${p.glass}" opacity="0.06"/>
    <path d="M${cx - 60} ${cy - 46} A74 74 0 0 1 ${cx - 6} ${cy - 74}" stroke="#FFFFFF" stroke-opacity="0.75" stroke-width="7" stroke-linecap="round" fill="none"/>
  </g>
  <g transform="translate(${cx} ${cy}) rotate(42)">
    <rect x="${r + 4}" y="-15" width="140" height="30" rx="15" fill="${p.ring}"/>
    <rect x="${r - 2}" y="-19" width="26" height="38" rx="6" fill="${p.ring}"/>
  </g>
  <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${p.ring}" stroke-width="13"/>
</svg>`;
  }

  global.SC_BANNER = (mode) => conceptC(mode, mode, 'inter');
})(typeof window !== 'undefined' ? window : globalThis);
