import platform
import subprocess
import importlib
import sys
import os
bl_info = {
    "name": "Blender Backup - Version Control Supercharged",
    "authon": "Nameless",
    "description": "Version control for Blender.",
    "blender": (3, 4, 1),
    "category": "Backup"
}


# Ensure pip is installed
try:
    import pip
except ModuleNotFoundError:
    # Installing pip
    import ensurepip
    ensurepip._main()

# Get executable path
executable = sys.executable

system = platform.system()
LINUX = "Linux"
WINDOWS = "Windows"
if system == LINUX:
    """
        Debian Bug: pygit2 import fails if /usr/lib/ssl/certs does not exist
        https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1011714
        Create ../bin/certs directory to overcome the bug
        -- bin/
            |-- python.exe (sys.executable)
            |-- certs/
            :
    """
    certsPath = os.path.abspath(os.path.join(executable, "..", "cert"))
    os.makedirs(certsPath, exist_ok=True)

    # Set SSL_CERT_DIR environment variable
    os.environ["SSL_CERT_DIR"] = certsPath
elif system == WINDOWS:
    """
        Set pip target to ../lib/site-packages to avoid 
        ImportError: DLL load failed while importing <module>
        -- python/
            |-- bin/
            |    |-- python.exe (sys.executable)
            |    :
            |-- lib/
            :    |-- site-packages/ (UAC elevation required to write)
            :    :
    """
    sitePath = os.path.abspath(
        os.path.join(executable, "..", "..", "lib", "site-packages"))

    os.environ["PIP_TARGET"] = sitePath

# Ensure Pygit2 is installed
try:
    import pygit2 as git
except ModuleNotFoundError:
    # Upgrade pip
    try:
        subprocess.check_call(
            [executable, "-m", "pip", "install", "-U", "pip", "--no-cache-dir"])
    except subprocess.CalledProcessError as e:
        print(f"Pip is upto data. {e}")

    # Install Pygit2
    subprocess.check_call(
        [executable, "-m", "pip", "install", "pygit2", "--no-cache-dir"])

    import pygit2 as git

print(f"{git.__name__} is installed.")

# Local imports implemented to support Blender refreshes
"""ORDER MATTERS"""
modulesNames = ("sourceControl", "commitDialog",
                "commitsPanel", "iconsPanel", "appHandlers", "preferences")
for module in modulesNames:
    if module in sys.modules:
        importlib.reload(sys.modules[module])
    else:
        globals()[module] = importlib.import_module(f"{__name__}.{module}")


def register():
    for moduleName in modulesNames:
        if hasattr(globals()[moduleName], "register"):
            globals()[moduleName].register()


def unregister():
    for module in modulesNames:
        if hasattr(globals()[module], "unregister"):
            globals()[module].unregister()
