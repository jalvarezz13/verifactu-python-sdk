from __future__ import annotations

from datetime import datetime
import importlib
from typing import Any

etree = importlib.import_module("lxml.etree")
Element = Any

from verifactu.exceptions import SOAPFaultError
from verifactu.models.enums import (
    EstadoEnvio,
    EstadoRegistro,
    EstadoRegistroConsulta,
    ResultadoConsulta,
    SiNo,
    TipoHuella,
    TipoOperacion,
)
from verifactu.models.identifiers import IDFactura, IDOtro, PersonaFisicaJuridica
from verifactu.models.query import (
    ClavePaginacion,
    DatosRegistroFacturacion,
    EstadoRegFactu,
    PeriodoImputacion,
    RegistroRespuestaConsulta,
    RespuestaConsulta,
)
from verifactu.models.response import (
    DatosPresentacion,
    Operacion,
    RegistroDuplicado,
    RespuestaEnvio,
    RespuestaLinea,
)
from verifactu.xml.namespaces import NSMAP_RESPONSE


def _local_name(node: Element) -> str:
    return etree.QName(node).localname


def _children(node: Element, name: str) -> list[Element]:
    return [child for child in node if _local_name(child) == name]


def _child(node: Element, name: str) -> Element | None:
    for child in node:
        if _local_name(child) == name:
            return child
    return None


def _first_desc(node: Element, name: str) -> Element | None:
    for child in node.iterdescendants():
        if _local_name(child) == name:
            return child
    return None


def _xpath_first(node: Element, expr: str) -> Element | None:
    result = node.xpath(expr, namespaces=NSMAP_RESPONSE)
    if not result:
        return None
    return result[0]


def _text(node: Element | None, name: str) -> str | None:
    if node is None:
        return None
    child = _child(node, name)
    if child is None or child.text is None:
        return None
    value = child.text.strip()
    return value or None


def _text_desc(node: Element | None, name: str) -> str | None:
    if node is None:
        return None
    child = _first_desc(node, name)
    if child is None or child.text is None:
        return None
    value = child.text.strip()
    return value or None


def _int_or_none(value: str | None) -> int | None:
    if value is None:
        return None
    return int(value)


def _parse_id_otro(node: Element | None) -> IDOtro | None:
    if node is None:
        return None
    return IDOtro(
        codigo_pais=_text(node, "CodigoPais"),
        id_type=_text(node, "IDType"),
        id=_text(node, "ID"),
    )


def _parse_persona(node: Element | None) -> PersonaFisicaJuridica | None:
    if node is None:
        return None
    id_otro = _parse_id_otro(_child(node, "IDOtro"))
    return PersonaFisicaJuridica(
        nombre_razon=_text(node, "NombreRazon"),
        nif=_text(node, "NIF"),
        id_otro=id_otro,
    )


def _parse_id_factura(node: Element | None) -> IDFactura:
    if node is None:
        raise ValueError("Missing IDFactura in response")
    id_emisor = _text(node, "IDEmisorFactura") or _text(node, "IDEmisorFacturaAnulada")
    num_serie = _text(node, "NumSerieFactura") or _text(node, "NumSerieFacturaAnulada")
    fecha = _text(node, "FechaExpedicionFactura") or _text(node, "FechaExpedicionFacturaAnulada")
    return IDFactura(
        id_emisor_factura=id_emisor,
        num_serie_factura=num_serie,
        fecha_expedicion_factura=fecha,
    )


def _parse_fault(root: Element) -> SOAPFaultError | None:
    fault = _xpath_first(root, "//env:Fault")
    if fault is None:
        fault = _first_desc(root, "Fault")
    if fault is None:
        return None
    detail_node = _child(fault, "detail")
    detail_text = None
    if detail_node is not None:
        detail_text = " ".join(part.strip() for part in detail_node.itertext() if part.strip()) or None
    return SOAPFaultError(
        fault_code=_text(fault, "faultcode") or "",
        fault_string=_text(fault, "faultstring") or "",
        detail=detail_text,
    )


def parse_soap_fault(xml_bytes: bytes) -> None:
    root = etree.fromstring(xml_bytes)
    fault = _parse_fault(root)
    if fault is not None:
        raise fault


def _parse_datos_presentacion(node: Element | None) -> DatosPresentacion | None:
    if node is None:
        return None
    timestamp = _text(node, "TimestampPresentacion")
    if timestamp is None:
        return None
    return DatosPresentacion(
        nif_presentador=_text(node, "NIFPresentador"),
        timestamp_presentacion=timestamp,
    )


