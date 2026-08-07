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
# Плейсхолдер, приклеенный к концу слова — английский суффикс множественного числа:
# "{{value0}} label{{value1}}" подставляет "s". В русском число выражается иначе,
# поэтому в переводе такой плейсхолдер опускается, и это не расхождение, а норма.
# Две буквы в lookbehind отсекают "Orca v{{value0}}" и ":L{{value0}}", где перед
# плейсхолдером стоит одиночная буква версии или номера строки, а не окончание слова.
PLURAL_SUFFIX_RE = re.compile(r"(?<=[A-Za-z]{2})(\{\{[^}]+\}\})(?![A-Za-z0-9_])")

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

    # переопределения по ключу: одно и то же английское слово в разных местах
    # значит разное — "Cursor" в каталоге агентов это редактор, а не курсор
    by_key_path = os.path.join(HERE, "dict", "by-key.json")
    by_key = {k: v for k, v in json.load(open(by_key_path)).items() if not k.startswith("_")}

    ru: dict[str, str] = {}
    print("словари:")
    for path in sorted(glob.glob(os.path.join(HERE, "dict", "*.json"))):
        if os.path.basename(path) == "by-key.json":
            continue
        entries = json.load(open(path))
        ru.update(entries)
        print(f"  {os.path.basename(path):20} {len(entries):5}")
    print(f"  {'by-key.json':20} {len(by_key):5} (переопределения по ключу)")

    translated, skipped, missing, overridden = {}, [], [], 0
    for key, raw in source.items():
        english = decode_js(raw)
        if key in by_key:
            # null означает «оставить английским»: i18next возьмёт defaultValue
            overridden += 1
            if by_key[key] is not None:
                translated[key] = by_key[key]
            continue
        if english not in ru:
            missing.append(english)
        elif protected(key):
            skipped.append(key)
        else:
            translated[key] = ru[english]

    # плейсхолдеры обязаны совпадать, иначе интерфейс покажет пустоту вместо значения —
    # кроме суффиксов множественного числа, которые в русском переводе положено выбрасывать
    broken, dropped_suffix = [], []
    for key, value in translated.items():
        english = decode_js(source[key])
        want = sorted(PLACEHOLDER_RE.findall(english))
        got = sorted(PLACEHOLDER_RE.findall(value))
        if want == got:
            continue
        suffixes = set(PLURAL_SUFFIX_RE.findall(english))
        if suffixes and sorted(p for p in want if p not in suffixes) == got:
            dropped_suffix.append(key)
        else:
            broken.append(key)

    # суффикс, оставленный в переводе, рисует в интерфейсе «меток: 3s»
    kept_suffix = [
        key for key, value in translated.items()
        if set(PLURAL_SUFFIX_RE.findall(decode_js(source[key]))) & set(PLACEHOLDER_RE.findall(value))
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
    print(f"переопределено:       {overridden} по ключу (контекст важнее словаря)")
    print(f"нет в словарях:       {len(set(missing))}")
    print(f"плейсхолдеры:         {len(broken)} расхождений")
    print(f"суффиксы мн. числа:   {len(dropped_suffix)} отброшено · {len(kept_suffix)} осталось (должно быть 0)")
    print(f"вложенность:          {depth(catalog)}/16 · записей {len(translated)}/20000")
    print(f"\nзаписано: {out}")

    if kept_suffix:
        print(f"\nАНГЛИЙСКИЙ СУФФИКС ОСТАЛСЯ В ПЕРЕВОДЕ ({len(kept_suffix)}) — в интерфейсе выйдет «меток: 3s»:")
        for key in kept_suffix[:20]:
            print(f"  en: {decode_js(source[key])!r}\n  ru: {translated[key]!r}")

    if broken:
        print("\nРАСХОЖДЕНИЯ ПО ПЛЕЙСХОЛДЕРАМ (перевод потеряет значение):")
        for key in broken[:20]:
            print(f"  {key}\n    en: {decode_js(source[key])!r}\n    ru: {translated[key]!r}")

    if missing:
        print(f"\nНЕ ХВАТАЕТ ПЕРЕВОДА ({len(set(missing))}) — добавьте в новый dict/*.json:")
        for text in sorted(set(missing))[:40]:
            print(f"  {text!r}")


main()
