"""
Raw Modbus RTU over TCP client for Polytropic heat pump.

Connects per-session (one TCP connection per coordinator cycle). On CRC or
transport failure the session is torn down and reopened before retrying once —
a desynced RS485-to-TCP gateway buffer can't be salvaged by flushing alone.
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

    Used as an async context manager: one TCP connection for one coordinator
    cycle. On CRC / transport failure, the connection is torn down, reopened,
    and the failing request is retried once.
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
    # Connection lifecycle
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "ModbusRTUClient":
        await self._connect()
        return self

    async def __aexit__(self, *_) -> None:
        await self._close()

    async def _connect(self) -> None:
        self._reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self._host, self._port),
            timeout=self._timeout,
        )
        _LOGGER.debug("Connected to %s:%s", self._host, self._port)
        await self._flush()

    async def _close(self) -> None:
        if self._writer is not None:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception as exc:  # noqa: BLE001
                _LOGGER.debug("Ignoring error during close: %s", exc)
        self._reader = None
        self._writer = None
        _LOGGER.debug("Disconnected from %s:%s", self._host, self._port)

    async def _reconnect(self) -> None:
        """Tear down and re-open the TCP session to recover from desync."""
        _LOGGER.debug("Reconnecting to %s:%s", self._host, self._port)
        await self._close()
        await self._connect()

    async def _flush(self) -> None:
        """Drain buffered bytes until the stream is silent for 100 ms."""
        if self._reader is None:
            return
        drained = 0
        while True:
            try:
                chunk = await asyncio.wait_for(self._reader.read(256), timeout=0.1)
            except asyncio.TimeoutError:
                break
            except Exception as exc:  # noqa: BLE001
                _LOGGER.debug("Flush aborted: %s", exc)
                break
            if not chunk:
                break
            drained += len(chunk)
        if drained:
            _LOGGER.debug("Flushed %d stale byte(s) from buffer", drained)

    # ------------------------------------------------------------------
    # Low-level send / receive
    # ------------------------------------------------------------------

    async def _do_request(self, request: bytes, expected: int) -> bytes:
        """Send one request, read the expected response, verify CRC.

        Raises ModbusError on CRC mismatch, truncated read, or transport
        error. The caller is responsible for retrying (and reconnecting if
        the failure was a desync).
        """
        if self._writer is None or self._reader is None:
            raise ModbusError("Client is not connected — use as async context manager")

        _LOGGER.debug("TX [%d bytes]: %s", len(request), request.hex())
        self._writer.write(request)
        await self._writer.drain()

        try:
            response = await asyncio.wait_for(
                self._reader.readexactly(expected),
                timeout=self._timeout,
            )
        except asyncio.IncompleteReadError as exc:
            raise ModbusError(f"Connection closed mid-read: {exc}") from exc

        _LOGGER.debug("RX [%d bytes]: %s", len(response), response.hex())
        await asyncio.sleep(self._delay)

        if not _check_crc(response):
            raise ModbusError(f"CRC mismatch (got {response.hex()})")
        return response

    async def _request_with_retry(self, request: bytes, expected: int) -> bytes:
        """Execute a request; on failure, reconnect the TCP session and retry once."""
        try:
            return await self._do_request(request, expected)
        except (ModbusError, asyncio.TimeoutError, ConnectionError, OSError) as first_exc:
            _LOGGER.warning(
                "Modbus request failed (%s), reconnecting and retrying", first_exc
            )

        try:
            await self._reconnect()
            return await self._do_request(request, expected)
        except (ModbusError, asyncio.TimeoutError, ConnectionError, OSError) as retry_exc:
            raise ModbusError(f"Request failed after reconnect: {retry_exc}") from retry_exc

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def read_holding_registers(self, address: int, count: int) -> list[int]:
        """Read `count` holding registers starting at `address`. Returns uint16 list."""
        request = build_read_holding(self._slave, address, count)
        expected = 3 + count * 2 + 2  # slave + fc + byte_count + data + crc

        response = await self._request_with_retry(request, expected)

        slave_r, fc = response[0], response[1]
        if slave_r != self._slave:
            raise ModbusError(f"Slave mismatch: expected {self._slave}, got {slave_r}")
        if fc & 0x80:
            raise ModbusError(f"Modbus exception code: {response[2]:#04x}")
        if fc != 0x03:
            raise ModbusError(f"Unexpected function code: {fc:#04x}")
        if response[2] != count * 2:
            raise ModbusError(
                f"Byte count mismatch: expected {count * 2}, got {response[2]}"
            )

        return [
            struct.unpack(">H", response[3 + i * 2 : 5 + i * 2])[0]
            for i in range(count)
        ]

    async def read_holding_register(self, address: int) -> int:
        return (await self.read_holding_registers(address, 1))[0]

    async def write_register(self, address: int, value: int) -> None:
        """Write a single holding register (FC 0x06)."""
        request = build_write_single(self._slave, address, value)
        response = await self._request_with_retry(request, 8)

        if response[0] != self._slave:
            raise ModbusError(
                f"Slave mismatch on write: expected {self._slave}, got {response[0]}"
            )
        if response[1] & 0x80:
            raise ModbusError(f"Modbus exception on write: {response[2]:#04x}")


class ModbusError(Exception):
    """Raised on Modbus protocol or transport errors."""