def _parse_operacion(node: Element | None) -> Operacion:
    if node is None:
        raise ValueError("Missing Operacion in response line")
    return Operacion(
        tipo_operacion=TipoOperacion(_text(node, "TipoOperacion")),
        subsanacion=_text(node, "Subsanacion"),
        rechazo_previo=_text(node, "RechazoPrevio"),
        sin_registro_previo=_text(node, "SinRegistroPrevio"),
    )


def _parse_registro_duplicado(node: Element | None) -> RegistroDuplicado | None:
    if node is None:
        return None
    return RegistroDuplicado(
        id_peticion_registro_duplicado=_text(node, "IdPeticionRegistroDuplicado"),
        estado_registro_duplicado=EstadoRegistroConsulta(_text(node, "EstadoRegistroDuplicado")),
        codigo_error_registro=_int_or_none(_text(node, "CodigoErrorRegistro")),
        descripcion_error_registro=_text(node, "DescripcionErrorRegistro"),
    )


def _parse_respuesta_linea(node: Element) -> RespuestaLinea:
    return RespuestaLinea(
        id_factura=_parse_id_factura(_child(node, "IDFactura")),
        operacion=_parse_operacion(_child(node, "Operacion")),
        ref_externa=_text(node, "RefExterna"),
        estado_registro=EstadoRegistro(_text(node, "EstadoRegistro")),
        codigo_error_registro=_int_or_none(_text(node, "CodigoErrorRegistro")),
        descripcion_error_registro=_text(node, "DescripcionErrorRegistro"),
        registro_duplicado=_parse_registro_duplicado(_child(node, "RegistroDuplicado")),
    )


def parse_submit_response(xml_bytes: bytes) -> RespuestaEnvio:
    root = etree.fromstring(xml_bytes)
    fault = _parse_fault(root)
    if fault is not None:
        raise fault

    payload = _xpath_first(root, "//sfR:RespuestaRegFactuSistemaFacturacion")
    if payload is None:
        payload = _xpath_first(root, "//sfR:RegFactuSistemaFacturacionRespuesta")
    if payload is None:
        payload = _xpath_first(root, "//sf:RespuestaRegFactuSistemaFacturacion")
    if payload is None:
        payload = _first_desc(root, "RegFactuSistemaFacturacionRespuesta")
    if payload is None:
        payload = root

    line_nodes = [node for node in payload.iterdescendants() if _local_name(node) == "RespuestaLinea"]
    return RespuestaEnvio(
        csv=_text_desc(payload, "CSV"),
        datos_presentacion=_parse_datos_presentacion(_first_desc(payload, "DatosPresentacion")),
        tiempo_espera_envio=_int_or_none(_text_desc(payload, "TiempoEsperaEnvio")) or 60,
        estado_envio=EstadoEnvio(_text_desc(payload, "EstadoEnvio")),
        respuesta_linea=[_parse_respuesta_linea(node) for node in line_nodes],
    )


def _parse_periodo_imputacion(node: Element | None) -> PeriodoImputacion:
    if node is None:
        raise ValueError("Missing PeriodoImputacion in query response")
    return PeriodoImputacion(
        ejercicio=_text(node, "Ejercicio"),
        periodo=_text(node, "Periodo"),
    )


def _parse_destinatarios(node: Element | None) -> list[PersonaFisicaJuridica] | None:
    if node is None:
        return None
    destinatarios: list[PersonaFisicaJuridica] = []
    for item in _children(node, "IDDestinatario"):
        destinatario = _parse_persona(item)
        if destinatario is not None:
            destinatarios.append(destinatario)
    return destinatarios or None


def _parse_datos_registro_facturacion(node: Element | None) -> DatosRegistroFacturacion:
    if node is None:
        return DatosRegistroFacturacion()
    return DatosRegistroFacturacion(
        nombre_razon_emisor=_text(node, "NombreRazonEmisor"),
        tipo_factura=_text(node, "TipoFactura"),
        descripcion_operacion=_text(node, "DescripcionOperacion"),
        destinatarios=_parse_destinatarios(_child(node, "Destinatarios")),
        cuota_total=_text(node, "CuotaTotal"),
        importe_total=_text(node, "ImporteTotal"),
        fecha_hora_huso_gen_registro=_text(node, "FechaHoraHusoGenRegistro"),
        tipo_huella=_text(node, "TipoHuella"),
        huella=_text(node, "Huella"),
    )


