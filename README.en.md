# Russian language pack for Orca

> 🇷🇺 **Русская версия** → [README.md](README.md)

Translates the [Orca](https://github.com/stablyai/orca) interface into Russian — **13 707 of 13 896 strings (98%)**. This is Orca by Stably AI, the agent development environment (ADE) — not the GNOME screen reader, the Microsoft MSI editor, or OrcaSlicer.

> **Built for Orca 1.4.196, works from 1.4.169 up.** The build version lives in [ORCA_VERSION](ORCA_VERSION), the compatibility floor in [COMPAT](COMPAT).

The pack uses Orca's own plugin mechanism (`contributes.languagePacks`): the app is never patched, so an Orca update cannot break it. Untranslated strings fall back to English through i18next.

## Install

### From the marketplace (recommended)

Orca then offers updates on its own whenever a new version ships.

1. **Settings → Plugins** — enable the plugin system
2. **Marketplace sources → Add source**, paste:

   ```
   https://github.com/imgusev/orca-plugins.git
   ```

3. On the **All** tab find «Русский язык для Orca» and press **Install**
4. **Settings → Appearance → Language** — pick Russian

### From a Git URL

One link, no source needed. The explicit `#ref` is required by Orca so the install is pinned to a version:

```
https://github.com/imgusev/orca-plugin-ru.git#v1.4.196
```

## Versioning

The package version equals the Orca version its catalog was extracted from — patch included. A catalog built from Orca 1.4.196 ships as `1.4.196`, tagged `v1.4.196`. The plugin card then tells you which app version the translation matches without checking anything else.

One consequence is worth knowing: a translation-only fix cannot ship without an Orca release. The manifest validator demands strict semver — there is no fourth segment, and `1.4.196-fix1` sorts *below* `1.4.196`, so Orca would not treat it as an update. Such a fix waits for the next Orca release; they arrive almost daily.

## How the catalog is built

The English catalog is fetched from the Orca repository **at the tag of the installed version** — `src/renderer/src/i18n/locales/en.json` at `v1.4.196`, never from `main`. A key added to `main` but not yet released is unknown to the installed validator, and it rejects **the entire catalog**, silently disabling the language. Parsing the minified `app.asar` is used only as a supplement: it yields 152 settings-search keys that `en.json` does not carry.

```bash
cd tools
python3 extract.py    # pull strings from the installed Orca → en-all.json + ORCA_VERSION
python3 build.py      # build locales/ru.json and report what is missing
```

`build.py` verifies placeholders, the 8192-character value limit, catalog depth and entry count, and strips the protected zone.

## Plural forms

Russian needs four forms where English has two. Where the app picks the form in JS (`count === 1 ? …_one : …_other`), no catalog can change it. But 67 call sites pass `count` without baking the suffix into the key — there i18next appends the suffix itself using the target language rules and asks for `_few` and `_many`, which the English catalog has no keys for. Those forms live in [`tools/dict/plurals.json`](tools/dict/plurals.json) and do reach the UI: «1 навык», «2 навыка», «5 навыков», «21 навык».

`extract.py` collects the keys that receive `count` into `plural-candidates.txt`, and `build.py` reports how many of them still lack forms — and fails if a form is declared for a key that never receives `count`, because such an entry would never be requested.

## Compatibility with older Orca

A pack update reaches users before the app update does, so the catalog must stay valid across the whole supported range. Exactly one class of change is dangerous: a path **allowed** for translation in a new Orca but still **protected** in an older one. A single such key rejects the whole catalog and the language quietly turns off — before **1.4.169** no allowlist existed at all and the entire `settings.plugin*` space was closed.

Two defences: `extract.py` builds `allowed-chrome.txt` as the **intersection** of the allowlists of the minimum supported version (see [COMPAT](COMPAT)) and the installed one; and `engines.orca` equals that same floor, so an older Orca refuses to install the pack with a clear error instead of breaking silently.

## What stays in English

189 strings, all deliberately. 180 of them Orca forbids language packs to replace — the copy a user reads when deciding whether to trust a plugin. 7 are overridden per key where a flat dictionary would guess the context wrong, and 2 are CSS blocks past the value-length limit. Another ~1000 strings are translated identically to themselves on purpose: commands, paths, environment variables, product names, state identifiers. Full breakdown in [UNTRANSLATED.md](UNTRANSLATED.md) (in Russian).

**Nothing is missing by oversight** — `build.py` reports zero uncovered strings.

## Terminology

Terms are kept consistent across the whole interface and aligned with the [glossary from smwbev/orca-russian](https://github.com/smwbev/orca-russian/blob/main/GLOSSARY.md), so that Russian packs for Orca do not drift apart. One deliberate difference: `worktree` stays in Latin script — `git worktree` is a command name, and the Russian rendering collides with «working tree».

## License

[MIT](LICENSE), like Orca itself. The English source strings belong to [stablyai/orca](https://github.com/stablyai/orca) and are used under its MIT license. This project is not officially affiliated with Stably AI.
