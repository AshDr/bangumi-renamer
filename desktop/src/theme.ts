import type { ThemePreference } from "./types";

export type ResolvedTheme = "light" | "dark";

export function resolveTheme(
    preference: ThemePreference,
    systemPrefersDark: boolean,
): ResolvedTheme {
    if (preference === "system") return systemPrefersDark ? "dark" : "light";
    return preference;
}

export function watchThemePreference(preference: ThemePreference): () => void {
    const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");
    const apply = () => {
        const resolved = resolveTheme(preference, systemTheme.matches);
        document.documentElement.dataset.theme = resolved;
        document.documentElement.style.colorScheme = resolved;
    };

    apply();
    if (preference === "system") systemTheme.addEventListener("change", apply);
    return () => systemTheme.removeEventListener("change", apply);
}