def _parse_estado_reg_factu(node: Element | None) -> EstadoRegFactu:
    if node is None:
        raise ValueError("Missing EstadoRegistro block in query response")
    timestamp = _text(node, "TimestampUltimaModificacion") or _text(node, "TimestampEstado")
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()
    return EstadoRegFactu(
        timestamp_ultima_modificacion=timestamp,
        estado_registro=EstadoRegistroConsulta(_text(node, "EstadoRegistro")),
        codigo_error_registro=_int_or_none(_text(node, "CodigoErrorRegistro")),
        descripcion_error_registro=_text(node, "DescripcionErrorRegistro"),
    )


def _parse_registro_respuesta_consulta(node: Element) -> RegistroRespuestaConsulta:
    return RegistroRespuestaConsulta(
        id_factura=_parse_id_factura(_first_desc(node, "IDFactura")),
        datos_registro_facturacion=_parse_datos_registro_facturacion(
            _first_desc(node, "DatosRegistroFacturacion"),
        ),
        estado_registro=_parse_estado_reg_factu(_first_desc(node, "EstadoRegistro")),
    )


def _parse_clave_paginacion(node: Element | None) -> ClavePaginacion | None:
    if node is None:
        return None
    return ClavePaginacion(
        id_emisor_factura=_text(node, "IDEmisorFactura"),
        num_serie_factura=_text(node, "NumSerieFactura"),
        fecha_expedicion_factura=_text(node, "FechaExpedicionFactura"),
    )


def parse_query_response(xml_bytes: bytes) -> RespuestaConsulta:
    root = etree.fromstring(xml_bytes)
    fault = _parse_fault(root)
    if fault is not None:
        raise fault

    payload = _xpath_first(root, "//sfLRRC:RespuestaConsultaFactuSistemaFacturacion")
    if payload is None:
        payload = _xpath_first(root, "//sfLRRC:ConsultaFactuSistemaFacturacionRespuesta")
    if payload is None:
        payload = _xpath_first(root, "//sf:RespuestaConsultaFactuSistemaFacturacion")
    if payload is None:
        payload = _first_desc(root, "ConsultaFactuSistemaFacturacionRespuesta")
    if payload is None:
        payload = root

    registros: list[RegistroRespuestaConsulta] = []
    for node in payload.iterdescendants():
        if _local_name(node) != "RegistroRespuestaConsulta":
            continue
        registros.append(_parse_registro_respuesta_consulta(node))

    return RespuestaConsulta(
        periodo_imputacion=_parse_periodo_imputacion(_first_desc(payload, "PeriodoImputacion")),
        indicador_paginacion=SiNo(_text_desc(payload, "IndicadorPaginacion")),
        resultado_consulta=ResultadoConsulta(_text_desc(payload, "ResultadoConsulta")),
        registros=registros,
        clave_paginacion=_parse_clave_paginacion(_first_desc(payload, "ClavePaginacion")),
    )


def parse_response(xml_bytes: bytes) -> RespuestaEnvio | RespuestaConsulta:
    root = etree.fromstring(xml_bytes)
    fault = _parse_fault(root)
    if fault is not None:
        raise fault

    if _xpath_first(root, "//sfLRRC:RespuestaConsultaFactuSistemaFacturacion") is not None:
        return parse_query_response(xml_bytes)
    if _xpath_first(root, "//sfR:RespuestaRegFactuSistemaFacturacion") is not None:
        return parse_submit_response(xml_bytes)

    if _first_desc(root, "RespuestaConsultaFactuSistemaFacturacion") is not None:
        return parse_query_response(xml_bytes)
    if _first_desc(root, "RespuestaRegFactuSistemaFacturacion") is not None:
        return parse_submit_response(xml_bytes)

    body = _first_desc(root, "Body")
    if body is not None:
        payload = next((child for child in body if _local_name(child) != "Fault"), None)
        if payload is not None:
            payload_name = _local_name(payload)
            if "Consulta" in payload_name:
                return parse_query_response(xml_bytes)
            if "RegFactu" in payload_name or "Suministro" in payload_name:
                return parse_submit_response(xml_bytes)

    if _first_desc(root, "ResultadoConsulta") is not None:
        return parse_query_response(xml_bytes)
    return parse_submit_response(xml_bytes)
