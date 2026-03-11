import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore } from "../authStore";
import { useAssetStore } from "../assetStore";
import { useSearchStore } from "../searchStore";
import { useCommentStore } from "../commentStore";
import { useWorkflowStore } from "../workflowStore";
import type { Comment, Workflow, WorkflowStep } from "@/types";

// ---------------------------------------------------------------------------
// authStore
// ---------------------------------------------------------------------------
describe("authStore", () => {
  beforeEach(() => {
    localStorage.clear();
    useAuthStore.setState({ token: null, user: null });
  });

  it("has null token and user as initial state when localStorage is empty", () => {
    const { token, user } = useAuthStore.getState();
    expect(token).toBeNull();
    expect(user).toBeNull();
  });

  it("reads token from localStorage on initialisation", () => {
    localStorage.setItem("dam_token", "pre-existing-token");
    // Re-create the store initial state the same way the store does it
    useAuthStore.setState({ token: localStorage.getItem("dam_token"), user: null });
    expect(useAuthStore.getState().token).toBe("pre-existing-token");
  });

  it("setAuth stores token in localStorage and updates state", () => {
    const user = { id: "u1", email: "alice@example.com", role: "editor", fullName: "Alice" };
    useAuthStore.getState().setAuth("tok123", user);

    expect(localStorage.getItem("dam_token")).toBe("tok123");
    const state = useAuthStore.getState();
    expect(state.token).toBe("tok123");
    expect(state.user).toEqual(user);
  });

  it("setAuth overwrites a previous token", () => {
    const user = { id: "u2", email: "bob@example.com", role: "viewer", fullName: "Bob" };
    useAuthStore.getState().setAuth("old-tok", user);
    useAuthStore.getState().setAuth("new-tok", { ...user, email: "bob2@example.com" });

    expect(localStorage.getItem("dam_token")).toBe("new-tok");
    expect(useAuthStore.getState().token).toBe("new-tok");
    expect(useAuthStore.getState().user?.email).toBe("bob2@example.com");
  });

  it("logout removes token from localStorage and resets state to null", () => {
    const user = { id: "u3", email: "carol@example.com", role: "admin", fullName: "Carol" };
    useAuthStore.getState().setAuth("tok-xyz", user);

    useAuthStore.getState().logout();

    expect(localStorage.getItem("dam_token")).toBeNull();
    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.user).toBeNull();
  });

  it("logout is safe when already logged out", () => {
    useAuthStore.getState().logout(); // should not throw
    expect(useAuthStore.getState().token).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// assetStore
// ---------------------------------------------------------------------------
describe("assetStore", () => {
  beforeEach(() => {
    useAssetStore.setState({ selectedAssets: new Set(), viewMode: "grid" });
  });

  it("starts with an empty selection and grid view mode", () => {
    const { selectedAssets, viewMode } = useAssetStore.getState();
    expect(selectedAssets.size).toBe(0);
    expect(viewMode).toBe("grid");
  });

  it("toggleAsset adds an id that is not yet selected", () => {
    useAssetStore.getState().toggleAsset("asset-1");
    expect(useAssetStore.getState().selectedAssets.has("asset-1")).toBe(true);
  });

  it("toggleAsset removes an id that is already selected", () => {
    useAssetStore.getState().toggleAsset("asset-1");
    useAssetStore.getState().toggleAsset("asset-1");
    expect(useAssetStore.getState().selectedAssets.has("asset-1")).toBe(false);
  });

  it("toggleAsset handles multiple distinct ids independently", () => {
    useAssetStore.getState().toggleAsset("asset-1");
    useAssetStore.getState().toggleAsset("asset-2");
    const { selectedAssets } = useAssetStore.getState();
    expect(selectedAssets.has("asset-1")).toBe(true);
    expect(selectedAssets.has("asset-2")).toBe(true);
    expect(selectedAssets.size).toBe(2);
  });

  it("selectAll replaces the selection with the provided ids", () => {
    useAssetStore.getState().toggleAsset("old-asset");
    useAssetStore.getState().selectAll(["a", "b", "c"]);
    const { selectedAssets } = useAssetStore.getState();
    expect(selectedAssets.size).toBe(3);
    expect(selectedAssets.has("a")).toBe(true);
    expect(selectedAssets.has("old-asset")).toBe(false);
  });

  it("selectAll with an empty array clears the selection", () => {
    useAssetStore.getState().selectAll(["x", "y"]);
    useAssetStore.getState().selectAll([]);
    expect(useAssetStore.getState().selectedAssets.size).toBe(0);
  });

  it("clearSelection empties the selection set", () => {
    useAssetStore.getState().selectAll(["a", "b", "c"]);
    useAssetStore.getState().clearSelection();
    expect(useAssetStore.getState().selectedAssets.size).toBe(0);
  });

  it("setViewMode changes from grid to list", () => {
    useAssetStore.getState().setViewMode("list");
    expect(useAssetStore.getState().viewMode).toBe("list");
  });

  it("setViewMode changes from list back to grid", () => {
    useAssetStore.getState().setViewMode("list");
    useAssetStore.getState().setViewMode("grid");
    expect(useAssetStore.getState().viewMode).toBe("grid");
  });
});

// ---------------------------------------------------------------------------
// searchStore
// ---------------------------------------------------------------------------
describe("searchStore", () => {
  beforeEach(() => {
    useSearchStore.setState({ query: "", filters: {} });
  });

  it("starts with empty query and empty filters", () => {
    const { query, filters } = useSearchStore.getState();
    expect(query).toBe("");
    expect(filters).toEqual({});
  });

  it("setQuery updates the query string", () => {
    useSearchStore.getState().setQuery("mountain landscape");
    expect(useSearchStore.getState().query).toBe("mountain landscape");
  });

  it("setQuery overwrites the previous query", () => {
    useSearchStore.getState().setQuery("first query");
    useSearchStore.getState().setQuery("second query");
    expect(useSearchStore.getState().query).toBe("second query");
  });

  it("setFilters merges new filters into existing ones", () => {
    useSearchStore.getState().setFilters({ mime_type: "image/jpeg" });
    useSearchStore.getState().setFilters({ min_width: 1920 });
    const { filters } = useSearchStore.getState();
    expect(filters.mime_type).toBe("image/jpeg");
    expect(filters.min_width).toBe(1920);
  });

  it("setFilters overwrites a previously set filter key", () => {
    useSearchStore.getState().setFilters({ mime_type: "image/png" });
    useSearchStore.getState().setFilters({ mime_type: "video/mp4" });
    expect(useSearchStore.getState().filters.mime_type).toBe("video/mp4");
  });

  it("setFilters preserves unrelated filter keys", () => {
    useSearchStore.getState().setFilters({ date_from: "2024-01-01", min_height: 1080 });
    useSearchStore.getState().setFilters({ tags: ["nature"] });
    const { filters } = useSearchStore.getState();
    expect(filters.date_from).toBe("2024-01-01");
    expect(filters.min_height).toBe(1080);
    expect(filters.tags).toEqual(["nature"]);
  });

  it("resetFilters clears all active filters without touching the query", () => {
    useSearchStore.getState().setQuery("sky");
    useSearchStore.getState().setFilters({ mime_type: "image/jpeg", min_width: 800 });
    useSearchStore.getState().resetFilters();
    const { query, filters } = useSearchStore.getState();
    expect(query).toBe("sky");
    expect(filters).toEqual({});
  });
});

// ---------------------------------------------------------------------------
// commentStore
// ---------------------------------------------------------------------------

const makeComment = (overrides: Partial<Comment> = {}): Comment => ({
  id: "c1",
  content: "Great shot!",
  userId: "u1",
  userName: "Alice",
  parentId: null,
  annotationData: null,
  createdAt: "2024-06-01T12:00:00Z",
  replies: [],
  ...overrides,
});

describe("commentStore", () => {
  beforeEach(() => {
    useCommentStore.setState({ comments: [], replyingTo: null });
  });

  it("starts with an empty comments array and no replyingTo", () => {
    const { comments, replyingTo } = useCommentStore.getState();
    expect(comments).toEqual([]);
    expect(replyingTo).toBeNull();
  });

  it("setComments replaces the comments array", () => {
    const initial = [makeComment({ id: "c0" })];
    useCommentStore.getState().setComments(initial);
    const replacement = [makeComment({ id: "c1" }), makeComment({ id: "c2" })];
    useCommentStore.getState().setComments(replacement);
    expect(useCommentStore.getState().comments).toHaveLength(2);
    expect(useCommentStore.getState().comments[0].id).toBe("c1");
  });

  it("addComment appends to the existing list", () => {
    useCommentStore.getState().setComments([makeComment({ id: "c1" })]);
    useCommentStore.getState().addComment(makeComment({ id: "c2", content: "Agreed!" }));
    const { comments } = useCommentStore.getState();
    expect(comments).toHaveLength(2);
    expect(comments[1].id).toBe("c2");
    expect(comments[1].content).toBe("Agreed!");
  });

  it("addComment does not mutate the previous array", () => {
    const first = makeComment({ id: "c1" });
    useCommentStore.getState().setComments([first]);
    const before = useCommentStore.getState().comments;
    useCommentStore.getState().addComment(makeComment({ id: "c2" }));
    const after = useCommentStore.getState().comments;
    expect(before).not.toBe(after);
  });

  it("setReplyingTo stores the given id", () => {
    useCommentStore.getState().setReplyingTo("c99");
    expect(useCommentStore.getState().replyingTo).toBe("c99");
  });

  it("setReplyingTo can be cleared by passing null", () => {
    useCommentStore.getState().setReplyingTo("c99");
    useCommentStore.getState().setReplyingTo(null);
    expect(useCommentStore.getState().replyingTo).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// workflowStore
// ---------------------------------------------------------------------------

const makeWorkflowStep = (overrides: Partial<WorkflowStep> = {}): WorkflowStep => ({
  id: "ws1",
  stepOrder: 1,
  stepType: "review",
  status: "pending",
  reviewerId: null,
  reviewerName: undefined,
  comment: null,
  dueDate: null,
  createdAt: "2024-06-01T09:00:00Z",
  ...overrides,
});

const makeWorkflow = (overrides: Partial<Workflow> = {}): Workflow => ({
  id: "wf1",
  name: "Design Review",
  status: "in_progress",
  assetId: "asset-42",
  steps: [makeWorkflowStep()],
  createdAt: "2024-06-01T08:00:00Z",
  ...overrides,
});

describe("workflowStore", () => {
  beforeEach(() => {
    useWorkflowStore.setState({ workflow: null });
  });

  it("starts with no workflow", () => {
    expect(useWorkflowStore.getState().workflow).toBeNull();
  });

  it("setWorkflow stores the given workflow", () => {
    const wf = makeWorkflow();
    useWorkflowStore.getState().setWorkflow(wf);
    expect(useWorkflowStore.getState().workflow).toEqual(wf);
  });

  it("setWorkflow updates when called a second time", () => {
    useWorkflowStore.getState().setWorkflow(makeWorkflow({ id: "wf-old" }));
    const updated = makeWorkflow({ id: "wf-new", status: "approved" });
    useWorkflowStore.getState().setWorkflow(updated);
    const { workflow } = useWorkflowStore.getState();
    expect(workflow?.id).toBe("wf-new");
    expect(workflow?.status).toBe("approved");
  });

  it("setWorkflow(null) clears the workflow", () => {
    useWorkflowStore.getState().setWorkflow(makeWorkflow());
    useWorkflowStore.getState().setWorkflow(null);
    expect(useWorkflowStore.getState().workflow).toBeNull();
  });

  it("stores workflow steps correctly", () => {
    const wf = makeWorkflow({
      steps: [
        makeWorkflowStep({ id: "ws1", stepOrder: 1 }),
        makeWorkflowStep({ id: "ws2", stepOrder: 2, status: "approved" }),
      ],
    });
    useWorkflowStore.getState().setWorkflow(wf);
    const { workflow } = useWorkflowStore.getState();
    expect(workflow?.steps).toHaveLength(2);
    expect(workflow?.steps[1].status).toBe("approved");
  });
});
