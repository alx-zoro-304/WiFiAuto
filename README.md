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

## الرفع لأول مرة (GitHub)

```bash
git init && git add -A && git commit -m "WiFi Auto official site v2.0"
git remote add origin https://github.com/ALX-ZORO/WiFiAuto.git
git branch -M main
git push -u origin main
```

ثم من صفحة الريبو: **Settings → Pages → Source: GitHub Actions**.
الموقع سيكون على: `https://alx-zoro-304.github.io/WiFiAuto/`

> ⚠️ إذا غيّرت اسم الريبو عن `WiFiAuto`، عدّل الروابط في:
> `tool/updater.py` (السطران UPDATE_URL و DOWNLOAD_BASE) و `version.json` (homepage).

## التطوير محلياً

```bash
npm install
npm run dev        # معاينة حية
./scripts/sync-tool.sh && npm run build   # بناء + مزامنة downloads
npm run preview    # معاينة البناء النهائي
```