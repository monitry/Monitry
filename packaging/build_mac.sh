#!/bin/sh
# Builds dist/Onitry.app and Onitry.dmg on a Mac. Run from anywhere: sh packaging/build_mac.sh
# Needs Python 3.11 with Tk (python.org or conda), and `pip install -r requirements.txt pyinstaller pillow`.
set -eu
cd "$(dirname "$0")/.."

python3 packaging/make_icon.py
python3 -m PyInstaller packaging/onitry.spec --noconfirm --clean

# Apple Silicon refuses unsigned code, so give it an ad-hoc signature (this is not Apple notarization).
codesign --force --deep --sign - dist/Onitry.app

# The bundle must be able to import everything without opening a window.
dist/Onitry.app/Contents/MacOS/Onitry --selftest

# A disk image with the app and an Applications shortcut, so installing is "drag this onto that".
STAGE="$(mktemp -d)"
cp -R dist/Onitry.app "$STAGE/"
ln -s /Applications "$STAGE/Applications"
DMG="${1:-dist/Onitry.dmg}"
rm -f "$DMG"
hdiutil create -volname "Onitry" -srcfolder "$STAGE" -ov -format UDZO "$DMG"
rm -rf "$STAGE"
echo "Built dist/Onitry.app and $DMG"
