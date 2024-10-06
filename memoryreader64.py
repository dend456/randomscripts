from ctypes import wintypes as wt
import ctypes as ct
import win32process
import win32ui
import win32api
import struct
import sys
import win32gui
import re
import multiprocessing as mp
from functools import partial


class MemoryReader:
    PROCESS_VM_READ = 0x0010
    PROCESS_VM_WRITE = 0x0020
    PROCESS_VM_OPERATION = 0x0008
    PAGE_READWRITE = 0x0004
    WM_SYSCOMMAND = 0x0112
    WM_ACTIVATE = 0x6
    WM_HOTKEY = 0x0312
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_TERMINATE = 0x0001

    class MemoryReadError(RuntimeError):
        pass

    def __init__(self, window_name, module_name=None, hwnd=None, regions=None):
        self.window_name = window_name
        self.module_name = module_name if module_name else window_name + '.exe'
        self.hwnd = hwnd
        if not hwnd:
            self.hwnd = win32ui.FindWindow(None, self.window_name).GetSafeHwnd()
        self.pid = win32process.GetWindowThreadProcessId(self.hwnd)[1]
        self.handle = self._get_handle()
        self.base_address, self.image_size = self._get_base_address()
        self.regions = regions or self._get_memory_regions()

        self.VirtualProtectEx = ct.windll.kernel32.VirtualProtectEx
        self.VirtualProtectEx.argtypes = [wt.HANDLE, wt.LPVOID, ct.c_size_t, wt.DWORD, wt.LPVOID]
        self.VirtualProtectEx.restype = wt.BOOL

    @classmethod
    def from_window(cls, hwnd, module_name=None):
        return cls(win32gui.GetWindowText(hwnd), module_name=module_name, hwnd=hwnd)

    def _get_handle(self):
        handle = ct.windll.kernel32.OpenProcess(ct.c_uint(MemoryReader.PROCESS_QUERY_INFORMATION |
                                                          MemoryReader.PROCESS_VM_READ | MemoryReader.PROCESS_VM_WRITE |
                                                          MemoryReader.PROCESS_VM_OPERATION),
                                                ct.c_int(1), ct.c_uint(self.pid))
        if handle == ct.c_void_p(0):
            raise RuntimeError('Unable to get process handle.')
        return handle

    def _get_base_address(self):
        class ModuleInfo(ct.Structure):
            _fields_ = [('baseOfDll', wt.LPVOID), ('sizeOfImage', wt.DWORD), ('entryPoint', wt.LPVOID)]
        class MODULEENTRY32(ct.Structure):
            _fields_ = [('dwSize', wt.DWORD),
                        ('th32ModuleID', wt.DWORD),
                        ('th32ProcessID', wt.DWORD),
                        ('GlblcntUsage', wt.DWORD),
                        ('ProccntUsage', wt.DWORD),
                        ('modBaseAddr', ct.POINTER(wt.BYTE)),
                        ('modBaseSize', wt.DWORD),
                        ('hModule', wt.HMODULE),
                        ('szModule', ct.c_char * 256),
                        ('szExePath', ct.c_char * 260)]


        buffer_size = 256

        handle = ct.windll.kernel32.CreateToolhelp32Snapshot(0x8, self.pid)
        if handle == -1:
            raise RuntimeError(f'Unable to create snapshot. Error: {win32api.GetLastError()}')

        me32 = MODULEENTRY32()
        me32.dwSize = ct.sizeof(MODULEENTRY32)
        ret = ct.windll.kernel32.Module32First(handle, ct.pointer(me32))
        if not ret:
            ct.windll.kernel32.CloseHandle(handle)
            raise RuntimeError(f'Unable to get module. Error: {win32api.GetLastError()}')

        while ret:
            if self.module_name == me32.szModule.decode("utf-8"):
                ct.windll.kernel32.CloseHandle(handle)
                return me32.hModule, me32.modBaseSize

            #ret = ct.windll.kernel32.Module32First(handle, ct.pointer(me32))
            ret = ct.windll.kernel32.Module32Next(handle, ct.pointer(me32))

        ct.windll.kernel32.CloseHandle(handle)
        return

    def __del__(self):
        ct.windll.kernel32.CloseHandle(self.handle)

    def read(self, address, bytes_to_read):
        bytes_read = ct.c_size_t(0)
        address = ct.c_void_p(address)
        btr = ct.c_size_t(bytes_to_read)
        buffer = ct.create_string_buffer(bytes_to_read)
        ct.windll.kernel32.ReadProcessMemory(self.handle, address, ct.byref(buffer), btr, ct.byref(bytes_read))
        return bytearray(buffer)

    def read_int(self, address):
        bs = self.read(address, 4)
        return int.from_bytes(bs, signed=True, byteorder=sys.byteorder)

    def read_uint(self, address):
        bs = self.read(address, 4)
        return int.from_bytes(bs, signed=False, byteorder=sys.byteorder)

    def read_uint64(self, address):
        bs = self.read(address, 8)
        return int.from_bytes(bs, signed=False, byteorder=sys.byteorder)

    def read_multi_level_pointer(self, address, offsets):
        if address == 0:
            address = self.baseAddress
        val = address
        for offset in offsets:
            val = self.read_int(val + offset)
        return val

    def read_byte(self, address):
        return self.read(address, 1)

    def read_float(self, address):
        bs = self.read(address, 4)
        return struct.unpack('f', bs)[0]

    def write(self, address, buffer):
        old_protect = ct.c_uint()
        to_write = ct.create_string_buffer(buffer, len(buffer))
        address = ct.c_void_p(address)
        bytes_written = ct.c_int()
        self.VirtualProtectEx(self.handle, address, ct.sizeof(to_write), MemoryReader.PAGE_READWRITE, ct.byref(old_protect))
        ct.windll.kernel32.WriteProcessMemory(self.handle, address, to_write, ct.sizeof(to_write), ct.byref(bytes_written))
        self.VirtualProtectEx(self.handle, address, ct.sizeof(to_write), old_protect, ct.byref(old_protect))
        return bytes_written.value

    def write_byte(self, address, byte):
        return self.write(address, bytes([byte]))

    def write_int(self, address, i):
        return self.write(address, struct.pack('i', i))

    def write_uint(self, address, i):
        return self.write(address, struct.pack('I', i))

    def write_float(self, address, f):
        return self.write(address, struct.pack('f', f))

    @staticmethod
    def memory_to_string(buff, base_offset=0):
        out = ''

        for r in range(0, len(buff) // 16):
            out += f'0x{r * 16 + base_offset:04x}) '
            for c in range(16):
                index = r * 16 + c
                out += f'{buff[index]:02x}'

                out += ' '
                if c % 4 == 3:
                    out += ' '

            out += '    '

            for c in range(16):
                index = r * 16 + c
                if chr(buff[index]).isalnum():
                    out += chr(buff[index])
                else:
                    out += '.'

            out += '\n'
        return out

    def find_ptr(self, pointer, start_addr=None, end_addr=None, buffer_size=1000000, max_offset=0x1000):
        if not start_addr:
            start_addr = self.base_address

        if not end_addr:
            end_addr = self.base_address + self.image_size

        buffer_offset = buffer_size % 4
        possibles = []
        for addr in range(start_addr, end_addr, buffer_size - buffer_offset):
            buff = self.read(addr, buffer_size)
            for i in range(0, buffer_size, 4):
                ptr_addr = struct.unpack('I', buff[i:i + 4])[0]
                if ptr_addr < pointer < ptr_addr + max_offset:
                    image_addr = addr + i - self.base_address
                    possibles.append((image_addr, pointer - ptr_addr))

        return possibles

    def find_group(self, group_str, start_addr=None, end_addr=None, buffer_size=1000000):
        size_types = {1: 'c', 2: 'h', 4: 'i', 8: 'q'}
        start_addr = start_addr or self.base_address
        end_addr = end_addr or (self.base_address + self.image_size)
        if end_addr < start_addr:
            return []

        buffer_size = min(buffer_size, end_addr - start_addr)

        group = group_str.split(' ')
        group = [x.split(':') for x in group]
        group = [(int(size), s) for size, s in group]
        search_str = b''
        for size, s in group:
            if s == '*':
                #size_i = str(int(size) * 2).encode('utf-8')
                #search_str += b'.{0,' + size_i + b'}'
                #search_str += b'.' * size
                search_str += b'.{0,' + str(size).encode('utf-8') + b'}'
            else:
                type_ = size_types[size]
                if type_ == 'c':
                    i = int(s).to_bytes(1, 'little')
                else:
                    i = int(s)
                s = struct.pack(type_, i)
                search_str += s

        regex_str = re.compile(search_str, re.DOTALL)

        buffer_offset = buffer_size % 4
        possibles = []
        for addr in range(start_addr, end_addr, buffer_size - buffer_offset):
            buff = self.read(addr, buffer_size)
            for match in regex_str.finditer(buff):
                possibles.append(match.start() + start_addr)

        return possibles

    @staticmethod
    def _find_group_in_region(window_name, module_name, group_str, start, size):
        try:
            mr = MemoryReader(window_name, module_name, regions=[])
            return mr.find_group(group_str, start_addr=start, end_addr=start + size, buffer_size=size)
        except MemoryError as e:
            return []

    def find_group_all_regions(self, group_str):
        all_pos = []
        args = [(self.window_name, self.module_name, group_str, r[0], r[1]) for r in self.regions]
        with mp.Pool(16) as pool:
            res = pool.starmap(MemoryReader._find_group_in_region, args)
        for x in res:
            if x:
                all_pos += x
        return all_pos

    def _get_memory_regions(self):
        class MemoryBasicInformation(ct.Structure):
            _fields_ = [('base_address', ct.c_size_t), ('allocation_base', ct.c_void_p),
                        ('allocation_protect', wt.DWORD),
                        ('partition_id', wt.WORD), ('size', ct.c_size_t), ('state', wt.DWORD),
                        ('protect', wt.DWORD), ('type', wt.DWORD)]

        PMEMORYBASICINFORMATION = ct.POINTER(MemoryBasicInformation)
        ct.windll.kernel32.VirtualProtectEx.argtypes = [wt.HANDLE, wt.LPCVOID, PMEMORYBASICINFORMATION, ct.c_size_t]
        ct.windll.kernel32.VirtualProtectEx.restype = ct.c_size_t

        addr = ct.c_size_t(0)
        regions = []
        mem_info = MemoryBasicInformation()
        while addr.value < 0x7fffffffffff:
            written = ct.windll.kernel32.VirtualQueryEx(self.handle, addr, ct.byref(mem_info), ct.sizeof(mem_info))
            if written == 0:
                break
            if mem_info.state == 0x1000:
                regions.append((mem_info.base_address or 0, mem_info.size))
            addr = ct.c_size_t(mem_info.base_address + mem_info.size)
        return regions

