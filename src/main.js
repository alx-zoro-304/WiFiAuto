import './style.css'

/* ============================================================
   ALX-ZORO — official site
   Bilingual (EN default / AR), particles, terminal animation,
   live version.json integration + PWA.
   ============================================================ */

const I18N = {
  en: {
    nav_about: 'About', nav_skills: 'Skills', nav_tools: 'Tools',
    nav_usage: 'How to use', nav_download: 'Download', nav_changelog: 'Changelog',
    nav_cta: 'Get my tools',
    hero_badge: 'Python Developer · Cybersecurity Enthusiast',
    hero_sub: 'I build self-contained Python tools that solve real technical and engineering problems — from network recovery to system automation. Every tool is portable, dependency-free, and tested the hard way.',
    hero_cta_1: 'Explore my tools', hero_cta_2: 'About me',
    hero_tick_1: 'Python engineering', hero_tick_2: 'Cybersecurity', hero_tick_3: 'Windows + Linux',
    about_tag: 'About me', about_title: "Hi, I'm ALX-ZORO",
    about_d1: "I'm a developer who loves solving real problems with code. I build technical and engineering solutions using Python — tools that are self-contained, portable, and honest about what they do.",
    about_d2: 'I also have a deep interest in cybersecurity: network analysis, device identification, and building tools that understand how systems actually behave — tested on real hardware, the hard way.',
    about_cta: 'See my tools',
    ab1_t: 'Python Development', ab1_d: 'GUI tools, automation scripts, and network utilities — written to run anywhere with zero dependencies.',
    ab2_t: 'Cybersecurity', ab2_d: 'Network analysis, device fingerprinting and low-level protocols — understanding systems from the packet up.',
    ab3_t: 'Engineering Solutions', ab3_d: 'Real-world problems solved the hard way: driver quirks, registry-level changes, and tested-on-hardware reliability.',
    ab4_t: 'Cross-Platform', ab4_d: 'Every tool ships for Windows and Linux — one codebase, native implementations for each system.',
    skills_tag: 'What I do', skills_title: 'Skills & focus areas',
    skills_sub: 'A few things I do every day — and the tools below are proof they work.',
    sk1_t: 'Networking', sk1_d: 'WiFi analysis, device discovery, ARP-level scanning, MAC manipulation and connectivity recovery.',
    sk2_t: 'System Automation', sk2_d: 'Registry work, privilege elevation, PowerShell inline scripting and launcher engineering.',
    sk3_t: 'Security Analysis', sk3_d: 'Understanding traffic, device identity, and how drivers enforce (or block) hardware changes.',
    sk4_t: 'GUI Engineering', sk4_d: 'Dark-themed, responsive tkinter applications with live logs and clean workflows.',
    sk5_t: 'Zero-Dependency', sk5_d: 'Self-contained tools that run from a single file — no installers, no bloat, no surprises.',
    sk6_t: 'Real-World Testing', sk6_d: 'Everything is tested on actual hardware (Realtek, Windows & Linux) before it ships.',
    tools_tag: 'My tools', tools_title: 'Tools I built',
    tools_sub: 'Free, self-contained, and regularly updated — each with its own auto-updater.',
    tools_wa_ver: 'v2.0 · Windows + Linux · single file',
    tools_mc_ver: 'v1.0 · Windows · all adapters',
    tools_d1: 'Finds open networks, deep-scans every device, ranks their activity, then recovers your internet automatically. One click, end to end.',
    tools_l1: 'Open network finder + auto connect',
    tools_l2: 'Deep scan of 2044 addresses',
    tools_l3: 'Smart MAC spoofing + internet test',
    tools_btn1: 'Download', tools_btn2: 'Download', tools_btn3: 'How to use',
    tools_d2: 'Standalone MAC address changer that detects every adapter, changes via registry with driver verification, and explains failures clearly.',
    tools_l4: 'All adapters with driver names',
    tools_l5: 'One-click restore original MAC',
    tools_l6: 'Clear failure diagnostics',
    tools_c1: 'More coming soon', tools_c2: 'New tools are in the works',
    tools_c3: 'This space is reserved for the next tool in the ALX-ZORO toolkit — watch this site, the tools update themselves automatically.',
    usage_tag: 'Quick start', usage_title: 'How to use',
    usage_sub: 'Both tools run in under a minute. Here is the whole guide — compact.',
    usage_win: 'Windows', usage_linux: 'Linux', usage_win2: 'Windows only',
    uw1: 'Run <code>start.bat</code> (UAC opens → Yes)',
    uw2: 'Pick an open network → press Start',
    uw3: 'Done — internet works automatically',
    ul1: 'Run <code>./start.sh</code> (asks sudo)',
    ul2: 'Pick an open network → press Start',
    ul3: 'Done — internet works automatically',
    um1: 'Run <code>start_changer.bat</code> (UAC opens → Yes)',
    um2: 'Select your adapter → enter a MAC',
    um3: 'Press Apply — or Restore to go back',
    usage_note1: 'Requires Python 3.8+. Needs admin/root for MAC change and deep scan.',
    usage_note2: 'If a driver rejects the change, the tool tells you exactly why and what to try.',
    dl_tag: 'Get it now', dl_title: 'Download',
    dl_sub: 'Always free. Your installed tools check this page automatically for updates.',
    dl_checking: 'Checking...', dl_ok: 'Up to date', dl_error: 'Offline preview — latest known:',
    dl_wa_platform: 'Windows + Linux',
    dl_mc_platform: 'Windows only',
    dl_zip: 'Windows — full package (ZIP)',
    dl_tar: 'Linux — full package (TAR.GZ)',
    dl_py: 'Both — wifi_auto_gui.py (raw)',
    dl_mc: 'Download mac_changer_pro.py',
    dl_exe: 'MAC-Address-Tool.exe',
    dl_note: 'All packages include <code class="font-mono text-cyan-400">updater.py</code> — the auto-update system. Backups are created before every update.',
    cl_tag: 'History', cl_title: 'Changelog',
  },
  ar: {
    nav_about: 'عني', nav_skills: 'مهاراتي', nav_tools: 'أدواتي',
    nav_usage: 'طريقة الاستخدام', nav_download: 'التحميل', nav_changelog: 'سجل التحديثات',
    nav_cta: 'حمّل أدواتي',
    hero_badge: 'مطور بايثون · مهتم بالأمن السيبراني',
    hero_sub: 'أصنع أدوات بايثون مكتفية بذاتها تحل مشاكل تقنية وهندسية حقيقية — من استعادة الشبكات إلى أتمتة الأنظمة. كل أداة محمولة، بدون اعتماديات، ومجرّبة بالطريقة الصعبة.',
    hero_cta_1: 'استكشف أدواتي', hero_cta_2: 'عني',
    hero_tick_1: 'هندسة بايثون', hero_tick_2: 'أمن سيبراني', hero_tick_3: 'ويندوز + لينكس',
    about_tag: 'عني', about_title: 'أهلاً، أنا ALX-ZORO',
    about_d1: 'مطور يحب حل المشاكل الحقيقية بالكود. أصنع حلولاً تقنية وهندسية باستخدام بايثون — أدوات مكتفية بذاتها، محمولة، وصادقة فيما تفعله.',
    about_d2: 'ولدي اهتمام عميق بالأمن السيبراني: تحليل الشبكات، تحديد الأجهزة، وبناء أدوات تفهم كيف تتصرف الأنظمة فعلياً — مجرّبة على أجهزة حقيقية، بالطريقة الصعبة.',
    about_cta: 'شاهد أدواتي',
    ab1_t: 'تطوير بايثون', ab1_d: 'أدوات واجهات، سكربتات أتمتة، وأدوات شبكات — مكتوبة لتعمل في أي مكان بدون أي اعتماديات.',
    ab2_t: 'الأمن السيبراني', ab2_d: 'تحليل الشبكات، بصمة الأجهزة، والبروتوكولات منخفضة المستوى — فهم الأنظمة من مستوى الحزم نفسها.',
    ab3_t: 'حلول هندسية', ab3_d: 'مشاكل واقعية تُحل بالطريقة الصعبة: غرائب التعريفات، تغييرات على مستوى السجل، وموثوقية مجرّبة على أجهزة حقيقية.',
    ab4_t: 'متعددة المنصات', ab4_d: 'كل أداة تُطرح لويندوز ولينكس — كود واحد، وتنفيذ أصلي لكل نظام.',
    skills_tag: 'ما أفعله', skills_title: 'المهارات ومجالات التركيز',
    skills_sub: 'أشياء أفعلها كل يوم — والأدوات بالأسفل دليل أنها تعمل.',
    sk1_t: 'الشبكات', sk1_d: 'تحليل الواي فاي، اكتشاف الأجهزة، فحص على مستوى ARP، التعامل مع الـ MAC واستعادة الاتصال.',
    sk2_t: 'أتمتة الأنظمة', sk2_d: 'العمل مع السجل، رفع الصلاحيات، سكربتات PowerShell مضمّنة وهندسة المشغلات.',
    sk3_t: 'تحليل الأمن', sk3_d: 'فهم الحركة، هوية الأجهزة، وكيف تفرض التعريفات (أو تمنع) تغييرات العتاد.',
    sk4_t: 'هندسة الواجهات', sk4_d: 'تطبيقات tkinter داكنة ومتجاوبة مع سجلات حية وسير عمل نظيف.',
    sk5_t: 'بدون اعتماديات', sk5_d: 'أدوات مكتفية بذاتها تعمل من ملف واحد — بدون مثبتات، بدون تضخم، بدون مفاجآت.',
    sk6_t: 'اختبار حقيقي', sk6_d: 'كل شيء يُختبر على عتاد فعلي (Realtek، ويندوز ولينكس) قبل الإصدار.',
    tools_tag: 'أدواتي', tools_title: 'أدوات صنعتها',
    tools_sub: 'مجانية، مكتفية بذاتها، ومحدّثة بانتظام — وكل واحدة فيها نظام تحديث تلقائي.',
    tools_wa_ver: 'v2.0 · ويندوز + لينكس · ملف واحد',
    tools_mc_ver: 'v1.0 · ويندوز · كل المحولات',
    tools_d1: 'يجد الشبكات المفتوحة، يفحص كل الأجهزة بفحص عميق، يرتب نشاطها، ثم يستعيد الإنترنت تلقائياً. بنقرة واحدة من البداية للنهاية.',
    tools_l1: 'مكتشف الشبكات المفتوحة + اتصال تلقائي',
    tools_l2: 'فحص عميق لـ 2044 عنواناً',
    tools_l3: 'انتحال MAC ذكي + اختبار الإنترنت',
    tools_btn1: 'حمّل', tools_btn2: 'حمّل', tools_btn3: 'طريقة الاستخدام',
    tools_d2: 'أداة مستقلة لتغيير MAC تكتشف كل المحولات، تغيّر عبر السجل مع تحقق من التعريف، وتشرح الأخطاء بوضوح.',
    tools_l4: 'كل المحولات مع أسماء التعريفات',
    tools_l5: 'استعادة MAC الأصلي بنقرة واحدة',
    tools_l6: 'تشخيص واضح للأخطاء',
    tools_c1: 'قريباً المزيد', tools_c2: 'أدوات جديدة قيد التطوير',
    tools_c3: 'هذه المساحة محجوزة للأداة القادمة في حقيبة ALX-ZORO — تابع الموقع، الأدوات تحدّث نفسها تلقائياً.',
    usage_tag: 'بداية سريعة', usage_title: 'طريقة الاستخدام',
    usage_sub: 'كلتا الأداتين تعملان في أقل من دقيقة. هذا هو الدليل كاملاً — بشكل مختصر.',
    usage_win: 'ويندوز', usage_linux: 'لينكس', usage_win2: 'ويندوز فقط',
    uw1: 'شغّل <code>start.bat</code> (تظهر UAC → نعم)',
    uw2: 'اختر شبكة مفتوحة → اضغط ابدأ',
    uw3: 'انتهى — الإنترنت يعمل تلقائياً',
    ul1: 'شغّل <code>./start.sh</code> (يطلب sudo)',
    ul2: 'اختر شبكة مفتوحة → اضغط ابدأ',
    ul3: 'انتهى — الإنترنت يعمل تلقائياً',
    um1: 'شغّل <code>start_changer.bat</code> (تظهر UAC → نعم)',
    um2: 'اختر المحول → أدخل MAC',
    um3: 'اضغط تطبيق — أو استعادة للرجوع',
    usage_note1: 'يلزم Python 3.8+. يحتاج صلاحيات مسؤول/root لتغيير MAC والفحص العميق.',
    usage_note2: 'إذا رفض التعريف التغيير، تخبرك الأداة بالسبب بالضبط وبماذا تجرب.',
    dl_tag: 'حمّله الآن', dl_title: 'التحميل',
    dl_sub: 'مجاني دائماً. أدواتك المثبتة تفحص هذه الصفحة تلقائياً بحثاً عن التحديثات.',
    dl_checking: 'جارٍ الفحص...', dl_ok: 'الموقع محدث', dl_error: 'معاينة بدون اتصال — آخر إصدار معروف:',
    dl_wa_platform: 'ويندوز + لينكس',
    dl_mc_platform: 'ويندوز فقط',
    dl_zip: 'ويندوز — الحزمة الكاملة (ZIP)',
    dl_tar: 'لينكس — الحزمة الكاملة (TAR.GZ)',
    dl_py: 'الاثنان — wifi_auto_gui.py (خام)',
    dl_mc: 'حمّل mac_changer_pro.py',
    dl_exe: 'MAC-Address-Tool.exe',
    dl_note: 'كل الحزم تتضمن <code class="font-mono text-cyan-400">updater.py</code> — نظام التحديث التلقائي. تُنشأ نسخ احتياطية قبل كل تحديث.',
    cl_tag: 'السجل', cl_title: 'سجل التحديثات',
  }
}

