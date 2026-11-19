import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "osu_rankstats.pyw")
ICO = os.path.join(HERE, "icon.ico")
WORK = os.path.join(HERE, "build")
ISCC_PATHS = [
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Inno Setup 6", "ISCC.exe"),
    os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Inno Setup 6", "ISCC.exe"),
    os.path.join(os.environ.get("ProgramFiles", ""), "Inno Setup 6", "ISCC.exe"),
]

subprocess.check_call([
    sys.executable, "-m", "PyInstaller", SRC,
    "--onefile", "--noconsole", "--noconfirm", "--clean",
    "--name", "osu-rankstats", "--icon", ICO,
    "--hidden-import", "pystray._win32",
    "--exclude-module", "numpy", "--exclude-module", "unittest",
    "--distpath", os.path.join(WORK, "dist"),
    "--workpath", os.path.join(WORK, "tmp"),
    "--specpath", WORK,
])

iscc = next((p for p in ISCC_PATHS if os.path.isfile(p)), None)
if not iscc:
    sys.exit("Inno Setup 6 not found: winget install JRSoftware.InnoSetup")
subprocess.check_call([iscc, "/Q", os.path.join(HERE, "installer.iss")])
print("\nOK:", os.path.join(HERE, "dist"))
