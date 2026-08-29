export type WorkflowPhase = "select" | "review" | "complete";
export type WorkflowEvent = "scanStarted" | "applySucceeded";

export interface WorkflowStepState {
    active: boolean;
    done: boolean;
}

export interface WorkflowActionKeys {
    rematch: "workspace.rematch" | "workspace.rescan";
    chooseFolder: "workspace.chooseOther" | "workspace.choose";
}

const transitions: Record<WorkflowPhase, Record<WorkflowEvent, WorkflowPhase>> = {
    select: { scanStarted: "review", applySucceeded: "complete" },
    review: { scanStarted: "review", applySucceeded: "complete" },
    complete: { scanStarted: "review", applySucceeded: "complete" },
};

export function nextWorkflowPhase(
    current: WorkflowPhase,
    event: WorkflowEvent,
): WorkflowPhase {
    return transitions[current][event];
}

export function workflowStepStates(phase: WorkflowPhase): WorkflowStepState[] {
    return [
        { active: phase === "select", done: phase !== "select" },
        { active: phase === "review", done: phase === "complete" },
        { active: phase === "complete", done: phase === "complete" },
    ];
}

export function workflowActionKeys(phase: WorkflowPhase): WorkflowActionKeys {
    return phase === "complete"
        ? { rematch: "workspace.rematch", chooseFolder: "workspace.chooseOther" }
        : { rematch: "workspace.rescan", chooseFolder: "workspace.choose" };
}

export function showMetadataLanguage(phase: WorkflowPhase): boolean {
    return phase !== "complete";
}
