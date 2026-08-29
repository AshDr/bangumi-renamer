import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { SettingsModal } from "./App";
import { resolveTheme } from "./theme";
import type { DesktopSettings } from "./types";

const settings: DesktopSettings = {
    metadata_provider: "thetvdb",
    ui_language: "en-US",
    conflict_policy: "suffix",
    theme: "system",
    has_api_key: true,
    api_key_from_environment: false,
    has_thetvdb_api_key: true,
    thetvdb_api_key_from_environment: false,
    has_thetvdb_pin: false,
    thetvdb_pin_from_environment: false,
    has_tmdb_api_key: false,
    tmdb_api_key_from_environment: false,
};

describe("desktop theme switching", () => {
    it("keeps explicit light and dark themes independent from the system", () => {
        expect(resolveTheme("light", true)).toBe("light");
        expect(resolveTheme("dark", false)).toBe("dark");
    });

    it("resolves the system theme from the operating system preference", () => {
        expect(resolveTheme("system", true)).toBe("dark");
        expect(resolveTheme("system", false)).toBe("light");
    });

    it("offers all theme preferences in desktop settings", () => {
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

        expect(html).toContain('<option value="system" selected="">Follow system</option>');
        expect(html).toContain('<option value="light">Light</option>');
        expect(html).toContain('<option value="dark">Dark</option>');
    });
});
