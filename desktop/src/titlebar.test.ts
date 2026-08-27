import { describe, expect, it } from "vitest";

import { titlebarClassName } from "./lib";

describe("title-bar platform spacing", () => {
    it("adds the native control safe-area class on macOS", () => {
        expect(titlebarClassName("darwin")).toBe("titlebar titlebar-macos");
    });

    it("keeps the default title-bar class on other platforms", () => {
        expect(titlebarClassName("windows")).toBe("titlebar");
        expect(titlebarClassName("linux")).toBe("titlebar");
    });
});
