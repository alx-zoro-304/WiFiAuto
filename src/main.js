import './style.css'

/* ============================================================
   WiFi Auto — official site
   Bilingual (EN default / AR), particles, terminal animation,
   live version.json integration + PWA.
   ============================================================ */

const I18N = {
  en: {
    nav_features: 'Features', nav_how: 'How it works', nav_tools: 'Tools',
    nav_download: 'Download', nav_changelog: 'Changelog', nav_about: 'About',
    nav_cta: 'Get v2.0',
    hero_badge: 'WiFi Auto v2.0 — Released',
    hero_title_1: 'Never lose', hero_title_2: 'your internet', hero_title_3: 'again.',
    hero_sub: 'WiFi Auto finds open networks, deep-scans every device, ranks their activity and re-connects you automatically — all from one self-contained tool. Built by <span class="text-cyan-400 font-semibold">ALX-ZORO</span>.',
    hero_cta_1: 'Download for Windows', hero_cta_2: 'See how it works',
    hero_tick_1: '100% Self-contained', hero_tick_2: 'No external tools', hero_tick_3: 'Windows + Linux',
    stat_1: 'addresses deep-scanned', stat_2: 'full-scan rounds', stat_3: 'external dependencies', stat_4: 'click recovery',
    features_tag: 'Capabilities',
    features_title: 'Engineered to do the impossible',
    features_sub: 'Every feature runs inside one script — no installs, no dependencies, no external binaries.',
    f1_t: 'Open Network Finder', f1_d: 'Scans and lists every open (passwordless) WiFi network around you and connects with a single click.',
    f2_t: 'Deep Device Scanner', f2_d: 'Sweeps 2044 addresses across /22 + /24 scopes in repeated 15-second rounds, merging every ARP sighting until even quiet devices appear.',
    f3_t: 'Activity Sniffer & Ranking', f3_d: 'Ranks device traffic and always tries the busiest MAC first — smart order, not random guesses.',
    f4_t: 'Native MAC Spoofing', f4_d: 'Disable → registry write → enable, proven on Realtek 8821CE. If the driver reverts, the tool skips it instantly and moves on.',
    f5_t: 'Auto Internet Recovery', f5_d: 'After every MAC change it tests real connectivity and repeats until the internet works — or you press Stop.',
    f6_t: 'Self-Contained & Portable', f6_d: 'One file, zero dependencies. Native Python pings, inline PowerShell, no .exe helpers, no .ps1 scripts. Works on Windows & Linux.',
    how_tag: 'The flow', how_title: 'How it works',
    how_sub: 'Four stages. Zero supervision needed after you press Start.',
    s1_t: 'Find & connect', s1_d: 'Scans open networks, you pick one, it connects instantly.',
    s2_t: 'Deep scan', s2_d: 'Sweeps thousands of addresses in rounds and collects every device MAC on the network.',
    s3_t: 'Sniff & rank', s3_d: 'Watches traffic 10 seconds and ranks which devices are most active.',
    s4_t: 'Spoof & verify', s4_d: 'Adopts the best scanned MAC, reconnects, tests the internet, repeats until success.',
    tools_tag: 'The toolkit', tools_title: 'Two tools, one developer',
    tools_sub: 'Both fully self-contained, dark-themed, and battle-tested on Realtek hardware.',
    tools_d1: 'The main weapon: open-network finder, deep scanner, traffic sniffer, MAC spoofing and automatic internet recovery — one click end-to-end.',
    tools_l1: 'Auto reconnect to open networks',
    tools_l2: 'Full session log to report.txt',
    tools_l3: 'Restore original MAC anytime',
    tools_btn1: 'Download WiFi Auto',
    tools_d2: 'Standalone MAC address changer that detects every adapter (WiFi + Ethernet), changes via registry with driver verification, and explains failures clearly.',
    tools_l4: 'Detects all adapters with driver names',
    tools_l5: 'Restore original MAC in one click',
    tools_l6: 'Detailed failure diagnostics',
    tools_btn2: 'Download MAC Changer',
    dl_tag: 'Get it now', dl_title: 'Download',
    dl_sub: 'Always free. Updates are announced here — and your installed tool checks this page automatically.',
    dl_latest: 'Latest release', dl_checking: 'Checking for updates...', dl_ok: 'Up to date', dl_error: 'Offline preview — latest known:',
    dl_zip: 'Download full package (ZIP)', dl_py: 'wifi_auto_gui.py', dl_mc: 'mac_changer_pro.py', dl_exe: 'MAC-Address-Tool.exe',
    dl_note: 'Need Python 3.8+ on your machine. Run <code class="font-mono text-cyan-400">start.bat</code> as Administrator — the launcher handles privileges for you.',
    cl_tag: 'History', cl_title: 'Changelog',
    about_tag: 'Developer', about_title: 'Built by ALX-ZORO',
    about_d: 'Developer of self-contained network tools that solve real everyday problems. Every tool is written to be portable, dependency-free and honest about what it does. WiFi Auto and MAC Changer Pro are tested on real Realtek hardware — the hard way.',
    about_cta: 'Get the tools',
  },
  ar: {
    nav_features: 'المميزات', nav_how: 'طريقة العمل', nav_tools: 'الأدوات',
    nav_download: 'التحميل', nav_changelog: 'سجل التحديثات', nav_about: 'عن المطور',
    nav_cta: 'حمّل v2.0',
    hero_badge: 'WiFi Auto v2.0 — تم الإصدار',
    hero_title_1: 'لا تفقد', hero_title_2: 'الإنترنت', hero_title_3: 'مرة أخرى.',
    hero_sub: 'WiFi Auto يجد الشبكات المفتوحة، يفحص كل الأجهزة بفحص عميق، يرتب نشاطها ويعيد توصيلك تلقائياً — كل ذلك من أداة واحدة مكتفية بذاتها. من تطوير <span class="text-cyan-400 font-semibold">ALX-ZORO</span>.',
    hero_cta_1: 'حمّل لنظام ويندوز', hero_cta_2: 'شاهد طريقة العمل',
    hero_tick_1: 'مكتفية ذاتياً 100%', hero_tick_2: 'بدون أدوات خارجية', hero_tick_3: 'ويندوز + لينكس',
    stat_1: 'عنوان يتم فحصه بعمق', stat_2: 'جولة فحص كاملة', stat_3: 'اعتماديات خارجية', stat_4: 'نقرة واحدة للاستعادة',
    features_tag: 'الإمكانيات',
    features_title: 'مصممة لتفعل المستحيل',
    features_sub: 'كل ميزة تعمل داخل سكربت واحد — بدون تثبيت، بدون اعتماديات، بدون ملفات خارجية.',
    f1_t: 'مكتشف الشبكات المفتوحة', f1_d: 'يفحص ويعرض كل شبكات الواي فاي المفتوحة (بدون كلمة مرور) من حولك ويتصل بها بنقرة واحدة.',
    f2_t: 'ماسح الأجهزة العميق', f2_d: 'يمسح 2044 عنواناً عبر نطاقات /22 و /24 في جولات متكررة لمدة 15 ثانية، ويدمج كل رصد ARP حتى تظهر الأجهزة الهادئة.',
    f3_t: 'مراقب النشاط والترتيب', f3_d: 'يرتب حركة الأجهزة ويجرب دائماً الـ MAC الأكثر نشاطاً أولاً — ترتيب ذكي، وليس تخميناً عشوائياً.',
    f4_t: 'تغيير MAC أصلي', f4_d: 'تعطيل ← كتابة في السجل ← تفعيل، مجرّب على Realtek 8821CE. إذا رفض التعريف التغيير، تتخطاه الأداة فوراً وتنتقل للذي يليه.',
    f5_t: 'استعادة الإنترنت تلقائياً', f5_d: 'بعد كل تغيير MAC تختبر الاتصال الحقيقي وتكرر حتى يعمل الإنترنت — أو تضغط إيقاف.',
    f6_t: 'مكتفية ذاتياً ومحمولة', f6_d: 'ملف واحد بدون أي اعتماديات. Ping أصلي بالبايثون، PowerShell مضمّن، بدون أدوات .exe أو سكربتات .ps1. تعمل على ويندوز ولينكس.',
    how_tag: 'الخطوات', how_title: 'طريقة العمل',
    how_sub: 'أربع مراحل. لا تحتاج أي إشراف بعد الضغط على ابدأ.',
    s1_t: 'ابحث واتصل', s1_d: 'يفحص الشبكات المفتوحة، تختار واحدة، فيتصل فوراً.',
    s2_t: 'الفحص العميق', s2_d: 'يمسح آلاف العناوين في جولات ويجمع كل أجهزة الشبكة وعناوين MAC الخاصة بها.',
    s3_t: 'راقب ورتب', s3_d: 'يراقب الحركة لمدة 10 ثوانٍ ويرتب الأجهزة الأكثر نشاطاً.',
    s4_t: 'انتحل وتحقق', s4_d: 'يتبنى أفضل MAC ممسوح، يعيد الاتصال، يختبر الإنترنت، ويكرر حتى النجاح.',
    tools_tag: 'الحقيبة', tools_title: 'أداتان، مطور واحد',
    tools_sub: 'كلتاهما مكتفيتان ذاتياً، بواجهة داكنة، ومجرّبتان على أجهزة Realtek الحقيقية.',
    tools_d1: 'السلاح الرئيسي: مكتشف الشبكات المفتوحة، الماسح العميق، مراقب الحركة، تغيير MAC والاستعادة التلقائية للإنترنت — كل ذلك بنقرة واحدة.',
    tools_l1: 'إعادة اتصال تلقائية بالشبكات المفتوحة',
    tools_l2: 'سجل كامل للجلسة في report.txt',
    tools_l3: 'استعادة MAC الأصلي في أي وقت',
    tools_btn1: 'حمّل WiFi Auto',
    tools_d2: 'أداة مستقلة لتغيير MAC تكتشف كل المحولات (واي فاي + إيثرنت)، تغير عبر السجل مع تحقق من التعريف، وتشرح الأخطاء بوضوح.',
    tools_l4: 'يكتشف كل المحولات مع أسماء التعريفات',
    tools_l5: 'استعادة MAC الأصلي بنقرة واحدة',
    tools_l6: 'تشخيص تفصيلي للأخطاء',
    tools_btn2: 'حمّل MAC Changer',
    dl_tag: 'حمّله الآن', dl_title: 'التحميل',
    dl_sub: 'مجاني دائماً. التحديثات تُعلن هنا — وأداتك المثبتة تفحص هذه الصفحة تلقائياً.',
    dl_latest: 'أحدث إصدار', dl_checking: 'جارٍ فحص التحديثات...', dl_ok: 'الموقع محدث', dl_error: 'معاينة بدون اتصال — آخر إصدار معروف:',
    dl_zip: 'حمّل الحزمة الكاملة (ZIP)', dl_py: 'wifi_auto_gui.py', dl_mc: 'mac_changer_pro.py', dl_exe: 'MAC-Address-Tool.exe',
    dl_note: 'يلزم تثبيت Python 3.8+ على جهازك. شغّل <code class="font-mono text-cyan-400">start.bat</code> كمسؤول — المشغل يتولى الصلاحيات عنك.',
    cl_tag: 'السجل', cl_title: 'سجل التحديثات',
    about_tag: 'المطور', about_title: 'من تطوير ALX-ZORO',
    about_d: 'مطور أدوات شبكات مكتفية ذاتياً تحل مشاكل يومية حقيقية. كل أداة مكتوبة لتكون محمولة، بدون اعتماديات، وصادقة فيما تفعله. WiFi Auto و MAC Changer Pro مجرّبتان على أجهزة Realtek حقيقية — بالطريقة الصعبة.',
    about_cta: 'حمّل الأدوات',
  }
}

