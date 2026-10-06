# Source and build notes

## Requirements

- Your own Mountain Lion and Mavericks installer images.
- A macOS build machine with Xcode command-line tools and Python 3.
- A Mavericks (10.9) machine for runtime checks. The launcher guards reject
  other systems and root execution.

All restoration sources are in `Mavericks System Apps/`. Builders resolve paths
relative to their own files. Python collectors and launch tools intended for
Mavericks use its system Python where required; builders use Python 3.

## Local inputs and generated files

Put `InstallESD.dmg` (Mountain Lion) and `InstallMacOSXMavericks.dmg` (Mavericks)
in `Mavericks System Apps/` locally. Extraction workflows expect the original
Apple file hierarchy under `originals/` and `mavericks-originals/`, plus the
Mountain Lion Essentials `Payload` and `Bom` under `work/Essentials/`.
Inspect extraction scripts before preparing these inputs; do not execute
installer package scripts. Selected account-plugin extraction scripts read
that payload and BOM.

This is a collection of staged research/build scripts, **not a one-command
clean build**. Many later builders copy specific earlier `builds/` outputs and
preserve existing destinations. Run the dependency stages referenced by each
script before its later stage, or supply those local outputs. No generated
Apple app bundle is provided here.

## Current package

- `package_preview_06.py` combines Notes Accounts04 with Preview05 Contacts,
  Calendar, and Birthday Bridge.
- `build_notes_accounts04.py` restores standard mail content identifiers;
  Accounts01–03 and the storage/probe scripts provide its prerequisite stages.
- `package_preview_05.py` contains Contacts Accounts02 + Background01 and the
  stable Calendar build from Preview04.
- `build_calendar_private_accounts10.py` is the tested Calendar account build.
- `birthday-bridge/` implements the export-based birthday workflow.

The older Google calendar bridge/mirror/reverse/sync directories and Google
sound experiments are retained as research source. They are not the current
native Google backend used by Preview06. Read a script's input paths before
running it; early experiments may use different identities and data stores.

Build scripts patch local copies, sign them, and create ZIPs in `deliverables/`.
Use packaged launchers on Mavericks so private storage and account routing
apply. Do not replace system apps/frameworks or launch legacy binaries on a
modern build host. Confirm behavior on Mavericks with disposable test data.
Keep installer assets, personal accounts, credentials, diagnostics, and generated
bundles out of Git. `.gitignore` excludes these local inputs and outputs.
