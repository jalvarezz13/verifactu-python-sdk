from __future__ import annotations

from enum import Enum
import importlib
from typing import Any

etree = importlib.import_module("lxml.etree")
Element = Any

from verifactu.models.breakdown import Desglose, DesgloseRectificacion, DetalleDesglose
from verifactu.models.cancellation import RegistroAnulacion
from verifactu.models.header import Cabecera, RemisionRequerimiento, RemisionVoluntaria
from verifactu.models.identifiers import (
    Encadenamiento,
    IDFactura,
    IDFacturaAR,
    IDFacturaBaja,
    IDOtro,
    PersonaFisicaJuridica,
    PersonaFisicaJuridicaES,
)
from verifactu.models.invoice import RegistroAlta
from verifactu.models.query import ClavePaginacion, ConsultaFactura, FiltroConsulta
from verifactu.models.system import SistemaInformatico
from verifactu.xml.namespaces import (
    NS_CONSULTA,
    NS_SOAPENV,
    NS_SUMINISTRO_INFO,
    NS_SUMINISTRO_LR,
    NSMAP_QUERY,
    NSMAP_SUBMIT,
)


def _qname(ns: str, tag: str) -> str:
    return f"{{{ns}}}{tag}"


def _enum_or_value(value: object) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def _add_text(parent: Element, ns: str, tag: str, value: object | None) -> Element | None:
    if value is None:
        return None
    element = etree.SubElement(parent, _qname(ns, tag))
    element.text = _enum_or_value(value)
    return element


def _append_id_otro(parent: Element, ns: str, id_otro: IDOtro, tag: str = "IDOtro") -> Element:
    node = etree.SubElement(parent, _qname(ns, tag))
    _add_text(node, ns, "CodigoPais", id_otro.codigo_pais)
    _add_text(node, ns, "IDType", id_otro.id_type)
    _add_text(node, ns, "ID", id_otro.id)
    return node


def _append_persona_es(parent: Element, ns: str, tag: str, persona: PersonaFisicaJuridicaES) -> Element:
    node = etree.SubElement(parent, _qname(ns, tag))
    _add_text(node, ns, "NombreRazon", persona.nombre_razon)
    _add_text(node, ns, "NIF", persona.nif)
    return node


def _append_persona(parent: Element, ns: str, tag: str, persona: PersonaFisicaJuridica) -> Element:
    node = etree.SubElement(parent, _qname(ns, tag))
    _add_text(node, ns, "NombreRazon", persona.nombre_razon)
    if persona.nif is not None:
        _add_text(node, ns, "NIF", persona.nif)
    elif persona.id_otro is not None:
        _append_id_otro(node, ns, persona.id_otro)
    return node


def _append_cabecera_submit(parent: Element, cabecera: Cabecera) -> Element:
    cab = etree.SubElement(parent, _qname(NS_SUMINISTRO_LR, "Cabecera"))
    _append_persona_es(cab, NS_SUMINISTRO_INFO, "ObligadoEmision", cabecera.obligado_emision)
    if cabecera.representante is not None:
        _append_persona_es(cab, NS_SUMINISTRO_INFO, "Representante", cabecera.representante)
    if cabecera.remision_voluntaria is not None:
        _append_remision_voluntaria(cab, cabecera.remision_voluntaria)
    if cabecera.remision_requerimiento is not None:
        _append_remision_requerimiento(cab, cabecera.remision_requerimiento)
    return cab


def _append_remision_voluntaria(parent: Element, data: RemisionVoluntaria) -> Element:
    node = etree.SubElement(parent, _qname(NS_SUMINISTRO_INFO, "RemisionVoluntaria"))
    _add_text(node, NS_SUMINISTRO_INFO, "FechaFinVerifactu", data.fecha_fin_verifactu)
    _add_text(node, NS_SUMINISTRO_INFO, "Incidencia", data.incidencia)
    return node


def _append_remision_requerimiento(parent: Element, data: RemisionRequerimiento) -> Element:
    node = etree.SubElement(parent, _qname(NS_SUMINISTRO_INFO, "RemisionRequerimiento"))
    _add_text(node, NS_SUMINISTRO_INFO, "RefRequerimiento", data.ref_requerimiento)
    _add_text(node, NS_SUMINISTRO_INFO, "FinRequerimiento", data.fin_requerimiento)
    return node


