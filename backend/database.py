"""Supabase dependency injection for FastAPI route handlers.

Provides FastAPI-compatible Depends() dependencies that yield Supabase clients:

    - get_db()      — Admin client (service_role key, bypasses RLS).
                      Use for admin endpoints, cron jobs, background workers.

    - get_user_db() — User-scoped client (anon key + user JWT, respects RLS).
                      Use for user-facing operations where RLS should enforce
                      row-level access control (profile, pipeline, history, etc.).

STORY-226 Track 1 (AC1-AC3): Dependency injection for Supabase.
SYS-023: Per-user Supabase tokens for user-scoped operations.

Usage in route handlers:

    # ADMIN operations (bypasses RLS):
    from database import get_db

    @router.get("/admin/users")
    async def admin_list_users(db=Depends(get_db)):
        result = db.table("profiles").select("*").execute()
        return result.data

    # USER-SCOPED operations (respects RLS):
    from database import get_user_db

    @router.get("/profile/context")
    async def get_profile_context(user_db=Depends(get_user_db)):
        # RLS automatically filters to the authenticated user's rows
        result = await sb_execute(user_db.table("profiles").select("context_data"))
        return result.data

Non-route code (services, helpers) should continue using
`from supabase_client import get_supabase` directly since they
cannot use FastAPI's Depends() mechanism.
"""

from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from supabase_client import get_supabase, get_user_supabase

# Re-use the same HTTPBearer scheme from auth.py (auto_error=False so
# get_user_db can raise a clear error instead of FastAPI's default).
_security = HTTPBearer(auto_error=False)


def get_db():
    """FastAPI dependency that provides the Supabase ADMIN client.

    BYPASSES RLS. Use only for:
        - Admin endpoints (/admin/*)
        - Background jobs (ARQ workers, cron)
        - System health checks and monitoring
        - User management (auth.admin.*)
        - Cross-user aggregations and analytics

    For user-scoped operations, use get_user_db() instead.

    Returns:
        supabase.Client: Authenticated Supabase client with admin privileges.
    """
    return get_supabase()


def get_user_db(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_security),
):
    """FastAPI dependency that provides a user-scoped Supabase client.

    Extracts the JWT access token from the Authorization header and creates
    a Supabase client that uses the anon key + user token. PostgREST will
    apply RLS policies based on auth.uid() from the JWT.

    RESPECTS RLS. Use for all user-facing operations:
        - Profile reads/updates (own profile only)
        - Pipeline CRUD (own items only)
        - Search history (own sessions only)
        - Messages (own conversations only)
        - Alert preferences (own settings only)

    Note: This dependency does NOT validate the JWT (that is done by
    require_auth). Always use require_auth alongside get_user_db to
    ensure the user is authenticated before creating the scoped client.

    Typical usage pattern:
        @router.get("/my-data")
        async def get_my_data(
            user: dict = Depends(require_auth),   # validates JWT, returns user info
            user_db=Depends(get_user_db),          # creates user-scoped client
        ):
            # user_db queries are filtered by RLS (auth.uid() = user's id)
            result = await sb_execute(user_db.table("my_table").select("*"))
            return result.data

    Args:
        credentials: Automatically injected from Authorization header.

    Returns:
        supabase.Client: User-scoped Supabase client that respects RLS.

    Raises:
        HTTPException 401: If no Authorization header is present.
    """
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Autenticacao necessaria. Faca login para continuar.",
        )

    access_token = credentials.credentials
    return get_user_supabase(access_token)
