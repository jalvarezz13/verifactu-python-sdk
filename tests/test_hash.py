"""Tests for SHA-256 hash calculation per AEAT specification.

Uses the official AEAT test vector from the hash specification document v0.1.2.
"""

from verifactu.hash import calculate_hash_alta, calculate_hash_anulacion


AEAT_OFFICIAL_HASH = "3C464DAF61ACB827C65FDA19F352A4E3BDC2C640E9E9FC4CC058073F38F12F60"


class TestCalculateHashAlta:
    def test_aeat_official_example(self):
        result = calculate_hash_alta(
            id_emisor_factura="89890001K",
            num_serie_factura="12345678/G33",
            fecha_expedicion_factura="01-01-2024",
            tipo_factura="F1",
            cuota_total="12.35",
            importe_total="123.45",
            huella_anterior="",
            fecha_hora_huso_gen_registro="2024-01-01T19:20:30+01:00",
        )
        assert result == AEAT_OFFICIAL_HASH

    def test_hash_is_uppercase_hex_64_chars(self):
        result = calculate_hash_alta(
            id_emisor_factura="A12345678",
            num_serie_factura="F001",
            fecha_expedicion_factura="15-06-2025",
            tipo_factura="F2",
            cuota_total="0",
            importe_total="100",
            huella_anterior="",
            fecha_hora_huso_gen_registro="2025-06-15T10:00:00+02:00",
        )
        assert len(result) == 64
        assert result == result.upper()
        assert all(c in "0123456789ABCDEF" for c in result)

    def test_first_record_empty_huella(self):
        result = calculate_hash_alta(
            id_emisor_factura="89890001K",
            num_serie_factura="001",
            fecha_expedicion_factura="01-01-2024",
            tipo_factura="F1",
            cuota_total="21",
            importe_total="121",
            huella_anterior="",
            fecha_hora_huso_gen_registro="2024-01-01T10:00:00+01:00",
        )
        assert len(result) == 64

    def test_chained_record_uses_previous_hash(self):
        first = calculate_hash_alta(
            id_emisor_factura="89890001K",
            num_serie_factura="001",
            fecha_expedicion_factura="01-01-2024",
            tipo_factura="F1",
            cuota_total="21",
            importe_total="121",
            huella_anterior="",
            fecha_hora_huso_gen_registro="2024-01-01T10:00:00+01:00",
        )
        second = calculate_hash_alta(
            id_emisor_factura="89890001K",
            num_serie_factura="002",
            fecha_expedicion_factura="01-01-2024",
            tipo_factura="F1",
            cuota_total="42",
            importe_total="242",
            huella_anterior=first,
            fecha_hora_huso_gen_registro="2024-01-01T10:01:00+01:00",
        )
        assert second != first
        assert len(second) == 64

    def test_spaces_are_stripped(self):
        with_spaces = calculate_hash_alta(
            id_emisor_factura="89890001K",
            num_serie_factura="12345678 /G33",
            fecha_expedicion_factura="01-01-2024",
            tipo_factura="F1",
            cuota_total="12.35",
            importe_total="123.45",
            huella_anterior="",
            fecha_hora_huso_gen_registro="2024-01-01T19:20:30+01:00",
        )
        without_spaces = calculate_hash_alta(
            id_emisor_factura="89890001K",
            num_serie_factura="12345678/G33",
            fecha_expedicion_factura="01-01-2024",
            tipo_factura="F1",
            cuota_total="12.35",
            importe_total="123.45",
            huella_anterior="",
            fecha_hora_huso_gen_registro="2024-01-01T19:20:30+01:00",
        )
        assert with_spaces == without_spaces


class TestCalculateHashAnulacion:
    def test_basic_cancellation_hash(self):
        result = calculate_hash_anulacion(
            id_emisor_factura_anulada="89890001K",
            num_serie_factura_anulada="12345678/G33",
            fecha_expedicion_factura_anulada="01-01-2024",
            huella_anterior="",
            fecha_hora_huso_gen_registro="2024-01-01T19:20:30+01:00",
        )
        assert len(result) == 64
        assert result == result.upper()

    def test_cancellation_with_previous_hash(self):
        result = calculate_hash_anulacion(
            id_emisor_factura_anulada="89890001K",
            num_serie_factura_anulada="001",
            fecha_expedicion_factura_anulada="01-01-2024",
            huella_anterior=AEAT_OFFICIAL_HASH,
            fecha_hora_huso_gen_registro="2024-01-02T10:00:00+01:00",
        )
        assert len(result) == 64
