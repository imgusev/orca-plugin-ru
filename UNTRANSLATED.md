# Что осталось на английском — и почему

Каталог покрывает **12 415 из 12 604** строк Orca 1.4.180 (98%).
Ниже — полный разбор оставшихся 189.

## 1. Запрещено самой Orca — защищённая зона

**180 ключей.** Тексты, по которым пользователь решает, доверять ли плагину:
статусы «заблокирован» и «требует проверки», источник установки, диалоги удаления и отката,
метаданные поиска по разделу плагинов.

Валидатор Orca отклоняет **весь каталог целиком**, если найдёт хоть один такой ключ
(`catalog cannot replace protected security copy`) — плагин тогда падает с
«The plugin stopped after an activation or worker error». Это защита от подмены
предупреждений безопасности на успокаивающий текст, и она правильная.

`tools/build.py` вырезает их автоматически. Белый список исключений (34 пути) —
`tools/allowed-chrome.txt`, снят прямо из бандла Orca; после обновления приложения
его стоит пересобрать (команда в README).

<details><summary>Полный список</summary>

- `auto.components.settings.PluginConsentDialog.capabilities`
- `auto.components.settings.PluginConsentDialog.capability.eventsSubscribe`
- `auto.components.settings.PluginConsentDialog.capability.notificationsShow`
- `auto.components.settings.PluginConsentDialog.capability.secrets`
- `auto.components.settings.PluginConsentDialog.capability.settingsOwn`
- `auto.components.settings.PluginConsentDialog.capability.storage`
- `auto.components.settings.PluginConsentDialog.capability.terminalSend`
- `auto.components.settings.PluginConsentDialog.capability.workspaceRead`
- `auto.components.settings.PluginConsentDialog.decisionFailed`
- `auto.components.settings.PluginConsentDialog.declarativeTrust`
- `auto.components.settings.PluginConsentDialog.declarativeWarning`
- `auto.components.settings.PluginConsentDialog.enable`
- `auto.components.settings.PluginConsentDialog.instructionalTitle`
- `auto.components.settings.PluginConsentDialog.instructionalTrust`
- `auto.components.settings.PluginConsentDialog.instructionalWarning`
- `auto.components.settings.PluginConsentDialog.keepDisabled`
- `auto.components.settings.PluginConsentDialog.mixedTitle`
- `auto.components.settings.PluginConsentDialog.panelTrust`
- `auto.components.settings.PluginConsentDialog.panelWarning`
- `auto.components.settings.PluginConsentDialog.reconsent`
- `auto.components.settings.PluginConsentDialog.reviewTitle`
- `auto.components.settings.PluginConsentDialog.subtitle`
- `auto.components.settings.PluginConsentDialog.title`
- `auto.components.settings.PluginConsentDialog.trustShortDeclarative`
- `auto.components.settings.PluginConsentDialog.trustShortInstructional`
- `auto.components.settings.PluginConsentDialog.trustShortPanel`
- `auto.components.settings.PluginConsentDialog.trustShortWorker`
- `auto.components.settings.PluginConsentDialog.warning`
- `auto.components.settings.PluginConsentDialog.workerTrust`
- `auto.components.settings.PluginConsentProvenance.bundled`
- `auto.components.settings.PluginConsentProvenance.commit`
- `auto.components.settings.PluginConsentProvenance.community`
- `auto.components.settings.PluginConsentProvenance.indexCommit`
- `auto.components.settings.PluginConsentProvenance.local`
- `auto.components.settings.PluginConsentProvenance.localCommit`
- `auto.components.settings.PluginConsentProvenance.official`
- `auto.components.settings.PluginConsentProvenance.source`
- `auto.components.settings.PluginConsentProvenance.sourceLabel`
- `auto.components.settings.PluginDevelopmentSection.help`
- `auto.components.settings.PluginDevelopmentSection.saveFailed`
- `auto.components.settings.PluginInstallDialog.cancel`
- `auto.components.settings.PluginInstallDialog.description`
- `auto.components.settings.PluginInstallDialog.gitHelp`
- `auto.components.settings.PluginInstallDialog.gitLabel`
- `auto.components.settings.PluginInstallDialog.gitPlaceholder`
- `auto.components.settings.PluginInstallDialog.gitRefRequired`
- `auto.components.settings.PluginInstallDialog.gitTab`
- `auto.components.settings.PluginInstallDialog.gitUrlInvalid`
- `auto.components.settings.PluginInstallDialog.gitUrlRequired`
- `auto.components.settings.PluginInstallDialog.install`
- `auto.components.settings.PluginInstallDialog.installFailed`
- `auto.components.settings.PluginInstallDialog.installing`
- `auto.components.settings.PluginInstallDialog.localHelp`
- `auto.components.settings.PluginInstallDialog.localLabel`
- `auto.components.settings.PluginInstallDialog.localPlaceholder`
- `auto.components.settings.PluginInstallDialog.localRequired`
- `auto.components.settings.PluginInstallDialog.localTab`
- `auto.components.settings.PluginInstallDialog.source`
- `auto.components.settings.PluginInstallDialog.title`
- `auto.components.settings.PluginKeybindingConsentPreview.global`
- `auto.components.settings.PluginKeybindingConsentPreview.heading`
- `auto.components.settings.PluginKeybindingConsentPreview.shadows`
- `auto.components.settings.PluginKeybindingConsentPreview.worktree`
- `auto.components.settings.PluginMarketplaceBrowser.installFailed`
- `auto.components.settings.PluginMarketplaceBrowser.loadFailed`
- `auto.components.settings.PluginMarketplaceBrowser.noSources`
- `auto.components.settings.PluginMarketplaceBrowser.previewFailed`
- `auto.components.settings.PluginMarketplaceBrowser.refreshFailed`
- `auto.components.settings.PluginMarketplaceListingRow.blocked`
- `auto.components.settings.PluginMarketplaceListingRow.blockedAction`
- `auto.components.settings.PluginMarketplaceListingRow.checkUpdate`
- `auto.components.settings.PluginMarketplaceListingRow.install`
- `auto.components.settings.PluginMarketplaceListingRow.installed`
- `auto.components.settings.PluginMarketplaceListingRow.noDescription`
- `auto.components.settings.PluginMarketplaceListingRow.official`
- `auto.components.settings.PluginMarketplacePreviewDialog.blocked`
- `auto.components.settings.PluginMarketplacePreviewDialog.cancel`
- `auto.components.settings.PluginMarketplacePreviewDialog.capabilities`
- `auto.components.settings.PluginMarketplacePreviewDialog.close`
- `auto.components.settings.PluginMarketplacePreviewDialog.commands`
- `auto.components.settings.PluginMarketplacePreviewDialog.commandsOne`
- `auto.components.settings.PluginMarketplacePreviewDialog.current`
- `auto.components.settings.PluginMarketplacePreviewDialog.events`
- `auto.components.settings.PluginMarketplacePreviewDialog.eventsOne`
- `auto.components.settings.PluginMarketplacePreviewDialog.includes`
- `auto.components.settings.PluginMarketplacePreviewDialog.install`
- `auto.components.settings.PluginMarketplacePreviewDialog.keybindings`
- `auto.components.settings.PluginMarketplacePreviewDialog.keybindingsOne`
- `auto.components.settings.PluginMarketplacePreviewDialog.languagePacks`
- `auto.components.settings.PluginMarketplacePreviewDialog.languagePacksOne`
- `auto.components.settings.PluginMarketplacePreviewDialog.noContributions`
- `auto.components.settings.PluginMarketplacePreviewDialog.panels`
- `auto.components.settings.PluginMarketplacePreviewDialog.panelsOne`
- `auto.components.settings.PluginMarketplacePreviewDialog.update`
- `auto.components.settings.PluginMarketplacePreviewDialog.versionLine`
- `auto.components.settings.PluginMarketplacePreviewDialog.vmRecipes`
- `auto.components.settings.PluginMarketplacePreviewDialog.vmRecipesOne`
- `auto.components.settings.PluginMarketplacePreviewDialog.worker`
- `auto.components.settings.PluginMarketplacePreviewDialog.workerWarning`
- `auto.components.settings.PluginMarketplaceSourceDialog.add`
- `auto.components.settings.PluginMarketplaceSourceDialog.addFailed`
- `auto.components.settings.PluginMarketplaceSourceDialog.adding`
- `auto.components.settings.PluginMarketplaceSourceDialog.configured`
- `auto.components.settings.PluginMarketplaceSourceDialog.description`
- `auto.components.settings.PluginMarketplaceSourceDialog.done`
- `auto.components.settings.PluginMarketplaceSourceDialog.empty`
- `auto.components.settings.PluginMarketplaceSourceDialog.official`
- `auto.components.settings.PluginMarketplaceSourceDialog.owner`
- `auto.components.settings.PluginMarketplaceSourceDialog.pinnedCommit`
- `auto.components.settings.PluginMarketplaceSourceDialog.refDescription`
- `auto.components.settings.PluginMarketplaceSourceDialog.refLabel`
- `auto.components.settings.PluginMarketplaceSourceDialog.refreshFailed`
- `auto.components.settings.PluginMarketplaceSourceDialog.refreshLabel`
- `auto.components.settings.PluginMarketplaceSourceDialog.removeFailed`
- `auto.components.settings.PluginMarketplaceSourceDialog.removeLabel`
- `auto.components.settings.PluginMarketplaceSourceDialog.stale`
- `auto.components.settings.PluginMarketplaceSourceDialog.title`
- `auto.components.settings.PluginMarketplaceSourceDialog.urlDescription`
- `auto.components.settings.PluginMarketplaceSourceDialog.urlLabel`
- `auto.components.settings.PluginMarketplaceSourceDialog.urlPlaceholder`
- `auto.components.settings.PluginRemoveDialog.cancel`
- `auto.components.settings.PluginRemoveDialog.description`
- `auto.components.settings.PluginRemoveDialog.remove`
- `auto.components.settings.PluginRemoveDialog.title`
- `auto.components.settings.PluginRollbackDialog.cancel`
- `auto.components.settings.PluginRollbackDialog.confirm`
- `auto.components.settings.PluginRollbackDialog.description`
- `auto.components.settings.PluginRollbackDialog.title`
- `auto.components.settings.PluginSettingsRow.blocked`
- `auto.components.settings.PluginSettingsRow.bundled`
- `auto.components.settings.PluginSettingsRow.dev`
- `auto.components.settings.PluginSettingsRow.disableLabel`
- `auto.components.settings.PluginSettingsRow.disabled`
- `auto.components.settings.PluginSettingsRow.enableLabel`
- `auto.components.settings.PluginSettingsRow.enabled`
- `auto.components.settings.PluginSettingsRow.error`
- `auto.components.settings.PluginSettingsRow.hideLogs`
- `auto.components.settings.PluginSettingsRow.invalid`
- `auto.components.settings.PluginSettingsRow.invalidPluginError`
- `auto.components.settings.PluginSettingsRow.killListMessage`
- `auto.components.settings.PluginSettingsRow.loadingLogs`
- `auto.components.settings.PluginSettingsRow.logCount`
- `auto.components.settings.PluginSettingsRow.moreActions`
- `auto.components.settings.PluginSettingsRow.needsReview`
- `auto.components.settings.PluginSettingsRow.noDescription`
- `auto.components.settings.PluginSettingsRow.noLogs`
- `auto.components.settings.PluginSettingsRow.official`
- `auto.components.settings.PluginSettingsRow.remove`
- `auto.components.settings.PluginSettingsRow.restartCount`
- `auto.components.settings.PluginSettingsRow.restarting`
- `auto.components.settings.PluginSettingsRow.reviewAndEnable`
- `auto.components.settings.PluginSettingsRow.rollback`
- `auto.components.settings.PluginSettingsRow.running`
- `auto.components.settings.PluginSettingsRow.runtimeError`
- `auto.components.settings.PluginSettingsRow.viewAdvisory`
- `auto.components.settings.PluginSettingsRow.viewLogs`
- `auto.components.settings.PluginVmRecipeConsentPreview.commandLabel`
- `auto.components.settings.PluginVmRecipeConsentPreview.create`
- `auto.components.settings.PluginVmRecipeConsentPreview.destroy`
- `auto.components.settings.PluginVmRecipeConsentPreview.heading`
- `auto.components.settings.PluginVmRecipeConsentPreview.resume`
- `auto.components.settings.PluginVmRecipeConsentPreview.suspend`
- `auto.components.settings.PluginsSettingsSection.description`
- `auto.components.settings.PluginsSettingsSection.experimental`
- `auto.components.settings.PluginsSettingsSection.featureOff`
- `auto.components.settings.PluginsSettingsSection.loadFailed`
- `auto.components.settings.PluginsSettingsSection.logsFailed`
- `auto.components.settings.PluginsSettingsSection.rollbackFailed`
- `auto.components.settings.PluginsSettingsSection.settingsUpdateFailed`
- `auto.components.settings.PluginsSettingsSection.systemDescription`
- `auto.components.settings.pluginError.consentChanged`
- `auto.components.settings.pluginError.incompatible`
- `auto.components.settings.pluginError.installGit`
- `auto.components.settings.pluginError.installLimit`
- `auto.components.settings.pluginError.installManifestInvalid`
- `auto.components.settings.pluginError.installManifestMissing`
- `auto.components.settings.pluginError.installUnsafePath`
- `auto.components.settings.pluginError.invalidArtifact`
- `auto.components.settings.pluginError.invalidManifest`
- `auto.components.settings.pluginError.invalidManifestMissing`

