from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Union, Literal, cast

import chromadb 
from chromadb import ClientAPI

from app.contracts.contract_vectors import (
    Metadata,
    VectorCreate,
    VectorQueryHit,
    VectorUpdate,
    VectorRead,
    VectorCollectionRead,
    VectorQueryRequest,
    VectorQueryResponse,
)

QueryMode = Literal["text", "embedding"]


class VectorRepository:
    """
    Repository for managing vectors in ChromaDB.

    Notes:
    - Uses "patch semantics" for metadata on update: merges provided keys into existing metadata.
      If a value is None, we delete that key (optional but often convenient).
    - Document update is optional; if provided, it overwrites the stored document.
    """

    def __init__(self, client: ClientAPI):
        self._client = client

    def _collection(self, name: str):
        # You could switch to get_collection if you prefer strictness.
        return self._client.get_or_create_collection(name=name)

    @staticmethod
    def _merge_metadata(existing: Metadata, patch: Optional[Metadata]) -> Metadata:
        if patch is None:
            return dict(existing)

        merged = dict(existing)
        for k, v in patch.items():
            if v is None:
                # "delete semantics" for None (optional; remove if you want None values stored)
                merged.pop(k, None)
            else:
                merged[k] = v
        return merged

    # -------------------------
    # CRUD
    # -------------------------

    def create_vector(self, collection: str, data: VectorCreate) -> VectorRead:
        col = self._collection(collection)

        col.add(
            ids=[data.id],
            documents=[data.document],
            metadatas=[data.metadata],
        )

        return VectorRead(collection=collection, id=data.id, document=data.document, metadata=data.metadata)

    def read_vector(self, collection: str, id: str) -> VectorRead:
        col = self._collection(collection)
        res = col.get(ids=[id], include=["documents", "metadatas"])

        ids = cast(List[str], res.get("ids") or [])
        if not ids:
            # choose your preferred error type; ValueError keeps it framework-agnostic
            raise ValueError(f"Vector not found: collection={collection} id={id}")

        doc = None
        docs = res.get("documents") or []
        if docs and docs[0] is not None:
            doc = cast(str, docs[0])

        meta_list = res.get("metadatas") or []
        metadata: Metadata = cast(Metadata, meta_list[0] or {}) if meta_list else {}

        return VectorRead(collection=collection, id=id, document=doc, metadata=metadata)

    def update_vector(self, data: VectorUpdate) -> VectorRead:
        """
        Patch semantics:
        - If data.document is provided => overwrite document.
        - If data.metadata is provided => merge into existing metadata (key-level).
        """
        # read existing first for patch semantics
        current = self.read_vector(collection=data.collection, id=data.id)
        new_metadata = self._merge_metadata(current.metadata, data.metadata)

        col = self._collection(data.collection)

        # Chroma's `update` expects only fields you want to change.
        # We'll update metadatas always (since merge might delete keys),
        # and documents only if supplied.
        if data.document is None:
            col.update(ids=[data.id], metadatas=[new_metadata])
            new_document = current.document
        else:
            col.update(ids=[data.id], documents=[data.document], metadatas=[new_metadata])
            new_document = data.document

        return VectorRead(
            collection=data.collection,
            id=data.id,
            document=new_document,
            metadata=new_metadata,
        )

    def delete_vector(self, collection: str, id: str) -> None:
        col = self._collection(collection)
        col.delete(ids=[id])

    # -------------------------
    # Query / Collections
    # -------------------------

    def query(self, req: VectorQueryRequest) -> VectorQueryResponse:
        col = self._collection(req.collection)

        queries: List[str] = [req.query] if isinstance(req.query, str) else list(req.query)

        res = col.query(
            query_texts=queries,
            n_results=req.n_results,
            where=req.where,
            where_document=req.where_document,
            include=["documents", "metadatas", "distances"],
        )

        ids_grouped = cast(List[List[str]], res.get("ids") or [[] for _ in queries])
        docs_grouped = cast(List[List[Optional[str]]], res.get("documents") or [[] for _ in queries])
        metas_grouped = cast(List[List[Optional[Dict[str, Any]]]], res.get("metadatas") or [[] for _ in queries])
        dists_grouped = cast(List[List[Optional[float]]], res.get("distances") or [[] for _ in queries])

        grouped: List[List[VectorQueryHit]] = []
        flat: List[VectorQueryHit] = []

        for qi in range(len(queries)):
            hits_for_q: List[VectorQueryHit] = []
            for i, vid in enumerate(ids_grouped[qi] if qi < len(ids_grouped) else []):
                doc = None
                if qi < len(docs_grouped) and i < len(docs_grouped[qi]):
                    doc = docs_grouped[qi][i]

                meta: Metadata = {}
                if qi < len(metas_grouped) and i < len(metas_grouped[qi]) and metas_grouped[qi][i]:
                    meta = cast(Metadata, metas_grouped[qi][i])

                dist = None
                if qi < len(dists_grouped) and i < len(dists_grouped[qi]):
                    dist = dists_grouped[qi][i]

                hit = VectorQueryHit(
                    collection=req.collection,
                    id=vid,
                    document=doc,
                    metadata=meta,
                    distance=dist,
                )
                hits_for_q.append(hit)
                flat.append(hit)

            grouped.append(hits_for_q)

        return VectorQueryResponse(hits=flat, grouped=grouped)

    def collection_info(self, collection: str) -> VectorCollectionRead:
        col = self._collection(collection)

        # Chroma collections have `count()`. Metadata support depends on version;
        # we keep it conservative and return {} unless you explicitly store it elsewhere.
        return VectorCollectionRead(collection=collection, count=col.count(), metadata={})
