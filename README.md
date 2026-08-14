# WiFi Auto — Official Website & Update Server

الموقع الرسمي لأداة **WiFi Auto** و **MAC Changer Pro** من تطوير **ALX-ZORO**.
يُنشر على GitHub Pages، ويُستخدم كخادم تحديثات: أي تغيير في `version.json`
يُشعر الأدوات المثبتة على أجهزة المستخدمين بوجود نسخة جديدة تلقائياً.

## البنية

```
├── index.html          # الموقع (إنجليزي/عربي)
├── src/                # JS + CSS (Vite + Tailwind v4)
├── public/             # icon, manifest, service worker
│   └── downloads/      # يتم توليدها من tool/ وقت البناء
├── tool/               # ملفات الأداة الفعلية (مصدر الحزمة)
│   ├── wifi_auto_gui.py
│   ├── mac_changer_pro.py
│   ├── updater.py      # نظام التحديث داخل الأداة
│   ├── start.bat / start_changer.bat
│   └── MAC-Address-Tool.exe
├── version.json        # ⭐ الملف الذي يحرّك نظام التحديث
├── scripts/sync-tool.sh
└── .github/workflows/deploy.yml   # نشر تلقائي على Pages
```

## طريقة إصدار نسخة جديدة (3 خطوات)

1. **عدّل `version.json`**: ارفع رقم `current_version` (مثال `2.1`) وأضف بنداً
   في `changelog` (بالعربي والإنجليزي).
2. **حدّث الملفات في `tool/`** ثم `npm run build` للتجربة محلياً.
3. **ارفع للـ GitHub** — الـ workflow يبني وينشر تلقائياً، والأدوات عند
   المستخدمين ستكتشف التحديث في أول تشغيل وتسألهم هل يريدون التثبيت.

> ملاحظة: كل ملف في `tool/` يُنسخ تلقائياً إلى `downloads/` وقت البناء،
> والحزمة `WiFiAuto_v2.zip` تُبنى من نفس المجلد.

## الرفع لأول مرة (GitHub) — تم بالفعل ✅

الموقع منشور حي على: **https://alx-zoro-304.github.io/WiFiAuto/**

النشر الحالي: فرع `gh-pages` (يحتوي مخرجات البناء) — يُحدَّث يدوياً بـ:

```bash
./scripts/sync-tool.sh && npm run build
git branch -D gh-pages 2>/dev/null; git checkout --orphan gh-pages
git rm -qrf . && cp -r dist/* . && touch .nojekyll
git add -A && git commit -m "deploy" && git push -f origin gh-pages
git checkout main
```

> ⚠️ ملف `.github/workflows/deploy.yml` (النشر التلقائي مع كل push) جاهز
> محفوظ في `~/.config/opencode` مؤقتاً، ويُستعاد ليفعل النشر التلقائي بعد
> إضافة صلاحية `workflow` للـ token عبر `gh auth refresh -s workflow`.

> ⚠️ إذا غيّرت اسم الريبو عن `WiFiAuto`، عدّل الروابط في:
> `tool/updater.py` (السطران UPDATE_URL و DOWNLOAD_BASE) و `version.json` (homepage).

## التطوير محلياً

```bash
npm install
npm run dev        # معاينة حية
./scripts/sync-tool.sh && npm run build   # بناء + مزامنة downloads
npm run preview    # معاينة البناء النهائي
```