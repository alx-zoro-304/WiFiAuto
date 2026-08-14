WiFi Auto - النسخة الينكس
==================================

المحتويات
---------
- wifi_auto_gui.py      : الأداة الرئيسية (WiFi Auto v2.0)
- mac_changer_pro.py    : أداة تغيير MAC مستقلة (نسخة لينكس)
- start_wifi_auto.sh    : تشغيل WiFi Auto (بصلاحيات root تلقائياً عبر pkexec)
- start_changer.sh      : تشغيل MAC Changer Pro
- "WiFi Auto.desktop"   : أيقونة تشغيل WiFi Auto (نقرة مزدوجة)
- "MAC Changer.desktop" : أيقونة تشغيل MAC Changer
- report.txt            : سجل الجلسة الحالية

التشغيل
-------
1. انقر نقراً مزدوجاً على WiFi Auto.desktop لتشغيل الأداة الرئيسية.
2. عند ظهور نافذة كلمة المرور اكتب كلمة سر المستخدم ثم اضغط OK.
3. لاستخدام أداة تغيير MAC المستقلة استخدم MAC Changer.desktop.
   (أو من الطرفية: ./start_wifi_auto.sh أو ./start_changer.sh)

الاعتماديات
-----------
- Python 3 + tkinter مثبتاً (على أغلب التوزيعات موجود).
- NetworkManager (لأمر nmcli) للبحث عن الشبكات المفتوحة والاتصال بها.
- iproute2 (لأمر ip) لتغيير الـ MAC - موجود افتراضياً على كل التوزيعات.

ملاحظات
-------
- تغيير الـ MAC هنا مؤقت: يعود لأصله بعد إعادة تشغيل الكارت أو الجهاز.
  لتثبيته بشكل دائم على الأجهزة الحقيقية استخدم NetworkManager
  (إعدادات الاتصال -> Ethernet/Wi-Fi -> Cloned MAC address).
- الأداة لا تحتاج أي حزم بايثون إضافية: كل شيء داخل السكربت
  (ping نصي، مسح ARP عبر raw sockets، وتغيير MAC عبر ip link).
- للفحص العميق يُفضل تشغيل الأداة من root (يتم تلقائياً).
- أي MAC يرفض التغيير (السائق يعيده) -> يتخطاه فوراً ويجرب التالي.

ملف MAC-Address-Tool.exe في مجلد WiFiAuto خاص بالويندوز فقط
ولا يعمل على لينكس - نسخة لينكس منه هي mac_changer_pro.py.

للإبلاغ عن مشكلة: راجع سجل report.txt داخل هذا المجلد.
