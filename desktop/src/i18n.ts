import type { UiLocale } from "./types";

export const supportedUiLocales: UiLocale[] = ["zh-CN", "zh-TW", "en-US", "ja-JP"];

const en = {
    "common.cancel": "Cancel",
    "common.close": "Close",
    "title.settings": "Settings",
    "workflow.label": "Workflow",
    "workflow.choose": "Folder",
    "workflow.review": "Matches",
    "workflow.apply": "Apply",
    "workspace.select": "Select a media folder",
    "workspace.hint": "Drop a folder here or use the picker.",
    "workspace.rescan": "Rescan",
    "workspace.choose": "Choose folder",
    "drop.title": "Bring order to your library",
    "drop.description": "Drop an anime or TV folder anywhere in this window",
    "drop.formats": "Video plus ASS, SSA, SRT, VTT, SUB, IDX, SUP and MKS subtitles",
    "summary.total": "Total files",
    "summary.ready": "Ready",
    "summary.review": "Needs review",
    "summary.rename": "Will rename",
    "table.empty": "No supported media files found",
    "table.emptyHint": "Try another folder.",
    "table.source": "Source",
    "table.planned": "Planned name",
    "table.match": "Match",
    "table.status": "Status",
    "table.unparsed": "Could not parse",
    "table.confidence": "{value}% confidence",
    "table.unmatched": "Unmatched",
    "table.pickMatch": "Pick another TMDB match",
    "status.OK": "Ready",
    "status.unparsed": "Unparsed",
    "status.no match": "No match",
    "status.no season": "No season",
    "status.conflict": "Conflict",
    "status.error": "Error",
    "footer.connected": "TMDB connected",
    "footer.keyRequired": "TMDB key required",
    "footer.previewCount": "{count} files",
    "footer.apply": "Apply",
    "notice.apiKeyRequired": "Add a TMDB API key before scanning.",
    "notice.previewReady": "Preview ready - {count} files inspected.",
    "notice.noFiles": "No supported video or subtitle files were found in this folder.",
    "notice.renamed": "Renamed {count} files. History saved to {path}",
    "notice.noRename": "No files needed renaming.",
    "notice.matched": "Matched {count} file(s) to {name}.",
    "notice.settingsSaved": "Settings saved.",
    "busy.scanning": "Scanning files and matching TMDB...",
    "busy.matching": "Rebuilding selected matches...",
    "busy.applying": "Applying verified renames...",
    "settings.title": "Desktop settings",
    "settings.subtitle": "TMDB access and rename preferences",
    "settings.apiKey": "TMDB API key",
    "settings.savedKey": "Key is saved - enter a new value to replace it",
    "settings.newKey": "Paste a TMDB v3 API key",
    "settings.environmentKey": "Managed by the TMDB_API_KEY environment variable.",
    "settings.uiLanguage": "Interface language",
    "settings.metadataLanguage": "Metadata language",
    "settings.metadataPlaceholder": "en-US",
    "settings.conflict": "When a target exists",
    "settings.conflictSuffix": "Add a numeric suffix",
    "settings.conflictSkip": "Skip the file",
    "settings.conflictOverwrite": "Overwrite target",
    "settings.appearance": "Appearance",
    "settings.themeSystem": "Follow system",
    "settings.themeLight": "Light",
    "settings.themeDark": "Dark",
    "settings.save": "Save settings",
    "locale.zh-CN": "简体中文",
    "locale.zh-TW": "繁體中文",
    "locale.en-US": "English",
    "locale.ja-JP": "日本語",
    "candidate.title": "Choose a TMDB match",
    "candidate.searching": "Searching TMDB...",
    "candidate.empty": "No candidates found.",
    "candidate.noOriginalTitle": "No original title",
    "candidate.noOverview": "No overview available.",
    "confirm.title": "Apply rename plan?",
    "confirm.subtitle": "This is the only step that changes files on disk.",
    "confirm.description": "{count} file(s) will be renamed. A recovery journal will be written under",
    "confirm.keepReviewing": "Keep reviewing",
    "confirm.applyNow": "Apply now",
} as const;

