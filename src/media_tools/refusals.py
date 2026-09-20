"""Machine-readable refusal tickets (prototype).

String contract: every helper returns a plain ``str`` whose text is
byte-identical to the historical ``Error: ...`` message. The structured
ticket rides along as an attribute (``.ticket``) / ``.to_dict()`` for
future agents. No caller is required to read it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Ticket:
    code: str
    reason: str
    fix_hint: str
    docs_link: str
    remedy: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


# Stable codes + their static metadata. ``reason`` is per-instance.
REGISTRY: dict[str, dict[str, str]] = {
    "E_OVERWRITE_BLOCKED": {
        "fix_hint": "Pass a different output path; edits are never in place.",
        "docs_link": "",
        "remedy": "use_different_output",
    },
    "E_ENCRYPTED_PDF": {
        "fix_hint": "Unlock the PDF first (pdf_unlock) or supply its password.",
        "docs_link": "",
        "remedy": "unlock_first",
    },
    "E_MISSING_BINARY": {
        "fix_hint": "Install Ghostscript: brew install ghostscript (macOS) "
        "or sudo apt-get install ghostscript (Debian/Ubuntu).",
        "docs_link": "",
        "remedy": "install_binary:gs",
    },
}


class TicketedString(str):
    """A str carrying its Ticket. Renders exactly like the plain message."""

    ticket: Ticket | None = None

    def __new__(cls, text: str, ticket: Ticket | None = None) -> TicketedString:
        obj = super().__new__(cls, text)
        obj.ticket = ticket
        return obj

    def to_dict(self) -> dict[str, str] | None:
        return self.ticket.to_dict() if self.ticket is not None else None


def _wrap(code: str, reason: str) -> TicketedString:
    meta = REGISTRY[code]
    return TicketedString(
        reason,
        Ticket(
            code=code,
            reason=reason,
            fix_hint=meta["fix_hint"],
            docs_link=meta["docs_link"],
            remedy=meta["remedy"],
        ),
    )


def overwrite_blocked(reason: str) -> TicketedString:
    """Ticket for refusal to write over the input (E_OVERWRITE_BLOCKED)."""
    return _wrap("E_OVERWRITE_BLOCKED", reason)


def encrypted_pdf(reason: str) -> TicketedString:
    """Ticket for encrypted-PDF refusal (E_ENCRYPTED_PDF)."""
    return _wrap("E_ENCRYPTED_PDF", reason)


def missing_binary(reason: str, binary: str = "gs") -> TicketedString:
    """Ticket for a missing external binary (E_MISSING_BINARY).

    The binary name stays in ``remedy`` (``install_binary:<name>``) and the
    human hint carries the brew/apt install commands.
    """
    s = _wrap("E_MISSING_BINARY", reason)
    if binary != "gs":
        t = s.ticket
        assert t is not None
        s.ticket = Ticket(
            code=t.code,
            reason=t.reason,
            fix_hint=f"Install {binary}: brew install {binary} (macOS) "
            f"or sudo apt-get install {binary} (Debian/Ubuntu).",
            docs_link=t.docs_link,
            remedy=f"install_binary:{binary}",
        )
    return s
