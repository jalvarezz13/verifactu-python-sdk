"""Tests for Pydantic models and their validation rules."""

import pytest

from verifactu.models.breakdown import DetalleDesglose
from verifactu.models.enums import (
    CalificacionOperacion,
    ClaveRegimen,
    OperacionExenta,
    SiNo,
    TipoFactura,
    TipoHuella,
    TipoImpuesto,
)
from verifactu.models.identifiers import (
    Encadenamiento,
    IDFactura,
    IDFacturaBaja,
    PersonaFisicaJuridica,
    PersonaFisicaJuridicaES,
)
from verifactu.models.system import SistemaInformatico


class TestIDFactura:
    def test_valid_id_factura(self):
        idf = IDFactura(
            id_emisor_factura="89890001K",
            num_serie_factura="F001/2024",
            fecha_expedicion_factura="15-03-2024",
        )
        assert idf.id_emisor_factura == "89890001K"

    def test_invalid_date_format(self):
        with pytest.raises(Exception):
            IDFactura(
                id_emisor_factura="89890001K",
                num_serie_factura="F001",
                fecha_expedicion_factura="2024-03-15",
            )

    def test_nif_must_be_9_chars(self):
        with pytest.raises(Exception):
            IDFactura(
                id_emisor_factura="123",
                num_serie_factura="F001",
                fecha_expedicion_factura="15-03-2024",
            )


class TestIDFacturaBaja:
    def test_valid_id_factura_baja(self):
        idf = IDFacturaBaja(
            id_emisor_factura_anulada="89890001K",
            num_serie_factura_anulada="F001/2024",
            fecha_expedicion_factura_anulada="15-03-2024",
        )
        assert idf.id_emisor_factura_anulada == "89890001K"


class TestPersonaFisicaJuridicaES:
    def test_valid_spanish_person(self):
        p = PersonaFisicaJuridicaES(
            nombre_razon="Empresa Test SL",
            nif="B12345678",
        )
        assert p.nif == "B12345678"


class TestPersonaFisicaJuridica:
    def test_with_nif(self):
        p = PersonaFisicaJuridica(
            nombre_razon="Test",
            nif="B12345678",
        )
        assert p.nif == "B12345678"
        assert p.id_otro is None

    def test_with_id_otro(self):
        from verifactu.models.identifiers import IDOtro
        from verifactu.models.enums import TipoIdentificacion

        p = PersonaFisicaJuridica(
            nombre_razon="Foreign Corp",
            id_otro=IDOtro(
                codigo_pais="DE",
                id_type=TipoIdentificacion.NIF_IVA,
                id="DE123456789",
            ),
        )
        assert p.id_otro is not None
        assert p.nif is None


class TestDetalleDesglose:
    def test_with_calificacion_operacion(self):
        d = DetalleDesglose(
            impuesto=TipoImpuesto.IVA,
            clave_regimen=ClaveRegimen.C01,
            calificacion_operacion=CalificacionOperacion.S1,
            tipo_impositivo="21",
            base_imponible_o_importe_no_sujeto="100",
            cuota_repercutida="21",
        )
        assert d.calificacion_operacion == CalificacionOperacion.S1

    def test_with_operacion_exenta(self):
        d = DetalleDesglose(
            operacion_exenta=OperacionExenta.E1,
            base_imponible_o_importe_no_sujeto="100",
        )
        assert d.operacion_exenta == OperacionExenta.E1

    def test_must_have_exactly_one_qualification(self):
        with pytest.raises(Exception):
            DetalleDesglose(
                calificacion_operacion=CalificacionOperacion.S1,
                operacion_exenta=OperacionExenta.E1,
                base_imponible_o_importe_no_sujeto="100",
            )

    def test_must_have_at_least_one_qualification(self):
        with pytest.raises(Exception):
            DetalleDesglose(
                base_imponible_o_importe_no_sujeto="100",
            )


class TestSistemaInformatico:
    def test_valid_system(self):
        s = SistemaInformatico(
            nombre_razon="Dev Corp",
            nif="B99999999",
            nombre_sistema_informatico="TestSIF",
            id_sistema_informatico="01",
            version="1.0.0",
            numero_instalacion="INST001",
            tipo_uso_posible_solo_verifactu=SiNo.SI,
            tipo_uso_posible_multi_ot=SiNo.NO,
            indicador_multiples_ot=SiNo.NO,
        )
        assert s.nombre_sistema_informatico == "TestSIF"


class TestEncadenamiento:
    def test_primer_registro(self):
        e = Encadenamiento(primer_registro=True)
        assert e.primer_registro is True
        assert e.huella is None

    def test_registro_anterior(self):
        e = Encadenamiento(
            primer_registro=False,
            id_emisor_factura="89890001K",
            num_serie_factura="F001",
            fecha_expedicion_factura="01-01-2024",
            huella="A" * 64,
        )
        assert e.huella == "A" * 64


class TestEnums:
    def test_tipo_factura_values(self):
        assert TipoFactura.F1.value == "F1"
        assert TipoFactura.R5.value == "R5"

    def test_tipo_huella_sha256(self):
        assert TipoHuella.SHA256.value == "01"

    def test_si_no(self):
        assert SiNo.SI.value == "S"
        assert SiNo.NO.value == "N"
