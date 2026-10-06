# Mountain Lion Apps on Mavericks

An experimental project restoring the classic Mountain Lion versions of
**Notes, Contacts, and Calendar** on OS X Mavericks (10.9), including their
original visual designs. Compatibility patches and app-local frameworks let
the restored apps run alongside the stock Mavericks apps with separate data.

The current Preview 06 includes native Google syncing for all three apps,
background Contacts syncing, and Calendar alerts with snooze, notification
clicks, and logout/restart recovery. Notes download and edit syncing have been
tested on Mavericks; additional creation/deletion and login checks are pending.
Google Calendar uses Message reminders; the experimental Google sound patches
are not part of the current preview. Birthdays use a Contacts vCard export.
iCloud testing and background Notes syncing are not yet complete.

This repository contains restoration source, build/package scripts, probes,
and tests. **Apple installers, extracted applications/frameworks, generated
app bundles, and personal diagnostic logs are not included.** Building requires
your own Mountain Lion and Mavericks installers and a Mavericks test machine.

## Source layout

- `notes/`: Notes restoration, account UI, private storage, and probes.
- `contacts/`: Contacts restoration, CardDAV setup, and background sync.
- `calendars/`: Calendar restoration, alerts, native accounts, and the birthday
  bridge. Shared account compatibility helpers and suite packagers also live here
  and are reused by Notes and Contacts.

See [BUILDING.md](BUILDING.md) for the source layout and build prerequisites.
The project is experimental and is not affiliated with Apple.
