from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_workspace
from app.core.event_dependencies import get_current_event
from app.models.event import Event
from app.models.user import User
from app.schemas.contract import ContractResponse, ContractUpdate
from app.schemas.workspace import WorkspaceAuth
from app.services.contract_service import ContractService

router = APIRouter(
    prefix="/workspaces/{workspace_id}/events/{event_id}/contracts",
    tags=["Contracts"],
)


@router.get("", response_model=list[ContractResponse])
async def list_contracts(
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> list[ContractResponse]:
    service = ContractService(session)
    return await service.list(event)


@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def upload_contract(
    title: str = Form(...),
    supplier_id: UUID | None = Form(default=None),
    file: UploadFile = File(...),
    auth: WorkspaceAuth = Depends(get_current_workspace),
    event: Event = Depends(get_current_event),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ContractResponse:
    service = ContractService(session)
    return await service.upload(auth, event, current_user, file, title, supplier_id)


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: UUID,
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> ContractResponse:
    service = ContractService(session)
    return await service.get(event, contract_id)


@router.get("/{contract_id}/download")
async def download_contract(
    contract_id: UUID,
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> FileResponse:
    service = ContractService(session)
    contract, path = await service.get_file_path(event, contract_id)
    return FileResponse(
        path=path,
        filename=contract.original_filename,
        media_type=contract.mime_type,
    )


@router.patch("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: UUID,
    data: ContractUpdate,
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> ContractResponse:
    service = ContractService(session)
    return await service.update(event, contract_id, data)


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(
    contract_id: UUID,
    auth: WorkspaceAuth = Depends(get_current_workspace),
    event: Event = Depends(get_current_event),
    session: AsyncSession = Depends(get_db),
) -> None:
    service = ContractService(session)
    await service.delete(auth, event, contract_id)
