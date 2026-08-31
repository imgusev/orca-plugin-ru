#!/usr/bin/env python3
"""Снимает статистику трафика репозитория и копит её в CSV.

GitHub отдаёт клоны и просмотры только за последние 14 дней и старое не хранит,
поэтому снимок нужно снимать регулярно, иначе история теряется. Скрипт сливает
свежие данные с уже накопленными: даты, которых в файле нет, добавляются,
пересекающиеся — обновляются (за сегодняшний день счётчик ещё растёт).

Клон здесь и есть установка: Orca ставит и обновляет плагин через git clone.
Отличить установку от обновления нельзя — оба выглядят одинаково.

Запуск: python3 tools/traffic.py [owner/repo] [путь к csv] — нужен gh с авторизацией.
"""
import csv
import json
import os
import subprocess
import sys

COLUMNS = ("date", "clones", "clone_uniques", "views", "view_uniques")


def fetch(repo: str, kind: str) -> dict:
    """kind — clones или views. Требует прав на push в репозиторий.

    Запрос идёт через gh, а не через urllib: системный python на macOS ходит
    без корневых сертификатов — та же причина, что и в extract.py.
    """
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/traffic/{kind}"],
            capture_output=True, text=True, check=True, timeout=120,
        )
    except FileNotFoundError:
        sys.exit("нужен gh CLI: brew install gh && gh auth login")
    except subprocess.CalledProcessError as err:
        sys.exit(f"{kind}: {err.stderr.strip()} — нужен токен с доступом на push")
    return json.loads(result.stdout)


def load(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, newline="") as handle:
        return {row["date"]: row for row in csv.DictReader(handle)}


def main() -> None:
    repo = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        sys.exit("укажите репозиторий: python3 traffic.py owner/repo")
    path = sys.argv[2] if len(sys.argv) > 2 else os.path.join("docs", "traffic.csv")

    rows = load(path)
    for kind, count_key, unique_key in (
        ("clones", "clones", "clone_uniques"),
        ("views", "views", "view_uniques"),
    ):
        for point in fetch(repo, kind).get(kind, []):
            day = point["timestamp"][:10]
            row = rows.setdefault(day, {column: "" for column in COLUMNS})
            row["date"] = day
            row[count_key] = str(point["count"])
            row[unique_key] = str(point["uniques"])

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for day in sorted(rows):
            writer.writerow({column: rows[day].get(column, "") for column in COLUMNS})

    total = sum(int(row.get("clone_uniques") or 0) for row in rows.values())
    print(f"{repo}: дней в истории {len(rows)}, уникальных клонов за всё время {total}")
    print(f"записано: {path}")


main()