export type TranslationKey = keyof typeof en;
type Messages = Record<TranslationKey, string>;
export type TranslationValues = Record<string, string | number>;
export type Translator = (key: TranslationKey, values?: TranslationValues) => string;

const zhCN: Messages = {
    "common.cancel": "取消", "common.close": "关闭", "title.settings": "设置",
    "workflow.label": "工作流程", "workflow.choose": "文件夹", "workflow.review": "匹配", "workflow.apply": "应用",
    "workspace.select": "选择媒体文件夹", "workspace.hint": "将文件夹拖到此处，或使用选择器。", "workspace.rescan": "重新扫描", "workspace.choose": "选择文件夹",
    "drop.title": "让媒体库井然有序", "drop.description": "将动漫或电视剧文件夹拖到窗口任意位置", "drop.formats": "视频，以及 ASS、SSA、SRT、VTT、SUB、IDX、SUP、MKS 字幕",
    "summary.total": "文件总数", "summary.ready": "已就绪", "summary.review": "需要检查", "summary.rename": "将重命名",
    "table.empty": "未找到支持的媒体文件", "table.emptyHint": "请尝试其他文件夹。", "table.source": "源文件", "table.planned": "计划名称", "table.match": "匹配", "table.status": "状态", "table.unparsed": "无法解析", "table.confidence": "置信度 {value}%", "table.unmatched": "未匹配", "table.pickMatch": "选择其他 TMDB 匹配",
    "status.OK": "就绪", "status.unparsed": "无法解析", "status.no match": "无匹配", "status.no season": "无季度", "status.conflict": "冲突", "status.error": "错误",
    "footer.connected": "TMDB 已连接", "footer.keyRequired": "需要 TMDB 密钥", "footer.previewCount": "{count} 个文件", "footer.apply": "应用",
    "notice.apiKeyRequired": "请先添加 TMDB API 密钥再扫描。", "notice.previewReady": "预览已就绪 - 已检查 {count} 个文件。", "notice.noFiles": "此文件夹中没有支持的视频或字幕文件。", "notice.renamed": "已重命名 {count} 个文件。历史记录已保存至 {path}", "notice.noRename": "没有需要重命名的文件。", "notice.matched": "已将 {count} 个文件匹配到 {name}。", "notice.settingsSaved": "设置已保存。",
    "busy.scanning": "正在扫描文件并匹配 TMDB...", "busy.matching": "正在重新生成所选匹配...", "busy.applying": "正在应用已确认的重命名...",
    "settings.title": "桌面设置", "settings.subtitle": "TMDB 访问与重命名偏好", "settings.apiKey": "TMDB API 密钥", "settings.savedKey": "密钥已保存 - 输入新值即可替换", "settings.newKey": "粘贴 TMDB v3 API 密钥", "settings.environmentKey": "由 TMDB_API_KEY 环境变量管理。", "settings.uiLanguage": "界面语言", "settings.metadataLanguage": "元数据语言", "settings.metadataPlaceholder": "zh-CN", "settings.conflict": "目标文件已存在时", "settings.conflictSuffix": "添加数字后缀", "settings.conflictSkip": "跳过文件", "settings.conflictOverwrite": "覆盖目标", "settings.appearance": "外观", "settings.themeSystem": "跟随系统", "settings.themeLight": "浅色", "settings.themeDark": "深色", "settings.save": "保存设置",
    "locale.zh-CN": "简体中文", "locale.zh-TW": "繁體中文", "locale.en-US": "English", "locale.ja-JP": "日本語",
    "candidate.title": "选择 TMDB 匹配", "candidate.searching": "正在搜索 TMDB...", "candidate.empty": "未找到候选项。", "candidate.noOriginalTitle": "无原始标题", "candidate.noOverview": "暂无简介。",
    "confirm.title": "应用重命名方案？", "confirm.subtitle": "这是唯一会更改磁盘文件的步骤。", "confirm.description": "将重命名 {count} 个文件。恢复日志将写入", "confirm.keepReviewing": "继续检查", "confirm.applyNow": "立即应用",
};

