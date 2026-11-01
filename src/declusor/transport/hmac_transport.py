"""Authenticated transport layer using HMAC-SHA256 frame envelopes."""

import hashlib
import hmac
import secrets
import struct
from typing import Final, Literal

from declusor import config, contract

HmacRole = Literal["initiator", "responder"]


class HmacTransport(contract.ITransportLayer):
    """Authenticate and integrity-protect a byte stream with a shared secret.

    This layer does not encrypt payloads. It performs a mutual HMAC handshake in
    ``establish()`` and then wraps each write in a length-delimited authenticated
    frame with an independent monotonic counter in each direction.
    """

    _HANDSHAKE_MAGIC: Final[bytes] = b"DECLHMAC1"
    _HANDSHAKE_NONCE_SIZE: Final[int] = 32
    _TAG_SIZE: Final[int] = hashlib.sha256().digest_size
    _FRAME_HEADER: Final[struct.Struct] = struct.Struct(">8sQI")
    _FRAME_MAGIC: Final[bytes] = b"DHMACFR1"

    def __init__(self, transport: contract.ITransport, key: bytes, *, role: HmacRole) -> None:
        """Initialize an HMAC transport with a non-empty pre-shared key."""

        super().__init__(transport)

        if not key:
            raise ValueError("HMAC key cannot be empty.")

        if role not in ("initiator", "responder"):
            raise ValueError(f"Unsupported HMAC role: {role!r}.")

        self._key = bytes(key)
        self._role = role
        self._established = False
        self._send_counter = 0
        self._receive_counter = 0
        self._pending_payload = bytearray()

    @property
    def is_established(self) -> bool:
        """Return whether the mutual HMAC handshake has completed."""

        return self._established

    def establish(self) -> None:
        """Perform mutual authentication before allowing application frames."""

        if self.is_closed:
            raise config.ConnectionClosed("Cannot establish a closed HMAC transport.")

        if self._established:
            return

        try:
            if self._role == "initiator":
                self._establish_initiator()
            else:
                self._establish_responder()
        except (config.ConnectionClosed, config.ConnectionTimeoutError, config.ConnectionError):
            self.close()
            raise
        except (ValueError, struct.error) as error:
            self.close()
            raise config.ConnectionError(f"Invalid HMAC handshake: {error}") from error

        self._established = True

    def read(self, max_bytes: int = config.DEFAULT_BUFFER_SIZE, /) -> bytes:
        """Read and authenticate one or more payload chunks from the stream."""

        if max_bytes <= 0:
            raise ValueError(f"max_bytes must be positive, got {max_bytes}.")

        if not self._established:
            raise config.ConnectionError("HMAC transport has not been established.")

        if self._pending_payload:
            return self._take_pending(max_bytes)

        header = self._transport.read_exact(self._FRAME_HEADER.size)
        magic, counter, length = self._FRAME_HEADER.unpack(header)

        if magic != self._FRAME_MAGIC:
            self._fail_protocol("Invalid HMAC frame magic.")

        if counter != self._receive_counter:
            self._fail_protocol(f"Unexpected HMAC frame counter {counter}; expected {self._receive_counter}.")

        if length > config.MAX_TLV_FRAME_SIZE:
            self._fail_protocol(f"HMAC frame payload size {length} exceeds maximum {config.MAX_TLV_FRAME_SIZE}.")

        payload = self._transport.read_exact(length)
        received_tag = self._transport.read_exact(self._TAG_SIZE)
        expected_tag = self._tag(self._receive_label, header, payload)

        if not hmac.compare_digest(received_tag, expected_tag):
            self._fail_protocol("HMAC frame authentication failed.")

        self._receive_counter += 1
        self._pending_payload.extend(payload)

        return self._take_pending(max_bytes)

    def write(self, data: bytes, /) -> None:
        """Authenticate and send one payload frame."""

        if not self._established:
            raise config.ConnectionError("HMAC transport has not been established.")

        if not data:
            return

        if len(data) > config.MAX_TLV_FRAME_SIZE:
            raise ValueError(f"HMAC frame payload exceeds maximum size of {config.MAX_TLV_FRAME_SIZE} bytes.")

        header = self._FRAME_HEADER.pack(self._FRAME_MAGIC, self._send_counter, len(data))

        self._transport.write(header + data + self._send_label_tag(header, data))
        self._send_counter += 1

    def _establish_initiator(self) -> None:
        initiator_nonce = secrets.token_bytes(self._HANDSHAKE_NONCE_SIZE)
        self._transport.write(self._HANDSHAKE_MAGIC + b"I" + initiator_nonce)

        response = self._transport.read_exact(len(self._HANDSHAKE_MAGIC) + 1 + self._HANDSHAKE_NONCE_SIZE + self._TAG_SIZE)

        if (
            response[: len(self._HANDSHAKE_MAGIC)] != self._HANDSHAKE_MAGIC
            or response[len(self._HANDSHAKE_MAGIC) : len(self._HANDSHAKE_MAGIC) + 1] != b"R"
        ):
            raise config.ConnectionError("Invalid HMAC responder handshake.")

        offset = len(self._HANDSHAKE_MAGIC) + 1

        responder_nonce = response[offset : offset + self._HANDSHAKE_NONCE_SIZE]
        received_tag = response[offset + self._HANDSHAKE_NONCE_SIZE :]

        transcript = initiator_nonce + responder_nonce

        if not hmac.compare_digest(received_tag, self._tag(b"response", transcript)):
            raise config.ConnectionError("HMAC responder authentication failed.")

        self._transport.write(self._HANDSHAKE_MAGIC + b"P" + self._tag(b"proof", transcript))
        confirmation = self._transport.read_exact(len(self._HANDSHAKE_MAGIC) + 1 + self._TAG_SIZE)

        if confirmation != self._HANDSHAKE_MAGIC + b"A" + self._tag(b"ack", transcript):
            raise config.ConnectionError("Invalid HMAC server confirmation.")

    def _establish_responder(self) -> None:
        hello = self._transport.read_exact(len(self._HANDSHAKE_MAGIC) + 1 + self._HANDSHAKE_NONCE_SIZE)

        if hello[: len(self._HANDSHAKE_MAGIC)] != self._HANDSHAKE_MAGIC or hello[len(self._HANDSHAKE_MAGIC) : len(self._HANDSHAKE_MAGIC) + 1] != b"I":
            raise config.ConnectionError("Invalid HMAC initiator handshake.")

        initiator_nonce = hello[len(self._HANDSHAKE_MAGIC) + 1 :]
        responder_nonce = secrets.token_bytes(self._HANDSHAKE_NONCE_SIZE)
        transcript = initiator_nonce + responder_nonce

        self._transport.write(self._HANDSHAKE_MAGIC + b"R" + responder_nonce + self._tag(b"response", transcript))

        proof = self._transport.read_exact(len(self._HANDSHAKE_MAGIC) + 1 + self._TAG_SIZE)

        if proof != self._HANDSHAKE_MAGIC + b"P" + self._tag(b"proof", transcript):
            raise config.ConnectionError("HMAC initiator authentication failed.")

        self._transport.write(self._HANDSHAKE_MAGIC + b"A" + self._tag(b"ack", transcript))

    def _tag(self, label: bytes, *parts: bytes) -> bytes:
        digest = hmac.new(self._key, digestmod=hashlib.sha256)
        digest.update(label)

        for part in parts:
            digest.update(part)

        return digest.digest()

    @property
    def _send_label(self) -> bytes:
        """Return the direction label for locally sent frames."""

        return b"initiator-frame" if self._role == "initiator" else b"responder-frame"

    @property
    def _receive_label(self) -> bytes:
        """Return the direction label for remotely sent frames."""

        return b"responder-frame" if self._role == "initiator" else b"initiator-frame"

    def _send_label_tag(self, header: bytes, payload: bytes) -> bytes:
        """Calculate the tag for a locally sent frame."""

        return self._tag(self._send_label, header, payload)

    def _take_pending(self, max_bytes: int) -> bytes:
        chunk = bytes(self._pending_payload[:max_bytes])

        del self._pending_payload[: len(chunk)]

        return chunk

    def _fail_protocol(self, message: str) -> None:
        self.close()
        raise config.ConnectionError(message)
