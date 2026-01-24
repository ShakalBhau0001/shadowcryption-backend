from PIL import Image


def bytes_to_bits(data: bytes):
    for b in data:
        for i in range(7, -1, -1):
            yield (b >> i) & 1


def bits_to_bytes(bits):
    out = bytearray()
    buf = 0
    cnt = 0
    for bit in bits:
        buf = (buf << 1) | (bit & 1)
        cnt += 1
        if cnt == 8:
            out.append(buf)
            buf = 0
            cnt = 0
    return bytes(out)


def embed_payload_in_image_file(input_fp: str, payload: bytes, output_fp: str):
    from PIL import Image

    img = Image.open(input_fp).convert("RGBA")
    w, h = img.size
    pixels = list(img.getdata())
    total_bits = w * h * 3
    bits_needed = len(payload) * 8
    if bits_needed > total_bits:
        raise ValueError("Payload too large")
    bit_iter = bytes_to_bits(payload)
    new_pixels = []
    for pix in pixels:
        r, g, b, a = pix
        comps = [r, g, b]
        for i in range(3):
            try:
                bit = next(bit_iter)
                comps[i] = (comps[i] & ~1) | bit
            except StopIteration:
                pass
        new_pixels.append((comps[0], comps[1], comps[2], a))
    steg = Image.new("RGBA", (w, h))
    steg.putdata(new_pixels)
    steg.save(output_fp, format="PNG", optimize=True)


def extract_payload_from_image_file(stego_fp: str, payload_length_bytes: int) -> bytes:
    img = Image.open(stego_fp).convert("RGBA")
    pixels = list(img.getdata())
    required_bits = payload_length_bytes * 8
    bits = []
    for pix in pixels:
        r, g, b, a = pix
        bits.append(r & 1)
        if len(bits) >= required_bits:
            break
        bits.append(g & 1)
        if len(bits) >= required_bits:
            break
        bits.append(b & 1)
        if len(bits) >= required_bits:
            break
    if len(bits) < required_bits:
        raise ValueError("Not enough embedded bits")
    return bits_to_bytes(bits[:required_bits])
