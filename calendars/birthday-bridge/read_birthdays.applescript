on cleanText(v)
 set s to v as text
 repeat with bad in {tab, return, linefeed}
  set oldDelimiters to AppleScript's text item delimiters
  set AppleScript's text item delimiters to contents of bad
  set parts to text items of s
  set AppleScript's text item delimiters to " "
  set s to parts as text
  set AppleScript's text item delimiters to oldDelimiters
 end repeat
 return s
end cleanText
on run argv
 set appPath to item 1 of argv
 set outputText to "MLBIRTHDAYS1" & linefeed
 with timeout of 120 seconds
  tell application appPath
   set birthdayPeople to every «class azf4»
   repeat with personRecord in birthdayPeople
    set birthValue to get «property az11» of personRecord
    if birthValue is not missing value then
     set personID to get «property ID  » of personRecord
     set personName to get «property pnam» of personRecord
     set birthMonth to (month of birthValue) as integer
     set birthDay to day of birthValue
     set outputText to outputText & my cleanText(personID) & tab & my cleanText(personName) & tab & birthMonth & tab & birthDay & linefeed
    end if
   end repeat
  end tell
 end timeout
 return outputText & "END"
end run
