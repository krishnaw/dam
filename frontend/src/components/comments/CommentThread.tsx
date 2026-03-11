import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Reply } from "lucide-react";
import { CommentInput } from "./CommentInput";
import type { Comment } from "@/types";

function formatTimeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function highlightMentions(text: string): React.ReactNode[] {
  const parts = text.split(/(@\w+)/g);
  return parts.map((part, i) =>
    part.startsWith("@") ? (
      <span key={i} className="font-semibold text-primary">
        {part}
      </span>
    ) : (
      <span key={i}>{part}</span>
    )
  );
}

interface CommentItemProps {
  comment: Comment;
  replyingTo: string | null;
  onReply: (id: string | null) => void;
  onSubmitReply: (content: string, parentId: string) => void;
  depth?: number;
}

function CommentItem({
  comment,
  replyingTo,
  onReply,
  onSubmitReply,
  depth = 0,
}: CommentItemProps) {
  const maxDepth = 4;
  return (
    <div className={depth > 0 ? "ml-6 border-l pl-4" : ""}>
      <div className="flex gap-3 py-2">
        <Avatar className="h-7 w-7 shrink-0">
          <AvatarFallback className="text-xs">
            {comment.userName?.charAt(0)?.toUpperCase() ?? "U"}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">
              {comment.userName ?? "User"}
            </span>
            <span className="text-xs text-muted-foreground">
              {formatTimeAgo(comment.createdAt)}
            </span>
          </div>
          <p className="mt-0.5 text-sm">{highlightMentions(comment.content)}</p>
          <Button
            variant="ghost"
            size="sm"
            className="mt-1 h-6 gap-1 px-2 text-xs text-muted-foreground"
            onClick={() => onReply(replyingTo === comment.id ? null : comment.id)}
          >
            <Reply className="h-3 w-3" />
            Reply
          </Button>
          {replyingTo === comment.id && (
            <div className="mt-2">
              <CommentInput
                placeholder={`Reply to ${comment.userName ?? "User"}...`}
                onSubmit={(content) => onSubmitReply(content, comment.id)}
                onCancel={() => onReply(null)}
                autoFocus
              />
            </div>
          )}
        </div>
      </div>
      {comment.replies &&
        depth < maxDepth &&
        comment.replies.map((reply) => (
          <CommentItem
            key={reply.id}
            comment={reply}
            replyingTo={replyingTo}
            onReply={onReply}
            onSubmitReply={onSubmitReply}
            depth={depth + 1}
          />
        ))}
    </div>
  );
}

interface CommentThreadProps {
  comments: Comment[];
  replyingTo: string | null;
  onReply: (id: string | null) => void;
  onSubmitReply: (content: string, parentId: string) => void;
}

export function CommentThread({
  comments,
  replyingTo,
  onReply,
  onSubmitReply,
}: CommentThreadProps) {
  if (comments.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        No comments yet. Start the conversation.
      </p>
    );
  }

  return (
    <div className="divide-y">
      {comments.map((comment) => (
        <CommentItem
          key={comment.id}
          comment={comment}
          replyingTo={replyingTo}
          onReply={onReply}
          onSubmitReply={onSubmitReply}
        />
      ))}
    </div>
  );
}
