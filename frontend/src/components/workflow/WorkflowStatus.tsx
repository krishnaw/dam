import { cn } from "@/lib/utils";
import type { WorkflowStep } from "@/types";

const statusColors: Record<string, string> = {
  pending: "bg-gray-300",
  in_review: "bg-blue-500",
  approved: "bg-green-500",
  rejected: "bg-red-500",
};

const statusRing: Record<string, string> = {
  in_review: "ring-2 ring-blue-500/30 ring-offset-2",
};

interface WorkflowStatusProps {
  steps: WorkflowStep[];
}

export function WorkflowStatus({ steps }: WorkflowStatusProps) {
  if (steps.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No workflow steps defined.</p>
    );
  }

  return (
    <div className="flex items-center gap-0">
      {steps.map((step, i) => (
        <div key={step.id} className="flex items-center">
          <div className="flex flex-col items-center gap-1">
            <div
              className={cn(
                "flex h-8 w-8 items-center justify-center rounded-full text-xs font-medium text-white",
                statusColors[step.status] ?? "bg-gray-300",
                statusRing[step.status],
                step.status === "in_review" && "animate-pulse"
              )}
            >
              {step.stepOrder}
            </div>
            <span className="max-w-[80px] truncate text-center text-[10px] text-muted-foreground">
              {step.stepType}
            </span>
            {step.reviewerName && (
              <span className="max-w-[80px] truncate text-center text-[10px] font-medium">
                {step.reviewerName}
              </span>
            )}
          </div>
          {i < steps.length - 1 && (
            <div
              className={cn(
                "mx-1 h-0.5 w-8",
                step.status === "approved" ? "bg-green-500" : "bg-gray-200"
              )}
            />
          )}
        </div>
      ))}
    </div>
  );
}
