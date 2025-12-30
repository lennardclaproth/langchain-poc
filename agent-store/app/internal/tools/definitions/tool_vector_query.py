from __future__ import annotations

from typing import Any, Dict, Optional

from app.contracts.spec_tools import (
    ToolContract,
    ToolResponseSpec,
    ToolInputSchema,
    JsonSchemaProperty,
    JsonType,
)
from app.internal.tools.registry import InternalToolDef, register_internal_tool
from app.internal.services.service_vectors import VectorService
from app.contracts.contract_vectors import VectorQueryRequest, VectorQueryResponse
from app.internal.store.repository_vectors import VectorRepository


# Define the tool contract
VECTOR_QUERY_CONTRACT = ToolContract(
    schema_version="jsonschema-2020-12",
    input_schema=ToolInputSchema(
        type="object",
        properties={
            "collection": JsonSchemaProperty(
                type="string",  # type: JsonType
                description="The name of the vector collection to query",
                minLength=1,
                x_static=True,
            ),
            "query": JsonSchemaProperty(
                type="string",  # type: JsonType
                description="The query text for semantic similarity search",
                minLength=1,
            ),
            "n_results": JsonSchemaProperty(
                type="integer",  # type: JsonType
                description="Number of results to return",
                minimum=1,
                maximum=100,
                default=5,
                x_static=True,
            ),
        },
        required=["collection", "query"],
        additionalProperties=False,
    ),
    tags=["vector", "search", "semantic", "similarity"],
    examples=[
        {
            "collection": "documents",
            "query": "machine learning algorithms",
            "n_results": 5,
        },
        {
            "collection": "articles",
            "query": "climate change",
            "n_results": 10,
        },
    ],
    read_only=True,
    idempotent=True,
    cache_ttl_seconds=300,
)

# Define the response schema
VECTOR_QUERY_RESPONSE = ToolResponseSpec(
    schema={
        "type": "object",
        "properties": {
            "hits": {
                "type": "array",
                "description": "List of matching vectors with distances",
                "items": {
                    "type": "object",
                    "properties": {
                        "collection": {"type": "string"},
                        "id": {"type": "string"},
                        "document": {"type": "string"},
                        "metadata": {"type": "object"},
                        "distance": {"type": ["number", "null"]},
                    },
                },
            },
        },
    },
    format="json",
)


async def vector_query_impl(
    collection: str,
    query: str,
    n_results: int = 5,
    **kwargs,
) -> Dict[str, Any]:
    """
    Query the vector database for semantic similarity matches.
    
    :param collection: Name of the collection to query
    :param query: Query text for similarity search
    :param n_results: Number of results to return (1-100, default 5)
    :return: Dictionary with query results
    """
    from app.internal.store import db_vector
    
    # Get the vector client
    client = db_vector.get_client()
    repo = VectorRepository(client)
    svc = VectorService(repo)
    
    # Create the query request
    req = VectorQueryRequest(
        collection=collection,
        query=query,
        n_results=n_results,
    )
    
    # Execute the query
    result: VectorQueryResponse = svc.query(req)
    
    # Convert to dict for JSON serialization
    return {
        "hits": [
            {
                "collection": hit.collection,
                "id": hit.id,
                "document": hit.document,
                "metadata": hit.metadata,
                "distance": hit.distance,
            }
            for hit in result.hits
        ],
    }


# Create and register the tool definition
VECTOR_QUERY_TOOL = InternalToolDef(
    key="vector_query",
    contract=VECTOR_QUERY_CONTRACT,
    response=VECTOR_QUERY_RESPONSE,
    fn=vector_query_impl,
)

register_internal_tool(VECTOR_QUERY_TOOL)
