from ctypes import wintypes as wt
import ctypes as ct
import win32process
import win32ui
import win32api
import struct
import sys
import win32gui
import re


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

    def __init__(self, window_name, module_name=None, hwnd=None):
        self.window_name = window_name
        self.module_name = module_name if module_name else window_name + '.exe'
        self.hwnd = hwnd
        if not hwnd:
            self.hwnd = win32ui.FindWindow(None, self.window_name).GetSafeHwnd()
        self.pid = win32process.GetWindowThreadProcessId(self.hwnd)[1]
        self.handle = self._get_handle()
        self.base_address, self.image_size = self._get_base_address()

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
        buffer_size = 256
        image_name = ct.create_string_buffer(buffer_size)
        length = ct.windll.psapi.GetProcessImageFileNameA(self.handle, image_name, wt.DWORD(buffer_size))
        if length <= 0:
            raise RuntimeError('Unable to get image file name.')
        modules = (ct.c_ulong * 1024)()
        count = ct.c_ulong()
        if ct.windll.psapi.EnumProcessModules(self.handle, modules, ct.sizeof(modules), ct.byref(count)) == 0:
            raise RuntimeError(f'Unable to enumerate modules. Error: {win32api.GetLastError()}')

        module_handle = 0
        module_name_in_bytes = bytes(self.module_name, 'utf-8')
        for i in range(0, count.value // ct.sizeof(wt.HMODULE)):
            module_name = ct.create_string_buffer(buffer_size)
            if ct.windll.psapi.GetModuleBaseNameA(self.handle, modules[0], module_name, ct.sizeof(module_name)) == 0:
                raise RuntimeError('Unable to get module name.')
            if module_name.value == module_name_in_bytes:
                module_handle = modules[i]
                break

        if module_handle == 0:
            raise RuntimeError('Unable to get module handle.')

        info = ModuleInfo()
        if ct.windll.psapi.GetModuleInformation(self.handle, modules[0], ct.byref(info), ct.sizeof(info)) == 0:
            raise RuntimeError('Unable to get module info.')

        return info.baseOfDll, info.sizeOfImage

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
        ct.windll.kernel32.VirtualProtectEx(self.handle, address, ct.sizeof(to_write),
                                            MemoryReader.PAGE_READWRITE, ct.byref(old_protect))
        ct.windll.kernel32.WriteProcessMemory(self.handle, address, to_write, ct.sizeof(to_write),
                                              ct.byref(bytes_written))
        ct.windll.kernel32.VirtualProtectEx(self.handle, address, ct.sizeof(to_write),
                                            old_protect, ct.byref(old_protect))
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
            out += f'0x{r*16+base_offset:04x}) '
            for c in range(16):
                index = r*16 + c
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
                ptr_addr = struct.unpack('I', buff[i:i+4])[0]
                if ptr_addr < pointer < ptr_addr + max_offset:
                    image_addr = addr + i - self.base_address
                    possibles.append((image_addr, pointer - ptr_addr))

        return possibles

    def find_group(self, group_str, start_addr=None, end_addr=None, buffer_size=1000000):
        size_types = {1: 'c', 2: 'h', 4: 'i', 8: 'q'}
        if not start_addr:
            start_addr = self.base_address

        if not end_addr:
            end_addr = self.base_address + self.image_size

        group = group_str.split(' ')
        group = [x.split(':') for x in group]
        group = [(int(size), s) for size, s in group]
        search_str = b''
        for size, s in group:
            if s == '*':
                search_str += b'.' * size
            else:
                i = int(s)
                s = struct.pack(size_types[size], i)
                search_str += s

        regex_str = re.compile(search_str, re.DOTALL)

        buffer_offset = buffer_size % 4
        possibles = []
        for addr in range(start_addr, end_addr, buffer_size - buffer_offset):
            buff = self.read(addr, buffer_size)
            for match in regex_str.finditer(buff):
                possibles.append(match.start())

        return possibles

def main():
    import time
    import os

    mr = MemoryReader('EverQuest', 'eqgame.exe')

    # while True:
    #     os.system('cls')
    #     addr = mr.read_uint(mr.base_address + 0x9e573c)
    #     buff = mr.read(addr + 0x400, 0x300)
    #     print(mr.memory_to_string(buff, 0x400))
    #     time.sleep(.5)

    addr = 0xde573c - 0x400000 + mr.base_address
    addr = mr.read_int(addr)
    print(f'base: {mr.base_address:x} end: {mr.base_address+mr.image_size:x} addr:{addr:x}')
    #
    #
    # pos = mr.find_group('4:-10 4:-15 100:* 4:15 4:2 4:10 4:10 4:0 8:* 4:198', start_addr=addr, end_addr=addr+0x10000000, buffer_size=1000000)
    # for p in pos:
    #     print(f'{p:x}')

    start_addr = mr.base_address
    end_addr = mr.base_address + mr.image_size
    memory = mr.read(start_addr, end_addr - start_addr)
    possible_addrs = []
    for addr in range(0, end_addr - start_addr, 4):
        next_addr = int.from_bytes(memory[addr:addr+4], 'little', signed=False)
        if 0x10000000 < next_addr < 0xffffffff:
            pos = mr.find_group('4:-10 4:-15 100:* 4:15 4:2 4:10 4:10 4:0 8:* 4:198', start_addr=next_addr, end_addr=next_addr+0x1000, buffer_size=0x1000)
            if pos:
                pos = [(addr + 0x400000, x) for x in pos]
                for x in pos:
                    print(f'Found possible: {x[0]:x} + {x[1]:x}')
                possible_addrs.extend(pos)


    #print(possible_addrs)

    # print(mr.image_size)
    # res = mr.find_ptr(0x2ECC466C)
    # for addr in res:
    #     print(f'0x{addr[0]:x} + 0x{addr[1]:x}')

if __name__ == '__main__':
    main()
