export interface User {
  id: string;
  email: string;
  full_name: string;
  role: "admin" | "manager" | "editor" | "reviewer" | "viewer";
  is_active: boolean;
  created_at: string;
}

export interface Asset {
  id: string;
  filename: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  width: number | null;
  height: number | null;
  storage_path: string;
  thumbnail_path: string | null;
  uploaded_by: string;
  created_at: string;
  updated_at: string;
  tags: Tag[];
  metadata: Record<string, unknown>;
}

export interface Collection {
  id: string;
  name: string;
  description: string | null;
  cover_asset_id: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
  asset_count: number;
}

export interface Tag {
  id: string;
  name: string;
}

export interface SearchResult {
  assets: Asset[];
  total: number;
  page: number;
  per_page: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
}

export interface Comment {
  id: string;
  content: string;
  userId: string;
  userName?: string;
  parentId: string | null;
  annotationData?: { x: number; y: number; width: number; height: number; text: string } | null;
  createdAt: string;
  replies?: Comment[];
}

export interface WorkflowStep {
  id: string;
  stepOrder: number;
  stepType: string;
  status: string;
  reviewerId: string | null;
  reviewerName?: string;
  comment: string | null;
  dueDate: string | null;
  createdAt: string;
}

export interface Workflow {
  id: string;
  name: string;
  status: string;
  assetId: string;
  steps: WorkflowStep[];
  createdAt: string;
}

export interface ShareLink {
  id: string;
  token: string;
  assetId: string | null;
  collectionId: string | null;
  expiresAt: string | null;
  permissions: string;
  isActive: boolean;
  accessCount: number;
  shareUrl: string;
  createdAt: string;
}

export interface Notification {
  id: string;
  type: string;
  message: string;
  assetId: string | null;
  isRead: boolean;
  createdAt: string;
}

export interface TransformOptions {
  width?: number;
  height?: number;
  fit?: "cover" | "contain" | "fill";
  format?: "jpeg" | "png" | "webp";
  quality?: number;
  rotate?: number;
}
