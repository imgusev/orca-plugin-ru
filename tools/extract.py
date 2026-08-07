#!/usr/bin/env python3
"""Извлекает англоязычные строки Orca из app.asar.

Английский текст лежит в бандле вторым аргументом вызовов вида
    t("auto.<хеш-ключ>", "English text")
то есть как defaultValue i18next. Языковой пакет подменяет строки
по тем же ключам, поэтому нужна карта «ключ → английский текст».

Результат: en-all.json рядом со скриптом (в .gitignore — файл производный)
и ORCA_VERSION в корне репозитория — версия сборки, из которой сняты строки.
"""
import json
import os
import plistlib
import re
import sys

DEFAULT_ASAR = "/Applications/Orca.app/Contents/Resources/app.asar"
PAIR = re.compile(r'"(auto\.[A-Za-z0-9_.]{3,90})"\s*,\s*"((?:[^"\\]|\\.){1,300})"')


def orca_version(asar: str) -> str | None:
    """Версия берётся из Info.plist того же бандла — чтобы каталог и версия не разъехались."""
    plist = os.path.join(os.path.dirname(asar), os.pardir, "Info.plist")
    try:
        with open(plist, "rb") as f:
            return plistlib.load(f).get("CFBundleShortVersionString")
    except (OSError, plistlib.InvalidFileException):
        return None


def main() -> None:
    asar = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_ASAR
    if not os.path.exists(asar):
        sys.exit(f"не найден {asar}\nукажите путь: python3 extract.py /path/to/app.asar")

    raw = open(asar, "rb").read().decode("utf-8", "ignore")
    pairs: dict[str, str] = {}
    for key, value in PAIR.findall(raw):
        # значение — JS-литерал: кавычки и слеши в нём экранированы
        value = value.replace('\\"', '"').replace("\\\\", "\\").replace("\\n", "\n")
        # один ключ может встретиться в нескольких бандлах (renderer/web) —
        # берём самый длинный вариант, он полнее
        if key not in pairs or len(value) > len(pairs[key]):
            pairs[key] = value

    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "en-all.json")
    json.dump(pairs, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"извлечено {len(pairs)} ключей → {out}")

    version = orca_version(asar)
    if version:
        open(os.path.join(here, os.pardir, "ORCA_VERSION"), "w").write(version + "\n")
        print(f"версия Orca: {version} → ORCA_VERSION")
    else:
        print("версия Orca не определена — Info.plist рядом с asar не прочитан")


main()