const zhTW: Messages = {
    ...zhCN,
    "common.cancel": "取消", "common.close": "關閉", "title.settings": "設定",
    "workflow.label": "工作流程", "workflow.choose": "資料夾", "workflow.review": "配對", "workflow.apply": "套用",
    "workspace.select": "選擇媒體資料夾", "workspace.hint": "將資料夾拖到此處，或使用選擇器。", "workspace.rescan": "重新掃描", "workspace.choose": "選擇資料夾",
    "drop.title": "讓媒體庫井然有序", "drop.description": "將動漫或電視劇資料夾拖到視窗任意位置", "drop.formats": "影片，以及 ASS、SSA、SRT、VTT、SUB、IDX、SUP、MKS 字幕",
    "summary.total": "檔案總數", "summary.ready": "已就緒", "summary.review": "需要檢查", "summary.rename": "將重新命名",
    "table.empty": "找不到支援的媒體檔案", "table.emptyHint": "請嘗試其他資料夾。", "table.source": "來源檔案", "table.planned": "計畫名稱", "table.match": "配對", "table.status": "狀態", "table.unparsed": "無法解析", "table.confidence": "信心度 {value}%", "table.unmatched": "未配對", "table.pickMatch": "選擇其他 TMDB 配對",
    "status.OK": "就緒", "status.unparsed": "無法解析", "status.no match": "無配對", "status.no season": "無季度", "status.conflict": "衝突", "status.error": "錯誤",
    "footer.connected": "TMDB 已連線", "footer.keyRequired": "需要 TMDB 金鑰", "footer.previewCount": "{count} 個檔案", "footer.apply": "套用",
    "notice.apiKeyRequired": "請先新增 TMDB API 金鑰再掃描。", "notice.previewReady": "預覽已就緒 - 已檢查 {count} 個檔案。", "notice.noFiles": "此資料夾中沒有支援的影片或字幕檔案。", "notice.renamed": "已重新命名 {count} 個檔案。歷史記錄已儲存至 {path}", "notice.noRename": "沒有需要重新命名的檔案。", "notice.matched": "已將 {count} 個檔案配對到 {name}。", "notice.settingsSaved": "設定已儲存。",
    "busy.scanning": "正在掃描檔案並配對 TMDB...", "busy.matching": "正在重新產生所選配對...", "busy.applying": "正在套用已確認的重新命名...",
    "settings.title": "桌面設定", "settings.subtitle": "TMDB 存取與重新命名偏好", "settings.apiKey": "TMDB API 金鑰", "settings.savedKey": "金鑰已儲存 - 輸入新值即可取代", "settings.newKey": "貼上 TMDB v3 API 金鑰", "settings.environmentKey": "由 TMDB_API_KEY 環境變數管理。", "settings.uiLanguage": "介面語言", "settings.metadataLanguage": "中繼資料語言", "settings.metadataPlaceholder": "zh-TW", "settings.conflict": "目標檔案已存在時", "settings.conflictSuffix": "加入數字後綴", "settings.conflictSkip": "略過檔案", "settings.conflictOverwrite": "覆寫目標", "settings.appearance": "外觀", "settings.themeSystem": "跟隨系統", "settings.themeLight": "淺色", "settings.themeDark": "深色", "settings.save": "儲存設定",
    "candidate.title": "選擇 TMDB 配對", "candidate.searching": "正在搜尋 TMDB...", "candidate.empty": "找不到候選項目。", "candidate.noOriginalTitle": "無原始標題", "candidate.noOverview": "暫無簡介。",
    "confirm.title": "套用重新命名方案？", "confirm.subtitle": "這是唯一會變更磁碟檔案的步驟。", "confirm.description": "將重新命名 {count} 個檔案。復原日誌將寫入", "confirm.keepReviewing": "繼續檢查", "confirm.applyNow": "立即套用",
};

