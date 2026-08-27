import { describe, expect, it } from "vitest";

import { actionableItems, summarize } from "./lib";
import type { PlanItem } from "./types";

const row = (status: string, target: string | null = "/shows/new.mkv"): PlanItem => ({
    source: "/shows/old.mkv",
    source_name: "old.mkv",
    target,
    target_name: target ? "new.mkv" : null,
    status,
    detail: "",
    parsed: null,
    match: null,
});

describe("plan helpers", () => {
    it("summarizes statuses and excludes no-op rows from apply", () => {
        const items = [row("OK"), row("OK", "/shows/old.mkv"), row("conflict", null)];

        expect(summarize(items)).toEqual({ OK: 2, conflict: 1 });
        expect(actionableItems(items)).toHaveLength(1);
    });
});
