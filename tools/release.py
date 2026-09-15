#!/usr/bin/env python3
"""Механическая часть регламента обновления — всё, кроме перевода строк.

Команды (запускать из любого места, скрипт сам находит корень репозитория):

  precheck   выход 0, если установленная Orca новее ORCA_VERSION, иначе 1.
             Дешёвая проверка для планировщика: пока версии совпадают,
             агент не запускается вовсе.
  check      extract.py + build.py; печатает отчёт приёмки и непокрытые
             строки с ключами. Запоминает состояние до перевода.
  build      build.py + приёмка. Выход 0 только при чистом отчёте.
  publish    документы, CHANGELOG, коммит, тег, push, релиз GitHub,
             индекс маркетплейса, заявка PR #6. Только при чистой приёмке
             и совпадении версии на диске с ORCA_VERSION.
             --theme "…"   тема для заголовка релиза (обязательна при изменениях)
             --agent NAME  кто подписывает коммит (по умолчанию Claude)
             --dry-run     показать, что изменилось бы, ничего не трогая
             --pretend-version X.Y.Z  только с --dry-run: прогон под чужой номер

Что нужно от агента между check и publish: новый tools/dict/stageN.json
с переводами, формы числа в plurals.json для новых ключей с count и файл
tools/CHANGELOG_ENTRY.md — от трёх до шести пунктов «- **тема** — …» в стиле
CHANGELOG.md. Если check сказал «перевод не нужен», ни того ни другого
не требуется: скрипт сам напишет запись про версионный релиз.

Индекс маркетплейса (репозиторий imgusev/orca-plugins) ожидается в соседней
папке рядом с этим чекаутом; другой путь — через переменную ORCA_PLUGINS_INDEX.

Приёмка (любое отклонение — отказ публиковать): нет в словарях 0,
плейсхолдеры 0, суффиксы 0 осталось, защищено 180, сверх лимита 2,
разрешённых путей 34, формы числа заданы для всех новых кандидатов.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import glob
import json
import os
import plistlib
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# индекс маркетплейса: соседний чекаут imgusev/orca-plugins, либо путь из ORCA_PLUGINS_INDEX
MARKETPLACE = os.environ.get("ORCA_PLUGINS_INDEX") or os.path.join(os.path.dirname(ROOT), "orca-plugins")
OFFICIAL_FORK = "imgusev/orca-plugins-official"
OFFICIAL_BRANCH = "add-russian-language-pack"
OFFICIAL_PR = ("stablyai/orca-plugins", 6)
PLIST = "/Applications/Orca.app/Contents/Info.plist"
STATE = os.path.join(HERE, "release-state.json")
ENTRY = os.path.join(HERE, "CHANGELOG_ENTRY.md")

EXPECT = {"protected": 180, "oversized": 2, "allowed_paths": 34}
ESC = re.compile(r"\\x([0-9a-fA-F]{2})|\\u([0-9a-fA-F]{4})")
PLURAL_ONLY = re.compile(r"_(few|many)$")
# файлы, которые вправе быть изменёнными к моменту publish
ALLOWED_DIRTY = re.compile(
    r"^(ORCA_VERSION|locales/ru\.json|tools/(dict/.*|plural-candidates\.txt|allowed-chrome\.txt|"
    r"extract\.py|release\.py|AUTOMATION\.md)|README\.md|README\.en\.md|UNTRANSLATED\.md|"
    r"CHANGELOG\.md|orca-plugin\.json|\.gitignore)$"
)


def sh(*cmd: str, cwd: str = ROOT, check: bool = True, quiet: bool = False) -> str:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise SystemExit(f"команда не удалась: {' '.join(cmd)}\n{result.stderr.strip()}")
    if not quiet and result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)
    return result.stdout


def installed_version() -> str:
    with open(PLIST, "rb") as f:
        return plistlib.load(f)["CFBundleShortVersionString"]


def built_version() -> str:
    return open(os.path.join(ROOT, "ORCA_VERSION")).read().strip()


def dec(value: str) -> str:
    return ESC.sub(lambda m: chr(int(m.group(1) or m.group(2), 16)), value.replace("\\'", "'"))


def flat(node: dict, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in node.items():
        full = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            out.update(flat(value, full))
        else:
            out[full] = value
    return out


def fmt(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def plural(n: int, one: str, few: str, many: str) -> str:
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def num_word(n: int) -> str:
    words = {0: "ни одного", 1: "один", 2: "два", 3: "три", 4: "четыре", 5: "пять",
             6: "шесть", 7: "семь", 8: "восемь", 9: "девять", 10: "десять"}
    return words.get(n, str(n))


# --- отчёт сборки -----------------------------------------------------------

REPORT_RE = {
    "total": r"всего строк в Orca:\s+(\d+)",
    "translated": r"переведено:\s+(\d+)",
    "protected": r"защищено Orca:\s+(\d+)",
    "overridden": r"переопределено:\s+(\d+)",
    "oversized": r"сверх лимита 8192:\s+(\d+)",
    "missing": r"нет в словарях:\s+(\d+)",
    "placeholders": r"плейсхолдеры:\s+(\d+)",
    "suffix_left": r"суффиксы мн\. числа:\s+\d+ отброшено · (\d+) осталось",
    "plural_entries": r"формы числа:\s+(\d+) записей",
    "plural_keys": r"формы числа:\s+\d+ записей для (\d+) ключей",
    "plural_pending": r"кандидатов без форм: (\d+)",
}


def run_build() -> tuple[dict[str, int], str]:
    out = subprocess.run([sys.executable, os.path.join(HERE, "build.py")], capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"build.py упал:\n{out.stdout[-2000:]}\n{out.stderr[-2000:]}")
    report = {}
    for name, pattern in REPORT_RE.items():
        m = re.search(pattern, out.stdout)
        if not m:
            raise SystemExit(f"в отчёте build.py нет строки «{name}» — формат изменился")
        report[name] = int(m.group(1))
    return report, out.stdout


def run_extract() -> dict[str, int]:
    out = subprocess.run([sys.executable, os.path.join(HERE, "extract.py")], capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"extract.py упал:\n{out.stdout[-2000:]}\n{out.stderr[-2000:]}")
    m_paths = re.search(r"разрешено (\d+) путей", out.stdout)
    m_count = re.search(r"формы числа:\s+(\d+) ключей принимают count", out.stdout)
    m_asar = re.search(r"добавлено из app\.asar:\s+(\d+)", out.stdout)
    if not (m_paths and m_count and m_asar):
        raise SystemExit(f"не разобрал вывод extract.py:\n{out.stdout}")
    print(out.stdout.strip())
    return {"allowed_paths": int(m_paths.group(1)), "count_keys": int(m_count.group(1)),
            "asar_extra": int(m_asar.group(1))}


def acceptance(report: dict[str, int], extract: dict[str, int] | None) -> list[str]:
    problems = []
    if report["missing"]:
        problems.append(f"нет в словарях: {report['missing']} (нужно 0)")
    if report["placeholders"]:
        problems.append(f"плейсхолдеры: {report['placeholders']} расхождений (нужно 0)")
    if report["suffix_left"]:
        problems.append(f"суффиксы мн. числа: {report['suffix_left']} осталось (нужно 0)")
    if report["protected"] != EXPECT["protected"]:
        problems.append(f"защищено Orca: {report['protected']} (ожидалось {EXPECT['protected']}) — защищённая зона поехала")
    if report["oversized"] != EXPECT["oversized"]:
        problems.append(f"сверх лимита: {report['oversized']} (ожидалось {EXPECT['oversized']}) — новое длинное значение")
    if extract and extract["allowed_paths"] != EXPECT["allowed_paths"]:
        problems.append(f"разрешённых путей: {extract['allowed_paths']} (ожидалось {EXPECT['allowed_paths']})")
    if extract and extract["count_keys"] == 0:
        problems.append("extract.py не видит ни одного ключа с count — регулярка перестала понимать бандл")
    state = load_state()
    if state and report["plural_pending"] > state.get("plural_pending_before", report["plural_pending"]):
        problems.append(f"кандидатов без форм числа стало больше: {report['plural_pending']} — новые счётчики без plurals.json")
    return problems


# --- состояние между check и publish -----------------------------------------

def load_state() -> dict:
    try:
        return json.load(open(STATE))
    except (OSError, ValueError):
        return {}


def save_state(data: dict) -> None:
    json.dump(data, open(STATE, "w"), ensure_ascii=False, indent=1)


def head_ru() -> dict[str, str]:
    raw = sh("git", "show", "HEAD:locales/ru.json", quiet=True)
    return flat(json.loads(raw))


def current_ru() -> dict[str, str]:
    return flat(json.load(open(os.path.join(ROOT, "locales", "ru.json"))))


def missing_with_keys() -> dict[str, list[str]]:
    src = json.load(open(os.path.join(HERE, "en-all.json")))
    ru: dict[str, str] = {}
    for path in sorted(glob.glob(os.path.join(HERE, "dict", "*.json"))):
        if os.path.basename(path) not in ("by-key.json",):
            ru.update(json.load(open(path)))
    by_key = json.load(open(os.path.join(HERE, "dict", "by-key.json")))
    out: dict[str, list[str]] = {}
    for key, raw in src.items():
        en = dec(raw)
        if len(en) <= 8192 and key not in by_key and en not in ru:
            out.setdefault(en, []).append(key)
    return out


def identity_count() -> int:
    src = json.load(open(os.path.join(HERE, "en-all.json")))
    ru: dict[str, str] = {}
    for path in sorted(glob.glob(os.path.join(HERE, "dict", "*.json"))):
        if os.path.basename(path) != "by-key.json":
            ru.update(json.load(open(path)))
    by_key = json.load(open(os.path.join(HERE, "dict", "by-key.json")))
    return sum(1 for k, v in src.items() if k not in by_key and ru.get(dec(v)) == dec(v))


def pending_plural_candidates() -> list[str]:
    """Новые ключи с count (их не было в plural-candidates.txt на HEAD), для которых
    в plurals.json ещё нет форм. Старые кандидаты без форм — те, где склонять нечего,
    они уже осознанно пропущены."""
    try:
        candidates = open(os.path.join(HERE, "plural-candidates.txt")).read().split()
    except FileNotFoundError:
        return []
    known = set(sh("git", "show", "HEAD:tools/plural-candidates.txt", check=False, quiet=True).split())
    plurals = json.load(open(os.path.join(HERE, "dict", "plurals.json")))
    return [k for k in candidates if k not in plurals and k not in known]


# --- команды -----------------------------------------------------------------

def cmd_precheck(_: argparse.Namespace) -> int:
    inst, built = installed_version(), built_version()
    if inst == built:
        print(f"Orca {inst} уже переведена — запуск не нужен")
        return 1
    print(f"нужно обновление: {built} → {inst}")
    return 0


def cmd_check(_: argparse.Namespace) -> int:
    inst, built = installed_version(), built_version()
    print(f"на диске Orca {inst}, каталог собран под {built}")
    old = head_ru()
    extract = run_extract()
    report, text = run_build()
    print(text[text.index("версия Orca:"):].rstrip())
    pre = current_ru()
    removed_or_rewritten = sorted(k for k in old if k not in pre)
    pending = pending_plural_candidates()
    save_state({
        "version": inst, "previous": built, "extract": extract,
        "removed_or_rewritten": removed_or_rewritten,
        # кандидатов без форм допустимо ровно столько, сколько было до новых ключей
        "plural_pending_before": report["plural_pending"] - len(pending),
        "pending_plural_candidates": pending,
        "checked_at": dt.datetime.now().isoformat(timespec="seconds"),
    })
    print()
    if removed_or_rewritten:
        print(f"ключи, у которых текст сменился или которые убраны ({len(removed_or_rewritten)}):")
        src = json.load(open(os.path.join(HERE, "en-all.json")))
        for k in removed_or_rewritten:
            now = dec(src[k]) if k in src else "— убран —"
            print(f"  {k}\n     было: {old[k]}\n     стало: {now}")
    if pending:
        print(f"\nновые ключи с count без форм числа ({len(pending)}) — добавить в dict/plurals.json:")
        for k in pending:
            print(f"  {k}")
    missing = missing_with_keys()
    if not missing:
        print("\nперевод не нужен — можно сразу publish")
        return 0
    print(f"\nНУЖЕН ПЕРЕВОД: {len(missing)} строк → новый файл dict/stage{next_stage()}.json")
    for en, keys in missing.items():
        print(f"  {en!r}\n     {', '.join(keys)}")
    return 0


def next_stage() -> int:
    nums = [int(m.group(1)) for p in glob.glob(os.path.join(HERE, "dict", "stage*.json"))
            if (m := re.match(r"stage(\d+)", os.path.basename(p)))]
    return max(nums, default=0) + 1


def cmd_build(_: argparse.Namespace) -> int:
    report, text = run_build()
    print(text[text.index("версия Orca:"):].rstrip())
    state = load_state()
    problems = acceptance(report, state.get("extract"))
    missing = missing_with_keys()
    if missing:
        print(f"\nНЕ ХВАТАЕТ ПЕРЕВОДА ({len(missing)}):")
        for en, keys in missing.items():
            print(f"  {en!r}\n     {', '.join(keys)}")
    if problems:
        print("\nПРИЁМКА НЕ ПРОЙДЕНА:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nприёмка пройдена")
    return 0


def replace_all(path: str, pairs: list[tuple[str, str]], dry: bool) -> None:
    text = open(path).read()
    new = text
    for old, repl in pairs:
        new = new.replace(old, repl)
    if new != text and not dry:
        open(path, "w").write(new)
    if dry and new != text:
        print(f"  [dry-run] {os.path.relpath(path, ROOT)}: изменился бы")


def cmd_publish(args: argparse.Namespace) -> int:
    dry = args.dry_run
    inst = args.pretend_version if (dry and args.pretend_version) else installed_version()
    built = built_version()
    if not dry and inst != built:
        print(f"на диске Orca {inst}, а ORCA_VERSION говорит {built} — приложение обновилось посреди работы, "
              f"вернитесь к check", file=sys.stderr)
        return 1
    version = inst
    previous = sh("git", "show", "HEAD:ORCA_VERSION", quiet=True).strip()
    if version == previous and not dry:
        print(f"HEAD уже собран под {version} — публиковать нечего", file=sys.stderr)
        return 1

    dirty = [line[3:] for line in sh("git", "status", "--porcelain", quiet=True).splitlines()]
    stray = [f for f in dirty if not ALLOWED_DIRTY.match(f)]
    if stray:
        print("в рабочем дереве посторонние изменения, публиковать поверх них нельзя:\n  " + "\n  ".join(stray),
              file=sys.stderr)
        return 1

    report, _ = run_build()
    state = load_state()
    problems = acceptance(report, state.get("extract"))
    if problems:
        print("ПРИЁМКА НЕ ПРОЙДЕНА:\n  - " + "\n  - ".join(problems), file=sys.stderr)
        return 1

    old = head_ru()
    final = current_ru()
    removed_or_rewritten = set(state.get("removed_or_rewritten", [k for k in old if k not in final]))
    rewritten = sorted(k for k in removed_or_rewritten if k in final)
    removed = sorted(k for k in removed_or_rewritten if k not in final)
    added = sorted(k for k in final if k not in old and not PLURAL_ONLY.search(k))
    no_changes = not (added or removed or rewritten)

    translated, total = report["translated"], report["total"]
    pct = translated * 100 // total
    identity = identity_count()
    old_docs = read_old_numbers()

    entry_body = ""
    if os.path.exists(ENTRY):
        entry_body = open(ENTRY).read().strip()
    if not no_changes and not entry_body:
        print("нет tools/CHANGELOG_ENTRY.md — опишите, что появилось в этой версии", file=sys.stderr)
        return 1
    if not no_changes and not args.theme:
        print("нужна --theme для заголовка релиза", file=sys.stderr)
        return 1
    theme = args.theme or "версионный релиз без изменений перевода"

    today = dt.date.today().isoformat()
    if no_changes:
        summary = (f"Каталог — {fmt(translated)} из {fmt(total)} строк ({pct}%), без изменений относительно "
                   f"{previous}: приложение не добавило, не убрало и не переписало ни одной строки. "
                   f"Выпуск нужен только для совпадения номера пакета с версией приложения.")
        bullets = ""
    else:
        summary = (f"Каталог — {fmt(translated)} из {fmt(total)} строк ({pct}%). Приложение добавило "
                   f"{len(added)} {plural(len(added), 'ключ', 'ключа', 'ключей')}, "
                   f"убрало {num_word(len(removed))} и переписало текст у {num_word(len(rewritten))}"
                   f"{'' if len(rewritten) != 1 else ' ключа'} — переведены все.")
        bullets = entry_body + "\n"
    protected_line = f"- Защищённая зона не изменилась: те же {EXPECT['protected']} ключей и {EXPECT['allowed_paths']} разрешённых пути"
    entry = (f"## {version} — {today} · Orca {version} (совместим с {compat()}+)\n\n"
             + wrap(summary) + "\n\n" + (bullets + protected_line + "\n\n" if not no_changes else ""))
    notes = release_notes(version, summary, entry_body, no_changes)

    print(f"версия {previous} → {version}; переведено {old_docs['translated']} → {fmt(translated)}, "
          f"всего {old_docs['total']} → {fmt(total)}, тождественных {old_docs['identity']} → {identity}")
    print(f"ключей: добавлено {len(added)}, убрано {len(removed)}, переписано {len(rewritten)}")

    # документы
    pairs = [(previous, version), (old_docs["translated"], fmt(translated)), (old_docs["total"], fmt(total))]
    for name in ("README.md", "README.en.md", "UNTRANSLATED.md", "orca-plugin.json"):
        extra = []
        if name in ("README.md", "UNTRANSLATED.md"):
            extra = [(f"{old_docs['identity']} строк", f"{identity} строк"),
                     (f"{old_docs['identity']} оставлены", f"{identity} оставлены")]
        replace_all(os.path.join(ROOT, name), pairs + extra, dry)
    # «каталог под NEW спокойно работает на PREV» — после общей замены там стоит позапрошлая версия
    readme = os.path.join(ROOT, "README.md")
    text = open(readme).read()
    fixed = re.sub(r"(каталог под " + re.escape(version) + r" спокойно работает на )\d+\.\d+\.\d+",
                   r"\g<1>" + previous, text)
    if fixed != text and not dry:
        open(readme, "w").write(fixed)
    replace_all(os.path.join(HERE, "extract.py"),
                [(f"{old_docs['catalog']} ключей для {previous}", f"{fmt(report['total'] - state.get('extract', {}).get('asar_extra', 0))} ключей для {version}")], dry)
    changelog = os.path.join(ROOT, "CHANGELOG.md")
    text = open(changelog).read()
    text = text.replace(f"Orca {previous} выходит как {previous}", f"Orca {version} выходит как {version}", 1)
    marker = f"## {previous} — "
    if marker not in text:
        print(f"в CHANGELOG.md нет записи {previous}", file=sys.stderr)
        return 1
    text = text.replace(marker, entry + marker, 1)
    if dry:
        print("\n[dry-run] запись CHANGELOG:\n" + entry)
        print("[dry-run] описание релиза:\n" + notes)
        print("[dry-run] ничего не записано, git не тронут")
        return 0
    open(changelog, "w").write(text)

    # git: коммит, тег, push, релиз
    commit_msg = (f"Перевод под Orca {version}\n\n" + wrap(summary.replace(" — переведены все.", " — переведены все новые."))
                  + ("\n\n" + wrap(bullets_to_prose(entry_body)) if entry_body else "")
                  + f"\n\nAuthor: @IMGusev with {args.agent}\n")
    if installed_version() != version:
        print("Orca обновилась, пока шла подготовка — коммит не сделан, вернитесь к check", file=sys.stderr)
        return 1
    sh("git", "add", "-A")
    subprocess.run(["git", "commit", "-q", "-F", "-"], cwd=ROOT, input=commit_msg, text=True, check=True)
    sh("git", "tag", "-a", f"v{version}", "-m", f"Русский язык для Orca {version}")
    sh("git", "push", "origin", "main", "--follow-tags")
    if f"refs/tags/v{version}" not in sh("git", "ls-remote", "--tags", "origin", f"v{version}", quiet=True):
        print("тег не появился на origin — индекс маркетплейса не трогаю", file=sys.stderr)
        return 1
    notes_path = os.path.join(HERE, ".release-notes.md")
    open(notes_path, "w").write(notes)
    url = sh("gh", "release", "create", f"v{version}", "--title", f"v{version} — Orca {version} · {theme}",
             "--notes-file", notes_path).strip()
    os.remove(notes_path)
    print(f"релиз: {url}")

    # индекс маркетплейса
    sh("git", "pull", "-q", "--rebase", "origin", "main", cwd=MARKETPLACE)
    replace_all(os.path.join(MARKETPLACE, "orca-marketplace.json"), [(f'"ref": "v{previous}"', f'"ref": "v{version}"')], False)
    replace_all(os.path.join(MARKETPLACE, "README.md"),
                [(f"{old_docs['translated']} из {old_docs['total']}", f"{fmt(translated)} из {fmt(total)}")], False)
    subprocess.run(["git", "commit", "-q", "-a", "-F", "-"], cwd=MARKETPLACE, text=True, check=True,
                   input=f"Русский язык для Orca {version}\n\nAuthor: @IMGusev with {args.agent}\n")
    sh("git", "push", "origin", "main", cwd=MARKETPLACE)
    print("индекс маркетплейса переключён на v" + version)

    # заявка в официальный маркетплейс
    update_official_pr(previous, version, old_docs, fmt(translated), fmt(total), pct, args.agent)
    for path in (ENTRY, STATE):
        if os.path.exists(path):
            os.remove(path)
    print("готово")
    return 0


def read_old_numbers() -> dict[str, str]:
    readme = open(os.path.join(ROOT, "README.md")).read()
    m = re.search(r"\*\*(\d[\d ]*) из (\d[\d ]*) строк \((\d+)%\)\*\*", readme)
    ident = re.search(r"(\d+) оставлены в оригинале намеренно", readme)
    cat = re.search(r"Полный каталог релиза — (\d[\d ]*) ключей для", open(os.path.join(HERE, "extract.py")).read())
    if not (m and ident and cat):
        raise SystemExit("не нашёл старые числа в README.md / extract.py — формат изменился")
    return {"translated": m.group(1), "total": m.group(2), "identity": ident.group(1), "catalog": cat.group(1)}


def compat() -> str:
    return open(os.path.join(ROOT, "COMPAT")).read().strip()


def wrap(text: str, width: int = 74) -> str:
    import textwrap
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False))


def bullets_to_prose(entry: str) -> str:
    items = []
    for block in re.split(r"\n(?=- )", entry.strip()):
        line = " ".join(block.strip().lstrip("- ").split())
        line = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        items.append(line)
    return "Новое: " + "; ".join(items) + "." if items else ""


def release_notes(version: str, summary: str, entry_body: str, no_changes: bool) -> str:
    head = summary.replace("Каталог — ", f"Каталог собран под **Orca {version}**: ", 1)
    parts = [head, ""]
    if not no_changes:
        joined = re.sub(r"\n(?!- )", " ", entry_body.strip())
        parts += ["## Что нового", "", joined, ""]
    parts.append(f"Защищённая зона не изменилась: те же {EXPECT['protected']} ключей и {EXPECT['allowed_paths']} "
                 f"разрешённых пути. Нижняя граница совместимости — **{compat()}**.")
    return "\n".join(parts) + "\n"


def update_official_pr(previous: str, version: str, old: dict[str, str], tr: str, total: str, pct: int, agent: str) -> None:
    repo, number = OFFICIAL_PR
    state = sh("gh", "pr", "view", str(number), "-R", repo, "--json", "state", "-q", ".state", quiet=True).strip()
    if state != "OPEN":
        print(f"PR #{number} в {repo}: {state} — не трогаю")
        return
    meta = json.loads(sh("gh", "api", f"repos/{OFFICIAL_FORK}/contents/orca-marketplace.json?ref={OFFICIAL_BRANCH}", quiet=True))
    content = base64.b64decode(meta["content"]).decode()
    new = content.replace(f'"ref": "v{previous}"', f'"ref": "v{version}"')
    if new == content:
        print(f"PR #{number}: ref v{previous} в ветке не найден — оставляю как есть")
    else:
        sh("gh", "api", "-X", "PUT", f"repos/{OFFICIAL_FORK}/contents/orca-marketplace.json",
           "-f", f"message=chore: bump russian-language-pack to v{version}\n\nAuthor: @IMGusev with {agent}",
           "-f", f"branch={OFFICIAL_BRANCH}", "-f", f"sha={meta['sha']}",
           "-f", "content=" + base64.b64encode(new.encode()).decode(), quiet=True)
    body = sh("gh", "pr", "view", str(number), "-R", repo, "--json", "body", "-q", ".body", quiet=True)
    body2 = (body.replace(f"pinned to `v{previous}`", f"pinned to `v{version}`")
             .replace(f"{old['translated']} of {old['total']} strings", f"{tr} of {total} strings")
             .replace(f"of the {previous} catalog", f"of the {version} catalog")
             .replace(f"so `{previous}` is the pack for {previous}", f"so `{version}` is the pack for {version}"))
    body2 = re.sub(r"strings \(\d+%\)", f"strings ({pct}%)", body2, count=1)
    if body2 != body:
        subprocess.run(["gh", "pr", "edit", str(number), "-R", repo, "--body-file", "-"], input=body2, text=True, check=True)
    print(f"PR #{number} в {repo} обновлён до v{version}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("precheck").set_defaults(fn=cmd_precheck)
    sub.add_parser("check").set_defaults(fn=cmd_check)
    sub.add_parser("build").set_defaults(fn=cmd_build)
    pub = sub.add_parser("publish")
    pub.add_argument("--theme", default="")
    pub.add_argument("--agent", default="Claude")
    pub.add_argument("--dry-run", action="store_true")
    pub.add_argument("--pretend-version", default="")
    pub.set_defaults(fn=cmd_publish)
    args = parser.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