let lang = localStorage.getItem('wa-lang') || 'en'

function applyLang() {
  const dict = I18N[lang]
  document.documentElement.lang = lang
  document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr'
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n
    if (dict[key]) el.innerHTML = dict[key]
  })
  const langEn = document.querySelectorAll('.lang-en')
  const langAr = document.querySelectorAll('.lang-ar')
  langEn.forEach(el => el.classList.toggle('hidden', lang === 'ar'))
  langAr.forEach(el => el.classList.toggle('hidden', lang === 'en'))
}

document.getElementById('langToggle').addEventListener('click', () => {
  lang = lang === 'en' ? 'ar' : 'en'
  localStorage.setItem('wa-lang', lang)
  applyLang()
})

/* ---------- Navbar scroll + mobile menu ---------- */
const navbar = document.getElementById('navbar')
window.addEventListener('scroll', () => {
  navbar.classList.toggle('scrolled', window.scrollY > 24)
}, { passive: true })

const menuBtn = document.getElementById('menuBtn')
const mobileMenu = document.getElementById('mobileMenu')
menuBtn.addEventListener('click', () => mobileMenu.classList.toggle('hidden'))
document.querySelectorAll('.mobile-link').forEach(a =>
  a.addEventListener('click', () => mobileMenu.classList.add('hidden')))

