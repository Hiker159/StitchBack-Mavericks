# -*- coding: utf-8 -*-
"""One-way birthday bridge via running apps' Apple events, never raw databases.
Mavericks system Python 2.7 and host Python 3 compatible. No background polling.
"""
from __future__ import print_function,unicode_literals
import datetime,hashlib,json,os,re,subprocess,sys,tempfile
try:
    text_type=unicode
except NameError:
    text_type=str
ROOT=os.path.dirname(os.path.realpath(__file__))
if not isinstance(ROOT,text_type):ROOT=ROOT.decode(sys.getfilesystemencoding() or 'utf-8')
SOURCES={'restored':('com.apple.AddressBook','Contacts Birthdays')}
def digest(value):return hashlib.sha256(value.encode('utf-8')).hexdigest()
def literal(value):
    # AppleScript string literals escape both backslash and quotes. Control
    # characters are rejected rather than being interpreted as script syntax.
    if any(ord(c)<32 for c in value):raise ValueError('Unexpected control character in scripting value')
    return '"'+value.replace('\\','\\\\').replace('"','\\"')+'"'
def parse_birthdays(text,source):
    lines=text.strip().splitlines()
    if not lines or lines[0]!='MLBIRTHDAYS1' or lines[-1]!='END':raise ValueError('Incomplete Contacts response; nothing will be removed')
    result={}
    for line in lines[1:-1]:
        fields=line.split('\t')
        if len(fields)!=4:raise ValueError('Malformed birthday record')
        uid,name,month,day=fields
        if not uid or not name:raise ValueError('Missing contact name or identity')
        month,day=int(month),int(day);datetime.date(2000,month,day)
        key=digest(source+'\0'+uid)
        if key in result:raise ValueError('Duplicate contact identity')
        fingerprint=digest(json.dumps([name,month,day],ensure_ascii=False))
        result[key]={'key':key,'name':name,'month':month,'day':day,'description':'MLB1|'+source+'|'+key+'|'+fingerprint}
    return result
def parse_calendar(text,source):
    lines=text.strip().splitlines()
    if not lines or not lines[0].startswith('MLCAL1\t') or lines[-1]!='END':raise ValueError('Incomplete Calendar response')
    uid=lines[0].split('\t',1)[1];records={}
    for line in lines[1:-1]:
        event_id,description=line.split('\t',1)
        match=re.match(r'^MLB1\|'+source+r'\|([a-f0-9]{64})\|([a-f0-9]{64})$',description)
        if not match or not event_id:raise ValueError('Malformed managed event marker')
        key=match.group(1)
        if key in records:raise ValueError('Duplicate birthday events; refusing ambiguous changes')
        records[key]={'uid':event_id,'description':description}
    if uid=='NONE' and records:raise ValueError('Events without calendar')
    return (None if uid=='NONE' else uid),records

def plan(desired,current):
    return {'create':[desired[k] for k in sorted(set(desired)-set(current))],
            'update':[(current[k],desired[k]) for k in sorted(set(desired)&set(current)) if current[k]['description']!=desired[k]['description']],
            'delete':[current[k] for k in sorted(set(current)-set(desired))]}