</details>

## 2. Не переводится по смыслу — технические литералы

**992 строки** оставлены в оригинале намеренно, тождественным переводом
(в словаре они есть, поэтому в отчёте сборки не выглядят пробелом):

- имена продуктов и агентов: Claude, Codex, Aider, Amp, Devin, Kilocode, Zed, Trae…
- команды и пути: `pnpm install`, `gh auth login`, `src/auth/session.ts`, `~/.orca/keybindings.json`
- переменные окружения: `ORCA_GITEA_TOKEN`, `http_proxy`, `DO_NOT_TRACK`
- плейсхолдеры шаблонов: `{prompt}`, `{basePrompt}`, `{{artifact_url}}`
- термины, которые ищут по-английски: `tmux`, `webgl`, `osc52`, `pwsh`, `ripgrep`
- демо-контент продуктового тура — он изображает реальный вывод инструментов,
  перевод сделал бы его ложью
- внутренние идентификаторы состояний и вариантов: `idle`, `error`, `closed`,
  `destructive`, `not-configured`, `killAll`. Значение выглядит словом, но уходит
  в `data-*`, `variant` или ключ состояния — перевод сломал бы логику
- служебные CSS-классы и блоки стилей витрины возможностей

## 3. Переопределения по ключу

**7 ключей** (`tools/dict/by-key.json`). Словари плоские — «английский текст → перевод», —
поэтому одно и то же слово переводится одинаково везде. Там, где контекст меняет смысл,
перевод задаётся для конкретного ключа, а `null` означает «оставить английским»:

- `Cursor` и `Continue` в каталоге агентов и в списке «Открыть в приложении» —
  это названия редактора и агента, а не «курсор» и «продолжить»
- `Claude Agent Teams` — название режима, не описание
- `idle` в трёх местах — состояние обновления и панели истории Git;
  официальные локали Orca (es, ja) его тоже не переводят

## 4. Не помещаются в лимит Orca

**2 строки.** CSS-блоки витрины возможностей — 9691 и 9965 символов при жёстком
лимите валидатора 8192 на одно значение (`translation at <path> exceeds 8192
characters`). Превышение отклоняет **весь каталог целиком**, поэтому `build.py`
их пропускает. Переводить в них всё равно нечего — это правила стилей.

## 5. Ничего не забыто

Строк, оставшихся без перевода по недосмотру: **0**.

Все строки вне защищённой зоны обработаны. Проверяется командой `python3 tools/build.py` —
строка «нет в словарях» в отчёте должна быть нулевой.
