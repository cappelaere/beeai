"""
Search documents tool - Semantic search through indexed PDF documents
"""

from beeai_framework.tools import StringToolOutput, tool

from agents.library.tools.document_utils import (
    get_embedding_model,
    load_faiss_index,
)


@tool
def search_documents(
    query: str,
    top_k: int = 5,
) -> StringToolOutput:
    """
    Search indexed PDF documents using semantic similarity.

    Args:
        query: The search query or question
        top_k: Number of most relevant chunks to return (default: 5, max: 20)

    Returns:
        Top-K relevant text chunks with document metadata and page information.
    """
    import agents.library.tools.document_utils as utils

    # Load index if not already loaded
    if utils._faiss_index is None:
        load_faiss_index()

    # Check if index is empty
    if utils._faiss_index.ntotal == 0:
        return StringToolOutput(
            "No documents have been indexed yet. "
            "Use reindex_all_documents to index existing documents, "
            "or upload new documents which will be indexed automatically."
        )

    # Validate and cap top_k
    top_k = max(1, min(int(top_k), 20))

    # Generate query embedding
    model = get_embedding_model()
    query_embedding = model.encode([query], convert_to_numpy=True).astype("float32")

    # Search FAISS index
    distances, indices = utils._faiss_index.search(query_embedding, top_k)

    # Collect results
    results = []
    for i, (distance, idx) in enumerate(zip(distances[0], indices[0], strict=False)):
        if idx >= len(utils._document_metadata):
            continue

        metadata = utils._document_metadata[idx]
        results.append(
            {
                "rank": i + 1,
                "relevance_score": float(1 / (1 + distance)),
                "document_name": metadata["document_name"],
                "document_path": metadata["document_path"],
                "chunk_index": metadata["chunk_index"],
                "total_chunks": metadata["total_chunks"],
                "text": metadata["chunk_text"][:500],
            }
        )

    output = {
        "query": query,
        "total_indexed_documents": len({m["document_name"] for m in utils._document_metadata}),
        "total_indexed_chunks": len(utils._document_metadata),
        "results_returned": len(results),
        "results": results,
    }

    import json

    return StringToolOutput(json.dumps(output, indent=2))
