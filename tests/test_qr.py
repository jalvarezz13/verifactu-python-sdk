"""Tests for QR code URL generation."""

from verifactu.config import Environment
from verifactu.qr import build_qr_url


class TestBuildQrUrl:
    def test_production_url(self):
        url = build_qr_url(
            nif="A12345678",
            num_serie="F001/2024",
            fecha="15-03-2024",
            importe="121.00",
            environment=Environment.PRODUCTION,
        )
        assert "www2.agenciatributaria.gob.es" in url
        assert "ValidarQR" in url
        assert "nif=A12345678" in url
        assert "numserie=F001" in url
        assert "fecha=15-03-2024" in url
        assert "importe=121.00" in url

    def test_sandbox_url(self):
        url = build_qr_url(
            nif="A12345678",
            num_serie="F001",
            fecha="15-03-2024",
            importe="100",
            environment=Environment.SANDBOX,
        )
        assert "prewww2.aeat.es" in url

    def test_url_structure(self):
        url = build_qr_url(
            nif="B99999999",
            num_serie="SERIE-001",
            fecha="01-01-2025",
            importe="250.50",
        )
        assert url.startswith("https://")
        assert "?" in url
        parts = url.split("?")
        assert len(parts) == 2