def _append_id_factura(parent: Element, id_factura: IDFactura) -> Element:
    node = etree.SubElement(parent, _qname(NS_SUMINISTRO_INFO, "IDFactura"))
    _add_text(node, NS_SUMINISTRO_INFO, "IDEmisorFactura", id_factura.id_emisor_factura)
    _add_text(node, NS_SUMINISTRO_INFO, "NumSerieFactura", id_factura.num_serie_factura)
    _add_text(node, NS_SUMINISTRO_INFO, "FechaExpedicionFactura", id_factura.fecha_expedicion_factura)
    return node


def _append_id_factura_baja(parent: Element, id_factura: IDFacturaBaja) -> Element:
    node = etree.SubElement(parent, _qname(NS_SUMINISTRO_INFO, "IDFactura"))
    _add_text(node, NS_SUMINISTRO_INFO, "IDEmisorFacturaAnulada", id_factura.id_emisor_factura_anulada)
    _add_text(node, NS_SUMINISTRO_INFO, "NumSerieFacturaAnulada", id_factura.num_serie_factura_anulada)
    _add_text(node, NS_SUMINISTRO_INFO, "FechaExpedicionFacturaAnulada", id_factura.fecha_expedicion_factura_anulada)
    return node


def _append_id_factura_ar(parent: Element, tag: str, item_tag: str, facturas: list[IDFacturaAR]) -> Element:
    node = etree.SubElement(parent, _qname(NS_SUMINISTRO_INFO, tag))
    for factura in facturas:
        item = etree.SubElement(node, _qname(NS_SUMINISTRO_INFO, item_tag))
        _add_text(item, NS_SUMINISTRO_INFO, "IDEmisorFactura", factura.id_emisor_factura)
        _add_text(item, NS_SUMINISTRO_INFO, "NumSerieFactura", factura.num_serie_factura)
        _add_text(item, NS_SUMINISTRO_INFO, "FechaExpedicionFactura", factura.fecha_expedicion_factura)
    return node


def _append_importe_rectificacion(parent: Element, rectificacion: DesgloseRectificacion) -> Element:
    node = etree.SubElement(parent, _qname(NS_SUMINISTRO_INFO, "ImporteRectificacion"))
    _add_text(node, NS_SUMINISTRO_INFO, "BaseRectificada", rectificacion.base_rectificada)
    _add_text(node, NS_SUMINISTRO_INFO, "CuotaRectificada", rectificacion.cuota_rectificada)
    _add_text(node, NS_SUMINISTRO_INFO, "CuotaRecargoRectificado", rectificacion.cuota_recargo_rectificado)
    return node


def _append_detalle_desglose(parent: Element, detalle: DetalleDesglose) -> Element:
    node = etree.SubElement(parent, _qname(NS_SUMINISTRO_INFO, "DetalleDesglose"))
    _add_text(node, NS_SUMINISTRO_INFO, "Impuesto", detalle.impuesto)
    _add_text(node, NS_SUMINISTRO_INFO, "ClaveRegimen", detalle.clave_regimen)
    if detalle.calificacion_operacion is not None:
        _add_text(node, NS_SUMINISTRO_INFO, "CalificacionOperacion", detalle.calificacion_operacion)
    elif detalle.operacion_exenta is not None:
        _add_text(node, NS_SUMINISTRO_INFO, "OperacionExenta", detalle.operacion_exenta)
    _add_text(node, NS_SUMINISTRO_INFO, "TipoImpositivo", detalle.tipo_impositivo)
    _add_text(
        node,
        NS_SUMINISTRO_INFO,
        "BaseImponibleOimporteNoSujeto",
        detalle.base_imponible_o_importe_no_sujeto,
    )
    _add_text(node, NS_SUMINISTRO_INFO, "BaseImponibleACoste", detalle.base_imponible_a_coste)
    _add_text(node, NS_SUMINISTRO_INFO, "CuotaRepercutida", detalle.cuota_repercutida)
    _add_text(node, NS_SUMINISTRO_INFO, "TipoRecargoEquivalencia", detalle.tipo_recargo_equivalencia)
    _add_text(node, NS_SUMINISTRO_INFO, "CuotaRecargoEquivalencia", detalle.cuota_recargo_equivalencia)
    return node


def _append_desglose(parent: Element, desglose: Desglose) -> Element:
    node = etree.SubElement(parent, _qname(NS_SUMINISTRO_INFO, "Desglose"))
    for detalle in desglose.detalle_desglose:
        _append_detalle_desglose(node, detalle)
    return node


