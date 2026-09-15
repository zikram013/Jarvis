"""Localiza y abre aplicaciones instaladas en Windows, macOS y Linux."""

import ctypes
import difflib
import json
import os
import platform
import re
import shlex
import shutil
import string
import subprocess
import unicodedata
from dataclasses import dataclass
from pathlib import Path


SO = platform.system()
PUNTUACION = re.compile(r"[^a-z0-9]+")
EXTENSIONES_EJECUTABLES = {".exe", ".com", ".bat", ".cmd", ".lnk"}


@dataclass(frozen=True)
class ApplicationTarget:
    """Aplicación localizada y mecanismo necesario para iniciarla."""

    name: str
    value: object
    kind: str


WINDOWS_KNOWN = {
    "configuracion": ApplicationTarget("Configuración", "start ms-settings:", "shell"),
    "panel de control": ApplicationTarget("Panel de control", "control", "shell"),
    "administrador de tareas": ApplicationTarget(
        "Administrador de tareas", "taskmgr", "shell"
    ),
    "bloc de notas": ApplicationTarget("Bloc de notas", "notepad", "shell"),
    "explorador de archivos": ApplicationTarget(
        "Explorador de archivos", "explorer", "shell"
    ),
    "cmd": ApplicationTarget("Símbolo del sistema", "cmd", "shell"),
    "simbolo del sistema": ApplicationTarget("Símbolo del sistema", "cmd", "shell"),
    "powershell": ApplicationTarget("PowerShell", "powershell", "shell"),
    "calculadora": ApplicationTarget("Calculadora", "calc", "shell"),
    "paint": ApplicationTarget("Paint", "mspaint", "shell"),
    "registro de windows": ApplicationTarget(
        "Registro de Windows", "regedit", "shell"
    ),
    "administrador de discos": ApplicationTarget(
        "Administrador de discos", "diskmgmt.msc", "shell"
    ),
    "servicios": ApplicationTarget("Servicios", "services.msc", "shell"),
}

MAC_KNOWN = {
    "configuracion": ApplicationTarget(
        "Configuración", ["open", "-b", "com.apple.systempreferences"], "argv"
    ),
    "explorador de archivos": ApplicationTarget("Finder", ["open", "."], "argv"),
    "terminal": ApplicationTarget("Terminal", ["open", "-a", "Terminal"], "argv"),
    "safari": ApplicationTarget("Safari", ["open", "-a", "Safari"], "argv"),
    "calculadora": ApplicationTarget(
        "Calculadora", ["open", "-a", "Calculator"], "argv"
    ),
}

LINUX_KNOWN = {
    "configuracion": ApplicationTarget(
        "Configuración", ["gnome-control-center"], "argv"
    ),
    "explorador de archivos": ApplicationTarget(
        "Explorador de archivos", ["xdg-open", "."], "argv"
    ),
    "terminal": ApplicationTarget("Terminal", ["gnome-terminal"], "argv"),
    "firefox": ApplicationTarget("Firefox", ["firefox"], "argv"),
    "calculadora": ApplicationTarget("Calculadora", ["gnome-calculator"], "argv"),
}

APP_CACHE = {}


def normalize(value):
    """Normaliza nombres para poder comparar dictado y nombres instalados."""
    value = unicodedata.normalize("NFKD", value.lower())
    value = "".join(character for character in value if not unicodedata.combining(character))
    return PUNTUACION.sub(" ", value).strip()


def _known_target(name):
    normalized = normalize(name)
    if SO == "Windows":
        return WINDOWS_KNOWN.get(normalized)
    if SO == "Darwin":
        return MAC_KNOWN.get(normalized)
    if SO == "Linux":
        return LINUX_KNOWN.get(normalized)
    return None


def _path_target(name):
    variants = (name, name.replace(" ", ""), name.replace(" ", "-"))
    for variant in variants:
        path = shutil.which(variant)
        if path:
            return ApplicationTarget(Path(path).stem, path, "path")
    return None


def _score(query, candidate):
    query = normalize(query)
    candidate = normalize(Path(candidate).stem)
    if not query or not candidate:
        return 0
    if query == candidate:
        return 100

    compact_query = query.replace(" ", "")
    compact_candidate = candidate.replace(" ", "")
    if compact_query == compact_candidate:
        return 99

    query_words = set(query.split())
    candidate_words = set(candidate.split())
    if query_words and query_words.issubset(candidate_words):
        return 94
    if candidate_words and candidate_words.issubset(query_words):
        return 91
    if query in candidate or candidate in query:
        return 88

    return round(difflib.SequenceMatcher(None, query, candidate).ratio() * 85)


def _best_target(query, targets, minimum_score=72):
    unique = {}
    for target in targets:
        key = (target.kind, str(target.value))
        unique[key] = target

    scored = [(_score(query, target.name), target) for target in unique.values()]
    scored = [item for item in scored if item[0] >= minimum_score]
    if not scored:
        return None
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1]


