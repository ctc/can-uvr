from crccheck.crc import CrcArc

def makeTACheckSum(b: bytes) -> bytes:
    return CrcArc.calc(b).to_bytes(2, 'little')

def appendTACheckSum(b: bytes) -> bytes:
    return b + makeTACheckSum(b)