import { readFileSync } from "node:fs";

import { describe, expect, it } from "vitest";

const stylesheet = readFileSync(new URL("./index.css", import.meta.url), "utf8");

describe("workspace toolbar layout", () => {
    it("keeps toolbar controls from shrinking or wrapping their labels", () => {
        expect(stylesheet).toMatch(/\.workspace-language\s*\{[^}]*flex-shrink:\s*0/s);
        expect(stylesheet).toMatch(/\.button\s*\{[^}]*white-space:\s*nowrap/s);
    });

    it("stacks the action group below the folder title in compact windows", () => {
        const compactLayout = stylesheet.slice(stylesheet.indexOf("@media (max-width: 1040px)"));

        expect(compactLayout).toMatch(/\.content-header\s*\{[^}]*flex-direction:\s*column/s);
        expect(compactLayout).toMatch(/\.header-actions\s*\{[^}]*justify-content:\s*flex-end/s);
    });
});
