"""Thread-safe hash chain manager for Verifactu records.

The chain is per-SIF (invoicing system), NOT per invoice series.
All records (alta + anulación) from the same system share one chain.

This module provides ``ChainManager`` which:
- Tracks the last record's hash and identifier per NIF
- Computes and assigns hashes to new records
- Sets the encadenamiento (chain link) fields
- Is thread-safe for concurrent invoice generation
- Supports persistence to/from JSON for crash recovery
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

from verifactu.hash import calculate_hash_alta, calculate_hash_anulacion
from verifactu.models.cancellation import RegistroAnulacion
from verifactu.models.identifiers import Encadenamiento
from verifactu.models.invoice import RegistroAlta


@dataclass
class ChainState:
    """State of a hash chain for a single NIF/SIF."""

    last_nif: str | None = None
    last_num_serie: str | None = None
    last_fecha: str | None = None
    last_huella: str | None = None
    record_count: int = 0

    @property
    def is_first(self) -> bool:
        return self.last_huella is None

    def to_dict(self) -> dict[str, object]:
        return {
            "last_nif": self.last_nif,
            "last_num_serie": self.last_num_serie,
            "last_fecha": self.last_fecha,
            "last_huella": self.last_huella,
            "record_count": self.record_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> ChainState:
        return cls(
            last_nif=data.get("last_nif"),  # type: ignore[arg-type]
            last_num_serie=data.get("last_num_serie"),  # type: ignore[arg-type]
            last_fecha=data.get("last_fecha"),  # type: ignore[arg-type]
            last_huella=data.get("last_huella"),  # type: ignore[arg-type]
            record_count=data.get("record_count", 0),  # type: ignore[arg-type]
        )


@dataclass
class ChainManager:
    """Thread-safe hash chain manager.

    Manages chain state per NIF (tax ID of the obligated party).
    All records from the same NIF share a single chain.

    Usage::

        chain = ChainManager()

        # Link and hash a new registration record
        chain.link_alta(alta_record)

        # Link and hash a cancellation record
        chain.link_anulacion(anulacion_record)

        # Persist state for crash recovery
        chain.save("/path/to/chain_state.json")

        # Restore state
        chain = ChainManager.load("/path/to/chain_state.json")
    """

    _chains: dict[str, ChainState] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def _get_or_create(self, nif: str) -> ChainState:
        if nif not in self._chains:
            self._chains[nif] = ChainState()
        return self._chains[nif]

    def link_alta(self, record: RegistroAlta) -> RegistroAlta:
        """Compute hash and set chain fields on a RegistroAlta.

        Modifies the record in-place and returns it.
        Thread-safe: acquires lock for the duration of the operation.

        Args:
            record: The alta record to chain. Its ``encadenamiento``,
                ``huella``, and ``fecha_hora_huso_gen_registro`` fields
                will be set/overwritten.

        Returns:
            The same record instance with hash and chain fields populated.
        """
        nif = record.id_factura.id_emisor_factura

        with self._lock:
            state = self._get_or_create(nif)

            # Set encadenamiento
            if state.is_first:
                record.encadenamiento = Encadenamiento(primer_registro=True)
            else:
                record.encadenamiento = Encadenamiento(
                    primer_registro=False,
                    id_emisor_factura=state.last_nif,
                    num_serie_factura=state.last_num_serie,
                    fecha_expedicion_factura=state.last_fecha,
                    huella=state.last_huella,
                )

            # Calculate hash
            huella = calculate_hash_alta(
                id_emisor_factura=record.id_factura.id_emisor_factura,
                num_serie_factura=record.id_factura.num_serie_factura,
                fecha_expedicion_factura=record.id_factura.fecha_expedicion_factura,
                tipo_factura=record.tipo_factura.value,
                cuota_total=record.cuota_total,
                importe_total=record.importe_total,
                huella_anterior=state.last_huella or "",
                fecha_hora_huso_gen_registro=record.fecha_hora_huso_gen_registro,
            )
            record.huella = huella

            # Update chain state
            state.last_nif = record.id_factura.id_emisor_factura
            state.last_num_serie = record.id_factura.num_serie_factura
            state.last_fecha = record.id_factura.fecha_expedicion_factura
            state.last_huella = huella
            state.record_count += 1

        return record

    def link_anulacion(self, record: RegistroAnulacion) -> RegistroAnulacion:
        """Compute hash and set chain fields on a RegistroAnulacion.

        Modifies the record in-place and returns it.
        Thread-safe: acquires lock for the duration of the operation.

        Args:
            record: The cancellation record to chain.

        Returns:
            The same record instance with hash and chain fields populated.
        """
        nif = record.id_factura.id_emisor_factura_anulada

        with self._lock:
            state = self._get_or_create(nif)

            # Set encadenamiento
            if state.is_first:
                record.encadenamiento = Encadenamiento(primer_registro=True)
            else:
                record.encadenamiento = Encadenamiento(
                    primer_registro=False,
                    id_emisor_factura=state.last_nif,
                    num_serie_factura=state.last_num_serie,
                    fecha_expedicion_factura=state.last_fecha,
                    huella=state.last_huella,
                )

            # Calculate hash
            huella = calculate_hash_anulacion(
                id_emisor_factura_anulada=record.id_factura.id_emisor_factura_anulada,
                num_serie_factura_anulada=record.id_factura.num_serie_factura_anulada,
                fecha_expedicion_factura_anulada=record.id_factura.fecha_expedicion_factura_anulada,
                huella_anterior=state.last_huella or "",
                fecha_hora_huso_gen_registro=record.fecha_hora_huso_gen_registro,
            )
            record.huella = huella

            # Update chain state
            state.last_nif = record.id_factura.id_emisor_factura_anulada
            state.last_num_serie = record.id_factura.num_serie_factura_anulada
            state.last_fecha = record.id_factura.fecha_expedicion_factura_anulada
            state.last_huella = huella
            state.record_count += 1

        return record

    def link(self, record: Union[RegistroAlta, RegistroAnulacion]) -> Union[RegistroAlta, RegistroAnulacion]:
        """Compute hash and set chain fields on any record type.

        Convenience method that dispatches to ``link_alta`` or
        ``link_anulacion`` based on the record type.
        """
        if isinstance(record, RegistroAlta):
            return self.link_alta(record)
        if isinstance(record, RegistroAnulacion):
            return self.link_anulacion(record)
        msg = f"Unsupported record type: {type(record).__name__}"
        raise TypeError(msg)

    def get_state(self, nif: str) -> ChainState | None:
        """Get current chain state for a NIF, or None if not tracked."""
        return self._chains.get(nif)

    def save(self, path: str | Path) -> None:
        """Persist all chain states to a JSON file."""
        path = Path(path)
        with self._lock:
            data = {nif: state.to_dict() for nif, state in self._chains.items()}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> ChainManager:
        """Restore chain states from a JSON file."""
        path = Path(path)
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        chains = {nif: ChainState.from_dict(state_data) for nif, state_data in data.items()}
        manager = cls()
        manager._chains = chains
        return manager
