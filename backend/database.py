"""Supabase dependency injection for FastAPI route handlers.

Provides a FastAPI-compatible Depends() dependency that yields the Supabase
client singleton. This replaces deferred `from supabase_client import get_supabase`
imports inside route handler bodies with proper DI.

STORY-226 Track 1 (AC1-AC3): Dependency injection for Supabase.

Usage in route handlers:
    from database import get_db

    @router.get("/example")
    async def example_route(db=Depends(get_db)):
        result = db.table("my_table").select("*").execute()
        return result.data

Non-route code (services, helpers) should continue using
`from supabase_client import get_supabase` directly since they
cannot use FastAPI's Depends() mechanism.
"""

from supabase_client import get_supabase


def get_db():
    """FastAPI dependency that provides the Supabase client.

    Returns the Supabase client singleton from supabase_client module.
    This is a thin wrapper that enables dependency injection in route
    handlers, making them easier to test (override via app.dependency_overrides).

    Returns:
        supabase.Client: Authenticated Supabase client with admin privileges.
    """
    return get_supabase()
