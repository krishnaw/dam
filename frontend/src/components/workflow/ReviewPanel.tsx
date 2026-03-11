import { useState } from "react";
import { CheckCircle, XCircle, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useSubmitReview, useReviewAction } from "@/api/useWorkflow";
import type { Workflow } from "@/types";
import { toast } from "sonner";

interface ReviewPanelProps {
  assetId: string;
  workflow: Workflow | null;
}

export function ReviewPanel({ assetId, workflow }: ReviewPanelProps) {
  const [comment, setComment] = useState("");
  const submitReview = useSubmitReview();
  const reviewAction = useReviewAction();

  const currentStep = workflow?.steps.find(
    (s) => s.status === "in_review" || s.status === "pending"
  );

  const handleSubmitForReview = () => {
    submitReview.mutate(
      { assetId, comment: comment || undefined },
      {
        onSuccess: () => {
          toast.success("Submitted for review");
          setComment("");
        },
      }
    );
  };

  const handleAction = (action: "approve" | "reject") => {
    if (!workflow || !currentStep) return;
    reviewAction.mutate(
      {
        workflowId: workflow.id,
        stepId: currentStep.id,
        action,
        comment: comment || undefined,
      },
      {
        onSuccess: () => {
          toast.success(action === "approve" ? "Approved" : "Rejected");
          setComment("");
        },
      }
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Review Actions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="Add review feedback..."
          rows={3}
          className="w-full resize-none rounded-md border bg-transparent px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        />

        {!workflow || workflow.status === "draft" ? (
          <Button
            className="w-full gap-2"
            onClick={handleSubmitForReview}
            disabled={submitReview.isPending}
          >
            <Send className="h-4 w-4" />
            Submit for Review
          </Button>
        ) : currentStep?.status === "in_review" ? (
          <div className="flex gap-2">
            <Button
              className="flex-1 gap-2"
              variant="default"
              onClick={() => handleAction("approve")}
              disabled={reviewAction.isPending}
            >
              <CheckCircle className="h-4 w-4" />
              Approve
            </Button>
            <Button
              className="flex-1 gap-2"
              variant="destructive"
              onClick={() => handleAction("reject")}
              disabled={reviewAction.isPending}
            >
              <XCircle className="h-4 w-4" />
              Reject
            </Button>
          </div>
        ) : (
          <p className="text-center text-sm text-muted-foreground">
            Workflow status: {workflow.status}
          </p>
        )}

        {workflow && workflow.steps.length > 0 && (
          <div className="space-y-1 border-t pt-3">
            <h4 className="text-xs font-semibold text-muted-foreground">
              History
            </h4>
            {workflow.steps
              .filter((s) => s.status !== "pending")
              .map((step) => (
                <div
                  key={step.id}
                  className="flex items-center justify-between text-xs"
                >
                  <span>
                    {step.reviewerName ?? "System"} -{" "}
                    <span className="font-medium">{step.status}</span>
                  </span>
                  <span className="text-muted-foreground">
                    {new Date(step.createdAt).toLocaleDateString()}
                  </span>
                </div>
              ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
