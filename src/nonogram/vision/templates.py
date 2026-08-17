"""OCR templates for digit recognition."""

import numpy as np

# Packed 1-bit templates for digits 0-9 (24x16)
PACKED_TEMPLATES = {
    0: bytes.fromhex("07e01ff81ff83c3c781c700e700ef00fe007e007e007e007e007e007e007e007f00f700e700e781e3c3c1ff81ff807e0"),
    1: bytes.fromhex("007f01ff0fff7fffff9ffe1ff01f801f001f001f001f001f001f001f001f001f001f001f001f001f001f001f001f001f"),
    2: bytes.fromhex("0fe01ff83ffc783ef01ee00ee00f000f000f001e001c003c007800f001f003e00f801f003e007c00f800ffffffffffff"),
    3: bytes.fromhex("0ff03ffc7ffc783ef00ee00e000f000e001e003c07f807f807fc001e000f00070007e007f00ff00f7c3e7ffc1ff807e0"),
    4: bytes.fromhex("0038007800f800f801f803f803b8073807380e381c381c38383838387038fffeffffffff7ffe00380038003800380038"),
    5: bytes.fromhex("7ffe7ffe7ffe7000f000f000e000e000e7f0fff8fffcfc3ef01fe00f000700070007e007f00ff81f7ffe3ffc1ff807e0"),
    6: bytes.fromhex("07f80ffc1ffe3c1e780f70077000f000e3f0e7f8effcfe3ef80ff80ff007f007f0077007780f380f3e3e1ffc0ff807e0"),
    7: bytes.fromhex("ffffffffffffffff001f001e003e003c00380078007000f000f001e003e003e007c007c0078007000f000f001e001c00"),
    8: bytes.fromhex("0ff01ffc3ffe7c1e780f700f7007700f780e3c3e1ffc1ff83ffc7c1e700ff007e007e007f007f00f7c1f7ffe1ffc0ff0"),
    9: bytes.fromhex("03001fe03ff07ff8f01cf01ee00ee00ee00ee00ee01e701f787e3ffe1fee0f8e000e000ef01ef01c7ff87ff01fe00380"),
}

TEMPLATES = {
    d: np.unpackbits(np.frombuffer(raw, dtype=np.uint8)).reshape(24, 16)
    for d, raw in PACKED_TEMPLATES.items()
}
