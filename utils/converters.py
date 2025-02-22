def binary2bool(binary_):
    return bool(int.from_bytes(binary_, byteorder='big'))
