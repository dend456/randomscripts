from ctypes import *
from ctypes import wintypes
import os,win32process,win32api,win32ui,time


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
        
    def __init__(self, windowName, moduleName = None):
        self.windowName = windowName
        if not moduleName:
            self.moduleName = self.windowName + '.exe'
        else:
            self.moduleName = moduleName

        self.hwnd = win32ui.FindWindow(None,self.windowName).GetSafeHwnd()
        self.processId = win32process.GetWindowThreadProcessId(self.hwnd)[1]
        self.handle = self.__getHandle()

        self.baseAddress = self.__getBaseAddress()

    def __getHandle(self):
        handle = windll.kernel32.OpenProcess(c_uint(MemoryReader.PROCESS_QUERY_INFORMATION | MemoryReader.PROCESS_VM_READ | MemoryReader.PROCESS_VM_WRITE | MemoryReader.PROCESS_VM_OPERATION), c_int(1), c_uint(self.processId))
        if handle == c_void_p(0):
            raise RuntimeError('Unable to get process handle.')
        return handle

    def __getBaseAddress(self):
        class ModuleInfo(Structure):
            _fields_ = [('baseOfDll', wintypes.LPVOID),
                        ('sizeOfImage', wintypes.DWORD),
                        ('entryPoint', wintypes.LPVOID)]
        bufferSize = 256
        imageName = create_string_buffer(bufferSize)

        length = windll.psapi.GetProcessImageFileNameA(self.handle, imageName, wintypes.DWORD(bufferSize))
        if length <= 0:
            raise RuntimeError('Unable to get image file name.')
        
        modules = (c_ulong * 1024)()
        count = c_ulong()
        
        if windll.psapi.EnumProcessModules(self.handle, modules, sizeof(modules), byref(count)) == 0:
            raise RuntimeError('Unable to enumerate modules.')

        moduleHandle = 0
        moduleNameInBytes = bytes(self.moduleName,'utf-8')
        
        for i in range(0,count.value // sizeof(wintypes.HMODULE)):
            moduleName = create_string_buffer(bufferSize)
        
            if windll.psapi.GetModuleBaseNameA(self.handle, modules[0], moduleName, sizeof(moduleName)) == 0:
                raise RuntimeError('Unable to get module name.')

            if moduleName.value == moduleNameInBytes:
                moduleHandle = modules[i]
                break

        if moduleHandle == 0:
            raise RuntimeError('Unable to get module handle.')


        info = ModuleInfo()

        if windll.psapi.GetModuleInformation(self.handle, modules[0], byref(info), sizeof(info)) == 0:
            raise RuntimeError('Unable to get module info.')

        return info.baseOfDll

    def read(self, address, bytesToRead):
        bytesRead = c_size_t(0)
        address = c_void_p(address)
        btr = c_size_t(bytesToRead)
        buffer = create_string_buffer(bytesToRead)
        windll.kernel32.ReadProcessMemory(self.handle, address, byref(buffer), btr, byref(bytesRead))

        return bytearray(buffer)
    
    def readInt(self, address):
        bs = self.read(address,4)
        return int.from_bytes(bs,byteorder='little')

    def __del__(self):
        windll.kernel32.CloseHandle(self.handle)
    
if __name__ == '__main__':
    mr = MemoryReader('Hearthstone')

    baseOffset = 0x00A1DD38
    offsets = [0x00A1DD38, 0x7F4, 0x408, 0x79C, 0x0, 0x78]

    while True:
        s = mr.baseAddress
        for offset in offsets:
            s = mr.readInt(s + offset)
        print(s)
        time.sleep(1)
