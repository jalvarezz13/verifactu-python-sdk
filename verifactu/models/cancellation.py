"""Invoice cancellation (anulación) record model.

Maps to XSD ``RegistroFacturacionAnulacionType`` from SuministroInformacion.xsd.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from verifactu.models.enums import GeneradoPor, SiNo, TipoHuella
from verifactu.models.identifiers import (
    Encadenamiento,
    IDFacturaBaja,
    PersonaFisicaJuridica,
)
from verifactu.models.system import SistemaInformatico


class RegistroAnulacion(BaseModel):
    """Invoice cancellation record (Anulación).

    Maps to XSD ``RegistroFacturacionAnulacionType``.
    """

    id_version: str = "1.0"
    """Schema version. Always '1.0'."""

    id_factura: IDFacturaBaja
    """Identifier of the invoice being cancelled."""

    ref_externa: str | None = Field(default=None, max_length=60)
    """External reference for correlation. Optional."""

    sin_registro_previo: SiNo | None = None
    """'S' if cancelling an invoice with no prior registration in AEAT."""

    rechazo_previo: SiNo | None = None
    """'S' if there was a previous rejection of this cancellation."""

    generado_por: GeneradoPor | None = None
    """Who generated the cancellation (E=issuer, D=recipient, T=third party)."""

    generador: PersonaFisicaJuridica | None = None
    """Person/entity that generated the cancellation. Optional."""

    encadenamiento: Encadenamiento
    """Chain link to previous record."""

    sistema_informatico: SistemaInformatico
    """Invoicing system identification."""

    fecha_hora_huso_gen_registro: str
    """Record generation timestamp ISO 8601: YYYY-MM-DDTHH:MM:SS+HH:00."""

    tipo_huella: TipoHuella = TipoHuella.SHA256
    """Hash algorithm type. Always '01' (SHA-256)."""

    huella: str = Field(max_length=64)
    """SHA-256 hash of this record (uppercase hex, 64 chars)."""
