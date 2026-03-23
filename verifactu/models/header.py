"""SOAP request header models matching AEAT XSD CabeceraType.

The header (Cabecera) identifies the obligated party and the submission mode.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from verifactu.models.enums import SiNo
from verifactu.models.identifiers import PersonaFisicaJuridicaES


class RemisionVoluntaria(BaseModel):
    """Voluntary submission metadata.

    Used in VERI*FACTU mode headers. Optional.
    """

    fecha_fin_verifactu: str | None = Field(default=None, min_length=10, max_length=10)
    """End date for VERI*FACTU mode (DD-MM-YYYY). Optional."""

    incidencia: SiNo | None = None
    """Whether records were generated during an incident (connectivity loss).
    Set to 'S' when sending records that were generated offline."""


class RemisionRequerimiento(BaseModel):
    """Submission by requirement metadata.

    Used in NO VERI*FACTU mode. Required in that mode's headers.
    """

    ref_requerimiento: str = Field(max_length=18)
    """AEAT requirement reference number (RefRequerimiento)."""

    fin_requerimiento: SiNo | None = None
    """Set to 'S' on the last submission for this requirement."""


class Cabecera(BaseModel):
    """Submission header.

    Maps to XSD ``CabeceraType``. Required in every submit request.
    """

    obligado_emision: PersonaFisicaJuridicaES
    """Tax obligated party (the invoice issuer)."""

    representante: PersonaFisicaJuridicaES | None = None
    """Representative/advisor of the obligated party. Optional."""

    remision_voluntaria: RemisionVoluntaria | None = None
    """Voluntary submission metadata (VERI*FACTU mode). Optional."""

    remision_requerimiento: RemisionRequerimiento | None = None
    """Requirement submission metadata (NO VERI*FACTU mode). Optional."""
