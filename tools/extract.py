#!/usr/bin/env python3
"""Извлекает англоязычные строки Orca из app.asar.

Английский текст лежит в бандле вторым аргументом вызовов вида
    t("auto.<хеш-ключ>", "English text")
то есть как defaultValue i18next. Языковой пакет подменяет строки
по тем же ключам, поэтому нужна карта «ключ → английский текст».

Результат: en-all.json рядом со скриптом (в .gitignore — файл производный).
"""
import json
import os
import re
import sys

DEFAULT_ASAR = "/Applications/Orca.app/Contents/Resources/app.asar"
PAIR = re.compile(r'"(auto\.[A-Za-z0-9_.]{3,90})"\s*,\s*"((?:[^"\\]|\\.){1,300})"')


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

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "en-all.json")
    json.dump(pairs, open(out, "w"), ensure_ascii=False, indent=1)
    print(f"извлечено {len(pairs)} ключей → {out}")


main()
