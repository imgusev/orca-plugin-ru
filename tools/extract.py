#!/usr/bin/env python3
"""Собирает карту «ключ i18next → английский текст» для установленной Orca.

Источников два, и порядок важен:

1. `src/renderer/src/i18n/locales/en.json` из репозитория Orca — берётся
   по тегу той версии, что стоит локально (`ORCA_VERSION`), а не из `main`.
   Ключ, добавленный в `main`, но не попавший в релиз, ломает языковой пакет
   у всех пользователей: валидатор релиза его не знает и отвергает каталог
   целиком. Полный каталог релиза — 13 592 ключа для 1.4.191.

2. Разбор `app.asar` — добавляет ключи, которых в `en.json` нет: строки
   поиска по настройкам объявляются в коде и в каталог не попадают.

Раньше единственным источником был asar, и регулярка находила лишь строки
с префиксом `auto.` — мимо проходило ~1850 ключей. Отсюда правило: asar
только дополняет, каталог релиза главнее.

Результат: en-all.json рядом со скриптом (в .gitignore — файл производный)
и ORCA_VERSION в корне репозитория. Заодно пересобирается allowed-chrome.txt —
белый список защищённой зоны, общий для всего диапазона поддерживаемых версий
(нижняя граница — файл COMPAT).
"""
import base64
import json
import os
import plistlib
import re
import subprocess
import sys

DEFAULT_ASAR = "/Applications/Orca.app/Contents/Resources/app.asar"
CATALOG_PATH = "src/renderer/src/i18n/locales/en.json"
CHROME_PATH = "src/shared/plugins/plugin-translatable-chrome.ts"
REPO = "stablyai/orca"
CHROME_RE = re.compile(r"'(auto\.components\.settings\.[A-Za-z0-9_.]+)'")
PAIR = re.compile(r'"(auto\.[A-Za-z0-9_.]{3,90})"\s*,\s*"((?:[^"\\]|\\.){1,300})"')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def orca_version(asar: str) -> str | None:
    """Версия берётся из Info.plist того же бандла — чтобы каталог и версия не разъехались."""
    plist = os.path.join(os.path.dirname(asar), os.pardir, "Info.plist")
    try:
        with open(plist, "rb") as f:
            return plistlib.load(f).get("CFBundleShortVersionString")
    except (OSError, plistlib.InvalidFileException):
        return None


def fetch_file(path: str, version: str) -> bytes:
    """Тянет файл по тегу через gh — системный python3 на macOS без корневых сертификатов."""
    ref = f"v{version}"
    try:
        raw = subprocess.run(
            ["gh", "api", f"repos/{REPO}/contents/{path}?ref={ref}", "--jq", ".content"],
            capture_output=True, text=True, check=True, timeout=120,
        ).stdout
    except FileNotFoundError:
        sys.exit("нужен gh CLI: brew install gh && gh auth login")
    except subprocess.CalledProcessError as err:
        sys.exit(f"не удалось получить {path} на теге {ref}:\n{err.stderr.strip()}")
    return base64.b64decode(raw)


def fetch_catalog(version: str) -> dict:
    return json.loads(fetch_file(CATALOG_PATH, version))


def fetch_allowed_chrome(version: str) -> set[str]:
    """Пути защищённой зоны, которые эта версия разрешает переводить."""
    return set(CHROME_RE.findall(fetch_file(CHROME_PATH, version).decode("utf-8")))


def compat_floor() -> str:
    """Минимальная версия Orca, на которой пакет обязан работать (файл COMPAT)."""
    with open(os.path.join(ROOT, "COMPAT")) as f:
        return f.read().strip()


def flatten(node: dict, prefix: str = "") -> dict:
    """en.json вложенный, а работаем мы с плоскими ключами через точку."""
    out = {}
    for key, value in node.items():
        if isinstance(value, dict):
            out.update(flatten(value, f"{prefix}{key}."))
        else:
            out[f"{prefix}{key}"] = value
    return out


def scan_asar(asar: str) -> dict:
    """Английский текст лежит в бандле как defaultValue: translate("auto.<ключ>", "English")."""
    raw = open(asar, "rb").read().decode("utf-8", "ignore")
    pairs: dict[str, str] = {}
    for key, value in PAIR.findall(raw):
        # значение — JS-литерал: кавычки и слеши в нём экранированы
        value = value.replace('\\"', '"').replace("\\\\", "\\").replace("\\n", "\n")
        # один ключ может встретиться в нескольких бандлах (renderer/web) —
        # берём самый длинный вариант, он полнее
        if key not in pairs or len(value) > len(pairs[key]):
            pairs[key] = value
    return pairs


def main() -> None:
    asar = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ASAR
    if not os.path.exists(asar):
        sys.exit(f"не найден {asar}\nукажите путь: python3 extract.py /path/to/app.asar")

    version = orca_version(asar)
    if not version:
        sys.exit("не удалось прочитать версию из Info.plist рядом с asar")

    catalog = flatten(fetch_catalog(version))
    print(f"каталог релиза v{version}: {len(catalog)} ключей")

    # Белый список защищённой зоны берётся ПЕРЕСЕЧЕНИЕМ минимальной поддерживаемой
    # версии и установленной. Путь, разрешённый в новой Orca, но ещё защищённый в
    # старой, отклонит каталог целиком у того, кто не обновился, — а обновление
    # пакета приходит раньше обновления приложения.
    floor = compat_floor()
    allowed = fetch_allowed_chrome(floor)
    if floor != version:
        allowed &= fetch_allowed_chrome(version)
    chrome_path = os.path.join(HERE, "allowed-chrome.txt")
    open(chrome_path, "w").write("\n".join(sorted(allowed)) + "\n")
    print(f"защищённая зона:      разрешено {len(allowed)} путей "
          f"(пересечение v{floor} … v{version})")

    bundle = scan_asar(asar)
    extra = {k: v for k, v in bundle.items() if k not in catalog}
    print(f"добавлено из app.asar:    {len(extra)} (нет в каталоге релиза)")

    pairs = {**catalog, **extra}
    out = os.path.join(HERE, "en-all.json")
    json.dump(pairs, open(out, "w"), ensure_ascii=False, indent=1)
    open(os.path.join(ROOT, "ORCA_VERSION"), "w").write(version + "\n")
    print(f"\nвсего {len(pairs)} ключей → {out}")
    print(f"версия Orca: {version} → ORCA_VERSION")


main()
