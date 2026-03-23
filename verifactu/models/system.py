"""SistemaInformatico model matching AEAT XSD SistemaInformaticoType.

Identifies the invoicing software system that generated the records.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from verifactu.models.enums import SiNo
from verifactu.models.identifiers import IDOtro


class SistemaInformatico(BaseModel):
    """Invoicing system identification.

    Maps to XSD ``SistemaInformaticoType``. Required in every alta and
    anulación record.
    """

    nombre_razon: str = Field(max_length=120)
    """Name or business name of the software producer."""

    nif: str | None = Field(default=None, min_length=9, max_length=9)
    """NIF of the producer (mutually exclusive with id_otro)."""

    id_otro: IDOtro | None = None
    """Foreign identification of the producer (mutually exclusive with nif)."""

    nombre_sistema_informatico: str = Field(max_length=30)
    """Software name (NombreSistemaInformatico)."""

    id_sistema_informatico: str = Field(max_length=2)
    """Software identifier code (IdSistemaInformatico)."""

    version: str = Field(max_length=50)
    """Software version string."""

    numero_instalacion: str = Field(max_length=100)
    """Installation identifier (NumeroInstalacion)."""

    tipo_uso_posible_solo_verifactu: SiNo = SiNo.SI
    """Whether the system operates exclusively in VERI*FACTU mode."""

    tipo_uso_posible_multi_ot: SiNo = SiNo.NO
    """Whether the system supports multiple tax obligated parties."""

    indicador_multiples_ot: SiNo = SiNo.NO
    """Whether this installation currently serves multiple tax obligated parties."""
