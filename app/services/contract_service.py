import uuid
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.contract import Contract
from app.models.enums import WorkspaceRole
from app.models.event import Event
from app.models.user import User
from app.repositories.contract_repository import ContractRepository
from app.repositories.supplier_repository import SupplierRepository
from app.schemas.contract import ContractResponse, ContractUpdate
from app.schemas.workspace import WorkspaceAuth
from app.services.audit_service import AuditService

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class ContractService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ContractRepository(session)
        self.supplier_repo = SupplierRepository(session)
        self.audit = AuditService(session)
        self.settings = get_settings()

    async def list(self, event: Event) -> list[ContractResponse]:
        contracts = await self.repo.list_by_event(event.id)
        return [ContractResponse.model_validate(c) for c in contracts]

    async def upload(
        self,
        auth: WorkspaceAuth,
        event: Event,
        user: User,
        file: UploadFile,
        title: str,
        supplier_id: UUID | None = None,
    ) -> ContractResponse:
        if supplier_id:
            supplier = await self.supplier_repo.get_by_id(
                supplier_id, auth.workspace.id
            )
            if supplier is None:
                raise HTTPException(404, "Supplier not found")

        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed: {file.content_type}",
            )

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="File exceeds maximum size of 10 MB",
            )

        from app.services.plan_limit_service import PlanLimitService

        limit_service = PlanLimitService(self.session)
        await limit_service.check_storage_limit(auth.workspace, len(content))

        storage_dir = (
            Path(self.settings.upload_dir)
            / str(auth.workspace.id)
            / str(event.id)
        )
        storage_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(file.filename or "file").suffix
        stored_name = f"{uuid.uuid4()}{ext}"
        file_path = storage_dir / stored_name
        file_path.write_bytes(content)

        contract = await self.repo.create(
            event_id=event.id,
            supplier_id=supplier_id,
            title=title,
            file_path=str(file_path),
            original_filename=file.filename or stored_name,
            file_size=len(content),
            mime_type=file.content_type or "application/octet-stream",
        )
        await limit_service.add_storage_usage(auth.workspace.id, len(content))

        await self.audit.log(
            auth.workspace.id,
            user,
            "contract",
            contract.id,
            "uploaded",
            {"title": title, "filename": contract.original_filename},
        )
        return ContractResponse.model_validate(contract)

    async def get(self, event: Event, contract_id: UUID) -> ContractResponse:
        contract = await self._get_or_404(event.id, contract_id)
        return ContractResponse.model_validate(contract)

    async def get_file_path(self, event: Event, contract_id: UUID) -> tuple[Contract, Path]:
        contract = await self._get_or_404(event.id, contract_id)
        path = Path(contract.file_path)
        if not path.exists():
            raise HTTPException(404, "Contract file not found on disk")
        return contract, path

    async def update(
        self,
        event: Event,
        contract_id: UUID,
        data: ContractUpdate,
    ) -> ContractResponse:
        contract = await self._get_or_404(event.id, contract_id)

        if data.title is not None:
            contract.title = data.title
        if data.supplier_id is not None:
            contract.supplier_id = data.supplier_id

        await self.session.flush()
        await self.session.refresh(contract)
        return ContractResponse.model_validate(contract)

    async def delete(
        self,
        auth: WorkspaceAuth,
        event: Event,
        contract_id: UUID,
    ) -> None:
        self._require_roles(auth, WorkspaceRole.OWNER, WorkspaceRole.ADMIN)
        contract = await self._get_or_404(event.id, contract_id)
        path = Path(contract.file_path)
        if path.exists():
            path.unlink()
        from app.services.plan_limit_service import PlanLimitService

        limit_service = PlanLimitService(self.session)
        await limit_service.remove_storage_usage(auth.workspace.id, contract.file_size)
        contract.soft_delete()

    async def _get_or_404(self, event_id: UUID, contract_id: UUID) -> Contract:
        contract = await self.repo.get_by_id(contract_id, event_id)
        if contract is None:
            raise HTTPException(404, "Contract not found")
        return contract

    @staticmethod
    def _require_roles(auth: WorkspaceAuth, *roles: WorkspaceRole) -> None:
        if auth.membership.role not in roles:
            raise HTTPException(403, "Insufficient permissions")
