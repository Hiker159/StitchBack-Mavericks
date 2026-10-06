# -*- coding: utf-8 -*-
import unittest,sys,types
from unittest.mock import patch
import birthday_bridge as b

def contacts(rows):return 'MLBIRTHDAYS1\n'+''.join('%s\t%s\t%s\t%s\n'%r for r in rows)+'END'
def current(desired):return {k:{'uid':'event-'+str(i),'description':row['description']} for i,(k,row) in enumerate(sorted(desired.items()))}
class BridgeTests(unittest.TestCase):
 def test_initial_repeat_and_change(self):
  first=b.parse_birthdays(contacts([('id1','Ana "A" \\ Test',1,4),('id2','Zoë',2,29)]),'restored')
  self.assertEqual(len(b.plan(first,{})['create']),2)
  saved=current(first);self.assertFalse(any(b.plan(first,saved).values()))
  second=b.parse_birthdays(contacts([('id1','New Name',3,2),('id3','Added',12,31)]),'restored')
  p=b.plan(second,saved);self.assertEqual([len(p[x]) for x in ['create','update','delete']],[1,1,1])
 def test_incomplete_invalid_duplicate_contacts_abort(self):
  for text in ['MLBIRTHDAYS1\nid\tName\t1\t1',contacts([('id','Name',2,30)]),contacts([('id','Name',1,1),('id','Again',1,2)]),contacts([('','Name',1,1)])]:
   with self.assertRaises(ValueError):b.parse_birthdays(text,'restored')
 def test_empty_complete_snapshot_removes_only_managed_set(self):
  saved=current(b.parse_birthdays(contacts([('id','Name',1,1)]),'restored'))
  p=b.plan(b.parse_birthdays(contacts([]),'restored'),saved)
  self.assertEqual(p['delete'],list(saved.values()))
 def test_calendar_snapshot_validation(self):
  desired=b.parse_birthdays(contacts([('id','Name',1,1)]),'restored');row=next(iter(desired.values()))
  text='MLCAL1\tcalendar-id\nevent-id\t'+row['description']+'\nEND'
  uid,saved=b.parse_calendar(text,'restored');self.assertEqual(uid,'calendar-id');self.assertFalse(any(b.plan(desired,saved).values()))
  for invalid in [text.replace('\nEND',''),text.replace('MLB1|restored','MLB1|stock'),text.replace('\nEND','\nevent2\t'+row['description']+'\nEND')]:
   with self.assertRaises(ValueError):b.parse_calendar(invalid,'restored')
 def test_guarded_script_and_escaping(self):
  first=b.parse_birthdays(contacts([('id','Old',1,1)]),'restored');saved=current(first)
  new=b.parse_birthdays(contacts([('id','New "Name" \\ text',12,31)]),'restored')
  script=b.apply_script('restored','cal',saved,b.plan(new,saved))
  self.assertLess(script.index('Calendar ownership changed'),script.index('set targetEvent'))
  self.assertLess(script.index('Birthday ownership changed'),script.index('set targetEvent'))
  self.assertIn('my makeDate(2001, 1, 1)',script)
  self.assertIn(b.literal('New "Name" \\ text'+"'s Birthday"),script)
  self.assertNotIn('/Applications/Contacts.app',script)
  with self.assertRaises(ValueError):b.literal('bad\nscript')
 def test_no_stock_source(self):self.assertEqual(set(b.SOURCES),{'restored'})
 def test_running_app_guard(self):
  class URL:
   def __init__(self,p):self.p=p
   def path(self):return self.p
  class App:
   def __init__(self,p):self.p=p
   def bundleIdentifier(self):return 'com.apple.AddressBook'
   def bundleURL(self):return URL(self.p)
   def localizedName(self):return 'Contacts'
   def executableURL(self):return URL(self.p+'/Contents/MacOS/Contacts')
   def processIdentifier(self):return 123
  apps=[App('/safe/Contacts.app')]
  workspace=types.SimpleNamespace(runningApplications=lambda:apps)
  module=types.SimpleNamespace(NSWorkspace=types.SimpleNamespace(sharedWorkspace=lambda:workspace))
  with patch.dict(sys.modules,{'AppKit':module}),patch.object(b.subprocess,'check_output',return_value=b'123 /safe/Contacts.app/Contents/MacOS/Contacts'):
   b.require_running('com.apple.AddressBook','/safe/Contacts.app')
   apps[:]=[App('/Applications/Contacts.app')]
   with self.assertRaisesRegex(RuntimeError,'different or unavailable bundle path'):b.require_running('com.apple.AddressBook','/safe/Contacts.app')
   apps[:]=[]
   with self.assertRaisesRegex(RuntimeError,'expected bundle identifier'):b.require_running('com.apple.AddressBook','/safe/Contacts.app')
   apps[:]=[App('/safe/Contacts.app'),App('/Applications/Contacts.app')]
   with self.assertRaises(RuntimeError):b.require_running('com.apple.AddressBook','/safe/Contacts.app')

class WorkflowTests(unittest.TestCase):
 def test_partial_contacts_response_never_reaches_calendar_writes(self):
  import tempfile,os
  with tempfile.TemporaryDirectory() as state:
   with patch.object(b.sys,'argv',['bridge','restored']),patch.object(b.subprocess,'check_output',return_value=b'10.9.5'),patch.object(b.os,'geteuid',return_value=501),patch.object(b.os.path,'expanduser',return_value=state),patch.object(b,'require_running'),patch.object(b,'run_script',return_value='MLBIRTHDAYS1\nid\tName\t1\t1') as script:
    with self.assertRaises(ValueError):b.main()
    self.assertEqual(script.call_count,1)
    self.assertFalse(os.path.exists(os.path.join(state,'refresh.lock')))
    self.assertFalse(os.path.exists(os.path.join(state,'last-refresh.json')))
 def test_unchanged_refresh_never_sends_apply_script(self):
  import tempfile,os
  data=contacts([('id','Name',1,1)]);desired=b.parse_birthdays(data,'restored');row=next(iter(desired.values()))
  snapshot='MLCAL1\tcal\nevent\t'+row['description']+'\nEND'
  with tempfile.TemporaryDirectory() as state:
   with patch.object(b.sys,'argv',['bridge','restored']),patch.object(b.subprocess,'check_output',return_value=b'10.9.5'),patch.object(b.os,'geteuid',return_value=501),patch.object(b.os.path,'expanduser',return_value=state),patch.object(b,'require_running'),patch.object(b,'run_script',side_effect=[data,snapshot]) as script:
    self.assertEqual(b.main(),0);self.assertEqual(script.call_count,2)
    self.assertFalse(os.path.exists(os.path.join(state,'refresh.lock')))

if __name__=='__main__':unittest.main()
