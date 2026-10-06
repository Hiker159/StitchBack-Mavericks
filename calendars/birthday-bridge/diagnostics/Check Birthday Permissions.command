#!/bin/bash
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
case "$(/usr/bin/sw_vers -productVersion)" in
  10.9|10.9.*) ;;
  *) echo 'Run this on the Mavericks laptop.'; exit 1 ;;
esac
if [ ! -f "$HERE/birthday_bridge.py" ]; then
  echo 'Place this command inside the existing Birthdays folder, then open it again.'
  read -r DONE
  exit 1
fi
OUT="$HERE/Birthday-permissions-$(/bin/date +%Y%m%d-%H%M%S)-$$"
/bin/mkdir "$OUT" || exit 1
/bin/date > "$OUT/system.txt"
/usr/bin/sw_vers >> "$OUT/system.txt"
# Run only the guarded Contacts reader: no Calendar read or write commands.
/usr/bin/python - "$HERE" > "$OUT/contacts-read.log" 2>&1 <<'PY'
from __future__ import print_function
import sys,os
sys.path.insert(0,sys.argv[1])
import birthday_bridge as b
try:
    app=os.path.join(os.path.dirname(b.ROOT),'Contacts','Mountain Lion Contacts.app')
    b.require_running('com.apple.AddressBook',app)
    result=b.run_script(os.path.join(b.ROOT,'read_birthdays.applescript'),[app])
    rows=b.parse_birthdays(result,'restored')
    print('Contacts read succeeded. Birthday count: %d' % len(rows))
except Exception as e:
    print('Contacts read failed: '+str(e))
    sys.exit(1)
PY
RESULT=$?
echo "Read exit status: $RESULT" >> "$OUT/contacts-read.log"
/usr/bin/python - "$OUT" <<'PY'
from __future__ import print_function
import os,sys,collections
out=sys.argv[1]
sources=[('contacts-security.log',os.path.expanduser('~/Library/Logs/Mountain Lion Restored Apps/Contacts.log')),
         ('system-security.log','/var/log/system.log')]
words=('tcc','audittoken','audit token','scripting','applescript','osascript','denied','permission','not permitted','securitypolicy')
for name,path in sources:
    with open(os.path.join(out,name),'w') as dest:
        try:
            with open(path,'r') as f:lines=collections.deque(f,maxlen=3000)
            matched=[line for line in lines if any(word in line.lower() for word in words)]
            dest.writelines(matched[-150:])
            if not matched:dest.write('No matching messages in the last 3000 log lines.\n')
        except Exception as e:dest.write('Log unavailable: %s\n'%e)
PY
/bin/cat "$OUT/contacts-read.log"
/usr/bin/ditto -c -k --keepParent "$OUT" "$OUT.zip"
echo "Diagnostics: $OUT.zip"
echo 'This test did not send any Calendar commands. Review logs before sharing.'
echo 'Press Return to close.'
read -r DONE
