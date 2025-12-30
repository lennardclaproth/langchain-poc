from fastapi import APIRouter, Depends
from app.api.deps import get_vector_service
from app.internal.services.service_vectors import VectorService
from app.contracts.contract_vectors import VectorQueryRequest, VectorCreate, VectorUpdate

router = APIRouter(prefix="/vectors", tags=["vectors"])

@router.post("/create")
def create_vectors(payload: list[VectorCreate], svc: VectorService = Depends(get_vector_service)):
    for item in payload:
        svc.create(item.collection, item)
    return {"ok": True}

@router.post("/query")
def query_vectors(payload: VectorQueryRequest, svc: VectorService = Depends(get_vector_service)):
    return svc.query(payload)

@router.patch("")
def update_vector(payload: VectorUpdate, svc: VectorService = Depends(get_vector_service)):
    svc.update(payload, merge_metadata=True)
    return {"ok": True}

@router.delete("")
def delete_vectors(collection: str, ids: list[str], svc: VectorService = Depends(get_vector_service)):
    svc.delete(collection, ids=ids)
    return {"ok": True}
