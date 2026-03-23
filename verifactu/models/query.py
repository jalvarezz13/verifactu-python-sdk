"""Query request and response models.

Maps to ConsultaLR.xsd and RespuestaConsultaLR.xsd.
Query operations are only available in VERI*FACTU mode.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from verifactu.models.enums import (
    EstadoRegistroConsulta,
    Periodo,
    ResultadoConsulta,
    SiNo,
    TipoHuella,
)
from verifactu.models.identifiers import (
    IDFactura,
    PersonaFisicaJuridica,
    PersonaFisicaJuridicaES,
)


# ---------------------------------------------------------------------------
# Query request models
# ---------------------------------------------------------------------------
class PeriodoImputacion(BaseModel):
    """Tax period (year + month)."""

    ejercicio: str = Field(min_length=4, max_length=4, pattern=r"^\d{4}$")
    """Year in YYYY format."""

    periodo: Periodo
    """Month (01-12)."""


class RangoFechaExpedicion(BaseModel):
    """Date range for filtering by issue date."""

    desde: str | None = Field(default=None, min_length=10, max_length=10)
    """Start date DD-MM-YYYY. Optional."""

    hasta: str | None = Field(default=None, min_length=10, max_length=10)
    """End date DD-MM-YYYY. Optional."""


class ClavePaginacion(BaseModel):
    """Pagination key for query results exceeding 10,000 records."""

    id_emisor_factura: str = Field(min_length=9, max_length=9)
    num_serie_factura: str = Field(min_length=1, max_length=60)
    fecha_expedicion_factura: str = Field(min_length=10, max_length=10)


class FiltroConsulta(BaseModel):
    """Query filter criteria."""

    periodo_imputacion: PeriodoImputacion
    """Required: tax period to query."""

    num_serie_factura: str | None = Field(default=None, max_length=60)
    """Filter by specific invoice number. Optional."""

    contraparte: PersonaFisicaJuridica | None = None
    """Filter by counterparty. Optional."""

    fecha_expedicion_factura: str | None = Field(default=None, min_length=10, max_length=10)
    """Filter by exact issue date DD-MM-YYYY. Optional."""

    rango_fecha_expedicion: RangoFechaExpedicion | None = None
    """Filter by date range. Optional."""

    ref_externa: str | None = Field(default=None, max_length=60)
    """Filter by external reference. Optional."""

    clave_paginacion: ClavePaginacion | None = None
    """Pagination key from a previous response. Optional."""


class ConsultaFactura(BaseModel):
    """Invoice query request.

    Maps to XSD ``ConsultaFactuSistemaFacturacionType``.
    """

    # Header
    obligado_emision: PersonaFisicaJuridicaES | None = None
    """Query by issuer. Mutually exclusive with destinatario."""

    destinatario: PersonaFisicaJuridicaES | None = None
    """Query by recipient. Mutually exclusive with obligado_emision."""

    indicador_representante: SiNo | None = None
    """'S' if the query is made by a representative."""

    # Filter
    filtro_consulta: FiltroConsulta
    """Query filter criteria."""

    # Additional response options
    mostrar_nombre_razon_emisor: SiNo | None = None
    """'S' to include issuer name in response (slower for recipient queries)."""

    mostrar_sistema_informatico: SiNo | None = None
    """'S' to include system info in response (slower)."""


# ---------------------------------------------------------------------------
# Query response models
# ---------------------------------------------------------------------------
class EstadoRegFactu(BaseModel):
    """Record status in query responses."""

    timestamp_ultima_modificacion: datetime
    estado_registro: EstadoRegistroConsulta
    codigo_error_registro: int | None = None
    descripcion_error_registro: str | None = None


class DatosRegistroFacturacion(BaseModel):
    """Invoice record data returned in query responses."""

    nombre_razon_emisor: str | None = None
    tipo_factura: str | None = None
    descripcion_operacion: str | None = None
    destinatarios: list[PersonaFisicaJuridica] | None = None
    cuota_total: str | None = None
    importe_total: str | None = None
    fecha_hora_huso_gen_registro: str | None = None
    tipo_huella: TipoHuella | None = None
    huella: str | None = None


class RegistroRespuestaConsulta(BaseModel):
    """Single record in a query response."""

    id_factura: IDFactura
    datos_registro_facturacion: DatosRegistroFacturacion
    estado_registro: EstadoRegFactu


class RespuestaConsulta(BaseModel):
    """Full query response.

    Maps to XSD ``RespuestaConsultaFactuSistemaFacturacionType``.
    """

    periodo_imputacion: PeriodoImputacion
    """Queried tax period."""

    indicador_paginacion: SiNo
    """'S' if there are more results available."""

    resultado_consulta: ResultadoConsulta
    """ConDatos or SinDatos."""

    registros: list[RegistroRespuestaConsulta] = Field(default_factory=list)
    """Query result records (0-10,000)."""

    clave_paginacion: ClavePaginacion | None = None
    """Pagination key for fetching next page."""

    @property
    def has_more_pages(self) -> bool:
        return self.indicador_paginacion == SiNo.SI

    @property
    def has_data(self) -> bool:
        return self.resultado_consulta == ResultadoConsulta.CON_DATOS
