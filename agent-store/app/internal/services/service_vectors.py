# app/internal/services/service_vectors.py
from __future__ import annotations

from typing import List, Optional, Sequence, Union

from app.contracts.contract_vectors import (
    VectorCreate,
    VectorUpdate,
    VectorRead,
    VectorQueryRequest,
    VectorQueryResponse,
    VectorCollectionRead
)

from app.internal.services.errors import NotFoundError, ValidationError
from app.internal.store.repository_vectors import VectorRepository

class VectorService:
    repo: VectorRepository
    def __init__(self, repo: VectorRepository):
        self.repo = repo

    @staticmethod
    def _require_non_empty(value: str, field: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"'{field}' must be a non-empty string")

    @staticmethod
    def _require_collection(collection: str) -> None:
        if not isinstance(collection, str) or not collection.strip():
            raise ValidationError("'collection' must be a non-empty string")

    @staticmethod
    def _normalize_collection(collection: str) -> str:
        # optional: keep collection naming consistent (trim spaces)
        return collection.strip()

    # -------------------------
    # Public API
    # -------------------------

    def create(self, collection: str, data: VectorCreate) -> VectorRead:
        """
        Create a new vector record in the given collection.
        """
        self._require_collection(collection)
        self._require_non_empty(data.id, "id")

        if not isinstance(data.document, str) or not data.document.strip():
            raise ValidationError("'document' must be a non-empty string")

        collection = self._normalize_collection(collection)

        # Delegate
        return self.repo.create_vector(collection=collection, data=data)

    def get(self, collection: str, id: str) -> VectorRead:
        """
        Read a vector by id.
        """
        self._require_collection(collection)
        self._require_non_empty(id, "id")

        collection = self._normalize_collection(collection)

        try:
            return self.repo.read_vector(collection=collection, id=id)
        except ValueError:
            # Repo stays generic; service gives domain error
            raise NotFoundError(collection=collection, id=id)

    def update(self, data: VectorUpdate) -> VectorRead:
        """
        Patch update semantics.
        - merges metadata keys
        - optionally updates document
        """
        self._require_collection(data.collection)
        self._require_non_empty(data.id, "id")

        data.collection = self._normalize_collection(data.collection)

        # Optional document: if present, require it not to be empty
        if data.document is not None and not data.document.strip():
            raise ValidationError("'document' must be non-empty when provided")

        try:
            return self.repo.update_vector(data=data)
        except ValueError:
            raise NotFoundError(collection=data.collection, id=data.id)

    def delete(self, collection: str, id: str) -> None:
        """
        Delete a vector by id.
        """
        self._require_collection(collection)
        self._require_non_empty(id, "id")

        collection = self._normalize_collection(collection)

        # Optional: enforce "must exist" behavior
        # - some teams prefer idempotent deletes (no error if missing)
        # - others want strict deletion
        #
        # We'll implement strict deletion since it is often safer.
        self.get(collection=collection, id=id)

        self.repo.delete_vector(collection=collection, id=id)

    def query(self, req: VectorQueryRequest) -> VectorQueryResponse:
        """
        Query the vector store.
        """
        self._require_collection(req.collection)

        req.collection = self._normalize_collection(req.collection)

        if req.n_results <= 0:
            raise ValidationError("'n_results' must be > 0")

        # If query is a string, ensure it isn't empty.
        if isinstance(req.query, str):
            if not req.query.strip():
                raise ValidationError("'query' must be non-empty")
        else:
            if not req.query:
                raise ValidationError("'query' list must not be empty")
            if any((not q or not q.strip()) for q in req.query):
                raise ValidationError("all items in 'query' list must be non-empty strings")

        return self.repo.query(req=req)

    def collection_info(self, collection: str) -> VectorCollectionRead:
        """
        Collection summary (count, metadata).
        """
        self._require_collection(collection)
        collection = self._normalize_collection(collection)
        return self.repo.collection_info(collection=collection)
