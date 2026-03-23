"""Tests for SOAP XML builder."""

from lxml import etree

from verifactu.models.breakdown import Desglose, DetalleDesglose
from verifactu.models.cancellation import RegistroAnulacion
from verifactu.models.enums import (
    CalificacionOperacion,
    ClaveRegimen,
    SiNo,
    TipoFactura,
    TipoHuella,
    TipoImpuesto,
)
from verifactu.models.header import Cabecera
from verifactu.models.identifiers import (
    Encadenamiento,
    IDFactura,
    IDFacturaBaja,
    PersonaFisicaJuridica,
    PersonaFisicaJuridicaES,
)
from verifactu.models.invoice import RegistroAlta
from verifactu.models.system import SistemaInformatico
from verifactu.xml.builder import build_submit_xml
from verifactu.xml.namespaces import NS_SOAPENV, NS_SUMINISTRO_INFO, NS_SUMINISTRO_LR


def _make_sistema():
    return SistemaInformatico(
        nombre_razon="Dev Corp",
        nif="B99999999",
        nombre_sistema_informatico="TestSIF",
        id_sistema_informatico="01",
        version="1.0.0",
        numero_instalacion="INST001",
    )


def _make_alta():
    return RegistroAlta(
        id_factura=IDFactura(
            id_emisor_factura="89890001K",
            num_serie_factura="12345",
            fecha_expedicion_factura="13-09-2024",
        ),
        nombre_razon_emisor="Test Company",
        tipo_factura=TipoFactura.F1,
        descripcion_operacion="Test operation",
        destinatarios=[
            PersonaFisicaJuridica(nombre_razon="Client", nif="B12345678"),
        ],
        desglose=Desglose(
            detalle_desglose=[
                DetalleDesglose(
                    impuesto=TipoImpuesto.IVA,
                    clave_regimen=ClaveRegimen.C01,
                    calificacion_operacion=CalificacionOperacion.S1,
                    tipo_impositivo="21",
                    base_imponible_o_importe_no_sujeto="100",
                    cuota_repercutida="21",
                ),
            ],
        ),
        cuota_total="21",
        importe_total="121",
        encadenamiento=Encadenamiento(primer_registro=True),
        sistema_informatico=_make_sistema(),
        fecha_hora_huso_gen_registro="2024-09-13T19:20:30+01:00",
        tipo_huella=TipoHuella.SHA256,
        huella="A" * 64,
    )


def _make_anulacion():
    return RegistroAnulacion(
        id_factura=IDFacturaBaja(
            id_emisor_factura_anulada="89890001K",
            num_serie_factura_anulada="12345",
            fecha_expedicion_factura_anulada="13-09-2024",
        ),
        encadenamiento=Encadenamiento(primer_registro=True),
        sistema_informatico=_make_sistema(),
        fecha_hora_huso_gen_registro="2024-09-13T19:20:30+01:00",
        huella="B" * 64,
    )


class TestBuildSubmitXml:
    def test_produces_valid_xml(self):
        cabecera = Cabecera(
            obligado_emision=PersonaFisicaJuridicaES(
                nombre_razon="Test Company",
                nif="89890001K",
            ),
        )
        xml_bytes = build_submit_xml(cabecera, [_make_alta()])
        root = etree.fromstring(xml_bytes)
        assert root.tag == f"{{{NS_SOAPENV}}}Envelope"

    def test_contains_cabecera(self):
        cabecera = Cabecera(
            obligado_emision=PersonaFisicaJuridicaES(
                nombre_razon="Test Company",
                nif="89890001K",
            ),
        )
        xml_bytes = build_submit_xml(cabecera, [_make_alta()])
        root = etree.fromstring(xml_bytes)
        ns = {"sum": NS_SUMINISTRO_LR, "sum1": NS_SUMINISTRO_INFO}
        cab = root.find(".//sum:Cabecera", ns)
        assert cab is not None
        nif = root.find(".//sum1:ObligadoEmision/sum1:NIF", ns)
        assert nif is not None
        assert nif.text == "89890001K"

    def test_alta_fields_present(self):
        cabecera = Cabecera(
            obligado_emision=PersonaFisicaJuridicaES(
                nombre_razon="Test", nif="89890001K",
            ),
        )
        xml_bytes = build_submit_xml(cabecera, [_make_alta()])
        root = etree.fromstring(xml_bytes)
        ns = {"sum1": NS_SUMINISTRO_INFO}
        assert root.find(".//sum1:TipoFactura", ns).text == "F1"
        assert root.find(".//sum1:CuotaTotal", ns).text == "21"
        assert root.find(".//sum1:ImporteTotal", ns).text == "121"
        assert root.find(".//sum1:TipoHuella", ns).text == "01"
        assert root.find(".//sum1:Huella", ns).text == "A" * 64

    def test_mixed_alta_and_anulacion(self):
        cabecera = Cabecera(
            obligado_emision=PersonaFisicaJuridicaES(
                nombre_razon="Test", nif="89890001K",
            ),
        )
        records = [_make_alta(), _make_anulacion()]
        xml_bytes = build_submit_xml(cabecera, records)
        root = etree.fromstring(xml_bytes)
        ns = {"sum": NS_SUMINISTRO_LR}
        registros = root.findall(".//sum:RegistroFactura", ns)
        assert len(registros) == 2

    def test_encadenamiento_primer_registro(self):
        cabecera = Cabecera(
            obligado_emision=PersonaFisicaJuridicaES(
                nombre_razon="Test", nif="89890001K",
            ),
        )
        xml_bytes = build_submit_xml(cabecera, [_make_alta()])
        root = etree.fromstring(xml_bytes)
        ns = {"sum1": NS_SUMINISTRO_INFO}
        primer = root.find(".//sum1:PrimerRegistro", ns)
        assert primer is not None
        assert primer.text == "S"

    def test_encadenamiento_registro_anterior(self):
        alta = _make_alta()
        alta.encadenamiento = Encadenamiento(
            primer_registro=False,
            id_emisor_factura="89890001K",
            num_serie_factura="44",
            fecha_expedicion_factura="13-09-2024",
            huella="C" * 64,
        )
        cabecera = Cabecera(
            obligado_emision=PersonaFisicaJuridicaES(
                nombre_razon="Test", nif="89890001K",
            ),
        )
        xml_bytes = build_submit_xml(cabecera, [alta])
        root = etree.fromstring(xml_bytes)
        ns = {"sum1": NS_SUMINISTRO_INFO}
        anterior = root.find(".//sum1:RegistroAnterior", ns)
        assert anterior is not None
        huella = anterior.find(f"{{{NS_SUMINISTRO_INFO}}}Huella")
        assert huella.text == "C" * 64
