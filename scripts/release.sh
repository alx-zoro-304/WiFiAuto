#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
SITE="https://alx-zoro-304.github.io/WiFiAuto"

CUR_VER=$(python3 -c "import json; print(json.load(open('version.json'))['current_version'])")
NEW_VER="${1:-}"
if [ -z "$NEW_VER" ]; then
  read -rp "النسخة الحالية: $CUR_VER — النسخة الجديدة (مثال: 2.1): " NEW_VER
fi
if ! [[ "$NEW_VER" =~ ^[0-9]+\.[0-9]+$ ]]; then
  echo "صيغة غير صحيحة — استخدم مثال: 2.1"
  exit 1
fi
if [ "$NEW_VER" = "$CUR_VER" ]; then
  echo "نفس الإصدار الحالي ($CUR_VER) — لا يوجد نشر"
  exit 1
fi

echo "==> تحديث version.json إلى v$NEW_VER"
python3 - "$NEW_VER" <<'EOF'
import json, sys, datetime
ver = sys.argv[1]
with open('version.json', encoding='utf-8') as f:
    d = json.load(f)
d['current_version'] = ver
d['published'] = datetime.date.today().isoformat()
with open('version.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
    f.write('\n')
EOF

read -rp "هل تغيّر MAC Changer Pro أيضاً؟ (y/N): " MC_CHANGED
if [[ "$MC_CHANGED" =~ ^[yY] ]]; then
  read -rp "إصدار MAC Changer الجديد (مثال: 1.1): " MC_VER
  python3 - "$MC_VER" <<'EOF'
import json, sys
ver = sys.argv[1]
with open('version.json', encoding='utf-8') as f:
    d = json.load(f)
d['mac_changer_version'] = ver
with open('version.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
    f.write('\n')
EOF
fi

read -rp "إضافة سطر في سجل التحديثات؟ (y/N): " ADD_CL
if [[ "$ADD_CL" =~ ^[yY] ]]; then
  read -rp "ملاحظة (إنجليزي، افصل بين النقاط بـ | ): " NOTE_EN
  read -rp "ملاحظة (عربي): " NOTE_AR
  python3 - "$NEW_VER" "$NOTE_EN" "$NOTE_AR" <<'EOF'
import json, sys, datetime
ver, en, ar = sys.argv[1], sys.argv[2], sys.argv[3]
with open('version.json', encoding='utf-8') as f:
    d = json.load(f)
entry = {'version': ver, 'date': datetime.date.today().isoformat()}
if en.strip():
    entry['notes_en'] = [n.strip() for n in en.split('|') if n.strip()]
if ar.strip():
    entry['notes_ar'] = [n.strip() for n in ar.split('|') if n.strip()]
d['changelog'].insert(0, entry)
with open('version.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
    f.write('\n')
EOF
fi

echo "==> البناء"
[ -d node_modules ] || npm install --silent
./scripts/sync-tool.sh
npm run build 2>&1 | tail -2
[ -f dist/index.html ] || { echo "فشل البناء"; exit 1; }

echo "==> رفع main"
git add -A
git diff --cached --quiet && { echo "لا تغييرات للرفع"; exit 1; }
git commit -q -m "release v$NEW_VER"
git push

echo "==> نشر gh-pages"
rm -rf /tmp/opencode/ghpage-wt
if git show-ref --verify --quiet refs/heads/gh-pages; then
  git worktree add /tmp/opencode/ghpage-wt gh-pages
  cd /tmp/opencode/ghpage-wt
  git rm -qrf . 2>/dev/null || true
  find . -mindepth 1 ! -name .git -delete
  cp -a "$ROOT"/dist/. .
  touch .nojekyll
  git add -A
  git commit -q -m "deploy v$NEW_VER"
  git push -f origin gh-pages
  cd "$ROOT"
  git worktree remove --force /tmp/opencode/ghpage-wt
else
  git checkout -q --orphan gh-pages
  git clean -fdx -q
  git rm -qrf . 2>/dev/null || true
  cp -a dist/. .
  touch .nojekyll
  git add -A
  git commit -q -m "deploy v$NEW_VER"
  git push -f origin gh-pages
  git checkout -q main
  [ -d node_modules ] || npm install --silent
fi

echo "==> التحقق من الموقع الحي (انتظر حتى يبني GitHub Pages...)"
sleep 20
CODE=$(curl -s -o /dev/null -w "%{http_code}" "$SITE/version.json")
LIVE_VER=$(curl -s "$SITE/version.json" | python3 -c "import json,sys; print(json.load(sys.stdin)['current_version'])" 2>/dev/null || echo "?")
echo "الموقع: HTTP $CODE — النسخة الحية: v$LIVE_VER"
if [ "$CODE" = "200" ] && [ "$LIVE_VER" = "$NEW_VER" ]; then
  echo "تم النشر بنجاح: $SITE"
else
  echo "النسخة المتوقعة: v$NEW_VER — لو ظهرت غير كده انتظر دقيقة ثم أعد الفحص:"
  echo "  curl -s $SITE/version.json"
fi