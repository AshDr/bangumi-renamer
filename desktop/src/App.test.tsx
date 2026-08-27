import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { PlanTable } from "./App";
import type { PlanItem } from "./types";

const row = (overrides: Partial<PlanItem> = {}): PlanItem => ({
    source: "/shows/A very long source filename.mkv",
    source_name: "A very long source filename.mkv",
    target: "/shows/A very long planned filename.mkv",
    target_name: "A very long planned filename.mkv",
    status: "OK",
    detail: "",
    parsed: { title: "A long series title", season: 1, episode: 1, year: null },
    match: {
        tmdb_id: 123,
        name: "A very long TMDB series name",
        confidence: 98,
        reason: "fuzzy=98",
    },
    ...overrides,
});

describe("desktop plan table tooltips", () => {
    it("exposes complete source, planned, and match names", () => {
        const html = renderToStaticMarkup(
            <PlanTable items={[row()]} busy={false} onPickMatch={() => undefined} />,
        );

        expect(html).toContain('title="A very long source filename.mkv"');
        expect(html).toContain('title="A very long planned filename.mkv"');
        expect(html).toContain('title="A very long TMDB series name"');
    });

    it("keeps missing planned names and matches free of empty tooltips", () => {
        const html = renderToStaticMarkup(
            <PlanTable
                items={[row({ target: null, target_name: null, match: null })]}
                busy={false}
                onPickMatch={() => undefined}
            />,
        );

        expect(html).toContain('<strong class="target-name">-</strong>');
        expect(html).toContain('<span class="muted">Unmatched</span>');
        expect(html).not.toContain('title=""');
    });
});
