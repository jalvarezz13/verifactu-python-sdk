"""AEAT Verifactu XML namespace constants.

These match the namespace URIs defined in the official XSD schemas and WSDL.
Prefix aliases follow the conventions used in AEAT's example XML documents.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# SOAP
# ---------------------------------------------------------------------------
NS_SOAPENV = "http://schemas.xmlsoap.org/soap/envelope/"

# ---------------------------------------------------------------------------
# AEAT Verifactu schemas — targetNamespace from each XSD
# ---------------------------------------------------------------------------
NS_SUMINISTRO_INFO = (
    "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/"
    "aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd"
)
NS_SUMINISTRO_LR = (
    "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/"
    "aplicaciones/es/aeat/tike/cont/ws/SuministroLR.xsd"
)
NS_RESPUESTA = (
    "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/"
    "aplicaciones/es/aeat/tike/cont/ws/RespuestaSuministro.xsd"
)
NS_CONSULTA = (
    "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/"
    "aplicaciones/es/aeat/tike/cont/ws/ConsultaLR.xsd"
)
NS_RESPUESTA_CONSULTA = (
    "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/"
    "aplicaciones/es/aeat/tike/cont/ws/RespuestaConsultaLR.xsd"
)
NS_XMLDSIG = "http://www.w3.org/2000/09/xmldsig#"

# ---------------------------------------------------------------------------
# Namespace map for lxml — prefix : URI
# ---------------------------------------------------------------------------
NSMAP_SUBMIT = {
    "soapenv": NS_SOAPENV,
    "sum": NS_SUMINISTRO_LR,
    "sum1": NS_SUMINISTRO_INFO,
}

NSMAP_QUERY = {
    "soapenv": NS_SOAPENV,
    "con": NS_CONSULTA,
    "sum": NS_SUMINISTRO_INFO,
}

NSMAP_RESPONSE = {
    "env": NS_SOAPENV,
    "sf": NS_SUMINISTRO_INFO,
    "sfR": NS_RESPUESTA,
    "sfLRRC": NS_RESPUESTA_CONSULTA,
}
