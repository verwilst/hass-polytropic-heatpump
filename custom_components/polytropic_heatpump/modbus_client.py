"""
Raw Modbus RTU over TCP client for Polytropic heat pump.

Connects per-request: opens a TCP socket, sends the frame, reads the
response, then closes the socket immediately.  Works with any RS485-to-TCP
gateway that passes RTU frames through transparently.  No pymodbus required.
"""
from __future__ import annotations

import asyncio
import struct
import logging

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CRC-16 (Modbus)
# ---------------------------------------------------------------------------

def _crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc


def _append_crc(frame: bytes) -> bytes:
    return frame + struct.pack("<H", _crc16(frame))


def _check_crc(frame: bytes) -> bool:
    if len(frame) < 2:
        return False
    return _crc16(frame[:-2]) == struct.unpack("<H", frame[-2:])[0]


# ---------------------------------------------------------------------------
# Frame builders
# ---------------------------------------------------------------------------

def build_read_holding(slave: int, address: int, count: int) -> bytes:
    """Function code 0x03 – Read Holding Registers."""
    return _append_crc(struct.pack(">BBHH", slave, 0x03, address, count))


def build_write_single(slave: int, address: int, value: int) -> bytes:
    """Function code 0x06 – Write Single Register."""
    return _append_crc(struct.pack(">BBHH", slave, 0x06, address, value & 0xFFFF))


# ---------------------------------------------------------------------------
# Async TCP client  (connect-per-session)
# ---------------------------------------------------------------------------

class ModbusRTUClient:
    """
    Async Modbus RTU client over raw TCP.

    Does not maintain a persistent connection.  Call async_session() as an
    async context manager to open a connection, perform all reads/writes for
    one coordinator cycle, then close automatically.
    """

    def __init__(
            self,
            host: str,
            port: int,
            slave: int,
            inter_request_delay: float = 0.1,
            timeout: float = 5.0,
    ) -> None:
        self._host = host
        self._port = port
        self._slave = slave
        self._delay = inter_request_delay
        self._timeout = timeout
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    # ------------------------------------------------------------------
    # Context manager  (one TCP connection for one coordinator poll)
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "ModbusRTUClient":
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self._host, self._port),
            timeout=self._timeout,
        )
        _LOGGER.debug("Connected to %s:%s", self._host, self._port)
        # Flush any stale bytes the gateway may have buffered
        await self._flush()
        return self

    async def _flush(self) -> None:
        """Drain any stale bytes from the read buffer after connecting."""
        try:
            await asyncio.wait_for(self._reader.read(256), timeout=0.1)
            _LOGGER.debug("Flushed stale bytes from buffer")
        except asyncio.TimeoutError:
            pass  # No stale data — expected
        except Exception:  # noqa: BLE001
            pass

    async def __aexit__(self, *_) -> None:
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:  # noqa: BLE001
                pass
        self._reader = None
        self._writer = None
        _LOGGER.debug("Disconnected from %s:%s", self._host, self._port)

    # ------------------------------------------------------------------
    # Low-level send / receive
    # ------------------------------------------------------------------

    async def _send_recv(self, request: bytes, expected_bytes: int) -> bytes:
        assert self._writer is not None and self._reader is not None, \
            "Use ModbusRTUClient as an async context manager"

        _LOGGER.debug("TX [%d bytes]: %s", len(request), request.hex())
        self._writer.write(request)
        await self._writer.drain()

        try:
            response = await asyncio.wait_for(
                self._reader.readexactly(expected_bytes),
                timeout=self._timeout,
            )
        except asyncio.IncompleteReadError as exc:
            raise ModbusError(f"Connection closed mid-read: {exc}") from exc

        _LOGGER.debug("RX [%d bytes]: %s", len(response), response.hex())
        await asyncio.sleep(self._delay)
        return response

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def read_holding_registers(self, address: int, count: int) -> list[int]:
        """Read `count` holding registers. Returns list of uint16."""
        request = build_read_holding(self._slave, address, count)
        expected = 3 + count * 2 + 2  # slave + fc + byte_count + data + crc

        try:
            response = await self._send_recv(request, expected)
        except (asyncio.TimeoutError, ConnectionError, OSError) as exc:
            raise ModbusError(f"Transport error: {exc}") from exc

        if not _check_crc(response):
            # Stale bytes may have corrupted the response — flush and retry once
            _LOGGER.debug("CRC mismatch, flushing and retrying")
            await self._flush()
            self._writer.write(request)
            await self._writer.drain()
            try:
                response = await asyncio.wait_for(
                    self._reader.readexactly(expected),
                    timeout=self._timeout,
                )
            except asyncio.IncompleteReadError as exc:
                raise ModbusError(f"Connection closed mid-read on retry: {exc}") from exc
            if not _check_crc(response):
                raise ModbusError("CRC mismatch in response after retry")

        slave_r, fc = response[0], response[1]
        if slave_r != self._slave:
            raise ModbusError(f"Slave mismatch: expected {self._slave}, got {slave_r}")
        if fc & 0x80:
            raise ModbusError(f"Modbus exception code: {response[2]:#04x}")
        if fc != 0x03:
            raise ModbusError(f"Unexpected function code: {fc:#04x}")

        return [
            struct.unpack(">H", response[3 + i * 2 : 5 + i * 2])[0]
            for i in range(count)
        ]

    async def read_holding_register(self, address: int) -> int:
        return (await self.read_holding_registers(address, 1))[0]

    async def read_holding_register_signed(self, address: int) -> int:
        val = await self.read_holding_register(address)
        return val if val < 0x8000 else val - 0x10000

    async def write_register(self, address: int, value: int) -> None:
        """Write a single holding register (FC 0x06)."""
        request = build_write_single(self._slave, address, value)
        try:
            response = await self._send_recv(request, 8)
        except (asyncio.TimeoutError, ConnectionError, OSError) as exc:
            raise ModbusError(f"Transport error: {exc}") from exc

        if not _check_crc(response):
            raise ModbusError("CRC mismatch in write response")
        if response[1] & 0x80:
            raise ModbusError(f"Modbus exception on write: {response[2]:#04x}")


class ModbusError(Exception):
    """Raised on Modbus protocol or transport errors."""