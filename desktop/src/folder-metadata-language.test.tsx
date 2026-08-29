import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import {
    SettingsModal,
    WorkspaceMetadataLanguageSelect,
    metadataLanguageForFolder,
} from "./App";
import { createTranslator } from "./i18n";
import type { DesktopSettings, MetadataLanguage } from "./types";

const settings: DesktopSettings = {
    metadata_provider: "tmdb",
    ui_language: "zh-CN",
    conflict_policy: "suffix",
    theme: "system",
    has_api_key: true,
    api_key_from_environment: false,
    has_thetvdb_api_key: false,
    thetvdb_api_key_from_environment: false,
    has_thetvdb_pin: false,
    thetvdb_pin_from_environment: false,
    has_tmdb_api_key: true,
    tmdb_api_key_from_environment: false,
};

describe("folder-scoped metadata language", () => {
    it("renders every metadata locale in the workspace control", () => {
        const html = renderToStaticMarkup(
            <WorkspaceMetadataLanguageSelect
                value="zh-CN"
                busy={false}
                onChange={() => undefined}
                t={createTranslator("zh-CN")}
            />,
        );

        expect(html).toContain('aria-label="元数据语言"');
        expect(html).toContain('<option value="zh-CN" selected="">简体中文</option>');
        expect(html).toContain('<option value="zh-TW">繁體中文</option>');
        expect(html).toContain('<option value="en-US">English</option>');
        expect(html).toContain('<option value="ja-JP">日本語</option>');
    });

    it("does not render metadata language in global settings", () => {
        const html = renderToStaticMarkup(
            <SettingsModal
                settings={settings}
                onClose={() => undefined}
                onSaved={() => undefined}
                onError={() => undefined}
                onThemePreview={() => undefined}
                onLanguagePreview={() => undefined}
            />,
        );

        expect(html).not.toContain("元数据语言");
    });

    it("resolves independent languages for each folder and defaults to the UI locale", () => {
        const choices: Record<string, MetadataLanguage> = {
            "/anime/chinese": "zh-CN",
            "/anime/english": "en-US",
        };

        expect(metadataLanguageForFolder(choices, "/anime/chinese", "ja-JP")).toBe("zh-CN");
        expect(metadataLanguageForFolder(choices, "/anime/english", "ja-JP")).toBe("en-US");
        expect(metadataLanguageForFolder(choices, "/anime/new", "ja-JP")).toBe("ja-JP");
    });
});