const jaJP: Messages = {
    ...en,
    "common.cancel": "キャンセル", "common.close": "閉じる", "title.settings": "設定",
    "workflow.label": "ワークフロー", "workflow.choose": "フォルダー", "workflow.review": "一致", "workflow.apply": "適用",
    "workspace.select": "メディアフォルダーを選択", "workspace.hint": "ここにフォルダーをドロップするか、選択画面を使用します。", "workspace.rescan": "再スキャン", "workspace.choose": "フォルダーを選択",
    "drop.title": "ライブラリをきれいに整理", "drop.description": "アニメまたはテレビ番組のフォルダーをウィンドウ内にドロップ", "drop.formats": "動画と ASS、SSA、SRT、VTT、SUB、IDX、SUP、MKS 字幕",
    "summary.total": "合計ファイル", "summary.ready": "準備完了", "summary.review": "要確認", "summary.rename": "変更予定",
    "table.empty": "対応メディアファイルが見つかりません", "table.emptyHint": "別のフォルダーをお試しください。", "table.source": "元のファイル", "table.planned": "変更後の名前", "table.match": "一致", "table.status": "状態", "table.unparsed": "解析できません", "table.confidence": "信頼度 {value}%", "table.unmatched": "未一致", "table.pickMatch": "別の TMDB 一致を選択",
    "status.OK": "準備完了", "status.unparsed": "解析不可", "status.no match": "一致なし", "status.no season": "シーズンなし", "status.conflict": "競合", "status.error": "エラー",
    "footer.connected": "TMDB 接続済み", "footer.keyRequired": "TMDB キーが必要です", "footer.previewCount": "{count} ファイル", "footer.apply": "適用",
    "notice.apiKeyRequired": "スキャンする前に TMDB API キーを追加してください。", "notice.previewReady": "プレビュー準備完了 - {count} ファイルを確認しました。", "notice.noFiles": "このフォルダーに対応する動画または字幕ファイルはありません。", "notice.renamed": "{count} ファイルの名前を変更しました。履歴: {path}", "notice.noRename": "名前を変更するファイルはありません。", "notice.matched": "{count} ファイルを {name} に一致させました。", "notice.settingsSaved": "設定を保存しました。",
    "busy.scanning": "ファイルをスキャンし TMDB と照合中...", "busy.matching": "選択した一致を再構築中...", "busy.applying": "確認済みの変更を適用中...",
    "settings.title": "デスクトップ設定", "settings.subtitle": "TMDB アクセスとリネーム設定", "settings.apiKey": "TMDB API キー", "settings.savedKey": "キーは保存済みです - 新しい値を入力して置換", "settings.newKey": "TMDB v3 API キーを貼り付け", "settings.environmentKey": "TMDB_API_KEY 環境変数で管理されています。", "settings.uiLanguage": "表示言語", "settings.metadataLanguage": "メタデータ言語", "settings.metadataPlaceholder": "ja-JP", "settings.conflict": "変更先が存在する場合", "settings.conflictSuffix": "数字の接尾辞を追加", "settings.conflictSkip": "ファイルをスキップ", "settings.conflictOverwrite": "変更先を上書き", "settings.appearance": "外観", "settings.themeSystem": "システムに合わせる", "settings.themeLight": "ライト", "settings.themeDark": "ダーク", "settings.save": "設定を保存",
    "locale.zh-CN": "简体中文", "locale.zh-TW": "繁體中文", "locale.en-US": "English", "locale.ja-JP": "日本語",
    "candidate.title": "TMDB の一致を選択", "candidate.searching": "TMDB を検索中...", "candidate.empty": "候補が見つかりません。", "candidate.noOriginalTitle": "原題なし", "candidate.noOverview": "概要はありません。",
    "confirm.title": "リネームプランを適用しますか？", "confirm.subtitle": "ディスク上のファイルを変更する唯一の手順です。", "confirm.description": "{count} ファイルの名前を変更します。復元用ジャーナルの保存先:", "confirm.keepReviewing": "確認を続ける", "confirm.applyNow": "今すぐ適用",
};

const messages: Record<UiLocale, Messages> = {
    "zh-CN": zhCN,
    "zh-TW": zhTW,
    "en-US": en,
    "ja-JP": jaJP,
};

export function normalizeUiLocale(locale: unknown): UiLocale {
    return typeof locale === "string" && supportedUiLocales.includes(locale as UiLocale)
        ? (locale as UiLocale)
        : "en-US";
}

export function createTranslator(locale: unknown): Translator {
    const dictionary = messages[normalizeUiLocale(locale)];
    return (key, values = {}) =>
        Object.entries(values).reduce(
            (text, [name, value]) => text.replaceAll(`{${name}}`, String(value)),
            dictionary[key],
        );
}
