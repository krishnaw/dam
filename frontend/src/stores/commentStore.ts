import { create } from "zustand";
import type { Comment } from "@/types";

interface CommentState {
  comments: Comment[];
  replyingTo: string | null;
  setComments: (comments: Comment[]) => void;
  addComment: (comment: Comment) => void;
  setReplyingTo: (id: string | null) => void;
}

export const useCommentStore = create<CommentState>((set) => ({
  comments: [],
  replyingTo: null,
  setComments: (comments) => set({ comments }),
  addComment: (comment) =>
    set((state) => ({ comments: [...state.comments, comment] })),
  setReplyingTo: (id) => set({ replyingTo: id }),
}));
