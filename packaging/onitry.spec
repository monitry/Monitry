# PyInstaller recipe for Onitry.app (Full Focus). Build with: pyinstaller packaging/onitry.spec --noconfirm
# Run from the repo root. packaging/build_mac.sh does the whole thing, including the icon and the .dmg.
import os

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

block_cipher = None

a = Analysis(
    [os.path.join(ROOT, "onitry_app.py")],
    pathex=[ROOT],
    binaries=[],
    datas=[],
    hiddenimports=[
        # keyring picks its backend at runtime, so PyInstaller cannot see it
        "keyring.backends.macOS",
        "keyring.backends.fail",
        # the app imports these lazily or through other modules
        "core.edition", "core.paths", "core.license", "core.auth", "core.bridge", "core.idle",
        "ai.review", "ai.client", "alerts.notifier", "capture.screen",
    ],
    hookspath=[],
    runtime_hooks=[],
    # not part of Full Focus: the menu bar app (rumps) and ClassWatch's heavy dependencies
    excludes=["rumps", "ultralytics", "torch", "torchvision", "matplotlib", "pytest", "IPython"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Onitry",
    debug=False,
    strip=False,
    upx=False,
    console=False,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Onitry")

app = BUNDLE(
    coll,
    name="Onitry.app",
    icon=os.path.join(ROOT, "packaging", "Onitry.icns"),
    bundle_identifier="app.onitry.focus",
    info_plist={
        "CFBundleName": "Onitry",
        "CFBundleDisplayName": "Onitry",
        "CFBundleShortVersionString": os.environ.get("ONITRY_VERSION", "1.0.0"),
        "CFBundleVersion": os.environ.get("ONITRY_VERSION", "1.0.0"),
        "NSHighResolutionCapable": True,
        "LSMinimumSystemVersion": "11.0",
        # shown if macOS asks whether Onitry may control System Events (the focus reminder uses it)
        "NSAppleEventsUsageDescription": "Onitry uses this to bring its focus reminder to the front.",
    },
)