def _append_destinatarios(parent: Element, destinatarios: list[PersonaFisicaJuridica]) -> Element:
    node = etree.SubElement(parent, _qname(NS_SUMINISTRO_INFO, "Destinatarios"))
    for destinatario in destinatarios:
        _append_persona(node, NS_SUMINISTRO_INFO, "IDDestinatario", destinatario)
    return node


def _append_encadenamiento(parent: Element, encadenamiento: Encadenamiento) -> Element:
    node = etree.SubElement(parent, _qname(NS_SUMINISTRO_INFO, "Encadenamiento"))
    if encadenamiento.primer_registro:
        _add_text(node, NS_SUMINISTRO_INFO, "PrimerRegistro", "S")
        return node
    anterior = etree.SubElement(node, _qname(NS_SUMINISTRO_INFO, "RegistroAnterior"))
    _add_text(anterior, NS_SUMINISTRO_INFO, "IDEmisorFactura", encadenamiento.id_emisor_factura)
    _add_text(anterior, NS_SUMINISTRO_INFO, "NumSerieFactura", encadenamiento.num_serie_factura)
    _add_text(
        anterior,
        NS_SUMINISTRO_INFO,
        "FechaExpedicionFactura",
        encadenamiento.fecha_expedicion_factura,
    )
    _add_text(anterior, NS_SUMINISTRO_INFO, "Huella", encadenamiento.huella)
    return node


def _append_sistema_informatico(parent: Element, sistema: SistemaInformatico) -> Element:
    node = etree.SubElement(parent, _qname(NS_SUMINISTRO_INFO, "SistemaInformatico"))
    _add_text(node, NS_SUMINISTRO_INFO, "NombreRazon", sistema.nombre_razon)
    if sistema.nif is not None:
        _add_text(node, NS_SUMINISTRO_INFO, "NIF", sistema.nif)
    elif sistema.id_otro is not None:
        _append_id_otro(node, NS_SUMINISTRO_INFO, sistema.id_otro)
    _add_text(node, NS_SUMINISTRO_INFO, "NombreSistemaInformatico", sistema.nombre_sistema_informatico)
    _add_text(node, NS_SUMINISTRO_INFO, "IdSistemaInformatico", sistema.id_sistema_informatico)
    _add_text(node, NS_SUMINISTRO_INFO, "Version", sistema.version)
    _add_text(node, NS_SUMINISTRO_INFO, "NumeroInstalacion", sistema.numero_instalacion)
    _add_text(
        node,
        NS_SUMINISTRO_INFO,
        "TipoUsoPosibleSoloVerifactu",
        sistema.tipo_uso_posible_solo_verifactu,
    )
    _add_text(node, NS_SUMINISTRO_INFO, "TipoUsoPosibleMultiOT", sistema.tipo_uso_posible_multi_ot)
    _add_text(node, NS_SUMINISTRO_INFO, "IndicadorMultiplesOT", sistema.indicador_multiples_ot)
    return node