def apply_script(source,calendar_uid,current,changes):
    marker='org.local.MLBirthdayBridge/'+source+'/v1'
    out=['on makeDate(y, m, d)', 'set x to «event misccurd»','set day of x to 1','set month of x to 1','set year of x to y','set month of x to m','set day of x to d','set time of x to 0','return x','end makeDate','on run argv','set appPath to item 1 of argv','with timeout of 120 seconds','tell application appPath']
    if calendar_uid:
        out+=['set matches to every «class wres» whose «property ID  » is '+literal(calendar_uid),'if (count of matches) is not 1 then error "Bridge calendar disappeared; refresh again."','set targetCalendar to item 1 of matches','if («property wr12» of targetCalendar) is not '+literal(marker)+' then error "Calendar ownership changed; refusing writes."','if («property wr05» of targetCalendar) is false then error "Bridge calendar is not writable."']
        # Preflight EVERY owned event before any updates/deletions. If an event
        # disappeared or its marker was edited since snapshot, fail closed.
        for n,(key,record) in enumerate(sorted(current.items())):
            out+=['set matches to every «class wrev» of targetCalendar whose «property ID  » is '+literal(record['uid']), 'if (count of matches) is not 1 then error "Birthday event changed; refresh again."','if («property wr12» of item 1 of matches) is not '+literal(record['description'])+' then error "Birthday ownership changed; refusing writes."']
    else:
        out+=['if (count of (every «class wres» whose «property wr12» is '+literal(marker)+')) is not 0 then error "Bridge calendar appeared; refresh again."', 'set targetCalendar to make new «class wres» with properties {«property pnam»:'+literal(SOURCES[source][1])+', «property wr12»:'+literal(marker)+'}']
    for existing,row in [(None,row) for row in changes['create']]+changes['update']:
        start=datetime.date(2000,row['month'],row['day']);end=start+datetime.timedelta(days=1)
        out+=['set startValue to my makeDate(%d, %d, %d)'%(start.year,start.month,start.day),'set endValue to my makeDate(%d, %d, %d)'%(end.year,end.month,end.day)]
        props=['«property wr11»:'+literal(row['name']+"'s Birthday"),'«property wr1s»:startValue','«property wr5s»:endValue','«property wrad»:true','«property wr15»:"FREQ=YEARLY"','«property wr12»:'+literal(row['description'])]
        if existing:
            out+=['set targetEvent to first «class wrev» of targetCalendar whose «property ID  » is '+literal(existing['uid'])]
            for prop in props:
                field,value=prop.split(':',1);out+=['set '+field+' of targetEvent to '+value]
        else:out+=['set targetEvent to make new «class wrev» at end of «class wrev» of targetCalendar with properties {'+', '.join(props)+'}']
        out+=['if («property wr11» of targetEvent) is not '+literal(row['name']+"'s Birthday")+' then error "Birthday title did not verify."',
              'if («property wrad» of targetEvent) is not true then error "Birthday all-day setting did not verify."',
              'if («property wr15» of targetEvent) does not contain "FREQ=YEARLY" then error "Birthday recurrence did not verify."']
        for prop,expected in [('wr1s',start),('wr5s',end)]:
            out+=['set checkedDate to «property '+prop+'» of targetEvent',
                  'if (year of checkedDate) is not %d or ((month of checkedDate) as integer) is not %d or (day of checkedDate) is not %d then error "Birthday date did not verify."'%(expected.year,expected.month,expected.day)]
    for record in changes['delete']:
        out+=['set targetEvent to first «class wrev» of targetCalendar whose «property ID  » is '+literal(record['uid']),
              'if («property wr12» of targetEvent) is not '+literal(record['description'])+' then error "Birthday changed before removal; refusing deletion."',
              'delete targetEvent']
    out+=['«event coresave»','end tell','end timeout','return "OK"','end run']
    return '\n'.join(out)+'\n'

