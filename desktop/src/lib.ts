import type { PlanItem } from "./types";

export function summarize(items: PlanItem[]): Record<string, number> {
    return items.reduce<Record<string, number>>((counts, item) => {
        counts[item.status] = (counts[item.status] || 0) + 1;
        return counts;
    }, {});
}

export function actionableItems(items: PlanItem[]): PlanItem[] {
    return items.filter(
        (item) => item.status === "OK" && item.target !== null && item.target !== item.source,
    );
}

export function rowsForMatch(items: PlanItem[], title: string): PlanItem[] {
    return items.filter((item) => item.parsed?.title === title);
}

export function titlebarClassName(platform: string | undefined): string {
    return platform === "darwin" ? "titlebar titlebar-macos" : "titlebar";
}
