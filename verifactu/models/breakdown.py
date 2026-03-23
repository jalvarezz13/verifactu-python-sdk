"""Tax breakdown models matching AEAT XSD DetalleType / DesgloseType.

Represents the tax detail lines (desglose) within an invoice record.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from verifactu.models.enums import (
    CalificacionOperacion,
    ClaveRegimen,
    OperacionExenta,
    TipoImpuesto,
)


class DetalleDesglose(BaseModel):
    """Single tax breakdown line.

    Maps to XSD ``DetalleType``. Either ``calificacion_operacion`` or
    ``operacion_exenta`` must be provided (mutually exclusive choice in XSD).
    """

    impuesto: TipoImpuesto | None = None
    """Tax type (01=IVA, 02=IPSI, 03=IGIC, 05=Otros). Optional."""

    clave_regimen: ClaveRegimen | None = None
    """Tax regime key. Optional."""

    calificacion_operacion: CalificacionOperacion | None = None
    """Operation qualification (S1, S2, N1, N2). Mutually exclusive with operacion_exenta."""

    operacion_exenta: OperacionExenta | None = None
    """Exempt operation code (E1-E8). Mutually exclusive with calificacion_operacion."""

    tipo_impositivo: str | None = Field(default=None, pattern=r"^\d{1,3}(\.\d{0,2})?$")
    """Tax rate (e.g. '21', '10', '4'). Format: up to 3 integer + 2 decimal digits."""

    base_imponible_o_importe_no_sujeto: str = Field(
        pattern=r"^(\+|-)?\d{1,12}(\.\d{0,2})?$",
    )
    """Tax base or non-subject amount (BaseImponibleOimporteNoSujeto)."""

    base_imponible_a_coste: str | None = Field(
        default=None,
        pattern=r"^(\+|-)?\d{1,12}(\.\d{0,2})?$",
    )
    """Tax base at cost. Optional."""

    cuota_repercutida: str | None = Field(
        default=None,
        pattern=r"^(\+|-)?\d{1,12}(\.\d{0,2})?$",
    )
    """Tax amount charged (CuotaRepercutida). Optional."""

    tipo_recargo_equivalencia: str | None = Field(
        default=None,
        pattern=r"^\d{1,3}(\.\d{0,2})?$",
    )
    """Equivalence surcharge rate. Optional."""

    cuota_recargo_equivalencia: str | None = Field(
        default=None,
        pattern=r"^(\+|-)?\d{1,12}(\.\d{0,2})?$",
    )
    """Equivalence surcharge amount. Optional."""

    @model_validator(mode="after")
    def _validate_qualification_choice(self) -> DetalleDesglose:
        """Exactly one of calificacion_operacion or operacion_exenta must be set."""
        has_calificacion = self.calificacion_operacion is not None
        has_exenta = self.operacion_exenta is not None
        if has_calificacion == has_exenta:
            msg = (
                "Exactly one of 'calificacion_operacion' or 'operacion_exenta' "
                "must be provided"
            )
            raise ValueError(msg)
        return self


class Desglose(BaseModel):
    """Tax breakdown container (up to 12 detail lines).

    Maps to XSD ``DesgloseType``.
    """

    detalle_desglose: list[DetalleDesglose] = Field(min_length=1, max_length=12)
    """List of tax breakdown detail lines (1-12)."""


class DesgloseRectificacion(BaseModel):
    """Rectification breakdown for substitutive corrective invoices.

    Maps to XSD ``DesgloseRectificacionType``.
    """

    base_rectificada: str = Field(pattern=r"^(\+|-)?\d{1,12}(\.\d{0,2})?$")
    """Rectified tax base amount."""

    cuota_rectificada: str = Field(pattern=r"^(\+|-)?\d{1,12}(\.\d{0,2})?$")
    """Rectified tax amount."""

    cuota_recargo_rectificado: str | None = Field(
        default=None,
        pattern=r"^(\+|-)?\d{1,12}(\.\d{0,2})?$",
    )
    """Rectified equivalence surcharge amount. Optional."""
