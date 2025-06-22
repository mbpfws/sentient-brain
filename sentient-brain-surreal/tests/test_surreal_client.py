import pytest
from db.surreal_client import get_surreal_client

@pytest.mark.asyncio
async def test_db_connection_and_query():
    """Tests that we can connect to the DB and run a simple query."""
    client = get_surreal_client()
    try:
        # The INFO FOR DB query is a good health check
        result = await client.query("INFO FOR DB;")
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0
        # The first result of the list should have a 'result' key
        assert "result" in result[0]
        print("\nSurrealDB connection successful and query returned valid data.")
    finally:
        await client.close()
