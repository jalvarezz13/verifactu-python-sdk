"""Identity and invoice identifier models matching AEAT XSD types.

Maps to: PersonaFisicaJuridicaESType, PersonaFisicaJuridicaType,
IDOtroType, IDFacturaExpedidaType, IDFacturaExpedidaBajaType.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from verifactu.models.enums import TipoIdentificacion


class PersonaFisicaJuridicaES(BaseModel):
    """Spanish natural or legal person (NIF required).

    Maps to XSD ``PersonaFisicaJuridicaESType``.
    """

    nombre_razon: str = Field(max_length=120)
    """Name or business name (NombreRazon)."""

    nif: str = Field(min_length=9, max_length=9)
    """Spanish tax identification number (NIF) — exactly 9 characters."""


class IDOtro(BaseModel):
    """Foreign identification for non-Spanish persons.

    Maps to XSD ``IDOtroType``.
    """

    codigo_pais: str | None = Field(default=None, min_length=2, max_length=2)
    """ISO 3166-1 alpha-2 country code (optional)."""

    id_type: TipoIdentificacion
    """Identification type (02=NIF-IVA, 03=Passport, etc.)."""

    id: str = Field(max_length=20)
    """Identification number."""


class PersonaFisicaJuridica(BaseModel):
    """Natural or legal person — Spanish or foreign.

    Maps to XSD ``PersonaFisicaJuridicaType``.
    Uses either ``nif`` (Spanish) or ``id_otro`` (foreign), not both.
    """

    nombre_razon: str = Field(max_length=120)
    """Name or business name."""

    nif: str | None = Field(default=None, min_length=9, max_length=9)
    """Spanish NIF (mutually exclusive with id_otro)."""

    id_otro: IDOtro | None = None
    """Foreign identification (mutually exclusive with nif)."""

    @field_validator("id_otro")
    @classmethod
    def _nif_xor_id_otro(cls, v: IDOtro | None, info: object) -> IDOtro | None:
        data = getattr(info, "data", None)
        if data and data.get("nif") and v is not None:
            msg = "Provide either 'nif' or 'id_otro', not both"
            raise ValueError(msg)
        return v


class IDFactura(BaseModel):
    """Invoice identifier for registration (alta) operations.

    Maps to XSD ``IDFacturaExpedidaType``.
    """

    id_emisor_factura: str = Field(min_length=9, max_length=9)
    """NIF of the invoice issuer (IDEmisorFactura)."""

    num_serie_factura: str = Field(min_length=1, max_length=60)
    """Invoice series + number (NumSerieFactura)."""

    fecha_expedicion_factura: str = Field(min_length=10, max_length=10)
    """Issue date in DD-MM-YYYY format (FechaExpedicionFactura)."""

    @field_validator("fecha_expedicion_factura")
    @classmethod
    def _validate_date_format(cls, v: str) -> str:
        """Validate DD-MM-YYYY format."""
        import re

        if not re.match(r"^\d{2}-\d{2}-\d{4}$", v):
            msg = f"Date must be DD-MM-YYYY format, got: {v}"
            raise ValueError(msg)
        return v


class IDFacturaBaja(BaseModel):
    """Invoice identifier for cancellation (anulación) operations.

    Maps to XSD ``IDFacturaExpedidaBajaType``.
    """

    id_emisor_factura_anulada: str = Field(min_length=9, max_length=9)
    """NIF of the issuer of the cancelled invoice."""

    num_serie_factura_anulada: str = Field(min_length=1, max_length=60)
    """Series + number of the cancelled invoice."""

    fecha_expedicion_factura_anulada: str = Field(min_length=10, max_length=10)
    """Issue date of the cancelled invoice in DD-MM-YYYY format."""

    @field_validator("fecha_expedicion_factura_anulada")
    @classmethod
    def _validate_date_format(cls, v: str) -> str:
        import re

        if not re.match(r"^\d{2}-\d{2}-\d{4}$", v):
            msg = f"Date must be DD-MM-YYYY format, got: {v}"
            raise ValueError(msg)
        return v


class IDFacturaAR(BaseModel):
    """Identifier for rectified or substituted invoices.

    Maps to XSD ``IDFacturaARType``.
    """

    id_emisor_factura: str = Field(min_length=9, max_length=9)
    num_serie_factura: str = Field(min_length=1, max_length=60)
    fecha_expedicion_factura: str = Field(min_length=10, max_length=10)

    @field_validator("fecha_expedicion_factura")
    @classmethod
    def _validate_date_format(cls, v: str) -> str:
        import re

        if not re.match(r"^\d{2}-\d{2}-\d{4}$", v):
            msg = f"Date must be DD-MM-YYYY format, got: {v}"
            raise ValueError(msg)
        return v


class Encadenamiento(BaseModel):
    """Chain link to the previous record.

    Maps to XSD ``EncadenamientoFacturaAnteriorType``.
    For the first record in a chain, use ``primer_registro=True`` instead.
    """

    primer_registro: bool = False
    """If True, this is the first record in the chain (PrimerRegistro=S)."""

    # Fields for RegistroAnterior (used when primer_registro=False)
    id_emisor_factura: str | None = Field(default=None, min_length=9, max_length=9)
    num_serie_factura: str | None = Field(default=None, max_length=60)
    fecha_expedicion_factura: str | None = Field(default=None, min_length=10, max_length=10)
    huella: str | None = Field(default=None, max_length=64)
