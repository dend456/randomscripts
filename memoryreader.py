from ctypes import wintypes as wt
import ctypes as ct
import win32process
import win32ui
import time
import struct
import sys
import win32gui


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
        self.base_address = self._get_base_address()

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
            raise RuntimeError('Unable to enumerate modules.')

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

        return info.baseOfDll

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


def main():
    mr = MemoryReader('Hearthstone')

    offsets = [0x00A1E264, 0x310, 0x6D0, 0x568, 0x6E4, 0xC8]

    while True:
        screen = mr.read_multi_level_pointer(0, offsets)
        print(screen)
        time.sleep(1)


if __name__ == '__main__':
    main()