const TYPED_PHRASES = {
  en: ['Technical & Engineering Solutions', 'Python Developer', 'Cybersecurity Enthusiast', 'Builder of Network Tools'],
  ar: ['حلول تقنية وهندسية', 'مطور بايثون', 'مهتم بالأمن السيبراني', 'صانع أدوات الشبكات']
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

/* ---------- Typing effect ---------- */
const typedEl = document.getElementById('typedText')
let typedIdx = 0
let charIdx = 0
let deleting = false

function typeLoop() {
  const phrases = TYPED_PHRASES[lang]
  const current = phrases[typedIdx]
  if (!deleting) {
    charIdx++
    typedEl.textContent = current.slice(0, charIdx)
    if (charIdx === current.length) {
      deleting = true
      setTimeout(typeLoop, 2200)
      return
    }
    setTimeout(typeLoop, 55)
  } else {
    charIdx--
    typedEl.textContent = current.slice(0, charIdx)
    if (charIdx === 0) {
      deleting = false
      typedIdx = (typedIdx + 1) % phrases.length
      setTimeout(typeLoop, 350)
      return
    }
    setTimeout(typeLoop, 28)
  }
}
setTimeout(typeLoop, 800)

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

/* ---------- Terminal animation ---------- */
const terminalLines = document.getElementById('terminalLines')
const lines = [
  ['', 'whoami', 'cyan'],
  ['', 'ALX-ZORO — technical & engineering solutions', 'green'],
  ['', 'skills.txt', 'cyan'],
  ['', 'python · networking · security · automation', 'green'],
  ['', './build wifi_auto --target all', 'cyan'],
  ['', 'compiling self-contained toolkit ...', 'yellow'],
  ['', 'OK — WiFi Auto v2.0 · MAC Changer Pro · updater', 'green'],
  ['', '_', 'cyan'],
]
lines.forEach(([, txt, cls], i) => {
  const div = document.createElement('div')
  div.className = 't-line'
  div.style.animationDelay = `${1.2 + i * .9}s`
  div.innerHTML = `<span class="t-${cls}">${cls === 'cyan' ? '$ ' : ''}${txt}</span>${txt === '_' ? '<span class="t-cursor">▊</span>' : ''}`
  terminalLines.appendChild(div)
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

/* ---------- Stat counters (footer version strip) ---------- */

/* ---------- version.json integration ---------- */
async function loadVersion() {
  const vNum = document.getElementById('vNum')
  const vNumMc = document.getElementById('vNumMc')
  const vDate = document.getElementById('vDate')
  const vStatus = document.getElementById('vStatus')
  try {
    const res = await fetch('./version.json', { cache: 'no-store' })
    if (!res.ok) throw new Error('not found')
    const data = await res.json()
    vNum.textContent = data.current_version
    if (vNumMc) vNumMc.textContent = data.mac_changer_version || '1.0'
    if (vDate) vDate.textContent = data.published
    vStatus.innerHTML = `<span class="pulse-dot"></span><span>${I18N[lang].dl_ok} — v${data.current_version}</span>`
    const dl = document.getElementById('dlZip')
    if (data.downloads?.zip) dl.href = data.downloads.zip
    const links = { dlTar: 'linux_tar', dlPy: 'wifi_auto_gui_py', dlMc: 'mac_changer_pro_py', dlExe: 'exe' }
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