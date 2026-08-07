#!/usr/bin/env python3
"""Собирает locales/ru.json из словарей dict/*.json.

Словарь — плоский JSON «английский текст» → «перевод». Каталог строится
по en-all.json (карта «ключ → английский текст», см. extract.py): каждому
ключу, чей текст найден в словарях, назначается перевод. Остальное
остаётся английским — i18next делает fallback на defaultValue из кода.

Печатает, каких строк не хватает, — их и надо дописать в новый dict/*.json.
"""
import glob
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ESCAPE_RE = re.compile(r"\\x([0-9a-fA-F]{2})|\\u([0-9a-fA-F]{4})")
PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}")

# Защищённая зона Orca: языковой пакет не может подменять тексты про доверие
# к плагинам. Если такой ключ попадёт в каталог, валидатор отклонит ВЕСЬ пакет
# ("catalog cannot replace protected security copy"), и плагин упадёт с
# "The plugin stopped after an activation or worker error".
PROTECTED_ROOT = "auto.components.settings."

try:
    ALLOWED_CHROME = set(open(os.path.join(HERE, "allowed-chrome.txt")).read().split())
except FileNotFoundError:
    ALLOWED_CHROME = set()


def protected(key: str) -> bool:
    if not key.startswith(PROTECTED_ROOT) or key in ALLOWED_CHROME:
        return False
    return key[len(PROTECTED_ROOT):].lower().startswith("plugin")


def decode_js(value: str) -> str:
    """Строки лежат в бандле как JS-литералы — раскрываем \\xNN и \\uNNNN."""
    return ESCAPE_RE.sub(
        lambda m: chr(int(m.group(1) or m.group(2), 16)),
        value.replace("\\'", "'"),
    )


def nest(flat: dict) -> dict:
    """Ключ auto.components.x.y → вложенные объекты: точка в ключе запрещена валидатором."""
    root: dict = {}
    for dotted, text in flat.items():
        node = root
        parts = dotted.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = text
    return root


def depth(node: dict, level: int = 1) -> int:
    return max([depth(v, level + 1) for v in node.values() if isinstance(v, dict)] + [level])


def main() -> None:
    source_path = os.path.join(HERE, "en-all.json")
    if not os.path.exists(source_path):
        raise SystemExit("нет en-all.json — сначала запустите: python3 extract.py")
    source = json.load(open(source_path))

    ru: dict[str, str] = {}
    print("словари:")
    for path in sorted(glob.glob(os.path.join(HERE, "dict", "*.json"))):
        entries = json.load(open(path))
        ru.update(entries)
        print(f"  {os.path.basename(path):20} {len(entries):5}")

    translated, skipped, missing = {}, [], []
    for key, raw in source.items():
        english = decode_js(raw)
        if english not in ru:
            missing.append(english)
        elif protected(key):
            skipped.append(key)
        else:
            translated[key] = ru[english]

    # плейсхолдеры обязаны совпадать, иначе интерфейс покажет пустоту вместо значения
    broken = [
        key for key, value in translated.items()
        if sorted(PLACEHOLDER_RE.findall(decode_js(source[key]))) != sorted(PLACEHOLDER_RE.findall(value))
    ]

    out = os.path.join(ROOT, "locales", "ru.json")
    catalog = nest(translated)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(catalog, open(out, "w"), ensure_ascii=False, indent=1)

    try:
        version = open(os.path.join(ROOT, "ORCA_VERSION")).read().strip()
    except FileNotFoundError:
        version = "неизвестна"

    total = len(source)
    print(f"\nверсия Orca:          {version}")
    print(f"всего строк в Orca:   {total}")
    print(f"переведено:           {len(translated)} ({len(translated) * 100 // total}%)")
    print(f"защищено Orca:        {len(skipped)} (остаются английскими — это норма)")
    print(f"нет в словарях:       {len(set(missing))}")
    print(f"плейсхолдеры:         {len(broken)} расхождений")
    print(f"вложенность:          {depth(catalog)}/16 · записей {len(translated)}/20000")
    print(f"\nзаписано: {out}")

    if broken:
        print("\nРАСХОЖДЕНИЯ ПО ПЛЕЙСХОЛДЕРАМ (перевод потеряет значение):")
        for key in broken[:20]:
            print(f"  {key}\n    en: {decode_js(source[key])!r}\n    ru: {translated[key]!r}")

    if missing:
        print(f"\nНЕ ХВАТАЕТ ПЕРЕВОДА ({len(set(missing))}) — добавьте в новый dict/*.json:")
        for text in sorted(set(missing))[:40]:
            print(f"  {text!r}")


main()
