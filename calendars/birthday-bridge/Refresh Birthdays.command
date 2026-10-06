#!/bin/bash
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
case "$(/usr/bin/sw_vers -productVersion)" in
  10.9|10.9.*) ;;
  *) echo 'Use this birthday test on Mavericks only.'; exit 1 ;;
esac
OUT="$HERE/Birthday-diagnostics-$(/bin/date +%Y%m%d-%H%M%S)-$$"
/bin/mkdir "$OUT" || exit 1
{
  /bin/date
  /usr/bin/sw_vers
} > "$OUT/system.txt"
/usr/bin/python "$HERE/birthday_bridge.py" restored "$HERE/Contacts.vcf" > "$OUT/refresh.log" 2>&1
RESULT=$?
/bin/cat "$OUT/refresh.log"
echo "Refresh exit status: $RESULT" >> "$OUT/refresh.log"
if [ -f "$HERE/bridge-manifest.json" ]; then /bin/cp "$HERE/bridge-manifest.json" "$OUT/bridge-manifest.json"; fi
/usr/bin/ditto -c -k --keepParent "$OUT" "$OUT.zip"
echo "Diagnostics: $OUT.zip"
echo 'Review the log before sharing. Local recovery data is not included.'
echo 'Press Return to close.'
read -r DONE
exit "$RESULT"
