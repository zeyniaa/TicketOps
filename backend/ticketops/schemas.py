from typing import Literal
from pydantic import BaseModel, Field, field_validator

Category = Literal['status_pengiriman','barang_rusak','barang_tidak_sesuai','retur_refund','pembatalan','pembayaran','akun','lainnya']
Team = Literal['logistik','retur','billing','customer_care']
Status = Literal['baru','ditinjau','disetujui','selesai']

class CreateTicket(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    message: str = Field(min_length=10, max_length=4000)
    order_code: str | None = Field(default=None, max_length=40, pattern=r'^[A-Za-z0-9_-]*$')
    customer: str = Field(default='Pelanggan demo', min_length=1, max_length=100)
    @field_validator('subject','message','customer')
    @classmethod
    def strip_text(cls, v):
        if not v.strip(): raise ValueError('Teks tidak boleh kosong')
        return v.strip()

class UpdateTicket(BaseModel):
    revision: int = Field(ge=1)
    category: Category | None = None
    team: Team | None = None
    priority: Literal['P1','P2','P3'] | None = None
    status: Status | None = None
    reason: str = Field(default='Koreksi operator', max_length=500)

class UpdateDraft(BaseModel):
    version: int = Field(ge=1)
    body: str = Field(min_length=10, max_length=5000)

class ApproveDraft(BaseModel):
    version: int = Field(ge=1)

class LLMOutput(BaseModel):
    draft: str = Field(min_length=120, max_length=4000, description='Isi jawaban langsung kepada pelanggan, 40–150 kata dalam bahasa Indonesia. Bukan instruksi penulisan, bukan schema atau penjelasan tugas.')
    policy_ids: list[str] = Field(min_length=1, max_length=3)
    missing_information: list[str] = Field(default_factory=list, max_length=6)
    review_flags: list[str] = Field(default_factory=list, max_length=6)
