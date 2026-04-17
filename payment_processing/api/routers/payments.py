from uuid import UUID

from fastapi import APIRouter

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
)


@router.get("/")
async def get_payments():
    return {"message": "Get all payments"}


@router.get("/{payment_id}")
async def get_payment(payment_id: UUID):
    return {"message": f"Get payment {payment_id}"}


@router.post("/")
async def create_payment():
    return {"message": "Create payment"}