def run_script(path,args):
    runner=os.path.join(ROOT,'Birthday Bridge.app','Contents','MacOS','BirthdayScriptRunner')
    if not os.path.isfile(runner):raise RuntimeError('Birthday Bridge.app is missing; install the complete Birthdays folder')
    p=subprocess.Popen([runner,path]+args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    out,err=p.communicate()
    if p.returncode:raise RuntimeError(err.decode('utf-8','replace').strip())
    return out.decode('utf-8').strip()

def require_running(bundle_id,path):
    # Preserve the exact-path guard while recording enough evidence to diagnose
    # direct-executable launches and stale Launch Services identities on 10.9.
    from AppKit import NSWorkspace
    expected=os.path.realpath(path)
    apps=list(NSWorkspace.sharedWorkspace().runningApplications())
    matches=[]
    print('Checking running app: '+expected)
    print('Expected bundle identifier: '+bundle_id)
    for app in apps:
        ident=app.bundleIdentifier()
        url=app.bundleURL()
        actual=os.path.realpath(url.path()) if url else None
        name=app.localizedName() or ''
        executable=app.executableURL()
        executable=executable.path() if executable else None
        relevant=(ident==bundle_id or actual==expected or
                  any(word in (name+' '+(actual or '')+' '+(executable or '')).lower()
                      for word in ['contacts','addressbook','calendar','ical.app']))
        if relevant:
            print('Observed app: '+json.dumps({'pid':int(app.processIdentifier()),
                  'name':name,'bundle_id':ident,'bundle_path':actual,
                  'executable_path':executable},ensure_ascii=True))
        if ident==bundle_id:matches.append(actual)
    if matches==[expected]:
        print('Running app identity verified.')
        return
    # Read-only process evidence catches a running executable omitted from the
    # workspace inventory. Do not treat it as authorization to send Apple events.
    try:
        processes=subprocess.check_output(['/bin/ps','-axo','pid=,comm=']).decode('utf-8','replace')
        for line in processes.splitlines():
            if any(word in line.lower() for word in ['/contacts','/address book','/calendar','/ical']):
                print('Related process: '+line.strip())
    except Exception as error:
        print('Process diagnostic unavailable: '+text_type(error))
    if not matches:
        reason='macOS did not report a running app with the expected bundle identifier.'
    elif len(matches)>1:
        reason='macOS reported multiple running apps with this bundle identifier.'
    else:
        reason='macOS reported a different or unavailable bundle path.'
    raise RuntimeError('App identity check failed: '+reason+
                       ' No birthday refresh was performed. Keep both restored apps open and send this diagnostic ZIP.')

def main():
    if len(sys.argv) not in (2,3) or sys.argv[1] not in SOURCES:raise ValueError('Choose restored Contacts')
    source=sys.argv[1]
    export=sys.argv[2] if len(sys.argv)==3 else None
    version=subprocess.check_output(['/usr/bin/sw_vers','-productVersion']).decode('ascii').strip()
    if not re.match(r'^10\.9(?:\.|$)',version) or os.geteuid()==0:raise RuntimeError('Use Mavericks as the temporary logged-in user, without sudo')
    suite=os.path.dirname(ROOT)
    contacts=os.path.join(suite,'Contacts','Mountain Lion Contacts.app')
    calendar=os.path.join(suite,'Calendar','Mountain Lion Calendar.app')
    if not export:require_running(SOURCES[source][0],contacts)
    require_running('org.local.iCal',calendar)
    state=os.path.expanduser('~/Library/Application Support/ML-Calendar/BirthdayBridge')
    if not os.path.isdir(state):os.makedirs(state)
    lock=os.path.join(state,'refresh.lock')
    try:os.mkdir(lock)
    except OSError:raise RuntimeError('A birthday refresh is already running or left a lock; do not start another.')
    try:
        included=None
        if export:
            import vcard_birthdays
            with open(export,'rb') as f:card_text=f.read().decode('utf-8')
            ids,rows=vcard_birthdays.parse(card_text)
            included=set(digest(source+'\0'+uid) for uid in ids)
            desired=parse_birthdays('MLBIRTHDAYS1\n'+''.join('%s\t%s\t%d\t%d\n'%row for row in rows)+'END',source)
            print('Read %d exported contacts; %d birthdays. Omitted contacts are preserved.'%(len(ids),len(desired)))
        else:
            desired=parse_birthdays(run_script(os.path.join(ROOT,'read_birthdays.applescript'),[contacts]),source)
        uid,current=parse_calendar(run_script(os.path.join(ROOT,'read_calendar.applescript'),[calendar,'org.local.MLBirthdayBridge/'+source+'/v1','MLB1|'+source+'|']),source)
        if included is not None:
            # A selected/partial export must never remove omitted people. An
            # included contact with no BDAY explicitly removes its old birthday.
            desired.update((k,dict(row)) for k,row in current.items() if k not in included)
        changes=plan(desired,current)
        print('Birthdays: %d; add %d, update %d, remove %d.'%(len(desired),len(changes['create']),len(changes['update']),len(changes['delete'])))
        if not any(changes.values()):print('Already up to date.');return 0
        # Keep only IDs/markers and intended changes as recovery evidence. Names
        # occur in planned new/updated events. Store locally with owner access.
        journal=os.path.join(state,'last-refresh.json')
        with open(journal,'w') as f:json.dump({'source':source,'calendar_uid':uid,'before':current,'changes':changes},f,ensure_ascii=True,indent=2)
        os.chmod(journal,0o600)
        script=apply_script(source,uid,current,changes)
        fd,path=tempfile.mkstemp(suffix='.applescript',dir=state)
        try:
            with os.fdopen(fd,'wb') as f:f.write(script.encode('utf-8'))
            if not export:require_running(SOURCES[source][0],contacts)
            require_running('org.local.iCal',calendar)
            if run_script(path,[calendar])!='OK':raise RuntimeError('Unexpected Calendar response')
        finally:os.remove(path)
        final_uid,final=parse_calendar(run_script(os.path.join(ROOT,'read_calendar.applescript'),[calendar,'org.local.MLBirthdayBridge/'+source+'/v1','MLB1|'+source+'|']),source)
        if set(final)!=set(desired) or any(final[k]['description']!=desired[k]['description'] for k in desired):raise RuntimeError('Refresh did not verify; preserve the log and retry only after review')
        print('Verified birthday refresh. Calendar is the only app changed.');return 0
    finally:os.rmdir(lock)
if __name__=='__main__':
    if sys.version_info[0]<3:
        import codecs
        sys.stdout=codecs.getwriter('utf-8')(sys.stdout)
    try:sys.exit(main())
    except Exception as e:print('Birthday refresh stopped: '+text_type(e));sys.exit(1)