def _append_registro_alta(parent: Element, record: RegistroAlta) -> Element:
    node = etree.SubElement(parent, _qname(NS_SUMINISTRO_INFO, "RegistroAlta"))
    _add_text(node, NS_SUMINISTRO_INFO, "IDVersion", record.id_version)
    _append_id_factura(node, record.id_factura)
    _add_text(node, NS_SUMINISTRO_INFO, "RefExterna", record.ref_externa)
    _add_text(node, NS_SUMINISTRO_INFO, "NombreRazonEmisor", record.nombre_razon_emisor)
    _add_text(node, NS_SUMINISTRO_INFO, "Subsanacion", record.subsanacion)
    _add_text(node, NS_SUMINISTRO_INFO, "RechazoPrevio", record.rechazo_previo)
    _add_text(node, NS_SUMINISTRO_INFO, "TipoFactura", record.tipo_factura)
    _add_text(node, NS_SUMINISTRO_INFO, "TipoRectificativa", record.tipo_rectificativa)
    if record.facturas_rectificadas:
        _append_id_factura_ar(
            node,
            tag="FacturasRectificadas",
            item_tag="IDFacturaRectificada",
            facturas=record.facturas_rectificadas,
        )
    if record.facturas_sustituidas:
        _append_id_factura_ar(
            node,
            tag="FacturasSustituidas",
            item_tag="IDFacturaSustituida",
            facturas=record.facturas_sustituidas,
        )
    if record.importe_rectificacion is not None:
        _append_importe_rectificacion(node, record.importe_rectificacion)
    _add_text(node, NS_SUMINISTRO_INFO, "FechaOperacion", record.fecha_operacion)
    _add_text(node, NS_SUMINISTRO_INFO, "DescripcionOperacion", record.descripcion_operacion)
    _add_text(
        node,
        NS_SUMINISTRO_INFO,
        "FacturaSimplificadaArt7273",
        record.factura_simplificada_art7273,
    )
    _add_text(
        node,
        NS_SUMINISTRO_INFO,
        "FacturaSinIdentifDestinatarioArt61d",
        record.factura_sin_identif_destinatario_art61d,
    )
    _add_text(node, NS_SUMINISTRO_INFO, "Macrodato", record.macrodato)
    _add_text(
        node,
        NS_SUMINISTRO_INFO,
        "EmitidaPorTerceroODestinatario",
        record.emitida_por_tercero_o_destinatario,
    )
    if record.tercero is not None:
        _append_persona(node, NS_SUMINISTRO_INFO, "Tercero", record.tercero)
    if record.destinatarios:
        _append_destinatarios(node, record.destinatarios)
    _add_text(node, NS_SUMINISTRO_INFO, "Cupon", record.cupon)
    _append_desglose(node, record.desglose)
    _add_text(node, NS_SUMINISTRO_INFO, "CuotaTotal", record.cuota_total)
    _add_text(node, NS_SUMINISTRO_INFO, "ImporteTotal", record.importe_total)
    _append_encadenamiento(node, record.encadenamiento)
    _append_sistema_informatico(node, record.sistema_informatico)
    _add_text(node, NS_SUMINISTRO_INFO, "FechaHoraHusoGenRegistro", record.fecha_hora_huso_gen_registro)
    _add_text(
        node,
        NS_SUMINISTRO_INFO,
        "NumRegistroAcuerdoFacturacion",
        record.num_registro_acuerdo_facturacion,
    )
    _add_text(
        node,
        NS_SUMINISTRO_INFO,
        "IdAcuerdoSistemaInformatico",
        record.id_acuerdo_sistema_informatico,
    )
    _add_text(node, NS_SUMINISTRO_INFO, "TipoHuella", record.tipo_huella)
    _add_text(node, NS_SUMINISTRO_INFO, "Huella", record.huella)
    return node


def _append_registro_anulacion(parent: Element, record: RegistroAnulacion) -> Element:
    node = etree.SubElement(parent, _qname(NS_SUMINISTRO_INFO, "RegistroAnulacion"))
    _add_text(node, NS_SUMINISTRO_INFO, "IDVersion", record.id_version)
    _append_id_factura_baja(node, record.id_factura)
    _add_text(node, NS_SUMINISTRO_INFO, "RefExterna", record.ref_externa)
    _add_text(node, NS_SUMINISTRO_INFO, "SinRegistroPrevio", record.sin_registro_previo)
    _add_text(node, NS_SUMINISTRO_INFO, "RechazoPrevio", record.rechazo_previo)
    _add_text(node, NS_SUMINISTRO_INFO, "GeneradoPor", record.generado_por)
    if record.generador is not None:
        _append_persona(node, NS_SUMINISTRO_INFO, "Generador", record.generador)
    _append_encadenamiento(node, record.encadenamiento)
    _append_sistema_informatico(node, record.sistema_informatico)
    _add_text(node, NS_SUMINISTRO_INFO, "FechaHoraHusoGenRegistro", record.fecha_hora_huso_gen_registro)
    _add_text(node, NS_SUMINISTRO_INFO, "TipoHuella", record.tipo_huella)
    _add_text(node, NS_SUMINISTRO_INFO, "Huella", record.huella)
    return node


def build_submit_xml(cabecera: Cabecera, records: list[RegistroAlta | RegistroAnulacion]) -> bytes:
    envelope = etree.Element(_qname(NS_SOAPENV, "Envelope"), nsmap=NSMAP_SUBMIT)
    etree.SubElement(envelope, _qname(NS_SOAPENV, "Header"))
    body = etree.SubElement(envelope, _qname(NS_SOAPENV, "Body"))
    request = etree.SubElement(body, _qname(NS_SUMINISTRO_LR, "RegFactuSistemaFacturacion"))

    _append_cabecera_submit(request, cabecera)
    for record in records:
        registro = etree.SubElement(request, _qname(NS_SUMINISTRO_LR, "RegistroFactura"))
        if isinstance(record, RegistroAlta):
            _append_registro_alta(registro, record)
        elif isinstance(record, RegistroAnulacion):
            _append_registro_anulacion(registro, record)
        else:
            msg = f"Unsupported record type: {type(record)!r}"
            raise TypeError(msg)

    return etree.tostring(envelope, xml_declaration=True, encoding="utf-8")


