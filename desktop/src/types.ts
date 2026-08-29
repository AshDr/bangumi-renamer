export type ConflictPolicy = "skip" | "suffix" | "overwrite";
export type ThemePreference = "system" | "light" | "dark";
export type UiLocale = "zh-CN" | "zh-TW" | "en-US" | "ja-JP";
export type MetadataLanguage = UiLocale;
export type MetadataProvider = "thetvdb" | "tmdb";

export interface DesktopSettings {
    metadata_provider: MetadataProvider;
    ui_language: UiLocale;
    conflict_policy: ConflictPolicy;
    theme: ThemePreference;
    has_api_key: boolean;
    api_key_from_environment: boolean;
    has_thetvdb_api_key: boolean;
    thetvdb_api_key_from_environment: boolean;
    has_thetvdb_pin: boolean;
    thetvdb_pin_from_environment: boolean;
    has_tmdb_api_key: boolean;
    tmdb_api_key_from_environment: boolean;
}

export interface ParsedEpisode {
    title: string;
    season: number;
    episode: number;
    year: number | null;
}

export interface MatchResult {
    tmdb_id: number;
    name: string;
    confidence: number;
    reason: string;
}

export interface PlanItem {
    source: string;
    source_name: string;
    target: string | null;
    target_name: string | null;
    status: string;
    detail: string;
    parsed: ParsedEpisode | null;
    match: MatchResult | null;
}

export interface Candidate extends MatchResult {
    original_name: string;
    first_air_year: number | null;
    overview: string;
}

export interface ScanResult {
    root: string;
    items: PlanItem[];
}

export interface ApplyResult {
    renamed: number;
    renames: Array<{ source: string; target: string }>;
    history_path: string | null;
}