def _windows_start_menu_targets():
    targets = []
    roots = [
        Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
        Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
    ]
    for root in roots:
        if not root.is_dir():
            continue
        for extension in ("*.lnk", "*.appref-ms"):
            for path in root.rglob(extension):
                targets.append(ApplicationTarget(path.stem, str(path), "path"))
    return targets


def _windows_start_apps_targets():
    command = (
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;"
        "Get-StartApps | Select-Object Name,AppID | ConvertTo-Json -Compress"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []
        applications = json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return []

    if isinstance(applications, dict):
        applications = [applications]
    return [
        ApplicationTarget(application["Name"], application["AppID"], "app_id")
        for application in applications
        if application.get("Name") and application.get("AppID")
    ]


def _registry_values(key, names):
    values = {}
    for name in names:
        try:
            values[name], _ = _winreg.QueryValueEx(key, name)
        except OSError:
            values[name] = None
    return values


def _open_registry_key(hive, path, access):
    try:
        return _winreg.OpenKey(hive, path, 0, access)
    except OSError:
        return None


def _registry_subkeys(hive, path):
    if _winreg is None:
        return

    views = {_winreg.KEY_READ}
    for flag_name in ("KEY_WOW64_32KEY", "KEY_WOW64_64KEY"):
        flag = getattr(_winreg, flag_name, 0)
        if flag:
            views.add(_winreg.KEY_READ | flag)

    for access in views:
        root = _open_registry_key(hive, path, access)
        if root is None:
            continue
        with root:
            index = 0
            while True:
                try:
                    subkey_name = _winreg.EnumKey(root, index)
                except OSError:
                    break
                index += 1
                subkey = _open_registry_key(hive, f"{path}\\{subkey_name}", access)
                if subkey is not None:
                    with subkey:
                        yield subkey_name, subkey


def _windows_app_paths_targets():
    if _winreg is None:
        return []

    targets = []
    registry_path = r"Software\Microsoft\Windows\CurrentVersion\App Paths"
    for hive in (_winreg.HKEY_CURRENT_USER, _winreg.HKEY_LOCAL_MACHINE):
        for subkey_name, subkey in _registry_subkeys(hive, registry_path):
            try:
                executable, _ = _winreg.QueryValueEx(subkey, None)
            except OSError:
                continue
            executable = str(executable).strip().strip('"')
            if Path(executable).is_file():
                targets.append(
                    ApplicationTarget(Path(subkey_name).stem, executable, "path")
                )
    return targets


def _display_icon_path(display_icon):
    if not display_icon:
        return None
    quoted = re.match(r'^"([^"]+)"', str(display_icon).strip())
    path = quoted.group(1) if quoted else str(display_icon).split(",", 1)[0]
    path = os.path.expandvars(path.strip().strip('"'))
    return path if Path(path).suffix.lower() in EXTENSIONES_EJECUTABLES else None


def _executable_from_install_location(location, display_name):
    if not location:
        return None
    root = Path(os.path.expandvars(str(location).strip().strip('"')))
    if not root.is_dir():
        return None

    targets = []
    try:
        for path in root.glob("*.exe"):
            targets.append(ApplicationTarget(path.stem, str(path), "path"))
        for child in root.iterdir():
            if child.is_dir():
                for path in child.glob("*.exe"):
                    targets.append(ApplicationTarget(path.stem, str(path), "path"))
    except OSError:
        return None
    match = _best_target(display_name, targets, minimum_score=60)
    return match.value if match else None


def _windows_uninstall_targets():
    if _winreg is None:
        return []

    targets = []
    registry_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"
    for hive in (_winreg.HKEY_CURRENT_USER, _winreg.HKEY_LOCAL_MACHINE):
        for _, subkey in _registry_subkeys(hive, registry_path):
            values = _registry_values(subkey, ("DisplayName", "DisplayIcon", "InstallLocation"))
            display_name = values["DisplayName"]
            if not display_name:
                continue
            executable = _display_icon_path(values["DisplayIcon"])
            if not executable or not Path(executable).is_file():
                executable = _executable_from_install_location(
                    values["InstallLocation"], display_name
                )
            if executable and Path(executable).is_file():
                targets.append(ApplicationTarget(display_name, executable, "path"))
    return targets


def _windows_registered_targets():
    targets = []
    targets.extend(_windows_start_menu_targets())
    targets.extend(_windows_start_apps_targets())
    targets.extend(_windows_app_paths_targets())
    targets.extend(_windows_uninstall_targets())
    return targets


def _windows_drives():
    try:
        mask = ctypes.windll.kernel32.GetLogicalDrives()
    except (AttributeError, OSError):
        return []
    drives = []
    for index, letter in enumerate(string.ascii_uppercase):
        if not mask & (1 << index):
            continue
        root = f"{letter}:\\"
        drive_type = ctypes.windll.kernel32.GetDriveTypeW(root)
        if drive_type in (2, 3):  # Unidad extraíble o disco fijo
            drives.append(root)
    return drives


def _windows_search_roots():
    common_roots = [
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
        os.environ.get("LOCALAPPDATA"),
        os.environ.get("USERPROFILE"),
    ]
    common_roots = [root for root in common_roots if root and Path(root).is_dir()]

    system_drive = os.environ.get("SystemDrive", "C:").upper() + "\\"
    drives = _windows_drives()
    other_drives = [drive for drive in drives if drive.upper() != system_drive]
    system_drives = [drive for drive in drives if drive.upper() == system_drive]

    roots = common_roots + other_drives + system_drives
    unique_roots = []
    seen = set()
    for root in roots:
        normalized_root = os.path.normcase(os.path.abspath(root))
        if normalized_root not in seen:
            seen.add(normalized_root)
            unique_roots.append(root)
    return unique_roots


def _deep_windows_search(name):
    """Último recurso: busca un ejecutable con ese nombre en todas las unidades."""
    wanted = normalize(name)
    wanted_compact = wanted.replace(" ", "")
    ignored_directories = {
        "$recycle.bin",
        "system volume information",
        "winsxs",
        "installer",
    }

    for search_root in _windows_search_roots():
        for root, directories, files in os.walk(search_root, onerror=lambda _: None):
            directories[:] = [
                directory
                for directory in directories
                if directory.lower() not in ignored_directories
            ]
            for filename in files:
                path = Path(root) / filename
                if path.suffix.lower() not in EXTENSIONES_EJECUTABLES:
                    continue
                stem = normalize(path.stem)
                if stem == wanted or stem.replace(" ", "") == wanted_compact:
                    return ApplicationTarget(path.stem, str(path), "path")
    return None


def _mac_targets():
    targets = []
    roots = (Path("/Applications"), Path("/System/Applications"), Path.home() / "Applications")
    for root in roots:
        if not root.is_dir():
            continue
        try:
            for path in root.rglob("*.app"):
                targets.append(ApplicationTarget(path.stem, str(path), "mac_app"))
        except OSError:
            continue
    return targets


def _parse_desktop_file(path):
    name = None
    spanish_name = None
    command = None
    try:
        with path.open(encoding="utf-8", errors="replace") as desktop_file:
            for line in desktop_file:
                if line.startswith("Name[es]="):
                    spanish_name = line.split("=", 1)[1].strip()
                elif line.startswith("Name=") and name is None:
                    name = line.split("=", 1)[1].strip()
                elif line.startswith("Exec=") and command is None:
                    command = line.split("=", 1)[1].strip()
    except OSError:
        return None

    display_name = spanish_name or name
    if not display_name:
        return None
    if shutil.which("gtk-launch"):
        return ApplicationTarget(display_name, path.stem, "desktop")
    if command:
        clean_command = re.sub(r"\s+%[a-zA-Z]", "", command)
        return ApplicationTarget(display_name, shlex.split(clean_command), "argv")
    return None


def _linux_targets():
    roots = (
        Path("/usr/share/applications"),
        Path("/usr/local/share/applications"),
        Path.home() / ".local/share/applications",
        Path.home() / ".local/share/flatpak/exports/share/applications",
        Path("/var/lib/flatpak/exports/share/applications"),
        Path("/var/lib/snapd/desktop/applications"),
    )
    targets = []
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.glob("*.desktop"):
            target = _parse_desktop_file(path)
            if target:
                targets.append(target)
    return targets


def find_application(name, on_deep_search=None):
    """Localiza la aplicación por nombre registrado, PATH o búsqueda profunda."""
    cache_key = (SO, normalize(name))
    if cache_key in APP_CACHE:
        return APP_CACHE[cache_key]

    target = _known_target(name) or _path_target(name)
    if target:
        APP_CACHE[cache_key] = target
        return target

    if SO == "Windows":
        target = _best_target(name, _windows_registered_targets())
        if target is None:
            if on_deep_search:
                on_deep_search()
            target = _deep_windows_search(name)
    elif SO == "Darwin":
        target = _best_target(name, _mac_targets())
    elif SO == "Linux":
        target = _best_target(name, _linux_targets())
    else:
        target = None

    if target:
        APP_CACHE[cache_key] = target
    return target


def launch_application(target):
    """Inicia una aplicación previamente localizada."""
    common_options = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if target.kind == "shell":
        subprocess.Popen(target.value, shell=True, **common_options)
    elif target.kind == "path" and SO == "Windows":
        os.startfile(target.value)
    elif target.kind == "app_id":
        subprocess.Popen(
            ["explorer.exe", f"shell:AppsFolder\\{target.value}"], **common_options
        )
    elif target.kind == "mac_app":
        subprocess.Popen(["open", target.value], **common_options)
    elif target.kind == "desktop":
        subprocess.Popen(["gtk-launch", target.value], **common_options)
    elif target.kind == "path":
        subprocess.Popen([target.value], **common_options)
    else:
        subprocess.Popen(target.value, **common_options)


try:
    import winreg as _winreg
except ImportError:
    _winreg = None
