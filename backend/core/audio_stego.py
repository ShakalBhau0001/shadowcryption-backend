import wave, sys, array


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


def embed_payload_in_wav_file(input_wav: str, payload: bytes, output_wav: str):
    with wave.open(input_wav, "rb") as wf:
        params = wf.getparams()
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        n_frames = wf.getnframes()
        frames = wf.readframes(n_frames)
    if sampwidth != 2:
        raise ValueError("Only 16-bit PCM WAV supported")
    total_samples = n_frames * n_channels
    bits_needed = len(payload) * 8
    if bits_needed > total_samples:
        raise ValueError("Payload too large")
    samples = array.array("h")
    samples.frombytes(frames)
    if sys.byteorder == "big":
        samples.byteswap()
    bit_iter = bytes_to_bits(payload)
    for i in range(len(samples)):
        try:
            b = next(bit_iter)
            samples[i] = (samples[i] & ~1) | b
        except StopIteration:
            break
    out_frames = samples.tobytes()
    if sys.byteorder == "big":
        out_arr = array.array("h")
        out_arr.frombytes(out_frames)
        out_arr.byteswap()
        out_frames = out_arr.tobytes()
    with wave.open(output_wav, "wb") as out_wf:
        out_wf.setparams(params)
        out_wf.writeframes(out_frames)


def extract_payload_from_wav_file(stego_wav: str, payload_length_bytes: int) -> bytes:
    with wave.open(stego_wav, "rb") as wf:
        sampwidth = wf.getsampwidth()
        if sampwidth != 2:
            raise ValueError("Only 16-bit PCM WAV supported")
        n_frames = wf.getnframes()
        frames = wf.readframes(n_frames)
    samples = array.array("h")
    samples.frombytes(frames)
    if sys.byteorder == "big":
        samples.byteswap()
    bits_required = payload_length_bytes * 8
    total_samples = len(samples)
    if bits_required > total_samples:
        raise ValueError("Not enough embedded bits")
    bits = [samples[i] & 1 for i in range(bits_required)]
    return bits_to_bytes(bits)
