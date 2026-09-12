"""Move achievement translations to native GetString call sites; never read/write XEX.

Input is the preserved, verified v1.0.0 Korean Windows x64 EXE. Output is separate.
The leaf dispatcher tail-calls the existing std::string constructor or GetString.
It never changes the guest memory, achievement records, scores, icons or voice.
"""
from pathlib import Path
import sys, struct, json, hashlib, ctypes

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'Tools/UIRuntime'))
import pefile
import capstone
from keystone import Ks, KS_ARCH_X86, KS_MODE_64
from extend_native_font_v101 import extend as extend_native_font

SOURCE_SHA = 'df253ffafab22583b8088c92a034e1023787132465e6f8f05de28e46a41bf9c9'
GET_STRING = 0x290770
CONSTRUCT = 0xcbf90
CALLERS = [(0x290910, 0x29115f), (0x291200, 0x29147b)]


def correct_native_terms(data, pe):
    """Shorten two existing immutable strings and their MSVC string lengths.

    The original table starts at .krui and has 64-byte records. No instruction,
    pointer, glyph, allocation or section address is moved by this correction.
    """
    section = next(s for s in pe.sections if s.Name.rstrip(b'\0') == b'.krui')
    start = section.PointerToRawData
    count_bytes = struct.unpack_from('<I', data, start)[0]
    assert count_bytes == 154 * 64
    desired = json.loads((R/'Translation/native-ui-ko.json').read_text(encoding='utf8'))
    corrections = []
    for index in range(154):
        entry = start + index * 64
        offset, length = struct.unpack_from('<II', data, entry + 8)
        before = bytes(data[start+offset:start+offset+length]).decode('utf8')
        if '웨어호그' not in before:
            continue
        after = before.replace('웨어호그', '웨어혹').replace('웨어혹로', '웨어혹으로')
        assert after in desired
        encoded = after.encode('utf8')
        assert len(encoded) <= length and data[start+offset+length] == 0
        assert struct.unpack_from('<Q', data, entry+32)[0] == length
        data[start+offset:start+offset+length+1] = encoded + bytes(length+1-len(encoded))
        struct.pack_into('<I', data, entry+12, len(encoded))
        struct.pack_into('<Q', data, entry+32, len(encoded))
        corrections.append({'table_index':index,'before':before,'after':after})
    assert len(corrections) == 2 and '웨어호그'.encode() not in data
    return corrections


