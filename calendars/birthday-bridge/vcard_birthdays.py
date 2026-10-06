# -*- coding: utf-8 -*-
"""Strict UTF-8 vCard 3/4 birthday reader; never treats omitted cards as deletions."""
from __future__ import unicode_literals
import datetime,re

def unescape(value):
    def replace(match):
        c=match.group(1)
        if c in 'nN':return ' '
        if c in ',;\\':return c
        raise ValueError('Unsupported vCard escape')
    return re.sub(r'\\(.)',replace,value)

def parse(text):
    lines=[]
    for line in text.lstrip('\ufeff').splitlines():
        if line.startswith((' ','\t')):
            if not lines:raise ValueError('Invalid vCard continuation')
            lines[-1]+=line[1:]
        else:lines.append(line)
    cards=[];card=None
    for line in lines:
        if not line:continue
        if line.upper()=='BEGIN:VCARD':
            if card is not None:raise ValueError('Nested vCard')
            card={};continue
        if line.upper()=='END:VCARD':
            if card is None:raise ValueError('Unexpected vCard end')
            cards.append(card);card=None;continue
        if card is None:raise ValueError('Content outside vCard')
        if ':' not in line:raise ValueError('Malformed vCard property')
        header,value=line.split(':',1)
        parts=header.split(';');key=parts[0].split('.')[-1].upper()
        if key not in ('VERSION','UID','X-ABUID','FN','BDAY'):continue
        if key in card:raise ValueError('Duplicate vCard identity/name/birthday property')
        if any(p.upper().startswith(('ENCODING=','CHARSET=')) for p in parts[1:]):
            raise ValueError('Export UTF-8 vCard 3.0 without encoded fields')
        card[key]=unescape(value)
    if card is not None or not cards:raise ValueError('Empty or incomplete vCard export')
    seen=set();rows=[];ids=[]
    for card in cards:
        if card.get('VERSION') not in ('3.0','4.0'):raise ValueError('Use vCard 3.0 or 4.0')
        # Apple exports the Address Book identifier under X-ABUID. Keep its
        # full value, including :ABPerson; names never define identity.
        standard=card.get('UID','');apple=card.get('X-ABUID','')
        if standard and apple and standard!=apple:
            raise ValueError('Conflicting UID and X-ABUID; refusing ambiguous identity')
        uid=standard or apple;name=card.get('FN','')
        if not uid or not name or any(ord(c)<32 for c in uid+name):raise ValueError('Contact requires UID or X-ABUID and formatted name')
        if uid in seen:raise ValueError('Duplicate contact UID in export')
        seen.add(uid);ids.append(uid)
        birth=card.get('BDAY')
        if birth is None:continue
        match=re.match(r'^(?:\d{4}-|--)(\d{2})-(\d{2})$',birth)
        if not match:match=re.match(r'^(?:\d{4}|--)(\d{2})(\d{2})$',birth)
        if not match:raise ValueError('Unsupported birthday date; export date-only birthdays')
        month,day=map(int,match.groups());datetime.date(2000,month,day)
        rows.append((uid,name,month,day))
    return ids,rows
