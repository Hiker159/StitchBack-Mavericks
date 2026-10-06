on run argv
 set appPath to item 1 of argv
 set calendarMarker to item 2 of argv
 set eventPrefix to item 3 of argv
 set foundIDs to {}
 set outputText to ""
 with timeout of 120 seconds
  tell application appPath
   repeat with calendarRecord in every «class wres»
    if («property wr12» of calendarRecord) is calendarMarker then
     set end of foundIDs to «property ID  » of calendarRecord
     set outputText to "MLCAL1" & tab & («property ID  » of calendarRecord) & linefeed
     repeat with eventRecord in every «class wrev» of calendarRecord
      set eventDescription to «property wr12» of eventRecord
      if eventDescription is not missing value then
       if eventDescription starts with eventPrefix then
        set outputText to outputText & («property ID  » of eventRecord) & tab & eventDescription & linefeed
       end if
      end if
     end repeat
    end if
   end repeat
  end tell
 end timeout
 if (count of foundIDs) > 1 then error "Multiple bridge calendars found; no changes made."
 if (count of foundIDs) is 0 then set outputText to "MLCAL1" & tab & "NONE" & linefeed
 return outputText & "END"
end run