def build():
    output = R / 'Build/FullBackend-v101/Native'
    output.mkdir(parents=True, exist_ok=True)
    raw = (R / 'Build/FieldMission-v056/Native/UnleashedRecomp.exe').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    pe = pefile.PE(data=raw)
    cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    ks = Ks(KS_ARCH_X86, KS_MODE_64)
    align = lambda n, a: (n + a - 1) // a * a
    va = align(pe.sections[-1].VirtualAddress + pe.sections[-1].Misc_VirtualSize,
               pe.OPTIONAL_HEADER.SectionAlignment)
    src = json.loads((R / 'Translation/achievements-source.json').read_text(encoding='utf8'))
    ko = json.loads((R / 'Translation/achievements-ko.json').read_text(encoding='utf8'))
    mapping = {}
    fields = 0
    for item in src['items']:
        for sid, text in zip(item['string_ids'], ko[str(item['id'])]):
            assert sid not in mapping or mapping[sid] == text
            mapping[sid] = text
            fields += 1
    assert len(ko) == 50 and fields == 150
    blob = bytearray(8 * len(mapping))
    for i, (sid, text) in enumerate(sorted(mapping.items())):
        struct.pack_into('<II', blob, i * 8, sid, len(blob))
        blob.extend(text.encode('utf8') + b'\0')
    blob.extend(bytes((-len(blob)) % 16))
    wrapper = va + len(blob)
    # No stack or nonvolatile register changes, and no calls: no new unwind entry.
    # RCX=this, RDX=return string, R8D=language, R9W=string ID (verified MS x64 ABI).
    code = f'''cmp r8d, 1
jne fallback
lea r10, [rip + 0]
mov r11d, {len(mapping)}
search:
cmp r9w, word ptr [r10]
je found
add r10, 8
dec r11d
jnz search
fallback:
jmp {GET_STRING}
found:
mov eax, dword ptr [r10 + 4]
lea r10, [rip + 0]
add r10, rax
mov rcx, rdx
mov rdx, r10
jmp {CONSTRUCT}
'''
    encoded = bytearray(ks.asm(code, wrapper)[0])
    cs.detail = True
    for ins in cs.disasm(encoded, wrapper):
        if ins.mnemonic == 'lea':
            struct.pack_into('<i', encoded, ins.address - wrapper + ins.disp_offset,
                             va - ins.address - ins.size)
    blob.extend(encoded)
    dispatcher_blob = bytes(blob)
    snapshot, texture, snapshot_size, font_report = extend_native_font(raw, pe)
    blob.extend(bytes((-len(blob)) % 16)); snapshot_rva = va + len(blob); blob.extend(snapshot)
    blob.extend(bytes((-len(blob)) % 16)); texture_rva = va + len(blob); blob.extend(texture)
    b = bytearray(raw)
    native_term_corrections = correct_native_terms(b, pe)
    for inst, target in ((0xfa9f4, snapshot_rva), (0xd0fa8, texture_rva)):
        ins=next(cs.disasm(pe.get_data(inst,7),inst));assert ins.mnemonic=='lea' and ins.size==7
        struct.pack_into('<i',b,pe.get_offset_from_rva(inst+3),target-inst-7)
    for loc,size in ((0xfa9f0,len(snapshot)),(0xd0fa4,len(texture))):
        struct.pack_into('<I',b,pe.get_offset_from_rva(loc),size)
    struct.pack_into('<Q',b,pe.get_offset_from_rva(0xfa8b2+7+0x323c6bf),snapshot_size)
    calls = []
    for start, end in CALLERS:
        for ins in cs.disasm(pe.get_data(start, end - start), start):
            if ins.mnemonic == 'call' and ins.op_str == hex(GET_STRING):
                assert ins.size == 5
                off = pe.get_offset_from_rva(ins.address)
                patch = bytes(ks.asm(f'call {wrapper}', ins.address)[0])
                b[off:off + 5] = patch
                calls.append({'rva': ins.address, 'before': ins.bytes.hex(), 'after': patch.hex()})
    assert len(calls) == 6, calls
    # Preserve every original instruction of GetString and its unwind metadata.
    assert pe.get_data(GET_STRING, 5) == bytes.fromhex('4157415656')
    assert pe.get_data(CONSTRUCT, 7) == bytes.fromhex('41574156565753')
    header = pe.sections[-1].get_file_offset() + 40
    assert header + 40 <= pe.OPTIONAL_HEADER.SizeOfHeaders and not any(b[header:header + 40])
    fileoff = align(len(b), pe.OPTIONAL_HEADER.FileAlignment)
    rawsize = align(len(blob), pe.OPTIONAL_HEADER.FileAlignment)
    struct.pack_into('<8s6I2HI', b, header, b'.krach\0\0', len(blob), va, rawsize, fileoff,
                     0, 0, 0, 0, 0x60000060)  # Read/execute; translation table is immutable.
    struct.pack_into('<H', b, pe.FILE_HEADER.get_field_absolute_offset('NumberOfSections'), len(pe.sections) + 1)
    struct.pack_into('<I', b, pe.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfImage'), align(va + len(blob), pe.OPTIONAL_HEADER.SectionAlignment))
    struct.pack_into('<I', b, pe.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfCode'), pe.OPTIONAL_HEADER.SizeOfCode + rawsize)
    b.extend(bytes(fileoff - len(b))); b.extend(blob); b.extend(bytes(rawsize - len(blob)))
    (output / 'UnleashedRecomp.exe').write_bytes(b)
    report = {'source_sha256': SOURCE_SHA, 'patched_sha256': hashlib.sha256(b).hexdigest(),
              'achievement_fields': fields, 'unique_string_ids': len(mapping), 'calls': calls,
              'section_rva': va, 'wrapper_rva': wrapper, 'native_term_corrections': native_term_corrections,
              'native_font':font_report,'font_snapshot_rva':snapshot_rva,'font_texture_rva':texture_rva,
              'xex_accessed': False, 'native_dispatch_test': test_dispatch(dispatcher_blob, wrapper - va, va, mapping, ks, cs),
              'in_game_validation': 'pending'}
    (output.parent / 'native-report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps(report, indent=2))


def test_dispatch(blob, entry, va, mapping, ks, cs):
    # Execute the actual dispatcher with leaf stubs for the game's two tail targets.
    # This tests routing and ABI arguments without launching the game or allocating
    # strings with another runtime's allocator. The real constructor is unchanged.
    data = bytearray(blob)
    fallback = len(data); data.extend(bytes(ks.asm('mov rax, 0x12345678; ret')[0]))
    construct = len(data); data.extend(bytes(ks.asm('mov [rcx], rdx; mov rax, rcx; ret')[0]))
    for ins in cs.disasm(blob[entry:], va + entry):
        if ins.mnemonic == 'jmp' and ins.op_str in (hex(GET_STRING), hex(CONSTRUCT)):
            dest = fallback if ins.op_str == hex(GET_STRING) else construct
            off = ins.address - va
            replacement = bytes(ks.asm(f'jmp {va + dest}', ins.address)[0])
            assert len(replacement) <= ins.size
            data[off:off + ins.size] = replacement + b'\x90' * (ins.size - len(replacement))
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.VirtualAlloc.restype = ctypes.c_void_p
    kernel.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong, ctypes.c_ulong]
    kernel.VirtualFree.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong]
    memory = kernel.VirtualAlloc(None, len(data), 0x3000, 0x40)
    assert memory
    try:
        ctypes.memmove(memory, bytes(data), len(data))
        fn = ctypes.WINFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint16)(memory + entry)
        result = ctypes.c_void_p()
        for sid, text in mapping.items():
            assert fn(None, ctypes.byref(result), 1, sid) == ctypes.addressof(result)
            assert ctypes.string_at(result.value).decode('utf8') == text
            for language in (0, 2, 3, 4, 5, 6, 7):
                assert fn(None, ctypes.byref(result), language, sid) == 0x12345678
        for sid in (0, 65535):
            assert sid not in mapping
            assert fn(None, ctypes.byref(result), 1, sid) == 0x12345678
    finally:
        kernel.VirtualFree(memory, 0, 0x8000)
    return {'passed': True, 'translated_ids': len(mapping), 'fallback_languages': 7, 'unknown_ids': 2}


if __name__ == '__main__':
    build()
