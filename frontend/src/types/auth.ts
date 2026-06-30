export type WorkspaceRole = "owner" | "admin" | "member" | "viewer";

export type WorkspaceSummary = {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
};

export type WorkspaceMembershipSummary = {
  workspace_id: string;
  role: WorkspaceRole;
  workspace: WorkspaceSummary;
};

export type AuthUser = {
  id: string;
  name: string;
  email: string;
  created_at: string;
  updated_at: string;
  memberships: WorkspaceMembershipSummary[];
};

export type TokenResponse = {
  access_token: string;
  token_type: "bearer";
};

export type ActiveWorkspaceResponse = {
  workspace_id: string;
  role: WorkspaceRole;
  workspace: WorkspaceSummary;
};
