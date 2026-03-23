"""Response models for submit operations.

Maps to XSD types from RespuestaSuministro.xsd.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from verifactu.models.enums import (
    EstadoEnvio,
    EstadoRegistro,
    EstadoRegistroConsulta,
    SiNo,
    TipoOperacion,
)
from verifactu.models.identifiers import IDFactura


class DatosPresentacion(BaseModel):
    """Submission metadata returned by AEAT."""

    nif_presentador: str
    """NIF of the submitter."""

    timestamp_presentacion: datetime
    """Submission timestamp."""


class Operacion(BaseModel):
    """Operation metadata in the response."""

    tipo_operacion: TipoOperacion
    """Alta or Anulacion."""

    subsanacion: SiNo | None = None
    rechazo_previo: str | None = None
    sin_registro_previo: SiNo | None = None


class RegistroDuplicado(BaseModel):
    """Duplicate record information (returned on error 3000)."""

    id_peticion_registro_duplicado: str
    """IdPeticion of the existing duplicate record."""

    estado_registro_duplicado: EstadoRegistroConsulta
    """Status of the existing duplicate record."""

    codigo_error_registro: int | None = None
    descripcion_error_registro: str | None = None


class RespuestaLinea(BaseModel):
    """Per-record response line."""

    id_factura: IDFactura
    """Invoice identifier this response refers to."""

    operacion: Operacion
    """Operation metadata."""

    ref_externa: str | None = None
    """External reference echoed back."""

    estado_registro: EstadoRegistro
    """Record status: Correcto, AceptadoConErrores, or Incorrecto."""

    codigo_error_registro: int | None = None
    """AEAT error code (1xxx, 2xxx, 3xxx) if applicable."""

    descripcion_error_registro: str | None = None
    """AEAT error description if applicable."""

    registro_duplicado: RegistroDuplicado | None = None
    """Duplicate record info (only present on error 3000)."""

    @property
    def is_accepted(self) -> bool:
        """Record was accepted (possibly with warnings)."""
        return self.estado_registro in (
            EstadoRegistro.CORRECTO,
            EstadoRegistro.ACEPTADO_CON_ERRORES,
        )


class RespuestaEnvio(BaseModel):
    """Full submission response.

    Maps to XSD ``RespuestaRegFactuSistemaFacturacionType``.
    """

    csv: str | None = None
    """Código Seguro de Verificación. Only present if submission not fully rejected."""

    datos_presentacion: DatosPresentacion | None = None
    """Submission metadata. Only present if submission not fully rejected."""

    tiempo_espera_envio: int = 60
    """Seconds to wait before next submission (TiempoEsperaEnvio)."""

    estado_envio: EstadoEnvio
    """Overall submission status."""

    respuesta_linea: list[RespuestaLinea] = Field(default_factory=list)
    """Per-record response lines (0-1000)."""

    @property
    def is_accepted(self) -> bool:
        """At least some records were accepted."""
        return self.estado_envio in (
            EstadoEnvio.CORRECTO,
            EstadoEnvio.PARCIALMENTE_CORRECTO,
        )

    @property
    def accepted_records(self) -> list[RespuestaLinea]:
        """Records that were accepted."""
        return [r for r in self.respuesta_linea if r.is_accepted]

    @property
    def rejected_records(self) -> list[RespuestaLinea]:
        """Records that were rejected."""
        return [r for r in self.respuesta_linea if not r.is_accepted]
