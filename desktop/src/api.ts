import { invoke } from "@tauri-apps/api/core";
import { open } from "@tauri-apps/plugin-dialog";

import type {
    ApplyResult,
    Candidate,
    ConnectionTestResult,
    DesktopSettings,
    MetadataLanguage,
    PlanItem,
    ScanResult,
} from "./types";

const inTauri = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

interface BridgeEnvelope<T> {
    ok: boolean;
    data?: T;
    error?: string;
}

async function bridge<T>(command: string, payload: Record<string, unknown> = {}): Promise<T> {
    if (!inTauri) return previewBridge(command, payload) as T;
    const response = await invoke<BridgeEnvelope<T>>("execute_bridge", { command, payload });
    if (!response.ok || response.data === undefined) {
        throw new Error(response.error || `Desktop command failed: ${command}`);
    }
    return response.data;
}

export const desktopApi = {
    getSettings: () => bridge<DesktopSettings>("settings.get"),
    saveSettings: (payload: Record<string, unknown>) =>
        bridge<DesktopSettings>("settings.save", payload),
    testConnection: (
        metadataProvider: DesktopSettings["metadata_provider"],
        credentials: Record<string, string>,
        language: MetadataLanguage,
    ) =>
        bridge<ConnectionTestResult>("settings.test_connection", {
            metadata_provider: metadataProvider,
            language,
            ...credentials,
        }),
    scan: (path: string, settings: DesktopSettings, language: MetadataLanguage) =>
        bridge<ScanResult>("plan.scan", {
            path,
            metadata_provider: settings.metadata_provider,
            language,
            conflict_policy: settings.conflict_policy,
        }),
    candidates: (query: string, settings: DesktopSettings, language: MetadataLanguage) =>
        bridge<{ candidates: Candidate[] }>("plan.candidates", {
            query,
            metadata_provider: settings.metadata_provider,
            language,
        }),
    rebuild: (
        sources: string[],
        providerId: number,
        settings: DesktopSettings,
        language: MetadataLanguage,
    ) =>
        bridge<{ items: PlanItem[] }>("plan.rebuild", {
            sources,
            provider_id: providerId,
            metadata_provider: settings.metadata_provider,
            language,
            conflict_policy: settings.conflict_policy,
        }),
    apply: (root: string, items: PlanItem[]) =>
        bridge<ApplyResult>("plan.apply", { root, items }),
    chooseFolder: async (title: string) => {
        if (!inTauri) return "/Preview/Anime Library";
        const selected = await open({ directory: true, multiple: false, title });
        return typeof selected === "string" ? selected : null;
    },
};

function previewBridge(command: string, payload: Record<string, unknown>): unknown {
    const settings: DesktopSettings = {
        metadata_provider: (payload.metadata_provider as DesktopSettings["metadata_provider"]) || "thetvdb",
        ui_language: (payload.ui_language as DesktopSettings["ui_language"]) || "en-US",
        conflict_policy: (payload.conflict_policy as DesktopSettings["conflict_policy"]) || "suffix",
        theme: (payload.theme as DesktopSettings["theme"]) || "system",
        has_api_key: true,
        api_key_from_environment: false,
        has_thetvdb_api_key: true,
        thetvdb_api_key_from_environment: false,
        has_thetvdb_pin: false,
        thetvdb_pin_from_environment: false,
        has_tmdb_api_key: true,
        tmdb_api_key_from_environment: false,
    };
    if (command === "settings.get" || command === "settings.save") return settings;
    if (command === "settings.test_connection") {
        return { provider: payload.metadata_provider, connected: true };
    }
    if (command === "plan.scan") return { root: String(payload.path), items: previewItems };
    if (command === "plan.candidates") {
        return {
            candidates: [
                {
                    tmdb_id: 209867,
                    name: "Frieren: Beyond Journey's End",
                    original_name: "葬送のフリーレン",
                    first_air_year: 2023,
                    overview: "After the party defeats the Demon King, an elven mage learns what a brief human life means.",
                    confidence: 97,
                    reason: "preview",
                },
                {
                    tmdb_id: 224372,
                    name: "Frieren Mini Anime",
                    original_name: "葬送のフリーレン ミニアニメ",
                    first_air_year: 2023,
                    overview: "Short companion episodes.",
                    confidence: 82,
                    reason: "preview",
                },
            ],
        };
    }
    if (command === "plan.rebuild") return { items: previewItems.slice(0, 1) };
    if (command === "plan.apply") {
        const items = payload.items as PlanItem[];
        return { renamed: items.length, renames: [], history_path: "/Preview/.bangumi-renamer/history/demo.json" };
    }
    throw new Error(`Unsupported preview command: ${command}`);
}

const previewItems: PlanItem[] = [
    {
        source: "/Preview/Anime Library/[SubsPlease] Frieren - 01 (1080p).mkv",
        source_name: "[SubsPlease] Frieren - 01 (1080p).mkv",
        target: "/Preview/Anime Library/Frieren-S01E01.mkv",
        target_name: "Frieren-S01E01.mkv",
        status: "OK",
        detail: "",
        parsed: { title: "Frieren", season: 1, episode: 1, year: null },
        match: { tmdb_id: 209867, name: "Frieren: Beyond Journey's End", confidence: 97, reason: "preview" },
    },
    {
        source: "/Preview/Anime Library/[SubsPlease] Frieren - 02 (1080p).mkv",
        source_name: "[SubsPlease] Frieren - 02 (1080p).mkv",
        target: "/Preview/Anime Library/Frieren-S01E02.mkv",
        target_name: "Frieren-S01E02.mkv",
        status: "OK",
        detail: "",
        parsed: { title: "Frieren", season: 1, episode: 2, year: null },
        match: { tmdb_id: 209867, name: "Frieren: Beyond Journey's End", confidence: 97, reason: "preview" },
    },
    {
        source: "/Preview/Anime Library/Mystery Show 2nd Season - 05.mkv",
        source_name: "Mystery Show 2nd Season - 05.mkv",
        target: null,
        target_name: null,
        status: "no season",
        detail: "Season 2 was not found on TheTVDB. Choose another match.",
        parsed: { title: "Mystery Show 2nd Season", season: 2, episode: 5, year: null },
        match: { tmdb_id: 95479, name: "Mystery Show", confidence: 89, reason: "preview" },
    },
];
