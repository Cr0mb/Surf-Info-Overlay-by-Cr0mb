import math
import time
import ctypes
import struct
import win32api, win32con, win32gui, win32ui
from ctypes import wintypes, windll, byref
from Process.offsets import Offsets

PROCESS_ALL_ACCESS = 0x1F0FFF

class Vec3(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float), ("z", ctypes.c_float)]

def read_bytes(handle, addr, size):
    buf = ctypes.create_string_buffer(size)
    windll.kernel32.ReadProcessMemory(handle, ctypes.c_void_p(addr), buf, size, None)
    return buf.raw

read_float       = lambda h, a: struct.unpack("f", read_bytes(h, a, 4))[0]
read_uint64      = lambda h, a: struct.unpack("Q", read_bytes(h, a, 8))[0]
safe_read_uint64 = lambda h, a: read_uint64(h, a) if a and a <= 0x7FFFFFFFFFFF else 0
read_vec3        = lambda h, a: Vec3.from_buffer_copy(read_bytes(h, a, 12))

class Overlay:
    def __init__(self, title="Surf Info", width=None, height=None):
        self.width, self.height = width or win32api.GetSystemMetrics(0), height or win32api.GetSystemMetrics(1)
        self.font_cache, self.pos, self.drag_offset, self.dragging = {}, [100, 400], [0, 0], False
        self.init_window(title)

    def init_window(self, title):
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc, wc.lpszClassName = self._wnd_proc, title
        wc.hInstance = win32api.GetModuleHandle(None)
        class_atom = win32gui.RegisterClass(wc)

        style = win32con.WS_POPUP
        ex_style = win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW
        self.hwnd = win32gui.CreateWindowEx(ex_style, class_atom, title, style, 0, 0, self.width, self.height, None, None, wc.hInstance, None)
        win32gui.SetLayeredWindowAttributes(self.hwnd, 0, 0, win32con.LWA_COLORKEY)
        win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)

        self.hdc = win32gui.GetDC(self.hwnd)
        self.hdc_obj = win32ui.CreateDCFromHandle(self.hdc)
        self.memdc = self.hdc_obj.CreateCompatibleDC()
        self.buffer = win32ui.CreateBitmap()
        self.buffer.CreateCompatibleBitmap(self.hdc_obj, self.width, self.height)
        self.memdc.SelectObject(self.buffer)

    def get_module_base(self, pid, module_name):
        class MODULEENTRY32(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD), ("th32ModuleID", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                ("GlblcntUsage", wintypes.DWORD), ("ProccntUsage", wintypes.DWORD), 
                ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)), ("modBaseSize", wintypes.DWORD),
                ("hModule", wintypes.HMODULE), ("szModule", ctypes.c_char * 256), ("szExePath", ctypes.c_char * 260),
            ]

        snapshot = windll.kernel32.CreateToolhelp32Snapshot(0x8, pid)
        me32 = MODULEENTRY32(); me32.dwSize = ctypes.sizeof(MODULEENTRY32)
        base = None

        if windll.kernel32.Module32First(snapshot, byref(me32)):
            while True:
                if me32.szModule.decode() == module_name:
                    base = ctypes.cast(me32.modBaseAddr, ctypes.c_void_p).value
                    break
                if not windll.kernel32.Module32Next(snapshot, byref(me32)):
                    break

        windll.kernel32.CloseHandle(snapshot)
        return base

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        x, y = lparam & 0xFFFF, (lparam >> 16) & 0xFFFF
        bx, by, bw, bh = *self.pos, 240, 72

        if msg == win32con.WM_LBUTTONDOWN and bx <= x <= bx + bw and by <= y <= by + bh:
            self.dragging = True
            self.drag_offset = [x - bx, y - by]
        elif msg == win32con.WM_MOUSEMOVE and self.dragging and (wparam & win32con.MK_LBUTTON):
            self.pos = [x - self.drag_offset[0], y - self.drag_offset[1]]
        elif msg == win32con.WM_LBUTTONUP:
            self.dragging = False
        elif msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
        else:
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
        return 0

    def get_font(self, size):
        if size not in self.font_cache:
            lf = win32gui.LOGFONT()
            lf.lfHeight, lf.lfWeight, lf.lfFaceName = size, 700, "Segoe UI"
            self.font_cache[size] = win32gui.CreateFontIndirect(lf)
        return self.font_cache[size]

    def draw_text(self, text, x, y, color=(255,255,255), size=14, centered=False):
        hdc = self.memdc.GetSafeHdc()
        font = self.get_font(size)
        win32gui.SelectObject(hdc, font)
        win32gui.SetTextColor(hdc, win32api.RGB(*color))
        win32gui.SetBkMode(hdc, win32con.TRANSPARENT)
        if centered:
            w, h = win32gui.GetTextExtentPoint32(hdc, text)
            x -= w // 2
            y -= h // 2
        self.memdc.TextOut(int(x), int(y), text)

    def draw_filled_rect(self, x, y, w, h, color):
        brush = win32gui.CreateSolidBrush(win32api.RGB(*color))
        win32gui.FillRect(self.memdc.GetSafeHdc(), (x, y, x + w, y + h), brush)
        win32gui.DeleteObject(brush)

    def draw_box(self, x, y, w, h, color):
        pen = win32gui.CreatePen(win32con.PS_SOLID, 1, win32api.RGB(*color))
        hdc = self.memdc.GetSafeHdc()
        old = win32gui.SelectObject(hdc, pen)
        win32gui.SelectObject(hdc, win32gui.GetStockObject(win32con.NULL_BRUSH))
        win32gui.Rectangle(hdc, x, y, x + w, y + h)
        win32gui.SelectObject(hdc, old)
        win32gui.DeleteObject(pen)

    def begin_scene(self):
        win32gui.FillRect(self.memdc.GetSafeHdc(), (0, 0, self.width, self.height), win32gui.GetStockObject(win32con.BLACK_BRUSH))

    def end_scene(self):
        self.hdc_obj.BitBlt((0, 0), (self.width, self.height), self.memdc, (0, 0), win32con.SRCCOPY)

    def draw_bhop_box(self, pos, velocity, speed):
        x, y = self.pos
        self.draw_filled_rect(x, y, 240, 72, (30, 30, 30))
        self.draw_box(x, y, 240, 72, (100, 100, 100))
        self.draw_filled_rect(x, y, 240, 24, (50, 50, 50))
        self.draw_text("Surf Info by Cr0mb", x + 120, y + 4, (200, 200, 255), 16, centered=True)

        self.draw_text(f"Coords: {pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f}", x + 6, y + 26, (200, 200, 255))
        self.draw_text(f"Velocity: {velocity.x:.1f}, {velocity.y:.1f}, {velocity.z:.1f}", x + 6, y + 42)
        self.draw_text(f"Speed: {speed:.1f} u/s", x + 6, y + 58, (180, 255, 180))

def main():
    hwnd = windll.user32.FindWindowW(None, "Counter-Strike 2")
    if not hwnd: return print("[!] CS2 not running.")

    pid = wintypes.DWORD()
    windll.user32.GetWindowThreadProcessId(hwnd, byref(pid))
    handle = windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid.value)
    overlay = Overlay("Surf Box")
    base = overlay.get_module_base(pid.value, "client.dll")

    def get_local_info():
        pawn = safe_read_uint64(handle, base + Offsets.dwLocalPlayerPawn)
        pos, vel = read_vec3(handle, pawn + Offsets.m_vOldOrigin), read_vec3(handle, pawn + Offsets.m_vecVelocity)
        speed = math.sqrt(vel.x**2 + vel.y**2 + vel.z**2)
        return pos, vel, speed

    while True:
        try:
            win32gui.PumpWaitingMessages()
            overlay.begin_scene()
            pos, vel, speed = get_local_info()
            overlay.draw_bhop_box(pos, vel, speed)
            overlay.end_scene()
            time.sleep(1 / 144)
        except Exception as e:
            print(f"[!] Error: {e}")
            break

if __name__ == "__main__":
    main()
