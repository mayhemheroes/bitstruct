#!/usr/bin/env python3
import atheris
import sys
from typing import List, Set, Dict, Tuple, Any

with atheris.instrument_imports():
    import bitstruct


def _handle_type(fdp: atheris.FuzzedDataProvider, ty_queue: List[type]) -> Any:
    """
    Handles the fuzzing of a single type.
    :param fdp: FuzzedDataProvider object
    :param ty_queue: The current stack of types to be used for fuzzing
    :return: The fuzzed element
    """
    if not ty_queue:
        return None
    ty = ty_queue.pop(0)
    if ty is bytes:
        return fdp.ConsumeBytes(fdp.ConsumeIntInRange(0, 100))
    elif ty is bytearray:
        return bytearray(fdp.ConsumeBytes(fdp.ConsumeIntInRange(0, 100)))
    elif ty is str:
        return fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 100))
    elif ty is float:
        return fdp.ConsumeRegularFloat()
    elif ty is bool:
        return fdp.ConsumeBool()
    elif ty is int:
        return fdp.ConsumeInt(4)
    elif ty is dict:
        return build_fuzz_dict(fdp, ty_queue)
    elif ty is list:
        return build_fuzz_list(fdp, ty_queue)
    elif ty is set:
        return build_fuzz_set(fdp, ty_queue)
    elif ty is tuple:
        return build_fuzz_tuple(fdp, ty_queue)
    else:
        return None


def build_fuzz_list(fdp: atheris.FuzzedDataProvider, ty_queue: List[type]) -> List[Any]:
    """
    Builds a list with fuzzer-defined elements.
    :param fdp: FuzzedDataProvider object
    :param ty_queue: The current stack of types to be used for fuzzing
    :return: The list
    """
    if not ty_queue:
        return []
    elem_count = fdp.ConsumeIntInRange(1, 5)
    gen_list = []

    for _ in range(elem_count):
        passed_queue = ty_queue.copy()
        elem = _handle_type(fdp, passed_queue)
        if elem is not None:
            gen_list.append(elem)
    ty_queue.pop(0)  # Pop elem type

    return gen_list


def build_fuzz_set(fdp: atheris.FuzzedDataProvider, ty_queue: List[type]) -> Set[Any]:
    """
    Builds a set with fuzzer-defined elements.
    :param fdp: FuzzedDataProvider object
    :param ty_queue: The current stack of types to be used for fuzzing
    :return: The set
    """
    if not ty_queue:
        return set()
    ty_queue.insert(0, list)

    fuzz_list = _handle_type(fdp, ty_queue)
    return set(fuzz_list)


def build_fuzz_tuple(fdp: atheris.FuzzedDataProvider, ty_queue: List[type]) -> Tuple[Any]:
    """
    Builds a tuple with fuzzer-defined elements.
    :param fdp: FuzzedDataProvider object
    :param ty_queue: The current stack of types to be used for fuzzing
    :return: The tuple
    """
    if not ty_queue:
        return tuple()
    ty_queue.insert(0, list)

    fuzz_list = _handle_type(fdp, ty_queue)
    return tuple(fuzz_list)


def build_fuzz_dict(fdp: atheris.FuzzedDataProvider, ty_queue: List[type]) -> Dict[Any, Any]:
    """
    Builds a dictionary with fuzzer-defined keys and values.
    :param fdp: FuzzedDataProvider object
    :param ty_queue: The current stack of types to be used for fuzzing
    :return: The dictionary
    """
    if not ty_queue:
        return {}

    ty_queue.insert(0, list)  # handle key
    key_list = _handle_type(fdp, ty_queue)
    ty_queue.insert(0, list)  # handle key
    val_list = _handle_type(fdp, ty_queue)

    # Shrink lists to match
    if len(key_list) > len(val_list):
        key_list = key_list[:len(val_list)]
    elif len(val_list) > len(key_list):
        val_list = val_list[:len(key_list)]

    return dict(zip(key_list, val_list))


def TestOneInput(data):
    fdp = atheris.FuzzedDataProvider(data)
    try:
        format_string = fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 100))
        packed_data = bitstruct.pack(format_string, fdp.ConsumeInt(4), -fdp.ConsumeInt(4),
                       fdp.ConsumeRegularFloat(), fdp.ConsumeBool(), fdp.ConsumeBytes(fdp.ConsumeIntInRange(0, 100)),
                       fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 100)))
        bitstruct.unpack(format_string, packed_data)
        bitstruct.calcsize(format_string)

        # Dicts
        names = build_fuzz_list(fdp, [str])
        dict_format_string = fdp.ConsumeUnicodeNoSurrogates(fdp.ConsumeIntInRange(0, 100))
        packed_dict = bitstruct.pack_dict(dict_format_string, names, build_fuzz_dict(fdp, [str, int]))
        bitstruct.unpack_dict(dict_format_string, names, packed_dict)
    except (bitstruct.Error, MemoryError):
        return -1



def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
