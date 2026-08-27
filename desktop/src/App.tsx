import { AnimatePresence, motion } from "framer-motion";
import {
    AlertCircle,
    Check,
    CheckCircle2,
    ChevronRight,
    FilePenLine,
    FolderOpen,
    KeyRound,
    LoaderCircle,
    RefreshCw,
    Search,
    Settings,
    ShieldCheck,
    X,
} from "lucide-react";
import { useCallback, useEffect, useLayoutEffect, useMemo, useState } from "react";

import { desktopApi } from "./api";
import { createTranslator, supportedUiLocales } from "./i18n";
import type { Translator } from "./i18n";
import { actionableItems, rowsForMatch, summarize, titlebarClassName } from "./lib";
import { watchThemePreference } from "./theme";
import type { Candidate, DesktopSettings, PlanItem, UiLocale } from "./types";

const defaultSettings: DesktopSettings = {
    ui_language: "en-US",
    language: "en-US",
    conflict_policy: "suffix",
    theme: "system",
    has_api_key: false,
    api_key_from_environment: false,
};

type BusyState = "idle" | "scanning" | "matching" | "applying";

const statusTranslationKeys = {
    OK: "status.OK",
    unparsed: "status.unparsed",
    "no match": "status.no match",
    "no season": "status.no season",
    conflict: "status.conflict",
    error: "status.error",
} as const;

