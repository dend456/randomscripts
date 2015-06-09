import ctypes as ct
from ctypes import wintypes as wt
import os,win32process,win32api,win32ui,time,struct,sys


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
        self.moduleName = moduleName if moduleName else windowName + '.exe'
        self.hwnd = win32ui.FindWindow(None,self.windowName).GetSafeHwnd()
        self.processId = win32process.GetWindowThreadProcessId(self.hwnd)[1]
        self.handle = self.__getHandle()
        self.baseAddress = self.__getBaseAddress()

    def __getHandle(self):
        handle = ct.windll.kernel32.OpenProcess(ct.c_uint(MemoryReader.PROCESS_QUERY_INFORMATION | MemoryReader.PROCESS_VM_READ | MemoryReader.PROCESS_VM_WRITE | MemoryReader.PROCESS_VM_OPERATION), ct.c_int(1), ct.c_uint(self.processId))
        if handle == ct.c_void_p(0):
            raise RuntimeError('Unable to get process handle.')
        return handle

    def __getBaseAddress(self):
        class ModuleInfo(ct.Structure):
            _fields_ = [('baseOfDll', wt.LPVOID),('sizeOfImage', wt.DWORD),('entryPoint', wt.LPVOID)]
        bufferSize = 256
        imageName = ct.create_string_buffer(bufferSize)
        length = ct.windll.psapi.GetProcessImageFileNameA(self.handle, imageName, wt.DWORD(bufferSize))
        if length <= 0:
            raise RuntimeError('Unable to get image file name.')
        modules = (ct.c_ulong * 1024)()
        count = ct.c_ulong()
        if ct.windll.psapi.EnumProcessModules(self.handle, modules, ct.sizeof(modules), ct.byref(count)) == 0:
            raise RuntimeError('Unable to enumerate modules.')

        moduleHandle = 0
        moduleNameInBytes = bytes(self.moduleName,'utf-8')
        for i in range(0,count.value // ct.sizeof(wt.HMODULE)):
            moduleName = ct.create_string_buffer(bufferSize)
            if ct.windll.psapi.GetModuleBaseNameA(self.handle, modules[0], moduleName, ct.sizeof(moduleName)) == 0:
                raise RuntimeError('Unable to get module name.')
            if moduleName.value == moduleNameInBytes:
                moduleHandle = modules[i]
                break

        if moduleHandle == 0:
            raise RuntimeError('Unable to get module handle.')

        info = ModuleInfo()
        if ct.windll.psapi.GetModuleInformation(self.handle, modules[0], ct.byref(info), ct.sizeof(info)) == 0:
            raise RuntimeError('Unable to get module info.')

        return info.baseOfDll

    def __del__(self):
        ct.windll.kernel32.CloseHandle(self.handle)

    def read(self, address, bytesToRead):
        bytesRead = ct.c_size_t(0)
        address = ct.c_void_p(address)
        btr = ct.c_size_t(bytesToRead)
        buffer = ct.create_string_buffer(bytesToRead)
        ct.windll.kernel32.ReadProcessMemory(self.handle, address, ct.byref(buffer), btr, ct.byref(bytesRead))
        return bytearray(buffer)

    def readInt(self, address):
        bs = self.read(address,4)
        return int.from_bytes(bs,signed=True,byteorder=sys.byteorder)

    def readUInt(self, address):
        bs = self.read(address,4)
        return int.from_bytes(bs,signed=False,byteorder=sys.byteorder)

    def readMultiLevelPointer(self, address, offsets):
        if address == 0:
            address = self.baseAddress
        val = address
        for offset in offsets:
            val = self.readInt(val + offset)
        return val

    def readByte(self, address):
        return self.read(address, 1)

    def readFloat(self, address):
        bs = self.read(address,4)
        return struct.unpack('f', bs)[0]

    def write(self, address, buffer):
        oldProtect = ct.c_uint()
        toWrite = ct.create_string_buffer(buffer)
        address = ct.c_void_p(address)
        bytesWritten = ct.c_int()
        ct.windll.kernel32.VirtualProtectEx(self.handle, address, ct.sizeof(toWrite), MemoryReader.PAGE_READWRITE, ct.byref(oldProtect))
        ct.windll.kernel32.WriteProcessMemory(self.handle, address, toWrite, ct.sizeof(toWrite), ct.byref(bytesWritten))
        return bytesWritten.value

    def writeByte(self, address, byte):
        return self.write(address, bytes([bytes]))

    def writeInt(self, address, i):
        return self.write(address, struct.pack('i',i))

    def writeUInt(self, address, i):
        return self.write(address, struct.pack('I',i))

    def writeFloat(self, address, f):
        return self.write(address, struct.pack('f',f))
    

if __name__ == '__main__':
    mr = MemoryReader('Hearthstone')

    offsets = [0x00A1E264, 0x310, 0x6D0, 0x568, 0x6E4, 0xC8]

    while True:
        screen = mr.readMultiLevelPointer(0, offsets)
        print(screen)
        time.sleep(1)