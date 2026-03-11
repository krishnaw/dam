import { create } from "zustand";
import type { Workflow } from "@/types";

interface WorkflowState {
  workflow: Workflow | null;
  setWorkflow: (workflow: Workflow | null) => void;
}

export const useWorkflowStore = create<WorkflowState>((set) => ({
  workflow: null,
  setWorkflow: (workflow) => set({ workflow }),
}));
