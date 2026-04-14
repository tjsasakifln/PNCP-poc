// STORY-2.1 (EPIC-TD-2026Q2): Shared admin types.
//
// Backend GET /admin/users currently returns users as `List[Dict[str, Any]]`
// (see backend/schemas/admin.py::AdminUsersListResponse), so the generated
// `components["schemas"]["AdminUsersListResponse"]` types the array as
// `{[k: string]: unknown}[]`. Until the backend hardens that schema we
// declare the richer UI-facing shape here and keep it consumed in a single
// place (admin page + AdminUserTable) instead of duplicating the interface.
//
// TODO (STORY-2.2 follow-up): tighten `AdminUsersListResponse.users` in
// backend/schemas/admin.py to a proper Pydantic model so the generated
// TypeScript can replace this local declaration.

export interface AdminUserSubscription {
  id: string;
  plan_id: string;
  credits_remaining: number | null;
  expires_at: string | null;
  is_active: boolean;
}

export interface AdminUserProfile {
  id: string;
  email: string;
  full_name: string | null;
  company: string | null;
  plan_type: string;
  created_at: string;
  user_subscriptions: AdminUserSubscription[];
}

export interface AdminUsersResponse {
  users: AdminUserProfile[];
  total: number;
}