def _append_cabecera_query(parent: Element, consulta: ConsultaFactura) -> Element:
    cabecera = etree.SubElement(parent, _qname(NS_CONSULTA, "Cabecera"))
    _add_text(cabecera, NS_SUMINISTRO_INFO, "IDVersion", "1.0")
    if consulta.obligado_emision is not None:
        _append_persona_es(cabecera, NS_SUMINISTRO_INFO, "ObligadoEmision", consulta.obligado_emision)
    if consulta.destinatario is not None:
        _append_persona_es(cabecera, NS_SUMINISTRO_INFO, "Destinatario", consulta.destinatario)
    _add_text(cabecera, NS_SUMINISTRO_INFO, "IndicadorRepresentante", consulta.indicador_representante)
    return cabecera


def _append_periodo_imputacion(parent: Element, filtro: FiltroConsulta) -> Element:
    node = etree.SubElement(parent, _qname(NS_CONSULTA, "PeriodoImputacion"))
    _add_text(node, NS_SUMINISTRO_INFO, "Ejercicio", filtro.periodo_imputacion.ejercicio)
    _add_text(node, NS_SUMINISTRO_INFO, "Periodo", filtro.periodo_imputacion.periodo)
    return node


def _append_clave_paginacion(parent: Element, clave: ClavePaginacion) -> Element:
    node = etree.SubElement(parent, _qname(NS_CONSULTA, "ClavePaginacion"))
    _add_text(node, NS_SUMINISTRO_INFO, "IDEmisorFactura", clave.id_emisor_factura)
    _add_text(node, NS_SUMINISTRO_INFO, "NumSerieFactura", clave.num_serie_factura)
    _add_text(node, NS_SUMINISTRO_INFO, "FechaExpedicionFactura", clave.fecha_expedicion_factura)
    return node


def _append_filtro_consulta(parent: Element, filtro: FiltroConsulta) -> Element:
    node = etree.SubElement(parent, _qname(NS_CONSULTA, "FiltroConsulta"))
    _append_periodo_imputacion(node, filtro)
    _add_text(node, NS_CONSULTA, "NumSerieFactura", filtro.num_serie_factura)
    if filtro.contraparte is not None:
        _append_persona(node, NS_SUMINISTRO_INFO, "Contraparte", filtro.contraparte)
    # FechaExpedicionFactura is a container element with a choice inside
    if filtro.fecha_expedicion_factura is not None or filtro.rango_fecha_expedicion is not None:
        fecha_container = etree.SubElement(
            node, _qname(NS_CONSULTA, "FechaExpedicionFactura")
        )
        if filtro.fecha_expedicion_factura is not None:
            _add_text(
                fecha_container, NS_SUMINISTRO_INFO,
                "FechaExpedicionFactura", filtro.fecha_expedicion_factura,
            )
        elif filtro.rango_fecha_expedicion is not None:
            rango = etree.SubElement(
                fecha_container, _qname(NS_SUMINISTRO_INFO, "RangoFechaExpedicion")
            )
            _add_text(rango, NS_SUMINISTRO_INFO, "Desde", filtro.rango_fecha_expedicion.desde)
            _add_text(rango, NS_SUMINISTRO_INFO, "Hasta", filtro.rango_fecha_expedicion.hasta)
    _add_text(node, NS_CONSULTA, "RefExterna", filtro.ref_externa)
    if filtro.clave_paginacion is not None:
        _append_clave_paginacion(node, filtro.clave_paginacion)
    return node


def build_query_xml(consulta: ConsultaFactura) -> bytes:
    envelope = etree.Element(_qname(NS_SOAPENV, "Envelope"), nsmap=NSMAP_QUERY)
    etree.SubElement(envelope, _qname(NS_SOAPENV, "Header"))
    body = etree.SubElement(envelope, _qname(NS_SOAPENV, "Body"))
    request = etree.SubElement(body, _qname(NS_CONSULTA, "ConsultaFactuSistemaFacturacion"))

    _append_cabecera_query(request, consulta)
    _append_filtro_consulta(request, consulta.filtro_consulta)
    _add_text(
        request,
        NS_CONSULTA,
        "MostrarNombreRazonEmisor",
        consulta.mostrar_nombre_razon_emisor,
    )
    _add_text(
        request,
        NS_CONSULTA,
        "MostrarSistemaInformatico",
        consulta.mostrar_sistema_informatico,
    )

    return etree.tostring(envelope, xml_declaration=True, encoding="utf-8")
