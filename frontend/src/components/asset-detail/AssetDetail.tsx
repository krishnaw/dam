import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Download, FileText, MessageSquare, GitBranch } from "lucide-react";
import { Button } from "@/components/ui/button";
import { MetadataPanel } from "./MetadataPanel";
import { AITags } from "./AITags";
import { ShareDialog } from "@/components/sharing/ShareDialog";
import { VideoPlayer } from "@/components/media/VideoPlayer";
import { AudioPlayer } from "@/components/media/AudioPlayer";
import { ImageEditor } from "@/components/media/ImageEditor";
import { DocumentViewer } from "@/components/media/DocumentViewer";
import { CommentThread } from "@/components/comments/CommentThread";
import { CommentInput } from "@/components/comments/CommentInput";
import { WorkflowStatus } from "@/components/workflow/WorkflowStatus";
import { ReviewPanel } from "@/components/workflow/ReviewPanel";
import { useComments, useAddComment } from "@/api/useComments";
import { useAssetWorkflow } from "@/api/useWorkflow";
import { useCommentStore } from "@/stores/commentStore";
import { cn } from "@/lib/utils";
import type { Asset } from "@/types";

type DetailTab = "details" | "comments" | "workflow";

interface AssetDetailProps {
  asset: Asset;
}

export function AssetDetail({ asset }: AssetDetailProps) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<DetailTab>("details");
  const { replyingTo, setReplyingTo } = useCommentStore();
  const { data: comments } = useComments(asset.id);
  const { data: workflow } = useAssetWorkflow(asset.id);
  const addComment = useAddComment();

  const isImage = asset.mime_type.startsWith("image/");
  const isVideo = asset.mime_type.startsWith("video/");
  const isAudio = asset.mime_type.startsWith("audio/");
  const isPdf = asset.mime_type === "application/pdf";
  const isDocument =
    isPdf ||
    asset.mime_type.includes("word") ||
    asset.mime_type.includes("spreadsheet") ||
    asset.mime_type.includes("presentation");

  const handleAddComment = (content: string, parentId?: string | null) => {
    addComment.mutate({
      assetId: asset.id,
      content,
      parentId: parentId ?? null,
    });
  };

  const tabs: { id: DetailTab; label: string; icon: React.ElementType }[] = [
    { id: "details", label: "Details", icon: FileText },
    { id: "comments", label: "Comments", icon: MessageSquare },
    { id: "workflow", label: "Workflow", icon: GitBranch },
  ];

  return (
    <div className="flex flex-col gap-6 lg:flex-row">
      <div className="flex-1 space-y-4">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-xl font-bold truncate">
            {asset.original_filename}
          </h1>
          <div className="ml-auto flex items-center gap-2">
            <ShareDialog assetId={asset.id} />
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open(`/api/assets/${asset.id}/download`)}
            >
              <Download className="mr-2 h-4 w-4" />
              Download
            </Button>
          </div>
        </div>

        <div className="flex items-center justify-center rounded-lg border bg-muted/30 p-4 min-h-[400px]">
          {isImage && !isVideo && (
            <ImageEditor
              assetId={asset.id}
              originalWidth={asset.width}
              originalHeight={asset.height}
            />
          )}
          {isVideo && (
            <VideoPlayer
              src={`/api/assets/${asset.id}/file`}
              poster={asset.thumbnail_path ? `/api/assets/${asset.id}/thumbnail` : undefined}
            />
          )}
          {isAudio && <AudioPlayer src={`/api/assets/${asset.id}/file`} />}
          {isDocument && (
            <DocumentViewer
              assetId={asset.id}
              totalPages={(asset.metadata?.page_count as number) ?? 1}
            />
          )}
          {!isImage && !isVideo && !isAudio && !isDocument && (
            <div className="text-center text-muted-foreground">
              <p className="text-lg font-medium">Preview not available</p>
              <p className="text-sm">Download the file to view it</p>
            </div>
          )}
        </div>
      </div>

      <aside className="w-full lg:w-80 shrink-0">
        <div className="rounded-lg border bg-card">
          <div className="flex border-b">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={cn(
                  "flex flex-1 items-center justify-center gap-1.5 px-3 py-2.5 text-sm font-medium transition-colors",
                  activeTab === id
                    ? "border-b-2 border-primary text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            ))}
          </div>

          <div className="p-4">
            {activeTab === "details" && (
              <div className="space-y-4">
                <MetadataPanel asset={asset} />
                <AITags asset={asset} />
              </div>
            )}

            {activeTab === "comments" && (
              <div className="space-y-4">
                <CommentInput
                  placeholder="Add a comment..."
                  onSubmit={(content) => handleAddComment(content)}
                />
                <CommentThread
                  comments={comments ?? []}
                  replyingTo={replyingTo}
                  onReply={setReplyingTo}
                  onSubmitReply={(content, parentId) =>
                    handleAddComment(content, parentId)
                  }
                />
              </div>
            )}

            {activeTab === "workflow" && (
              <div className="space-y-4">
                {workflow?.steps && <WorkflowStatus steps={workflow.steps} />}
                <ReviewPanel
                  assetId={asset.id}
                  workflow={workflow ?? null}
                />
              </div>
            )}
          </div>
        </div>
      </aside>
    </div>
  );
}