/* ---------- Particles canvas ---------- */
const canvas = document.getElementById('particles')
const ctx = canvas.getContext('2d')
let particles = []
function resizeCanvas() {
  canvas.width = canvas.offsetWidth
  canvas.height = canvas.offsetHeight
}
resizeCanvas()
window.addEventListener('resize', resizeCanvas)

function initParticles() {
  const count = Math.min(70, Math.floor(canvas.width / 22))
  particles = Array.from({ length: count }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    vx: (Math.random() - .5) * .35,
    vy: (Math.random() - .5) * .35,
    r: Math.random() * 1.6 + .4,
    a: Math.random() * .4 + .15
  }))
}
initParticles()

function drawParticles() {
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  for (const p of particles) {
    p.x += p.vx; p.y += p.vy
    if (p.x < 0 || p.x > canvas.width) p.vx *= -1
    if (p.y < 0 || p.y > canvas.height) p.vy *= -1
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(34,211,238,${p.a})`
    ctx.fill()
  }
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const a = particles[i], b = particles[j]
      const d = Math.hypot(a.x - b.x, a.y - b.y)
      if (d < 110) {
        ctx.beginPath()
        ctx.moveTo(a.x, a.y)
        ctx.lineTo(b.x, b.y)
        ctx.strokeStyle = `rgba(34,211,238,${(1 - d / 110) * .18})`
        ctx.lineWidth = 1
        ctx.stroke()
      }
    }
  }
  requestAnimationFrame(drawParticles)
}
drawParticles()

/* ---------- Terminal typing animation ---------- */
const terminalLines = document.getElementById('terminalLines')
const lines = [
  ['[12:03:03]', 'Scanning 1022 address(es) for up to 15s ...', 'cyan'],
  ['[12:03:17]', 'Deep scan pass 8: 7 device(s) so far', 'green'],
  ['[12:03:35]', 'Attempt: spoofing MAC 72:3d:9a:9f:05:90', 'yellow'],
  ['[12:04:39]', 'OK: Wi-Fi MAC changed to 72:3d:9a:9f:05:90', 'green'],
  ['[12:05:01]', 'Testing internet ...', 'cyan'],
  ['', 'SUCCESS — internet works!', 'green'],
]
lines.forEach(([t, txt, cls], i) => {
  const div = document.createElement('div')
  div.className = 't-line'
  div.style.animationDelay = `${1.4 + i * 1.15}s`
  div.innerHTML = `${t ? `<span class="t-time">${t}</span> ` : ''}<span class="t-${cls}">${txt}</span>`
  terminalLines.insertBefore(div, terminalLines.lastElementChild)
})

/* ---------- Scroll reveal ---------- */
const observer = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('visible'); observer.unobserve(e.target) }
  })
}, { threshold: 0.12 })
document.querySelectorAll('.reveal').forEach(el => observer.observe(el))

/* ---------- Card mouse glow ---------- */
document.querySelectorAll('.card').forEach(card => {
  card.addEventListener('mousemove', e => {
    const r = card.getBoundingClientRect()
    card.style.setProperty('--mx', `${e.clientX - r.left}px`)
    card.style.setProperty('--my', `${e.clientY - r.top}px`)
  })
})

/* ---------- Stat counters ---------- */
function animateCount(el) {
  const target = +el.dataset.count
  const dur = 1400
  const start = performance.now()
  function step(now) {
    const p = Math.min((now - start) / dur, 1)
    el.textContent = Math.floor(target * (1 - Math.pow(1 - p, 3)))
    if (p < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}
const statObserver = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.querySelectorAll('[data-count]').forEach(animateCount)
      statObserver.unobserve(e.target)
    }
  })
}, { threshold: .4 })
document.querySelector('.stat').parentElement && statObserver.observe(document.querySelectorAll('.stat')[0]?.parentElement)

/* ---------- version.json integration ---------- */
async function loadVersion() {
  const vNum = document.getElementById('vNum')
  const vDate = document.getElementById('vDate')
  const vStatus = document.getElementById('vStatus')
  const badge = document.querySelector('.hero-badge span:last-child')
  try {
    const res = await fetch('./version.json', { cache: 'no-store' })
    if (!res.ok) throw new Error('not found')
    const data = await res.json()
    vNum.textContent = data.current_version
    vDate.textContent = data.published
    vStatus.innerHTML = `<span class="pulse-dot"></span><span>${I18N[lang].dl_ok} — v${data.current_version}</span>`
    if (badge) badge.textContent = `${data.app} v${data.current_version} — ${I18N[lang].hero_badge.split('—')[1] || I18N[lang].hero_badge}`
    const dl = document.getElementById('dlZip')
    if (data.downloads?.zip) dl.href = data.downloads.zip
    const links = { dlPy: 'wifi_auto_gui_py', dlMc: 'mac_changer_pro_py', dlExe: 'exe' }
    for (const [id, key] of Object.entries(links)) {
      const el = document.getElementById(id)
      if (data.downloads?.[key]) el.href = data.downloads[key]
    }
    document.getElementById('footerVer').textContent = `version.json · live v${data.current_version}`
    renderChangelog(data.changelog || [])
  } catch {
    vStatus.innerHTML = `<span class="text-amber-400">${I18N[lang].dl_error}</span>`
  }
}

function renderChangelog(entries) {
  const list = document.getElementById('changelogList')
  list.innerHTML = ''
  entries.forEach((item, i) => {
    const div = document.createElement('div')
    div.className = 'changelog-item reveal'
    if (i === 0) div.classList.add('visible')
    const notes = lang === 'ar' && item.notes_ar ? item.notes_ar : item.notes_en
    div.innerHTML = `
      <div class="flex items-center gap-3">
        <span class="version-chip">v${item.version}</span>
        <span class="text-slate-500 text-sm font-mono">${item.date}</span>
      </div>
      <ul class="mt-4 space-y-2 text-slate-300 text-sm">
        ${notes.map(n => `<li class="flex gap-2"><span class="tick">✓</span>${n}</li>`).join('')}
      </ul>`
    list.appendChild(div)
  })
}

/* ---------- PWA ---------- */
if ('serviceWorker' in navigator && location.protocol === 'https:') {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').catch(() => {})
  })
}

applyLang()
loadVersion()