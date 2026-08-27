import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { SettingsModal } from "./App";
import { createTranslator, normalizeUiLocale, supportedUiLocales } from "./i18n";
import type { DesktopSettings } from "./types";

describe("desktop interface localization", () => {
    it("provides translated settings labels for every supported locale", () => {
        expect(supportedUiLocales).toEqual(["zh-CN", "zh-TW", "en-US", "ja-JP"]);
        expect(createTranslator("zh-CN")("settings.title")).toBe("桌面设置");
        expect(createTranslator("zh-TW")("settings.title")).toBe("桌面設定");
        expect(createTranslator("en-US")("settings.title")).toBe("Desktop settings");
        expect(createTranslator("ja-JP")("settings.title")).toBe("デスクトップ設定");
    });

    it("falls back to English and interpolates dynamic values", () => {
        expect(normalizeUiLocale("fr-FR")).toBe("en-US");
        expect(createTranslator("fr-FR")("notice.previewReady", { count: 12 })).toBe(
            "Preview ready - 12 files inspected.",
        );
    });

    it("offers all supported interface languages in desktop settings", () => {
        const settings: DesktopSettings = {
            ui_language: "zh-CN",
            language: "zh-CN",
            conflict_policy: "suffix",
            theme: "system",
            has_api_key: true,
            api_key_from_environment: false,
        };
        const html = renderToStaticMarkup(
            createElement(SettingsModal, {
                settings,
                onClose: () => undefined,
                onSaved: () => undefined,
                onError: () => undefined,
                onThemePreview: () => undefined,
                onLanguagePreview: () => undefined,
            }),
        );

        expect(html).toContain('<option value="zh-CN" selected="">简体中文</option>');
        expect(html).toContain('<option value="zh-TW">繁體中文</option>');
        expect(html).toContain('<option value="en-US">English</option>');
        expect(html).toContain('<option value="ja-JP">日本語</option>');
    });
});
