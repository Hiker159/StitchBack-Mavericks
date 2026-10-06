import unittest
import vcard_birthdays as v
import birthday_bridge as b

def card(uid='one',name='Name',birthday='2000-02-29'):
 return 'BEGIN:VCARD\nVERSION:3.0\nUID:'+uid+'\nFN:'+name+'\n'+('BDAY:'+birthday+'\n' if birthday is not None else '')+'END:VCARD\n'
class VCardTests(unittest.TestCase):
 def test_unicode_folding_and_escapes(self):
  ids,rows=v.parse(card(name='Zoë\\, Long\n  Name'))
  self.assertEqual(rows,[('one','Zoë, Long Name',2,29)])
 def test_date_forms(self):
  for d in ['20000229','--0229','--02-29','1604-02-29']:
   self.assertEqual(v.parse(card(birthday=d))[1][0][2:],(2,29))
 def test_missing_birthday_retains_identity(self):
  self.assertEqual(v.parse(card(birthday=None)),(['one'],[]))
 def test_bad_exports_fail(self):
  for value in ['',card()[:-12],card()+card(),card(uid=''),card(birthday='2000-02-30'),card(birthday='unknown'),card().replace('VERSION:3.0','VERSION:2.1')]:
   with self.assertRaises(ValueError):v.parse(value)
 def test_partial_export_preserves_absent_and_removes_explicit(self):
  desired=b.parse_birthdays('MLBIRTHDAYS1\na\tA\t1\t1\nb\tB\t2\t2\nEND','restored')
  current={k:{'uid':k,'description':r['description']} for k,r in desired.items()}
  included={b.digest('restored\0a')}
  incoming={k:dict(r) for k,r in current.items() if k not in included}
  changes=b.plan(incoming,current)
  self.assertEqual(len(changes['delete']),1)
  self.assertEqual(changes['delete'][0]['uid'],b.digest('restored\0a'))
  self.assertFalse(changes['create'] or changes['update'])

 def test_apple_export_identity_and_date(self):
  text=card(uid='example-id:ABPerson',name='Test Two',birthday='2007-09-30').replace('UID:','X-ABUID:')
  ids,rows=v.parse(text)
  self.assertEqual(ids,['example-id:ABPerson'])
  self.assertEqual(rows,[('example-id:ABPerson','Test Two',9,30)])
  changed=v.parse(text.replace('Test Two','Renamed').replace('2007-09-30','2007-10-01'))
  self.assertEqual(ids,changed[0])
  self.assertEqual(changed[1][0][1:],('Renamed',10,1))
 def test_apple_duplicate_and_conflicting_identity_rejected(self):
  apple=card().replace('UID:','X-ABUID:')
  for text in [apple+apple,apple.replace('X-ABUID:one','UID:other\nX-ABUID:one'),apple.replace('X-ABUID:one','X-ABUID:one\nX-ABUID:two')]:
   with self.assertRaises(ValueError):v.parse(text)
 def test_matching_aliases_and_missing_birthday(self):
  text=card(birthday=None).replace('UID:one','UID:one\nX-ABUID:one')
  self.assertEqual(v.parse(text),(['one'],[]))
