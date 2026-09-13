"""Run HedgeArcPack in a Windows Job with hard memory/time limits."""
from pathlib import Path
import ctypes, os, subprocess
from ctypes import wintypes as wt

R = Path(__file__).resolve().parents[1]

def unpack(path, timeout=20):
    path = Path(path)
    with path.open('rb') as stream:
        header = stream.read(32)
    if header[:4] == bytes.fromhex('0ff512ee') and int.from_bytes(header[28:32], 'big') > 128*1024*1024:
        raise RuntimeError('Declared decompressed split exceeds 128 MiB; deferred for manual inspection')
    if os.name != 'nt':
        raise RuntimeError('This safety wrapper requires Windows Job limits')
    class Basic(ctypes.Structure):
        _fields_ = [('ProcessTime', ctypes.c_longlong), ('JobTime', ctypes.c_longlong),
                    ('Flags', wt.DWORD), ('MinimumWorkingSet', ctypes.c_size_t), ('MaximumWorkingSet', ctypes.c_size_t),
                    ('ActiveProcesses', wt.DWORD), ('Affinity', ctypes.c_size_t), ('PriorityClass', wt.DWORD), ('SchedulingClass', wt.DWORD)]
    class IO(ctypes.Structure):
        _fields_ = [(name, ctypes.c_ulonglong) for name in ('ReadOps','WriteOps','OtherOps','ReadBytes','WriteBytes','OtherBytes')]
    class Extended(ctypes.Structure):
        _fields_ = [('Basic', Basic), ('IO', IO), ('ProcessMemory', ctypes.c_size_t), ('JobMemory', ctypes.c_size_t),
                    ('PeakProcessMemory', ctypes.c_size_t), ('PeakJobMemory', ctypes.c_size_t)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wt.LPCWSTR]
    kernel.CreateJobObjectW.restype = wt.HANDLE
    kernel.SetInformationJobObject.argtypes = [wt.HANDLE, ctypes.c_int, ctypes.c_void_p, wt.DWORD]
    kernel.AssignProcessToJobObject.argtypes = [wt.HANDLE, wt.HANDLE]
    kernel.CloseHandle.argtypes = [wt.HANDLE]
    job = kernel.CreateJobObjectW(None, None)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    process = None
    try:
        limits = Extended()
        limits.Basic.Flags = 0x100 | 0x2000 | 0x2  # process memory, kill on close, CPU time
        limits.Basic.ProcessTime = 10 * 10_000_000
        limits.ProcessMemory = 384*1024*1024
        if not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            raise ctypes.WinError(ctypes.get_last_error())
        process = subprocess.Popen([str(R/'Tools/HedgeArcPack/HedgeArcPack.exe'), str(path)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW | 0x4)  # suspended until the hard limit is assigned
        if not kernel.AssignProcessToJobObject(job, wt.HANDLE(int(process._handle))):
            raise ctypes.WinError(ctypes.get_last_error())
        resume = ctypes.WinDLL('ntdll').NtResumeProcess
        resume.argtypes = [wt.HANDLE]; resume.restype = ctypes.c_long
        if resume(wt.HANDLE(int(process._handle))) != 0:
            raise RuntimeError('Could not resume bounded extraction')
        stdout, stderr = process.communicate('\n', timeout=timeout)
        if process.returncode:
            raise RuntimeError(f'Archive decoder failed or hit resource limit ({process.returncode}): {(stderr or stdout)[-300:]}')
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.communicate()
        kernel.CloseHandle(job)
