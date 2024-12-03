import pytest
from csp_py import CspId, CspPacketPriority, CspPacketFlags


def test_csp_id_reply() -> None:
    pkt_id = CspId(
        priority=CspPacketPriority.Low,
        flags=CspPacketFlags(12),
        src=10,
        dst=20,
        dport=30,
        sport=40,
    )

    assert pkt_id.reply_id() == CspId(
        priority=CspPacketPriority.Low,
        flags=CspPacketFlags(12),
        src=20,
        dst=10,
        dport=40,
        sport=30,
    )


def test_flag_can_hold_any_value() -> None:
    v = CspPacketFlags(12)
    assert int(v) == 12
    assert int(v | CspPacketFlags.Zero) == 12
    assert int(v | CspPacketFlags.CRC32) == 13


@pytest.mark.parametrize(
    ('value', 'inherit', 'expected'),
    [
        (CspPacketFlags.Zero, CspPacketFlags.Zero, CspPacketFlags.Zero),
        (CspPacketFlags.Inherit, CspPacketFlags.Zero, CspPacketFlags.Zero),
        (CspPacketFlags.Inherit, CspPacketFlags.Inherit, CspPacketFlags.Zero),
        (CspPacketFlags.Zero, CspPacketFlags.Inherit, CspPacketFlags.Zero),

        (CspPacketFlags.CRC32, CspPacketFlags.Zero, CspPacketFlags.CRC32),
        (CspPacketFlags.Inherit, CspPacketFlags.CRC32, CspPacketFlags.CRC32),
        (CspPacketFlags.CRC32 | CspPacketFlags.Inherit, CspPacketFlags.CRC32, CspPacketFlags.CRC32),

        (CspPacketFlags(8) | CspPacketFlags(16), CspPacketFlags.Zero, CspPacketFlags(8) | CspPacketFlags(16)),
        (CspPacketFlags(8) | CspPacketFlags(16) | CspPacketFlags.Inherit, CspPacketFlags(32), CspPacketFlags(8) | CspPacketFlags(16) | CspPacketFlags(32)),
    ]
)
def test_resolve_inheritance_of_flags(value: CspPacketFlags, inherit: CspPacketFlags, expected: CspPacketFlags) -> None:
    resolved = value.resolve(inherit)
    assert resolved == expected