export default function App() {
    const [settings, setSettings] = useState<DesktopSettings>(defaultSettings);
    const [root, setRoot] = useState<string | null>(null);
    const [items, setItems] = useState<PlanItem[]>([]);
    const [busy, setBusy] = useState<BusyState>("idle");
    const [error, setError] = useState<string | null>(null);
    const [notice, setNotice] = useState<string | null>(null);
    const [settingsOpen, setSettingsOpen] = useState(false);
    const [matchRow, setMatchRow] = useState<PlanItem | null>(null);
    const [confirmApply, setConfirmApply] = useState(false);
    const [previewTheme, setPreviewTheme] = useState<DesktopSettings["theme"] | null>(null);
    const [previewLanguage, setPreviewLanguage] = useState<UiLocale | null>(null);

    const counts = useMemo(() => summarize(items), [items]);
    const actionable = useMemo(() => actionableItems(items), [items]);
    const uiLanguage = previewLanguage || settings.ui_language;
    const t = useMemo(() => createTranslator(uiLanguage), [uiLanguage]);

    useLayoutEffect(
        () => watchThemePreference(previewTheme || settings.theme),
        [previewTheme, settings.theme],
    );

    useEffect(() => {
        document.documentElement.lang = uiLanguage;
    }, [uiLanguage]);

    useEffect(() => {
        desktopApi
            .getSettings()
            .then((value) => {
                setSettings(value);
                if (!value.has_api_key) setSettingsOpen(true);
            })
            .catch((reason: unknown) => setError(errorText(reason)));
    }, []);

    const scanPath = useCallback(
        async (path: string) => {
            if (!settings.has_api_key) {
                setSettingsOpen(true);
                setError(t("notice.apiKeyRequired"));
                return;
            }
            setBusy("scanning");
            setError(null);
            setNotice(null);
            try {
                const result = await desktopApi.scan(path, settings);
                setRoot(result.root);
                setItems(result.items);
                setNotice(
                    result.items.length
                        ? t("notice.previewReady", { count: result.items.length })
                        : t("notice.noFiles"),
                );
            } catch (reason) {
                setError(errorText(reason));
            } finally {
                setBusy("idle");
            }
        },
        [settings, t],
    );

    useEffect(() => {
        let unlisten: (() => void) | undefined;
        import("@tauri-apps/api/webview")
            .then(({ getCurrentWebview }) =>
                getCurrentWebview().onDragDropEvent((event) => {
                    if (event.payload.type === "drop" && event.payload.paths[0]) {
                        void scanPath(event.payload.paths[0]);
                    }
                }),
            )
            .then((dispose) => {
                unlisten = dispose;
            })
            .catch(() => undefined);
        return () => unlisten?.();
    }, [scanPath]);

    async function chooseFolder() {
        try {
            const path = await desktopApi.chooseFolder(t("workspace.choose"));
            if (path) await scanPath(path);
        } catch (reason) {
            setError(errorText(reason));
        }
    }

    async function applyPlan() {
        if (!root || actionable.length === 0) return;
        setConfirmApply(false);
        setBusy("applying");
        setError(null);
        try {
            const result = await desktopApi.apply(root, actionable);
            setNotice(
                result.history_path
                    ? t("notice.renamed", { count: result.renamed, path: result.history_path })
                    : t("notice.noRename"),
            );
            await scanPath(root);
        } catch (reason) {
            setError(errorText(reason));
            setBusy("idle");
        }
    }

    async function applyCandidate(candidate: Candidate) {
        if (!matchRow?.parsed) return;
        setBusy("matching");
        setError(null);
        try {
            const related = rowsForMatch(items, matchRow.parsed.title);
            const result = await desktopApi.rebuild(
                related.map((item) => item.source),
                candidate.tmdb_id,
                settings,
            );
            const replacements = new Map(result.items.map((item) => [item.source, item]));
            setItems((current) => current.map((item) => replacements.get(item.source) || item));
            setMatchRow(null);
            setNotice(t("notice.matched", { count: related.length, name: candidate.name }));
        } catch (reason) {
            setError(errorText(reason));
        } finally {
            setBusy("idle");
        }
    }

    return (
        <div className="app-shell">
            <header
                className={titlebarClassName(import.meta.env.TAURI_ENV_PLATFORM)}
                data-tauri-drag-region
            >
                <div className="brand" data-tauri-drag-region>
                    <div className="brand-mark"><FilePenLine size={18} /></div>
                    <span>Bangumi Renamer</span>
                    <span className="version-pill">0.1</span>
                </div>
                <div className="titlebar-actions">
                    <button className="icon-button" onClick={() => setSettingsOpen(true)} title={t("title.settings")}>
                        <Settings size={18} />
                    </button>
                </div>
            </header>

            <main className="workspace">
                <aside className="sidebar">
                    <div className="sidebar-copy">
                        <span className="eyebrow">{t("sidebar.eyebrow")}</span>
                        <h1>{t("sidebar.heading")}</h1>
                        <p>{t("sidebar.description")}</p>
                    </div>

                    <nav className="steps" aria-label={t("workflow.label")}>
                        <Step number="01" label={t("workflow.choose")} active={!root} done={Boolean(root)} />
                        <Step number="02" label={t("workflow.review")} active={Boolean(root)} done={items.length > 0} />
                        <Step number="03" label={t("workflow.apply")} active={actionable.length > 0} done={false} />
                    </nav>

                    <div className="safety-card">
                        <ShieldCheck size={20} />
                        <div>
                            <strong>{t("safety.title")}</strong>
                            <span>{t("safety.description")}</span>
                        </div>
                    </div>
                </aside>

                <section className="content">
                    <div className="content-header">
                        <div>
                            <span className="eyebrow">{t("workspace.eyebrow")}</span>
                            <h2>{root ? lastPathPart(root) : t("workspace.select")}</h2>
                            <p className="path-label">{root || t("workspace.hint")}</p>
                        </div>
                        <div className="header-actions">
                            {root && (
                                <button className="button secondary" disabled={busy !== "idle"} onClick={() => void scanPath(root)}>
                                    <RefreshCw size={16} /> {t("workspace.rescan")}
                                </button>
                            )}
                            <button className="button primary" disabled={busy !== "idle"} onClick={() => void chooseFolder()}>
                                <FolderOpen size={17} /> {t("workspace.choose")}
                            </button>
                        </div>
                    </div>

                    <AnimatePresence mode="wait">
                        {!root ? (
                            <motion.button
                                key="empty"
                                className="drop-zone"
                                onClick={() => void chooseFolder()}
                                initial={{ opacity: 0, y: 12 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0 }}
                            >
                                <span className="drop-icon"><FolderOpen size={28} /></span>
                                <strong>{t("drop.title")}</strong>
                                <span>{t("drop.description")}</span>
                                <em>{t("drop.formats")}</em>
                            </motion.button>
                        ) : (
                            <motion.div key="plan" className="plan-area" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                                <SummaryStrip total={items.length} counts={counts} actionable={actionable.length} t={t} />
                                <PlanTable items={items} busy={busy !== "idle"} onPickMatch={setMatchRow} uiLocale={uiLanguage} />
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {(error || notice || busy !== "idle") && (
                        <StatusBanner busy={busy} error={error} notice={notice} onClose={() => { setError(null); setNotice(null); }} t={t} />
                    )}
                </section>
            </main>

            <footer className="apply-bar">
                <div>
                    <span className={`api-dot ${settings.has_api_key ? "ready" : ""}`} />
                    {settings.has_api_key ? t("footer.connected") : t("footer.keyRequired")}
                    {root && <><span className="footer-separator" />{t("footer.previewCount", { count: items.length })}</>}
                </div>
                <button
                    className="button apply"
                    disabled={!root || actionable.length === 0 || busy !== "idle"}
                    onClick={() => setConfirmApply(true)}
                >
                    <Check size={17} /> {actionable.length === 1
                        ? t("footer.applyOne")
                        : t("footer.apply", { count: actionable.length || "" })}
                </button>
            </footer>

            <AnimatePresence>
                {settingsOpen && (
                    <SettingsModal
                        settings={settings}
                        onClose={() => { setPreviewTheme(null); setPreviewLanguage(null); setSettingsOpen(false); }}
                        onSaved={(value) => { setSettings(value); setPreviewTheme(null); setPreviewLanguage(null); setSettingsOpen(false); setNotice(createTranslator(value.ui_language)("notice.settingsSaved")); }}
                        onError={(message) => setError(message)}
                        onThemePreview={setPreviewTheme}
                        onLanguagePreview={setPreviewLanguage}
                    />
                )}
                {matchRow && (
                    <CandidateModal
                        row={matchRow}
                        settings={settings}
                        onClose={() => setMatchRow(null)}
                        onSelect={(candidate) => void applyCandidate(candidate)}
                        t={t}
                    />
                )}
                {confirmApply && (
                    <ConfirmModal count={actionable.length} onCancel={() => setConfirmApply(false)} onConfirm={() => void applyPlan()} t={t} />
                )}
            </AnimatePresence>
        </div>
    );
}

function Step({ number, label, active, done }: { number: string; label: string; active: boolean; done: boolean }) {
    return (
        <div className={`step ${active ? "active" : ""} ${done ? "done" : ""}`}>
            <span>{done ? <Check size={14} /> : number}</span>
            <strong>{label}</strong>
            <ChevronRight size={15} />
        </div>
    );
}

function SummaryStrip({ total, counts, actionable, t }: { total: number; counts: Record<string, number>; actionable: number; t: Translator }) {
    return (
        <div className="summary-strip">
            <div><span>{t("summary.total")}</span><strong>{total}</strong></div>
            <div><span>{t("summary.ready")}</span><strong className="green">{counts.OK || 0}</strong></div>
            <div><span>{t("summary.review")}</span><strong className="amber">{total - (counts.OK || 0)}</strong></div>
            <div><span>{t("summary.rename")}</span><strong>{actionable}</strong></div>
        </div>
    );
}

function PlanText({ value, className, fallback = "-" }: { value: string | null; className?: string; fallback?: string }) {
    return <strong className={className} title={value || undefined}>{value || fallback}</strong>;
}

export function PlanTable({ items, busy, onPickMatch, uiLocale = "en-US" }: { items: PlanItem[]; busy: boolean; onPickMatch: (item: PlanItem) => void; uiLocale?: UiLocale }) {
    const t = createTranslator(uiLocale);
    if (!items.length) {
        return <div className="empty-table"><Search size={28} /><strong>{t("table.empty")}</strong><span>{t("table.emptyHint")}</span></div>;
    }
    return (
        <div className="table-wrap">
            <table>
                <thead><tr><th>{t("table.source")}</th><th>{t("table.planned")}</th><th>{t("table.match")}</th><th>{t("table.status")}</th><th /></tr></thead>
                <tbody>
                    {items.map((item, index) => (
                        <motion.tr key={item.source} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: Math.min(index * 0.025, 0.3) }}>
                            <td><div className="file-cell"><span>{index + 1}</span><div><PlanText value={item.source_name} /><small>{item.parsed ? `S${pad(item.parsed.season)} E${pad(item.parsed.episode)}` : t("table.unparsed")}</small></div></div></td>
                            <td><PlanText className="target-name" value={item.target_name} />{item.detail && <small className="row-detail">{item.detail}</small>}</td>
                            <td>{item.match ? <div className="match-cell"><PlanText value={item.match.name} /><small>{t("table.confidence", { value: Math.round(item.match.confidence) })}</small></div> : <span className="muted">{t("table.unmatched")}</span>}</td>
                            <td><StatusPill status={item.status} t={t} /></td>
                            <td><button className="row-action" disabled={busy || !item.parsed} onClick={() => onPickMatch(item)} title={t("table.pickMatch")}><Search size={15} /></button></td>
                        </motion.tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

function StatusPill({ status, t }: { status: string; t: Translator }) {
    const ok = status === "OK";
    const translationKey = statusTranslationKeys[status as keyof typeof statusTranslationKeys];
    const label = translationKey ? t(translationKey) : status;
    return <span className={`status-pill ${ok ? "ok" : "warn"}`}>{ok ? <CheckCircle2 size={13} /> : <AlertCircle size={13} />}{label}</span>;
}

function StatusBanner({ busy, error, notice, onClose, t }: { busy: BusyState; error: string | null; notice: string | null; onClose: () => void; t: Translator }) {
    const labels: Record<BusyState, string> = { idle: "", scanning: t("busy.scanning"), matching: t("busy.matching"), applying: t("busy.applying") };
    return (
        <motion.div className={`status-banner ${error ? "error" : ""}`} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
            {busy !== "idle" ? <LoaderCircle className="spin" size={17} /> : error ? <AlertCircle size={17} /> : <CheckCircle2 size={17} />}
            <span>{error || labels[busy] || notice}</span>
            {busy === "idle" && <button onClick={onClose} title={t("common.close")}><X size={14} /></button>}
        </motion.div>
    );
}

function ModalFrame({ children, onClose, title, subtitle, closeLabel }: { children: React.ReactNode; onClose: () => void; title: string; subtitle: string; closeLabel: string }) {
    return (
        <motion.div className="modal-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onMouseDown={onClose}>
            <motion.section className="modal" initial={{ opacity: 0, scale: 0.96, y: 14 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.97 }} onMouseDown={(event) => event.stopPropagation()}>
                <div className="modal-header"><div><h3>{title}</h3><p>{subtitle}</p></div><button className="icon-button" onClick={onClose} title={closeLabel}><X size={18} /></button></div>
                {children}
            </motion.section>
        </motion.div>
    );
}

interface SettingsModalProps {
    settings: DesktopSettings;
    onClose: () => void;
    onSaved: (value: DesktopSettings) => void;
    onError: (message: string) => void;
    onThemePreview: (theme: DesktopSettings["theme"]) => void;
    onLanguagePreview: (language: UiLocale) => void;
}

export function SettingsModal({
    settings,
    onClose,
    onSaved,
    onError,
    onThemePreview,
    onLanguagePreview,
}: SettingsModalProps) {
    const [apiKey, setApiKey] = useState("");
    const [language, setLanguage] = useState(settings.language);
    const [uiLanguage, setUiLanguage] = useState(settings.ui_language);
    const [policy, setPolicy] = useState(settings.conflict_policy);
    const [theme, setTheme] = useState(settings.theme);
    const [saving, setSaving] = useState(false);
    const t = createTranslator(uiLanguage);

    function changeTheme(value: DesktopSettings["theme"]) {
        setTheme(value);
        onThemePreview(value);
    }

    function changeLanguage(value: UiLocale) {
        setUiLanguage(value);
        onLanguagePreview(value);
    }

    async function save() {
        setSaving(true);
        try {
            const value = await desktopApi.saveSettings({ api_key: apiKey, ui_language: uiLanguage, language, conflict_policy: policy, theme });
            onSaved(value);
        } catch (reason) {
            onError(errorText(reason));
            setSaving(false);
        }
    }

    return (
        <ModalFrame title={t("settings.title")} subtitle={t("settings.subtitle")} onClose={onClose} closeLabel={t("common.close")}>
            <div className="form-stack">
                <label><span>{t("settings.apiKey")}</span><div className="input-with-icon"><KeyRound size={16} /><input type="password" value={apiKey} onChange={(event) => setApiKey(event.target.value)} placeholder={settings.has_api_key ? t("settings.savedKey") : t("settings.newKey")} /></div>{settings.api_key_from_environment && <small>{t("settings.environmentKey")}</small>}</label>
                <label>
                    <span>{t("settings.uiLanguage")}</span>
                    <select value={uiLanguage} onChange={(event) => changeLanguage(event.target.value as UiLocale)}>
                        {supportedUiLocales.map((locale) => (
                            <option key={locale} value={locale}>{t(`locale.${locale}`)}</option>
                        ))}
                    </select>
                </label>
                <label><span>{t("settings.metadataLanguage")}</span><input value={language} onChange={(event) => setLanguage(event.target.value)} placeholder={t("settings.metadataPlaceholder")} /></label>
                <label><span>{t("settings.conflict")}</span><select value={policy} onChange={(event) => setPolicy(event.target.value as DesktopSettings["conflict_policy"])}><option value="suffix">{t("settings.conflictSuffix")}</option><option value="skip">{t("settings.conflictSkip")}</option><option value="overwrite">{t("settings.conflictOverwrite")}</option></select></label>
                <label>
                    <span>{t("settings.appearance")}</span>
                    <select
                        value={theme}
                        onChange={(event) => changeTheme(event.target.value as DesktopSettings["theme"])}
                    >
                        <option value="system">{t("settings.themeSystem")}</option>
                        <option value="light">{t("settings.themeLight")}</option>
                        <option value="dark">{t("settings.themeDark")}</option>
                    </select>
                </label>
            </div>
            <div className="modal-actions"><button className="button secondary" onClick={onClose}>{t("common.cancel")}</button><button className="button primary" disabled={saving} onClick={() => void save()}>{saving && <LoaderCircle className="spin" size={15} />} {t("settings.save")}</button></div>
        </ModalFrame>
    );
}

function CandidateModal({ row, settings, onClose, onSelect, t }: { row: PlanItem; settings: DesktopSettings; onClose: () => void; onSelect: (candidate: Candidate) => void; t: Translator }) {
    const [candidates, setCandidates] = useState<Candidate[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    useEffect(() => {
        if (!row.parsed) return;
        desktopApi.candidates(row.parsed.title, settings).then((value) => setCandidates(value.candidates)).catch((reason: unknown) => setError(errorText(reason))).finally(() => setLoading(false));
    }, [row, settings]);
    return (
        <ModalFrame title={t("candidate.title")} subtitle={row.parsed?.title || row.source_name} onClose={onClose} closeLabel={t("common.close")}>
            <div className="candidate-list">
                {loading && <div className="modal-state"><LoaderCircle className="spin" /><span>{t("candidate.searching")}</span></div>}
                {error && <div className="modal-state error-text"><AlertCircle /><span>{error}</span></div>}
                {!loading && !error && !candidates.length && <div className="modal-state"><Search /><span>{t("candidate.empty")}</span></div>}
                {candidates.map((candidate) => (
                    <button key={candidate.tmdb_id} className="candidate" onClick={() => onSelect(candidate)}>
                        <div><strong>{candidate.name}</strong><span>{candidate.original_name || t("candidate.noOriginalTitle")}{candidate.first_air_year ? ` - ${candidate.first_air_year}` : ""}</span><p>{candidate.overview || t("candidate.noOverview")}</p></div>
                        <em>{Math.round(candidate.confidence)}%</em>
                    </button>
                ))}
            </div>
        </ModalFrame>
    );
}

function ConfirmModal({ count, onCancel, onConfirm, t }: { count: number; onCancel: () => void; onConfirm: () => void; t: Translator }) {
    return (
        <ModalFrame title={t("confirm.title")} subtitle={t("confirm.subtitle")} onClose={onCancel} closeLabel={t("common.close")}>
            <div className="confirm-copy"><span><ShieldCheck size={24} /></span><p>{t("confirm.description", { count })} <code>.bangumi-renamer/history/</code>.</p></div>
            <div className="modal-actions"><button className="button secondary" onClick={onCancel}>{t("confirm.keepReviewing")}</button><button className="button apply" onClick={onConfirm}><Check size={16} /> {t("confirm.applyNow")}</button></div>
        </ModalFrame>
    );
}

function errorText(reason: unknown): string {
    return reason instanceof Error ? reason.message : String(reason);
}

function lastPathPart(path: string): string {
    return path.split(/[\\/]/).filter(Boolean).at(-1) || path;
}

function pad(value: number): string {
    return String(value).padStart(2, "0");
}
