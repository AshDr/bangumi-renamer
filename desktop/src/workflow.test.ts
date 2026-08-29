import { describe, expect, it } from "vitest";

import { createTranslator } from "./i18n";
import {
    nextWorkflowPhase,
    showMetadataLanguage,
    workflowActionKeys,
    workflowStepStates,
} from "./workflow";

describe("desktop workflow state", () => {
    it("renders exactly one active phase and marks only earlier work as done", () => {
        expect(workflowStepStates("select")).toEqual([
            { active: true, done: false },
            { active: false, done: false },
            { active: false, done: false },
        ]);
        expect(workflowStepStates("review")).toEqual([
            { active: false, done: true },
            { active: true, done: false },
            { active: false, done: false },
        ]);
        expect(workflowStepStates("complete")).toEqual([
            { active: false, done: true },
            { active: false, done: true },
            { active: true, done: true },
        ]);
    });

    it("enters completion after apply and returns to review when another scan starts", () => {
        expect(nextWorkflowPhase("review", "applySucceeded")).toBe("complete");
        expect(nextWorkflowPhase("complete", "scanStarted")).toBe("review");
    });

    it("uses restart actions after completion", () => {
        expect(workflowActionKeys("complete")).toEqual({
            rematch: "workspace.rematch",
            chooseFolder: "workspace.chooseOther",
        });
        expect(workflowActionKeys("review")).toEqual({
            rematch: "workspace.rescan",
            chooseFolder: "workspace.choose",
        });
    });

    it("hides metadata language only after the workflow completes", () => {
        expect(showMetadataLanguage("complete")).toBe(false);
        expect(showMetadataLanguage("review")).toBe(true);
    });

    it("uses task-oriented workflow labels", () => {
        const t = createTranslator("zh-CN");

        expect([t("workflow.choose"), t("workflow.review"), t("workflow.apply")]).toEqual([
            "选择文件夹",
            "确认匹配",
            "重命名完成",
        ]);
    });
});
