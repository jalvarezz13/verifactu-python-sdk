# VERI\*FACTU Python SDK

Python SDK for Spain's AEAT Verifactu electronic invoicing system (Real Decreto 1007/2023).

---

> **⚠️ DISCLAIMER**
>
> This library is an **independent open-source contribution** and is **not affiliated with, endorsed by, or produced by** the Spanish Tax Agency (AEAT) or any official software manufacturer.
>
> The author (`Javier Álvarez`) provides this SDK on a best-effort basis. **No warranty is given** regarding correctness, completeness, fitness for a particular purpose, or compliance with any specific version of the Verifactu regulation. Tax obligations are your responsibility. Always verify your submissions against official AEAT documentation and consult a qualified tax advisor before using this software in production.
>
> By using this SDK, you accept that the author bears **no liability** for any direct or indirect damages arising from its use, including but not limited to rejected invoices, regulatory penalties, or data loss.

---

## What this SDK does

`verifactu` lets Python applications submit electronic invoice records to Spain's AEAT Verifactu system via SOAP over mTLS. It handles:

- Building and validating `RegistroAlta` (invoice registration) and `RegistroAnulacion` (cancellation) records
- Computing the SHA-256 hash chain required by the regulation
- Signing SOAP requests with a qualified electronic certificate (PEM or PKCS#12)
- Sending submissions and queries to the AEAT endpoints (production and sandbox)
- Generating QR validation URLs and PNG images for printed invoices

**What it does NOT do:**

- XAdES digital signatures (required for NO VERI\*FACTU / requerimiento mode — not implemented)
- EventosSIF (system events, NO VERI\*FACTU only — not implemented)
- Any accounting, PDF generation, or invoice storage

---

## Requirements

- Python 3.10 or later
- A valid qualified electronic certificate issued by a recognized eIDAS CA (e.g., FNMT) — required even for the sandbox
- Dependencies installed automatically: `pydantic>=2.0`, `lxml>=5.0`, `requests>=2.28`, `cryptography>=41.0`

---

## Installation

```bash
pip install verifactu
```

To also generate QR images (requires Pillow):

```bash
pip install verifactu[qr]
```

---

## Quickstart

This example submits a single F1 invoice in VERI\*FACTU mode using the sandbox.

```python
from datetime import datetime, timezone, timedelta
from pathlib import Path
from verifactu import VeriFactuClient, ChainManager, Environment, CertificateType
from verifactu.models import (
    Cabecera, RegistroAlta, IDFactura, SistemaInformatico,
    Desglose, DetalleDesglose, Encadenamiento, PersonaFisicaJuridicaES,
)
from verifactu.models.enums import (
    TipoFactura, TipoImpuesto, CalificacionOperacion, ClaveRegimen, SiNo,
)

# 1. Load or create the chain manager (persists hash state between runs)
chain_file = Path("chain_state.json")
chain = ChainManager.load(chain_file) if chain_file.exists() else ChainManager()

# 2. Build the invoice record
now = datetime.now(tz=timezone(timedelta(hours=1)))
timestamp = now.strftime("%Y-%m-%dT%H:%M:%S+01:00")

record = RegistroAlta(
    id_factura=IDFactura(
        id_emisor_factura="B12345678",
        num_serie_factura="2024-001",
        fecha_expedicion_factura="15-03-2024",
    ),
    nombre_razon_emisor="Mi Empresa S.L.",
    tipo_factura=TipoFactura.F1,
    descripcion_operacion="Servicios de consultoría",
    desglose=Desglose(
        detalle_desglose=[
            DetalleDesglose(
                impuesto=TipoImpuesto.IVA,
                clave_regimen=ClaveRegimen.C01,
                calificacion_operacion=CalificacionOperacion.S1,
                tipo_impositivo="21",
                base_imponible_o_importe_no_sujeto="1000",
                cuota_repercutida="210",
            )
        ]
    ),
    cuota_total="210",
    importe_total="1210",
    sistema_informatico=SistemaInformatico(
        nombre_razon="Mi Software S.L.",
        nif="B87654321",
        nombre_sistema_informatico="FacturApp",
        id_sistema_informatico="01",
        version="1.0",
        numero_instalacion="INST-001",
        tipo_uso_posible_solo_verifactu=SiNo.SI,
        tipo_uso_posible_multi_ot=SiNo.NO,
        indicador_multiples_ot=SiNo.NO,
    ),
    encadenamiento=Encadenamiento(),
    fecha_hora_huso_gen_registro=timestamp,
    huella="placeholder",  # ChainManager overwrites this
)

# 3. Link the record into the chain (sets encadenamiento + huella)
chain.link_alta(record)

# 4. Build the submission header
cabecera = Cabecera(
    obligado_emision=PersonaFisicaJuridicaES(
        nombre_razon="Mi Empresa S.L.",
        nif="B12345678",
    ),
)

# 5. Submit
with VeriFactuClient(
    environment=Environment.SANDBOX,
    certificate_type=CertificateType.PERSONAL,
    pfx_path="my_certificate.p12",
    pfx_password="secret",
) as client:
    response = client.submit(cabecera, [record])

print(response.estado_envio)          # EstadoEnvio.CORRECTO
print(response.accepted_records)      # list of accepted RespuestaLinea
print(response.rejected_records)      # list of rejected RespuestaLinea

# 6. Persist chain state for the next run
chain.save(chain_file)
```

---

## Certificate configuration

The client accepts certificates in two formats.

**PEM files (separate cert + key):**

```python
client = VeriFactuClient(
    cert_path="certificate.pem",
    key_path="private_key.pem",
)
```

**PKCS#12 (.p12 / .pfx):**

```python
client = VeriFactuClient(
    pfx_path="certificate.p12",
    pfx_password="your_password",
)
```

The SDK converts PKCS#12 to PEM internally using the `cryptography` library. No manual conversion needed.

---

## Environments and endpoints

Pass `environment=Environment.PRODUCTION` or `environment=Environment.SANDBOX` (default).

| Mode        | Certificate type | Environment | Host                             |
| ----------- | ---------------- | ----------- | -------------------------------- |
| VERI\*FACTU | Personal         | Production  | `www1.agenciatributaria.gob.es`  |
| VERI\*FACTU | Entity seal      | Production  | `www10.agenciatributaria.gob.es` |
| VERI\*FACTU | Personal         | Sandbox     | `prewww1.aeat.es`                |
| VERI\*FACTU | Entity seal      | Sandbox     | `prewww10.aeat.es`               |

The same four combinations apply to NO VERI\*FACTU (requerimiento) mode, using a different SOAP path.

You can inspect the resolved URLs at runtime:

```python
print(client.submit_url)
print(client.query_url)
```

---

## VeriFactuClient reference

```python
class VeriFactuClient:
    def __init__(
        self,
        *,
        environment: Environment = Environment.SANDBOX,
        certificate_type: CertificateType = CertificateType.PERSONAL,
        cert_path: str | Path | None = None,
        key_path: str | Path | None = None,
        pfx_path: str | Path | None = None,
        pfx_password: str | None = None,
        is_verifactu: bool = True,
        timeout: int = 30,
    ) -> None: ...
```

Set `is_verifactu=False` to target the requerimiento (NO VERI\*FACTU) endpoint. Note that XAdES signatures are not implemented, so this mode is only partially supported.

### Methods

| Method                      | Description                                                                               |
| --------------------------- | ----------------------------------------------------------------------------------------- |
| `submit(cabecera, records)` | Send up to 1000 `RegistroAlta` or `RegistroAnulacion` records. Returns `RespuestaEnvio`.  |
| `query(consulta)`           | Query submitted invoices. Returns `RespuestaConsulta`.                                    |
| `close()`                   | Release the underlying HTTP session. Called automatically when used as a context manager. |

### Properties

| Property         | Type  | Description                                          |
| ---------------- | ----- | ---------------------------------------------------- |
| `submit_url`     | `str` | Resolved SOAP submission endpoint                    |
| `query_url`      | `str` | Resolved SOAP query endpoint                         |
| `last_wait_time` | `int` | `TiempoEsperaEnvio` from the last response (seconds) |

### Exceptions raised

| Exception          | When                                                                        |
| ------------------ | --------------------------------------------------------------------------- |
| `ValidationError`  | Record fails Pydantic validation before sending                             |
| `CertificateError` | Certificate cannot be loaded or is invalid                                  |
| `SOAPFaultError`   | AEAT returns a SOAP fault; `.is_retryable` is `True` for server-side faults |
| `AEATError`        | AEAT returns an application-level error code                                |
| `ConnectionError`  | Network or TLS failure                                                      |
| `ChainError`       | Hash chain state is inconsistent                                            |

---

## ChainManager reference

The hash chain is mandatory under the Verifactu regulation. `ChainManager` maintains the chain state **per NIF** and is thread-safe.

```python
@dataclass
class ChainManager:
    def link_alta(self, record: RegistroAlta) -> RegistroAlta: ...
    def link_anulacion(self, record: RegistroAnulacion) -> RegistroAnulacion: ...
    def link(self, record: RegistroAlta | RegistroAnulacion) -> RegistroAlta | RegistroAnulacion: ...
    def get_state(self, nif: str) -> ChainState | None: ...
    def save(self, path: str | Path) -> None: ...

    @classmethod
    def load(cls, path: str | Path) -> ChainManager: ...
```

`link_alta` and `link_anulacion` modify the record **in-place** and return it. They set both `encadenamiento` and `huella` automatically. For the first record in a chain, `encadenamiento.primer_registro` is set to `True`. For subsequent records, the previous record's ID and hash are referenced.

**Persisting state between runs:**

```python
# Load existing state (or start fresh)
from pathlib import Path
chain_file = Path("chain_state.json")
chain = ChainManager.load(chain_file) if chain_file.exists() else ChainManager()

# ... build and link records ...

# Save after each successful submission
chain.save(chain_file)
```

**Important:** The chain state is per NIF (per invoicing system installation), not per invoice series. Do not reset the chain between series.

---

## Hash functions reference

You can compute hashes directly if you need to verify or debug the chain.

```python
from verifactu import calculate_hash_alta, calculate_hash_anulacion

huella = calculate_hash_alta(
    id_emisor_factura="89890001K",
    num_serie_factura="12345678/G33",
    fecha_expedicion_factura="01-01-2024",
    tipo_factura="F1",
    cuota_total="12.35",
    importe_total="123.45",
    huella_anterior="",          # Empty string for the first record
    fecha_hora_huso_gen_registro="2024-01-01T19:20:30+01:00",
)
# Returns: "3C464DAF61ACB827C65FDA19F352A4E3BDC2C640E9E9FC4CC058073F38F12F60"
```

The hash is computed as `SHA-256(UTF-8(Key1=Val1&Key2=Val2&...))`, returned as uppercase hex (64 characters). Spaces are stripped from values. For the first record, `huella_anterior` is an empty string, which produces `Huella=` in the input string.

The test vector above is the official AEAT example and is verified in the test suite.

---

## QR code functions reference

Every Verifactu invoice must include a QR code linking to the AEAT validation portal.

```python
from verifactu import build_qr_url, build_qr_url_from_alta, generate_qr_image, Environment

# Build the URL manually
url = build_qr_url(
    nif="B12345678",
    num_serie="2024-001",
    fecha="15-03-2024",
    importe="1210.00",
    environment=Environment.PRODUCTION,
)

# Or derive it directly from a RegistroAlta
url = build_qr_url_from_alta(record, environment=Environment.PRODUCTION)

# Generate a PNG image (requires verifactu[qr])
png_bytes = generate_qr_image(url, box_size=10, border=4)
with open("qr.png", "wb") as f:
    f.write(png_bytes)
```

Production QR base URL: `https://www2.agenciatributaria.gob.es/wlpl/TIKE-CONT/ValidarQR`

`generate_qr_image` raises `ImportError` if the `qrcode[pil]` extra is not installed.

---

## Querying submitted invoices

```python
from verifactu.models import (
    ConsultaFactura, FiltroConsulta, PeriodoImputacion, PersonaFisicaJuridicaES,
)
from verifactu.models.enums import Periodo

consulta = ConsultaFactura(
    obligado_emision=PersonaFisicaJuridicaES(
        nombre_razon="Mi Empresa S.L.",
        nif="B12345678",
    ),
    filtro_consulta=FiltroConsulta(
        periodo_imputacion=PeriodoImputacion(
            ejercicio="2024",
            periodo=Periodo.ENERO,
        ),
    ),
)

with VeriFactuClient(...) as client:
    result = client.query(consulta)

print(result.resultado_consulta)   # ResultadoConsulta.CON_DATOS or SIN_DATOS
for reg in result.registros:
    print(reg.id_factura, reg.datos_registro_facturacion.importe_total)
```

The query response returns up to 10,000 records. Pagination is supported via `ClavePaginacion`.

---

## Cancelling an invoice

```python
from verifactu.models import RegistroAnulacion, IDFacturaBaja, Encadenamiento, SistemaInformatico

anulacion = RegistroAnulacion(
    id_factura=IDFacturaBaja(
        id_emisor_factura_anulada="B12345678",
        num_serie_factura_anulada="2024-001",
        fecha_expedicion_factura_anulada="15-03-2024",
    ),
    sistema_informatico=SistemaInformatico(...),  # same as your RegistroAlta
    encadenamiento=Encadenamiento(),
    fecha_hora_huso_gen_registro=timestamp,
    huella="placeholder",  # ChainManager overwrites this
)

chain.link_anulacion(anulacion)

with VeriFactuClient(...) as client:
    response = client.submit(cabecera, [anulacion])
```

---

## Response handling

```python
response = client.submit(cabecera, records)

if response.is_accepted:
    print("All records accepted. CSV:", response.csv)
else:
    for line in response.rejected_records:
        print(line.id_factura, line.codigo_error_registro, line.descripcion_error_registro)

# Respect the wait time before the next submission
import time
time.sleep(response.tiempo_espera_envio)
```

`response.estado_envio` is one of `EstadoEnvio.CORRECTO`, `PARCIALMENTE_CORRECTO`, or `INCORRECTO`.

---

## Error handling

```python
from verifactu import VeriFactuClient
from verifactu.exceptions import SOAPFaultError, AEATError, CertificateError, ConnectionError

try:
    response = client.submit(cabecera, records)
except CertificateError as e:
    print("Certificate problem:", e)
except SOAPFaultError as e:
    if e.is_retryable:
        # Server-side fault, safe to retry after waiting
        time.sleep(60)
    else:
        raise
except AEATError as e:
    if e.is_duplicate:
        pass  # Already submitted, not an error in most cases
    elif e.is_full_rejection:
        raise  # 4xxx: entire submission rejected
    else:
        print(e.code, e.description)
except ConnectionError as e:
    print("Network error:", e)
```

### AEATError code ranges

| Code range | Meaning                   | Property                   |
| ---------- | ------------------------- | -------------------------- |
| 1xxx       | Record-level rejection    | `.is_record_rejection`     |
| 2xxx       | Accepted with errors      | `.is_accepted_with_errors` |
| 3000       | Duplicate submission      | `.is_duplicate`            |
| 4xxx       | Full submission rejection | `.is_full_rejection`       |

---

## Protocol limits and constants

| Constant                              | Value       |
| ------------------------------------- | ----------- |
| Max records per submission            | 1,000       |
| Max records per query response        | 10,000      |
| Default wait time between submissions | 60 seconds  |
| Max generation-to-send window         | 240 seconds |
| Verifactu protocol version            | 1.0         |

AEAT dynamically adjusts the wait time via `TiempoEsperaEnvio` in each response. Always read `response.tiempo_espera_envio` (or `client.last_wait_time`) and wait that many seconds before the next submission.

---

## Data formats

| Field type            | Format                                                                 |
| --------------------- | ---------------------------------------------------------------------- |
| Dates                 | `DD-MM-YYYY`                                                           |
| Timestamps            | `YYYY-MM-DDTHH:MM:SS+HH:00` (ISO 8601 with timezone offset)            |
| Monetary amounts      | Signed decimal, up to 12 digits + 2 decimal places (e.g., `"1210.00"`) |
| NIF                   | 9 characters                                                           |
| Invoice series number | 1-60 characters                                                        |
| SHA-256 hash          | 64-character uppercase hex string                                      |

---

## Key enums

All enums live in `verifactu.models.enums`.

**TipoFactura** — invoice type:
`F1` (standard), `F2` (simplified), `F3` (summary), `R1`-`R5` (corrective types)

**TipoRectificativa** — corrective method:
`SUSTITUTIVA` ("S"), `INCREMENTAL` ("I")

**TipoImpuesto** — tax type:
`IVA` ("01"), `IPSI` ("02"), `IGIC` ("03"), `OTROS` ("05")

**CalificacionOperacion** — VAT qualification:
`S1`, `S2` (subject), `N1`, `N2` (not subject)

**OperacionExenta** — exemption reason:
`E1` through `E8`

**ClaveRegimen** — special regime key:
`C01`-`C11`, `C14`, `C15`, `C17`-`C21`

**Periodo** — billing period:
`ENERO` through `DICIEMBRE` ("01"-"12")

**SiNo** — boolean flag:
`SI` ("S"), `NO` ("N")

---

## Limitations

- **XAdES signatures not implemented.** The NO VERI\*FACTU (requerimiento) mode requires XAdES-T signatures on the SOAP payload. This SDK does not produce them. `is_verifactu=False` routes to the correct endpoint but the request will be rejected without a valid XAdES signature.
- **EventosSIF not implemented.** The system events API (NO VERI\*FACTU only) is not covered.
- **No retry logic.** The SDK does not automatically retry failed requests. Implement your own retry loop using `SOAPFaultError.is_retryable` and `response.tiempo_espera_envio`.
- **No invoice storage.** The SDK does not persist submitted invoices. Your application is responsible for storing records and chain state.
- **Sandbox requires a real certificate.** AEAT's sandbox does not accept self-signed certificates. You need a valid FNMT or equivalent eIDAS-recognized certificate.

---

## Regulatory context

Verifactu is Spain's mandatory electronic invoicing verification system, established by Real Decreto 1007/2023 and developed under Orden HAC/1177/2024. It requires invoicing software to submit invoice records to AEAT in real time (or near real time) using a cryptographic hash chain.

**Compliance deadlines:**

- Companies: January 1, 2027
- Self-employed: July 1, 2027

For official documentation and technical specifications, consult the AEAT developer portal. For technical questions about the Verifactu system itself, contact AEAT at `verifactu@correo.aeat.es`.

---

## Development

```bash
git clone https://github.com/jalvarezz13/verifactu-python-sdk
cd verifactu-python-sdk
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,qr]"
```

Run tests:

```bash
pytest -v --cov=verifactu
```

Lint and type-check:

```bash
ruff check .
mypy verifactu/
```

---

## License

MIT. See `LICENSE` for details.

<br>

---

<br>

<div align="center">
    Made with ❤️ by <a href="https://www.linkedin.com/in/jalvarezz13/" target="_blank"><b>jalvarezz13</b></a>
    <br>
</div>
