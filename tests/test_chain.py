"""Tests for ChainManager — thread-safe hash chain management."""

import json
import tempfile
from pathlib import Path

from verifactu.chain import ChainManager
from verifactu.models.breakdown import Desglose, DetalleDesglose
from verifactu.models.cancellation import RegistroAnulacion
from verifactu.models.enums import CalificacionOperacion, ClaveRegimen, TipoFactura, TipoImpuesto
from verifactu.models.identifiers import Encadenamiento, IDFactura, IDFacturaBaja
from verifactu.models.invoice import RegistroAlta
from verifactu.models.system import SistemaInformatico


def _make_sistema():
    return SistemaInformatico(
        nombre_razon="Dev Corp",
        nif="B99999999",
        nombre_sistema_informatico="TestSIF",
        id_sistema_informatico="01",
        version="1.0.0",
        numero_instalacion="INST001",
    )


def _make_alta(nif: str = "89890001K", num: str = "001", fecha: str = "01-01-2024"):
    return RegistroAlta(
        id_factura=IDFactura(
            id_emisor_factura=nif,
            num_serie_factura=num,
            fecha_expedicion_factura=fecha,
        ),
        nombre_razon_emisor="Test",
        tipo_factura=TipoFactura.F1,
        descripcion_operacion="Test",
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
        fecha_hora_huso_gen_registro="2024-01-01T10:00:00+01:00",
        huella="placeholder",
    )


def _make_anulacion(nif: str = "89890001K", num: str = "001"):
    return RegistroAnulacion(
        id_factura=IDFacturaBaja(
            id_emisor_factura_anulada=nif,
            num_serie_factura_anulada=num,
            fecha_expedicion_factura_anulada="01-01-2024",
        ),
        encadenamiento=Encadenamiento(primer_registro=True),
        sistema_informatico=_make_sistema(),
        fecha_hora_huso_gen_registro="2024-01-01T10:00:00+01:00",
        huella="placeholder",
    )


class TestChainManager:
    def test_first_record_sets_primer_registro(self):
        chain = ChainManager()
        alta = _make_alta()
        chain.link_alta(alta)
        assert alta.encadenamiento.primer_registro is True
        assert len(alta.huella) == 64

    def test_second_record_links_to_first(self):
        chain = ChainManager()
        first = _make_alta(num="001")
        chain.link_alta(first)

        second = _make_alta(num="002")
        second.fecha_hora_huso_gen_registro = "2024-01-01T10:01:00+01:00"
        chain.link_alta(second)

        assert second.encadenamiento.primer_registro is False
        assert second.encadenamiento.huella == first.huella
        assert second.huella != first.huella

    def test_anulacion_chains_after_alta(self):
        chain = ChainManager()
        alta = _make_alta()
        chain.link_alta(alta)

        anulacion = _make_anulacion()
        anulacion.fecha_hora_huso_gen_registro = "2024-01-01T10:01:00+01:00"
        chain.link_anulacion(anulacion)

        assert anulacion.encadenamiento.primer_registro is False
        assert anulacion.encadenamiento.huella == alta.huella

    def test_link_dispatches_correctly(self):
        chain = ChainManager()
        alta = _make_alta()
        result = chain.link(alta)
        assert result is alta
        assert len(alta.huella) == 64

    def test_different_nifs_have_separate_chains(self):
        chain = ChainManager()
        alta1 = _make_alta(nif="89890001K", num="001")
        alta2 = _make_alta(nif="B12345678", num="001")

        chain.link_alta(alta1)
        chain.link_alta(alta2)

        assert alta1.encadenamiento.primer_registro is True
        assert alta2.encadenamiento.primer_registro is True

    def test_save_and_load(self):
        chain = ChainManager()
        alta = _make_alta()
        chain.link_alta(alta)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        chain.save(path)
        loaded = ChainManager.load(path)

        state = loaded.get_state("89890001K")
        assert state is not None
        assert state.last_huella == alta.huella
        assert state.record_count == 1

        Path(path).unlink()

    def test_load_nonexistent_returns_empty(self):
        chain = ChainManager.load("/nonexistent/path.json")
        assert chain.get_state("89890001K") is None
