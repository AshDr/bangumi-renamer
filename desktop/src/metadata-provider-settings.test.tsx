import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { SettingsModal } from "./App";
import { createTranslator } from "./i18n";
import type { DesktopSettings } from "./types";

function settings(metadataProvider: DesktopSettings["metadata_provider"]): DesktopSettings {
    return {
        metadata_provider: metadataProvider,
        ui_language: "en-US",
        conflict_policy: "suffix",
        theme: "system",
        has_api_key: false,
        api_key_from_environment: false,
        has_thetvdb_api_key: false,
        thetvdb_api_key_from_environment: false,
        has_thetvdb_pin: false,
        thetvdb_pin_from_environment: false,
        has_tmdb_api_key: false,
        tmdb_api_key_from_environment: false,
    };
}

function renderSettings(metadataProvider: DesktopSettings["metadata_provider"]): string {
    return renderToStaticMarkup(
        createElement(SettingsModal, {
            settings: settings(metadataProvider),
            onClose: () => undefined,
            onSaved: () => undefined,
            onError: () => undefined,
            onThemePreview: () => undefined,
            onLanguagePreview: () => undefined,
        }),
    );
}

describe("metadata provider settings", () => {
    it("shows TheTVDB credentials for the default provider", () => {
        const html = renderSettings("thetvdb");

        expect(html).toContain("TheTVDB API key");
        expect(html).toContain("TheTVDB PIN");
        expect(html).toContain("Test TheTVDB connection");
        expect(html).not.toContain("TMDB API key");
    });

    it("shows only the TMDB credential for the alternate provider", () => {
        const html = renderSettings("tmdb");

        expect(html).toContain("TMDB API key");
        expect(html).toContain("Test TMDB connection");
        expect(html).not.toContain("TheTVDB API key");
        expect(html).not.toContain("TheTVDB PIN");
    });

    it("interpolates the selected provider in shared interface copy", () => {
        const t = createTranslator("en-US");

        expect(t("footer.connected", { provider: "TheTVDB" })).toBe("TheTVDB connected");
        expect(t("candidate.searching", { provider: "TMDB" })).toBe("Searching TMDB...");
    });
});
