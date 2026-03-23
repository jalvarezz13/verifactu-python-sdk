"""AEAT Verifactu enumerations derived from XSD schemas.

Each enum maps directly to an XSD simpleType restriction with enumeration values.
Docstrings reference the official AEAT XSD documentation.
"""

from __future__ import annotations

from enum import Enum


# ---------------------------------------------------------------------------
# Invoice types — ClaveTipoFacturaType
# ---------------------------------------------------------------------------
class TipoFactura(str, Enum):
    """Invoice type codes (Art. 6, 7 RD 1619/2012)."""

    F1 = "F1"
    """Factura (Art. 6, 7.2 y 7.3 del RD 1619/2012)."""

    F2 = "F2"
    """Factura simplificada y facturas sin identificación del destinatario Art. 6.1.d)."""

    F3 = "F3"
    """Factura emitida en sustitución de facturas simplificadas facturadas y declaradas."""

    R1 = "R1"
    """Factura rectificativa (Art. 80.1, 80.2 y error fundado en derecho)."""

    R2 = "R2"
    """Factura rectificativa (Art. 80.3)."""

    R3 = "R3"
    """Factura rectificativa (Art. 80.4)."""

    R4 = "R4"
    """Factura rectificativa (Resto)."""

    R5 = "R5"
    """Factura rectificativa en facturas simplificadas."""


# ---------------------------------------------------------------------------
# Corrective invoice type — ClaveTipoRectificativaType
# ---------------------------------------------------------------------------
class TipoRectificativa(str, Enum):
    """Corrective invoice method."""

    SUSTITUTIVA = "S"
    """Replacement (sustitución)."""

    INCREMENTAL = "I"
    """Incremental (diferencia)."""


# ---------------------------------------------------------------------------
# Tax qualification — CalificacionOperacionType
# ---------------------------------------------------------------------------
class CalificacionOperacion(str, Enum):
    """Operation tax qualification."""

    S1 = "S1"
    """Sujeta y no exenta — sin inversión del sujeto pasivo."""

    S2 = "S2"
    """Sujeta y no exenta — con inversión del sujeto pasivo."""

    N1 = "N1"
    """No sujeta — Artículo 7, 14, otros."""

    N2 = "N2"
    """No sujeta — por reglas de localización."""


# ---------------------------------------------------------------------------
# Exempt operation — OperacionExentaType
# ---------------------------------------------------------------------------
class OperacionExenta(str, Enum):
    """Exempt operation cause codes."""

    E1 = "E1"
    E2 = "E2"
    E3 = "E3"
    E4 = "E4"
    E5 = "E5"
    E6 = "E6"
    E7 = "E7"
    E8 = "E8"


# ---------------------------------------------------------------------------
# Tax type — ImpuestoType
# ---------------------------------------------------------------------------
class TipoImpuesto(str, Enum):
    """Tax type identifier."""

    IVA = "01"
    """Impuesto sobre el Valor Añadido."""

    IPSI = "02"
    """Impuesto sobre la Producción, los Servicios y la Importación (Ceuta y Melilla)."""

    IGIC = "03"
    """Impuesto General Indirecto Canario."""

    OTROS = "05"
    """Otros."""


# ---------------------------------------------------------------------------
# Tax regime keys — IdOperacionesTrascendenciaTributariaType
# ---------------------------------------------------------------------------
class ClaveRegimen(str, Enum):
    """Tax regime key codes."""

    C01 = "01"
    C02 = "02"
    C03 = "03"
    C04 = "04"
    C05 = "05"
    C06 = "06"
    C07 = "07"
    C08 = "08"
    C09 = "09"
    C10 = "10"
    C11 = "11"
    C14 = "14"
    C15 = "15"
    C17 = "17"
    C18 = "18"
    C19 = "19"
    C20 = "20"
    C21 = "21"


# ---------------------------------------------------------------------------
# Hash type — TipoHuellaType
# ---------------------------------------------------------------------------
class TipoHuella(str, Enum):
    """Hash algorithm identifier. Currently only SHA-256."""

    SHA256 = "01"
    """SHA-256."""


# ---------------------------------------------------------------------------
# ID type for foreign persons — PersonaFisicaJuridicaIDTypeType
# ---------------------------------------------------------------------------
class TipoIdentificacion(str, Enum):
    """Foreign person identification type."""

    NIF_IVA = "02"
    """NIF-IVA."""

    PASAPORTE = "03"
    """Passport."""

    ID_PAIS_RESIDENCIA = "04"
    """ID in country of residence."""

    CERTIFICADO_RESIDENCIA = "05"
    """Residence certificate."""

    OTRO_DOCUMENTO = "06"
    """Other supporting document."""

    NO_CENSADO = "07"
    """Not registered in census."""


# ---------------------------------------------------------------------------
# S/N flags — SiNoType
# ---------------------------------------------------------------------------
class SiNo(str, Enum):
    """Boolean flag as S(í)/N(o)."""

    SI = "S"
    NO = "N"


# ---------------------------------------------------------------------------
# Third party or recipient — TercerosODestinatarioType
# ---------------------------------------------------------------------------
class TerceroODestinatario(str, Enum):
    """Who issued the invoice on behalf of the obligated party."""

    DESTINATARIO = "D"
    """Recipient (destinatario)."""

    TERCERO = "T"
    """Third party (tercero)."""


# ---------------------------------------------------------------------------
# Who generated the cancellation — GeneradoPorType
# ---------------------------------------------------------------------------
class GeneradoPor(str, Enum):
    """Who generated the cancellation record."""

    EXPEDIDOR = "E"
    """Issuer (obligado a expedir la factura anulada)."""

    DESTINATARIO = "D"
    """Recipient."""

    TERCERO = "T"
    """Third party."""


# ---------------------------------------------------------------------------
# Response statuses — from RespuestaSuministro.xsd
# ---------------------------------------------------------------------------
class EstadoEnvio(str, Enum):
    """Submission-level status."""

    CORRECTO = "Correcto"
    PARCIALMENTE_CORRECTO = "ParcialmenteCorrecto"
    INCORRECTO = "Incorrecto"


class EstadoRegistro(str, Enum):
    """Individual record status."""

    CORRECTO = "Correcto"
    ACEPTADO_CON_ERRORES = "AceptadoConErrores"
    INCORRECTO = "Incorrecto"


class EstadoRegistroConsulta(str, Enum):
    """Record status in query responses."""

    CORRECTO = "Correcto"
    ACEPTADO_CON_ERRORES = "AceptadoConErrores"
    ANULADO = "Anulado"


class ResultadoConsulta(str, Enum):
    """Query result indicator."""

    CON_DATOS = "ConDatos"
    SIN_DATOS = "SinDatos"


class TipoOperacion(str, Enum):
    """Operation type in response."""

    ALTA = "Alta"
    ANULACION = "Anulacion"


# ---------------------------------------------------------------------------
# Period — TipoPeriodoType
# ---------------------------------------------------------------------------
class Periodo(str, Enum):
    """Tax period (month)."""

    ENERO = "01"
    FEBRERO = "02"
    MARZO = "03"
    ABRIL = "04"
    MAYO = "05"
    JUNIO = "06"
    JULIO = "07"
    AGOSTO = "08"
    SEPTIEMBRE = "09"
    OCTUBRE = "10"
    NOVIEMBRE = "11"
    DICIEMBRE = "12"
