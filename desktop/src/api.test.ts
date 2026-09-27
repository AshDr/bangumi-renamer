import { afterEach, describe, expect, it, vi } from "vitest";

const invoke = vi.hoisted(() => vi.fn());
vi.mock("@tauri-apps/api/core", () => ({ invoke }));

afterEach(() => {
    vi.unstubAllGlobals();
    vi.resetModules();
    invoke.mockReset();
});

describe("manual scan requests", () => {
    it("sends explicit naming inputs even when no API credential is configured", async () => {
        vi.stubGlobal("window", { __TAURI_INTERNALS__: {} });
        const { desktopApi } = await import("./api");
        invoke.mockResolvedValueOnce({ ok: true, data: {
            metadata_provider: "tmdb", conflict_policy: "skip", has_api_key: false,
        } });
        const settings = await desktopApi.getSettings();
        invoke.mockResolvedValueOnce({ ok: true, data: { root: "/shows", items: [] } });
        await desktopApi.scan("/shows", settings, "en-US", { title: "Custom", season: 0 });
        expect(invoke).toHaveBeenLastCalledWith("execute_bridge", {
            command: "plan.scan", payload: {
                path: "/shows", metadata_provider: "tmdb", language: "en-US",
                conflict_policy: "skip", manual: { title: "Custom", season: 0 },
            },
        });
    });
});
