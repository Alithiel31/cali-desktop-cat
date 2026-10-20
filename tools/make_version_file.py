"""Écrit le fichier de métadonnées Windows de l'exécutable (Propriétés > Détails), lu par PyInstaller :

    python tools/make_version_file.py              # -> build/version_info.txt
    pyinstaller ... --version-file build/version_info.txt main.py

Tout vient de `desktopcat.__version__` : une seule source de vérité pour le panneau, le tag et l'exe.
Le nom du produit et la version sont ainsi identiques d'un build à l'autre.
"""
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

PRODUCT = "Desktop Cat"
EXE = "DesktopCat.exe"
AUTHOR = "Jacques Duchamplecheval (alithiel31)"
OUT = os.path.join(ROOT, "build", "version_info.txt")


def version_tuple(version: str) -> tuple:
    """« 0.4.1 » -> (0, 4, 1, 0) : Windows veut exactement 4 nombres."""
    parts = [int(p) for p in version.split(".")]
    if not 1 <= len(parts) <= 4 or any(p < 0 or p > 65535 for p in parts):
        raise ValueError(f"version invalide pour Windows : {version!r}")
    return tuple(parts + [0] * (4 - len(parts)))


def version_info(version: str) -> str:
    v = version_tuple(version)
    strings = {
        "CompanyName": AUTHOR,
        "FileDescription": PRODUCT,
        "FileVersion": version,
        "InternalName": "DesktopCat",
        "LegalCopyright": f"MIT License - {AUTHOR}",
        "OriginalFilename": EXE,
        "ProductName": PRODUCT,
        "ProductVersion": version,
    }
    table = ",\n          ".join(f"StringStruct({k!r}, {val!r})" for k, val in strings.items())
    return f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(filevers={v}, prodvers={v}, mask=0x3f, flags=0x0, OS=0x40004,
                    fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
          {table}])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def main(out: str = OUT) -> str:
    from desktopcat import __version__
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(version_info(__version__))
    print("Métadonnées écrites :", out, f"({PRODUCT} {__version__})")
    return out


if __name__ == "__main__":
    main(*sys.argv[1:])
