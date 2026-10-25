#!/usr/bin/env python3
# THE FORGE  |  Copyright (c) 2026 Yannie D. Forest. All rights reserved.
# NO LICENCE IS GRANTED. No copying, adaptation, redistribution, reverse
# engineering or commercial use without the author's written permission.
# See LICENCE.txt. Every distributed copy carries a build marker.
"""
The Forge — desktop launcher.

This is a thin native-window shell around the app. All of the
app's behaviour lives in the bundled HTML/JavaScript file (the_forge.html);
this script only opens it in a proper desktop window using the system's native
web view. The app still runs entirely offline: nothing is sent anywhere.

Run it with:   python the_forge_app.py
"""

import os
import re
import sys
import threading
import time

# 9s57: the moment this program started. The log says how long the window and
# the page took from here (see _watch_start). perf_counter measures durations;
# the wall clock taken beside it places the page's own timings on the same line.
_START = time.perf_counter()
_START_WALL = time.time()

# The window title and starting size. The app itself is responsive, so these are
# just sensible defaults; the window can be resized and maximised freely.
WINDOW_TITLE = "The Forge"
DEFAULT_WIDTH = 1180
DEFAULT_HEIGHT = 820
MIN_WIDTH = 380      # the app works down to a narrow width
MIN_HEIGHT = 560

# 9s57: the window opens in the colour the page paints first, so nothing
# flashes while it loads. That colour is learned from the page itself: its
# splash script (cd-splash-theme) leaves it on <html> as --cd-splash-bg, and
# the ready watch reads it there and keeps it, with the look, in a small file
# beside the work (_remember_theme). So a page whose colours change, or
# another app made with this template, still opens in its own colour from the
# second start on. The map below is only for a first start, before anything
# has been learned: the colours the splash script painted when this was
# written (#f5f5f7 by day, #121013 at night, #f1ebe1 and #141210 in the Folio
# look; the body's --bg is #F5F5F7 by day and #121013 at night). Check it
# against the page's cd-splash-theme script whenever the palette changes.
WINDOW_COLORS = {
    "day": "#F5F5F7",
    "night": "#121013",
    "day folio": "#F1EBE1",
    "night folio": "#141210",
}

# 9s57: one copy at a time (see _another_copy_is_open). "Local\" keeps the
# name inside this person's sign-in session (Microsoft, CreateMutexW).
SINGLE_INSTANCE_NAME = "Local\\TheForge.windows.single"

# 9s57: how long the page has to say it is ready, and how often it is asked.
READY_LIMIT_S = 120
READY_POLL_S = 0.25


def tell_user(text, title="The Forge"):
    """Say something the person will actually see.

    The packaged exe is built windowed, with no console attached, so anything
    written to stderr disappears. Every message below therefore goes to a native
    dialog on Windows, and to the terminal when one exists (running the script
    directly, or on macOS and Linux).
    """
    try:
        sys.stderr.write(text if text.endswith("\n") else text + "\n")
    except Exception:
        pass
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, str(text), str(title), 0x40)
            return
        except Exception:
            pass


def open_in_browser(app_html):
    """Last resort: the page itself is the whole application.

    If a native window cannot be created, opening the same file in the default
    browser still gives the entire app, offline. It is better than an exe that
    appears to do nothing.
    """
    try:
        import webbrowser
        from pathlib import Path
        webbrowser.open(Path(app_html).as_uri())
        return True
    except Exception:
        return False


def resource_path(filename):
    """Return an absolute path to a file that sits next to this script.

    This also works when the app has been frozen by PyInstaller, where bundled
    files are found through sys._MEIPASS: the program's own _internal folder
    in the program-folder build that the installer puts in place (or, in an
    older single-file build, a temporary folder).
    """
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, filename)


def find_app_html():
    """Locate the bundled app HTML, with several sensible fallbacks.

    A frozen build finds the page through resource_path first (in the
    program-folder build it sits in _internal, beside the program's
    libraries). The extra candidates cover running from source, and a build
    started from a different working folder.
    """
    here_script = os.path.dirname(os.path.abspath(__file__))
    try:
        here_exe = os.path.dirname(os.path.abspath(sys.executable))
    except Exception:
        here_exe = here_script
    candidates = [
        resource_path("the_forge.html"),
        resource_path("the_forge.html"),
        os.path.join(here_script, "the_forge.html"),
        os.path.join(here_exe, "the_forge.html"),
        os.path.join(os.getcwd(), "the_forge.html"),
    ]
    seen = set()
    for path in candidates:
        if path and path not in seen:
            seen.add(path)
            if os.path.isfile(path):
                return path
    return None


def friendly_missing_dependency_message():
    """A clear, non-technical message shown if pywebview is not installed."""
    return (
        "\n"
        "The Forge needs one small free component to open its window.\n"
        "\n"
        "Please install it once by running this in a terminal or command prompt:\n"
        "\n"
        "    pip install pywebview\n"
        "\n"
        "On Windows you may instead need:   py -m pip install pywebview\n"
        "On some Linux systems you may also need a web view backend, e.g.:\n"
        "    sudo apt install python3-webview   (or)   pip install pywebview[qt]\n"
        "\n"
        "Then run this program again.\n"
    )


def storage_dir():
    """A persistent place for the web view's own storage.

    pywebview runs in PRIVATE MODE by default, which discards localStorage when
    the window closes. Everything written in the desktop app was therefore lost
    on exit, not only a sticky note: curriculum progress, documents, reminders,
    all of it. A onefile build also unpacks into a temporary directory that is
    deleted afterwards, so the storage must live in the user's own profile and
    not beside the executable.
    """
    import os
    home = os.path.expanduser("~")
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or os.path.join(home, "AppData", "Local")
    elif sys.platform == "darwin":
        base = os.path.join(home, "Library", "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(home, ".local", "share")
    path = os.path.join(base, "TheForge", "storage")
    try:
        os.makedirs(path, exist_ok=True)
        return path
    except Exception:
        log_problem("storage_dir: could not create %r" % path)
        return None


def crash_log_path():
    """Beside the work, as Inkwell keeps its log: %LOCALAPPDATA%\\TheForge.

    9s58 win_like_ink: earlier builds wrote it beside the program, and before
    every line created and deleted a small test file in the program's folder
    to see whether that folder could be written to. An installed program
    keeps its record with the person's own data instead, so that test is gone.
    The home folder is the fallback.
    """
    import os
    home = os.path.expanduser("~")
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or os.path.join(home, "AppData", "Local")
    elif sys.platform == "darwin":
        base = os.path.join(home, "Library", "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(home, ".local", "share")
    d = os.path.join(base, "TheForge")
    try:
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, "the_forge_crash.log")
    except Exception:
        return os.path.join(home, "the_forge_crash.log")


def log_problem(tag, exc_info=None):
    """Record a fault so a crash leaves evidence instead of vanishing."""
    import datetime, traceback
    try:
        with open(crash_log_path(), "a", encoding="utf-8") as fh:
            fh.write("\n=== %s  %s ===\n" % (datetime.datetime.now().isoformat(timespec="seconds"), tag))
            if exc_info:
                traceback.print_exception(exc_info[0], exc_info[1], exc_info[2], file=fh)
            else:
                traceback.print_exc(file=fh)
    except Exception:
        pass


def log_note(tag):
    """One line in the same record, with nothing under it.

    log_problem() writes the exception being handled beneath its line (or
    "NoneType: None" when there is none). A note on how the start went needs
    neither, and a traceback in the record stops the GitHub build's open test.
    """
    import datetime
    try:
        with open(crash_log_path(), "a", encoding="utf-8") as fh:
            fh.write("\n=== %s  %s ===\n" % (datetime.datetime.now().isoformat(timespec="seconds"), tag))
    except Exception:
        pass


def _seconds():
    """Seconds since this program started, for the start lines in the log."""
    return time.perf_counter() - _START


def save_bytes(win, name, mime, data_b64):
    """Write an exported file from Python.

    A synthetic <a download> click inside a native web view is handed to the
    platform's download machinery. That is the path the Windows crash was
    reported on, and writing the bytes here avoids it entirely. Returns the path
    written, or False so the page can fall back to the anchor.
    """
    import base64, os
    try:
        raw = base64.b64decode(data_b64 or "")
    except Exception:
        log_problem("save_bytes: undecodable payload")
        return False
    keep = " ._-()[]"
    safe = "".join(c for c in str(name or "download") if c.isalnum() or c in keep).strip() or "download"
    target = None
    shown = False
    try:
        import webview
        # THE EXPORT CRASH (mac/windows): "Export to file" hands the webview a blob
        # download; without download support pywebview can bring the window down.
        # Recent pywebview honours this switch; older ones ignore the unknown key.
        try:
            webview.settings['ALLOW_DOWNLOADS'] = True
        except Exception:
            pass
        w = win
        if w is None:
            ws = [x for x in (getattr(webview, "windows", None) or []) if x is not None]
            w = ws[0] if ws else None
        if w is not None:
            shown = True
            res = w.create_file_dialog(webview.SAVE_DIALOG, save_filename=safe)
            if res:
                target = res if isinstance(res, str) else res[0]
    except Exception:
        # a missing dialog is not a cancellation: fall through to the folder
        log_problem("save_bytes: file dialog unavailable")
        shown = False
        target = None
    if shown and not target:
        # the person chose Cancel, so nothing is written and nothing falls back
        return "cancelled"
    if not target:
        try:
            d = os.path.join(os.path.expanduser("~"), "Downloads")
            if not os.path.isdir(d):
                d = os.path.expanduser("~")
            target = os.path.join(d, safe.lstrip(".") or "download")
            # 647 (forge_shell_647.py): never over a file already there
            stem, ext = os.path.splitext(target)
            n = 2
            while os.path.exists(target) and n < 1000:
                target = "%s (%d)%s" % (stem, n, ext)
                n += 1
        except Exception:
            log_problem("save_bytes: no writable folder")
            return False
    try:
        with open(target, "wb") as fh:
            fh.write(raw)
        return target
    except Exception:
        log_problem("save_bytes: write failed")
        return False


# ---------------------------------------------------------------- clipboard
# 9s58: THE CLIPBOARD, for the page's own right-click menu. Its Paste, Paste
# as plain text, Copy and Cut reach the Windows clipboard through
#   window.pywebview.api.read_clipboard()        -> {"text": ..., "html": ...}
#   window.pywebview.api.write_clipboard(text, html)  -> true or false
# so a link copied in any other program pastes from the menu, and nothing
# asks for keys to be pressed. (A page inside a web view may read the
# clipboard by itself only while a person presses the keys; a Windows
# program may read it at any time, so the page asks this one.)
#
# Only the clipboard functions every Windows program has (user32 and
# kernel32, through ctypes): nothing new is installed. Two kinds travel:
#   CF_UNICODETEXT  the text, in UTF-16 (a standard format, number 13);
#   "HTML Format"   the formatted copy, a registered format (cf_html_build).
#
# WHY A WORKER THREAD IS SAFE HERE. pywebview runs every js_api call on a
# new thread of its own (webview.util.js_bridge_call: "The function is
# executed in a separate thread to prevent blocking the UI thread"). These
# are the plain Win32 clipboard functions: they belong to no window's thread
# and need no COM apartment. (That need is the OLE clipboard's,
# OleGetClipboard and OleSetClipboard, and of .NET's Clipboard class built
# on it; none of them is used.) OpenClipboard gives the clipboard to ONE
# thread until CloseClipboard; meanwhile any other thread or program is
# refused, so this asks again for half a second, and _CLIPBOARD_LOCK keeps
# two of this program's own calls from queueing at that door. All that a
# call does (open, copy the bytes out or in, close) happens inside that one
# call on that one thread, with CloseClipboard in a finally, so the
# clipboard is never left locked. The window's own thread never waits for
# these calls, so a program that hands over its copy only when asked
# (WM_RENDERFORMAT) is answered by its own thread, never blocked by ours.

CF_UNICODETEXT = 13
CF_HTML_NAME = "HTML Format"
GMEM_MOVEABLE = 0x0002
HWND_MESSAGE = -3                 # the parent of a message-only window
CLIPBOARD_TRIES = 20              # OpenClipboard, up to 20 times,
CLIPBOARD_PAUSE_S = 0.025         # 25 ms apart: half a second in all
_CLIPBOARD_LOCK = threading.Lock()
_WIN32 = None


class ClipboardUnavailable(Exception):
    """The clipboard could not be read just now; the page tries its next way."""


_CF_HTML_HEADER = ("Version:0.9\r\nStartHTML:%010d\r\nEndHTML:%010d\r\n"
                   "StartFragment:%010d\r\nEndFragment:%010d\r\n")
_CF_HTML_BEFORE = "<html>\r\n<body>\r\n<!--StartFragment-->"
_CF_HTML_AFTER = "<!--EndFragment-->\r\n</body>\r\n</html>"
_CF_HTML_MARKS = re.compile(rb"<!--\s*StartFragment\s*-->(.*?)<!--\s*EndFragment\s*-->", re.S | re.I)


def cf_html_build(fragment):
    """The clipboard's "HTML Format" block for a piece of HTML, as UTF-8 bytes.

    Microsoft's layout ("HTML Clipboard Format"): a header of Key:value
    lines, then the HTML, with the copied part between <!--StartFragment-->
    and <!--EndFragment-->. Every number in the header is a BYTE offset from
    the block's first byte, counted in UTF-8 (so "é" counts two). Each is
    written with ten digits, so the header always has the same length and
    the offsets are known before it is written. No NUL at the end: the
    caller adds the one the clipboard wants.
    """
    frag = str(fragment or "").encode("utf-8", "replace")   # a lone surrogate becomes "?"
    before = _CF_HTML_BEFORE.encode("ascii")
    after = _CF_HTML_AFTER.encode("ascii")
    start_html = len(_CF_HTML_HEADER % (0, 0, 0, 0))
    start_frag = start_html + len(before)
    end_frag = start_frag + len(frag)
    end_html = end_frag + len(after)
    head = (_CF_HTML_HEADER % (start_html, end_html, start_frag, end_frag)).encode("ascii")
    return head + before + frag + after


def cf_html_fragment(block):
    """The copied part of an "HTML Format" block (bytes), as text; "" if none.

    StartFragment and EndFragment are byte offsets into the UTF-8 block, so
    the bytes are cut first and decoded after. When they are missing or
    impossible (pointing into the header, past the end, or backwards), the
    <!--StartFragment--> and <!--EndFragment--> marks are used instead; and
    failing those, StartHTML and EndHTML; and failing those, everything
    after the header. Anything from the first NUL on is not part of it.
    """
    if not block:
        return ""
    data = bytes(block)
    nul = data.find(b"\0")
    if nul >= 0:
        data = data[:nul]
    first_tag = data.find(b"<")
    head = data if first_tag < 0 else data[:first_tag]
    fields = {}
    for line in head.splitlines():
        key, sep, value = line.partition(b":")
        if sep:
            fields[key.strip().lower()] = value.strip()

    def offset(name):
        try:
            n = int(fields.get(name, b""))
        except ValueError:
            return None
        return n if 0 <= n <= len(data) else None

    body = len(head)
    start, end = offset(b"startfragment"), offset(b"endfragment")
    if start is not None and end is not None and body <= start <= end:
        piece = data[start:end]
    else:
        marks = _CF_HTML_MARKS.search(data, body)
        if marks:
            piece = marks.group(1)
        else:
            start, end = offset(b"starthtml"), offset(b"endhtml")
            if start is not None and end is not None and body <= start <= end:
                piece = data[start:end]
            else:
                piece = data[body:]
    return piece.decode("utf-8", "replace")


def _plain_newlines(text):
    """Windows writes a new line as CR LF; the page wants LF alone."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _windows_newlines(text):
    """Every new line as CR LF, which every Windows program reads."""
    return _plain_newlines(text).replace("\n", "\r\n")


def _win32():
    """user32 and kernel32 with every argument and result type stated.

    Without argtypes and restype, ctypes passes and returns plain C ints, 32
    bits wide: on 64-bit Windows a handle or an address above 4 GB would be
    cut in half. These are this program's own copies of the two libraries
    (WinDLL), so the types set here change nothing for pywebview or .NET,
    which call through ctypes.windll.
    """
    global _WIN32
    if _WIN32 is None:
        import ctypes
        import types
        from ctypes import wintypes
        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        table = (
            (user32, "OpenClipboard", (wintypes.HWND,), wintypes.BOOL),
            (user32, "CloseClipboard", (), wintypes.BOOL),
            (user32, "EmptyClipboard", (), wintypes.BOOL),
            (user32, "GetClipboardData", (wintypes.UINT,), wintypes.HANDLE),
            (user32, "SetClipboardData", (wintypes.UINT, wintypes.HANDLE), wintypes.HANDLE),
            (user32, "RegisterClipboardFormatW", (wintypes.LPCWSTR,), wintypes.UINT),
            (user32, "CreateWindowExW", (wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                         wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                         ctypes.c_int, wintypes.HWND, wintypes.HMENU,
                                         wintypes.HINSTANCE, wintypes.LPVOID), wintypes.HWND),
            (user32, "DestroyWindow", (wintypes.HWND,), wintypes.BOOL),
            (kernel32, "GlobalAlloc", (wintypes.UINT, ctypes.c_size_t), wintypes.HGLOBAL),
            (kernel32, "GlobalLock", (wintypes.HGLOBAL,), wintypes.LPVOID),
            (kernel32, "GlobalUnlock", (wintypes.HGLOBAL,), wintypes.BOOL),
            (kernel32, "GlobalSize", (wintypes.HGLOBAL,), ctypes.c_size_t),
            (kernel32, "GlobalFree", (wintypes.HGLOBAL,), wintypes.HGLOBAL),
        )
        calls = {}
        for lib, name, args, result in table:
            fn = getattr(lib, name)
            fn.argtypes = args
            fn.restype = result
            calls[name] = fn
        _WIN32 = types.SimpleNamespace(**calls)
    return _WIN32


def _open_clipboard(w, owner):
    """OpenClipboard, asked again while another program holds it."""
    for attempt in range(CLIPBOARD_TRIES):
        if w.OpenClipboard(owner):
            return True
        if attempt + 1 < CLIPBOARD_TRIES:
            time.sleep(CLIPBOARD_PAUSE_S)
    return False


def _clipboard_bytes(w, handle):
    """A copy of the bytes behind a clipboard handle, b"" if none.

    The handle stays the clipboard's: it is locked only while its bytes are
    copied out, and never freed here. GlobalSize bounds the copy, so a block
    that lacks its closing NUL is still read safely.
    """
    import ctypes
    size = w.GlobalSize(handle)
    if not size:
        return b""
    address = w.GlobalLock(handle)
    if not address:
        return b""
    try:
        return ctypes.string_at(address, size)
    finally:
        w.GlobalUnlock(handle)


def _clipboard_put(w, fmt, data):
    """Hand one format's bytes to the open clipboard. True when it took them.

    SetClipboardData wants movable global memory (GMEM_MOVEABLE). Once it
    accepts, the memory is the clipboard's; if it refuses, it is still ours
    to free.
    """
    import ctypes
    handle = w.GlobalAlloc(GMEM_MOVEABLE, len(data))
    if not handle:
        return False
    address = w.GlobalLock(handle)
    if not address:
        w.GlobalFree(handle)
        return False
    try:
        ctypes.memmove(address, data, len(data))
    finally:
        w.GlobalUnlock(handle)
    if w.SetClipboardData(fmt, handle):
        return True
    w.GlobalFree(handle)
    return False


def clipboard_read():
    """What the clipboard holds: {"text": ..., "html": ...}.

    Each is "" when the clipboard holds none; an empty clipboard is not a
    failure. When the clipboard cannot be opened (another program held it
    for the whole half second), or this is not Windows, this raises
    ClipboardUnavailable: pywebview then rejects the page's Promise, and the
    page tries its next way.
    """
    if not sys.platform.startswith("win"):
        raise ClipboardUnavailable("this clipboard bridge is for Windows")
    w = _win32()
    with _CLIPBOARD_LOCK:
        if not _open_clipboard(w, None):
            log_note("clipboard: another program kept the clipboard; the page tries its next way")
            raise ClipboardUnavailable("the clipboard is busy in another program")
        try:
            text = ""
            handle = w.GetClipboardData(CF_UNICODETEXT)
            if handle:
                raw = _clipboard_bytes(w, handle)
                text = raw[:len(raw) - len(raw) % 2].decode("utf-16-le", "replace").split("\0", 1)[0]
            html = ""
            fmt = w.RegisterClipboardFormatW(CF_HTML_NAME)
            if fmt:
                handle = w.GetClipboardData(fmt)
                if handle:
                    html = cf_html_fragment(_clipboard_bytes(w, handle))
        finally:
            w.CloseClipboard()
    return {"text": _plain_newlines(text), "html": html}


def clipboard_write(text, html=""):
    """Put text on the clipboard, with its formatted copy when html is given.

    True when the text is on the clipboard. If only the formatted copy was
    refused, the text still went, so that is True too, and the log says so.
    (9s58 run 2: never raises.) Anything unexpected is one plain line in the
    log and False, so the page's Promise is always true or false.
    """
    if not sys.platform.startswith("win"):
        return False
    try:
        text = "" if text is None else str(text)
        html = "" if html is None else str(html)
        # Made ready before the clipboard is opened, so it is held only
        # briefly. A JavaScript string may hold half of an emoji's pair on
        # its own; "surrogatepass" keeps it as the UTF-16 unit it was (as
        # Windows text may), instead of stopping the copy.
        data = (_windows_newlines(text) + "\0").encode("utf-16-le", "surrogatepass")
        block = (cf_html_build(html) + b"\0") if html else b""
        return _clipboard_write_bytes(_win32(), data, block)
    except Exception as exc:
        log_note("clipboard: nothing was copied (%s)" % (exc.__class__.__name__,))
        return False


def _clipboard_write_bytes(w, data, block):
    """clipboard_write's part with the clipboard open: the text, then the HTML Format block."""
    with _CLIPBOARD_LOCK:
        # The clipboard's new owner must be a window. Microsoft, on
        # OpenClipboard: "If an application calls OpenClipboard with hwnd set
        # to NULL, EmptyClipboard sets the clipboard owner to NULL; this
        # causes SetClipboardData to fail." A message-only window of the plain
        # STATIC class serves: made on this thread, never shown, and destroyed
        # on this thread straight after. What it put there stays for every
        # program, because the content is handed over in full, not on demand.
        owner = w.CreateWindowExW(0, "STATIC", None, 0, 0, 0, 0, 0,
                                  HWND_MESSAGE, None, None, None)
        try:
            if not _open_clipboard(w, owner):
                log_note("clipboard: another program kept the clipboard; nothing was copied")
                return False
            try:
                if not w.EmptyClipboard():
                    return False
                done = _clipboard_put(w, CF_UNICODETEXT, data)
                if done and block:
                    fmt = w.RegisterClipboardFormatW(CF_HTML_NAME)
                    if not (fmt and _clipboard_put(w, fmt, block)):
                        log_note("clipboard: the text was copied, its formatting was not")
                return done
            finally:
                w.CloseClipboard()
        finally:
            if owner:
                w.DestroyWindow(owner)


CLIPBOARD_CHECK_WRITTEN = "clip written 9s58"


def _clipboard_check(window):
    """9s58: for the GitHub build's open test only (CD_CLIPBOARD_CHECK).

    The test puts a line of text on the clipboard and starts this program
    with CD_CLIPBOARD_CHECK set to that same line. Once the page is ready,
    the page reads the clipboard through its bridge, as its Paste does
    (window.pywebview.api.read_clipboard), then writes
    CLIPBOARD_CHECK_WRITTEN through write_clipboard, as its Copy does, and
    the test reads that back. One line in the log says how both went. What
    was on the clipboard is never written down, only whether it matched.
    Without CD_CLIPBOARD_CHECK this does nothing at all.
    """
    expected = os.environ.get("CD_CLIPBOARD_CHECK")
    if not expected:
        return
    import json

    def ask(call):
        got, done = [], threading.Event()

        def answer(value):   # on pywebview's thread: only keep the answer
            got.append(value)
            done.set()

        js = ("(window.pywebview&&window.pywebview.api&&window.pywebview.api.%s"
              "?window.pywebview.api.%s:Promise.reject(new Error('the page has no %s')))"
              ".then(function(v){return {ok:true,v:v};},"
              "function(e){return {ok:false,v:String(e&&e.message||e)};})"
              % (call.split("(")[0], call, call.split("(")[0]))
        try:
            window.evaluate_js(js, callback=answer)
        except Exception as exc:
            return {"ok": False, "v": exc.__class__.__name__}
        if not done.wait(10):
            return {"ok": False, "v": "no answer within 10 s"}
        return got[0] if isinstance(got[0], dict) else {"ok": False, "v": "an answer of the wrong kind"}

    try:
        r = ask("read_clipboard()")
        if r.get("ok") and isinstance(r.get("v"), dict):
            text = str(r["v"].get("text", ""))
            read = "matched" if text.strip() == expected.strip() else "did NOT match (%d characters)" % len(text)
        else:
            read = "failed (%s)" % (r.get("v"),)
        w = ask("write_clipboard(%s, %s)" % (json.dumps(CLIPBOARD_CHECK_WRITTEN),
                                             json.dumps("<b>%s</b>" % CLIPBOARD_CHECK_WRITTEN)))
        if w.get("ok"):
            wrote = "answered %s" % ("true" if w.get("v") is True else repr(w.get("v")))
        else:
            wrote = "failed (%s)" % (w.get("v"),)
        log_note("clipboard check: read through the page %s; write through the page %s" % (read, wrote))
    except Exception as exc:
        log_note("clipboard check: could not run (%s)" % (exc,))


class TabulaWindowApi:
    """JS API for a floating app window: close, save, and open a sibling window.

    open_app delegates to the main window's API. Without it, pressing Imago
    inside the Tabula window had no way to ask for a window of its own, so the
    page fell back to tearing Tabula down and building Imago in its place, which
    is the heaviest thing a secondary web view can be asked to do.
    """

    def __init__(self, host=None):
        self._win = None
        self._host = host

    def open_app(self, which):
        try:
            if self._host is not None:
                return self._host.open_app(which)
        except Exception:
            log_problem("TabulaWindowApi.open_app(%r)" % (which,))
        return False

    def save_file(self, name, mime, data_b64):
        """The floating window previously had no way to write a file at all."""
        return save_bytes(self._win, name, mime, data_b64)

    def read_clipboard(self):
        """9s58: the clipboard, for the page's own Paste (see clipboard_read)."""
        return clipboard_read()

    def write_clipboard(self, text, html=""):
        """9s58: the page's own Copy and Cut (see clipboard_write)."""
        return clipboard_write(text, html)

    def close_self(self):
        try:
            if self._win is not None:
                self._win.destroy()
                return True
        except Exception:
            pass
        return False


def _session_flag():
    """Where the breadcrumb for 'a run started and has not finished' lives."""
    import os
    d = storage_dir() or os.path.expanduser("~")
    return os.path.join(d, "the_forge_session.flag")


def _begin_session():
    """Record that a run has started, and report how many ended badly before.

    A crash inside the graphics layer of a web view takes the whole process with
    it: no exception, no traceback, nothing for Python to catch. The only way to
    know it happened is to notice, next time, that the previous run never wrote
    its own ending. That count is what lets the app protect itself on hardware
    where the graphics path is unsound, instead of failing the same way forever.
    """
    import os
    prior = 0
    path = _session_flag()
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as fh:
                prior = int((fh.read() or "0").strip() or "0") or 1
    except Exception:
        prior = 1
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(str(prior + 1))
    except Exception:
        log_problem("could not write the session breadcrumb")
    return prior


def _end_session():
    """A clean ending, so the next run knows the last one was well."""
    import os
    try:
        os.remove(_session_flag())
    except Exception:
        pass


def _closing_is_clean():
    """The window is closing on purpose: its close button, Alt+F4, the taskbar,
    or Windows itself shutting down, restarting or signing out.

    A shutdown can end the process before webview.start() returns, so the clean
    exit in main() never runs, and two shutdowns with the app open were counted
    as two bad endings: the next start then opened the browser instead of the
    app's own window. The window's closing event runs for every one of these
    before the app goes, so the mark is cleared here. A crash still leaves it,
    which is what the safeguard is for. Returns nothing, so the closing goes
    ahead.
    """
    _end_session()


_loaded_once = []
_shown_once = []


def _page_loaded():
    """Recorded once, so a slow first start can be measured from the log."""
    if not _loaded_once:
        _loaded_once.append(1)
        log_note("start: the page has loaded after %.1f s" % _seconds())


def _window_shown():
    """9s57: the moment the window appears (pywebview's shown event), once."""
    if not _shown_once:
        _shown_once.append(1)
        log_note("start: window shown after %.1f s" % _seconds())


# 9s57: asked of the page every READY_POLL_S until it is ready. One call
# returns, in order: the page's own ready mark (the_forge.html sets
# data-forge-ready="1" on <body> once its whole engine has run: "the boot
# guard's sentinel, reached only when the whole engine has run"); how far the
# document has loaded; its first paint and the end of its parsing, as clock
# times in milliseconds so they can be set against this program's start; and
# the look it shows (data-theme on <body>, set by applyTheme to "light" or
# "night"; the class mode-folio, set by applyMode); and the colour its splash
# script painted first (--cd-splash-bg on <html>), for the window colour of
# the next start.
_READY_JS = (
    "(function(){var b=document.body,p=window.performance,o=0,f=null,c=null;"
    "try{o=p.timeOrigin||(p.timing&&p.timing.navigationStart)||0;}catch(e){}"
    "try{var a=p.getEntriesByName('first-contentful-paint');if(a&&a.length&&o)f=o+a[0].startTime;}catch(e){}"
    "try{var n=p.getEntriesByType('navigation');if(n&&n.length&&n[0].domContentLoadedEventEnd&&o)c=o+n[0].domContentLoadedEventEnd;}catch(e){}"
    "return [b?b.getAttribute('data-forge-ready'):null,document.readyState,f,c,"
    "b?b.getAttribute('data-theme'):null,!!(b&&b.classList&&b.classList.contains('mode-folio'))"
    ",(document.documentElement&&document.documentElement.style.getPropertyValue(\"--cd-splash-bg\")||\"\").trim()];})()"
)

# 9s57: the line that SETS the ready mark, in either kind of quotes. The page
# also reads the mark in its boot guard; a page that kept the guard but lost
# the line that sets it would otherwise wait for a mark that never comes.
_READY_MARK_SETTERS = (b'setAttribute("data-forge-ready"', b"setAttribute('data-forge-ready'")


def _page_has_ready_mark(app_html):
    """True when the page file sets the ready mark (see _READY_MARK_SETTERS).

    This launcher serves every app The Forge packages. A page that does not
    set the mark (Carpe Diem's own, for one) counts as ready when its
    document has finished loading. Read in pieces, on the watching thread, so
    a large page costs the start nothing.
    """
    keep = max(len(n) for n in _READY_MARK_SETTERS) - 1
    try:
        tail = b""
        with open(app_html, "rb") as fh:
            while True:
                block = fh.read(1 << 20)
                if not block:
                    return False
                look = tail + block
                for needle in _READY_MARK_SETTERS:
                    if needle in look:
                        return True
                tail = look[-keep:]
    except Exception:
        return False


def _watch_start(window, app_html):
    """9s57: write down how long the page took to be ready, then remember its
    look and the colour it painted first.

    Runs on its own background thread and never touches the window except to
    ask the page the question above. pywebview's evaluate_js waits for the
    page's bridge, which comes with the loaded event, so the question is only
    asked once the page has loaded; until then, and if it fails while the page
    reloads, it simply waits for the next turn. It gives up after
    READY_LIMIT_S, and stops at once if the window is closing.
    """
    try:
        has_mark = _page_has_ready_mark(app_html)
        limit = time.perf_counter() + READY_LIMIT_S
        last = None
        while time.perf_counter() < limit:
            try:
                if window.events.closing.is_set():
                    log_note("start: the window was closed before the page was ready (%.1f s)" % _seconds())
                    return
            except Exception:
                pass
            state = None
            try:
                if window.events.loaded.is_set():
                    state = window.evaluate_js(_READY_JS)
            except Exception:
                state = None
            if isinstance(state, (list, tuple)) and len(state) >= 6:
                last = state
                ready = (str(state[0]) == "1") if has_mark else (state[1] == "complete")
                if ready:
                    took = _seconds()
                    how = ["its ready mark"] if has_mark else ["the document has loaded; this page sets no ready mark"]
                    for label, when in (("first paint", state[2]), ("page read", state[3])):
                        try:
                            if when:
                                how.append("%s at %.1f s" % (label, float(when) / 1000.0 - _START_WALL))
                        except Exception:
                            pass
                    log_note("start: page ready in %.1f s (%s)" % (took, "; ".join(how)))
                    # The look, and the colour the page painted first, for
                    # the window colour of the next start.
                    colour = state[6] if len(state) > 6 else None
                    if state[4] in ("light", "night"):
                        _remember_theme(dark=(state[4] == "night"), folio=bool(state[5]), colour=colour)
                    else:
                        _remember_theme(colour=colour)
                    _clipboard_check(window)   # 9s58: only when the open test asks
                    return
            time.sleep(READY_POLL_S)
        log_note("start: page NOT ready after %d s (last answer: %r)" % (READY_LIMIT_S, last))
    except Exception as exc:
        log_note("start: the ready watch stopped (%s)" % (exc,))


def _theme_file():
    d = storage_dir()
    return os.path.join(d, "the_forge_window_theme.txt") if d else None


_COLOUR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _remembered_theme():
    """The look the page last showed, and the colour it painted first.

    Returns (look, colour): look is a key of WINDOW_COLORS ("day" if the
    file is missing or holds anything unknown); colour is the "#RRGGBB" the
    page's splash script painted, learned at ready, or None when none has
    been learned for this look. The file holds the look on its first line
    and, when known, the colour on its second.
    """
    try:
        path = _theme_file()
        if path and os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as fh:
                lines = fh.read().splitlines()
            look = " ".join((lines[0] if lines else "").split()).lower()
            if look in WINDOW_COLORS:
                colour = lines[1].strip() if len(lines) > 1 else ""
                return look, (colour.upper() if _COLOUR_RE.match(colour) else None)
    except Exception:
        pass
    return "day", None


def _remember_theme(dark=None, folio=None, colour=None):
    """9s57: keep the page's look, and its first colour, for the next start.

    Called when the page reports a theme change (broadcast_theme, which says
    day or night only, so the Folio part is kept as it was, and gives no
    colour) and when the page is ready (which says both, and gives the
    colour its splash script painted, --cd-splash-bg). A "#RRGGBB" colour is
    kept beside the look. With no colour (broadcast_theme), a colour already
    learned stays only while the look is the same: after a change of look it
    belonged to the other look, so it is dropped and WINDOW_COLORS serves
    until the next ready. A page that reports no usable colour at ready
    drops it too. Writes only when something changed.
    """
    try:
        old, old_colour = _remembered_theme()
        if dark is None:
            dark = old.startswith("night")
        if folio is None:
            folio = old.endswith("folio")
        look = ("night" if dark else "day") + (" folio" if folio else "")
        if colour is None:
            keep = old_colour if look == old else None
        else:
            c = str(colour).strip()
            keep = c.upper() if _COLOUR_RE.match(c) else None
        path = _theme_file()
        if path and (look != old or keep != old_colour or not os.path.isfile(path)):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(look + "\n" + (keep + "\n" if keep else ""))
        return look
    except Exception:
        return None


def _another_copy_is_open():
    """9s57: True when this app is already open in this sign-in.

    Its window is then restored and brought forward, and this copy ends at
    once, without touching the session mark. Before this, a second click while
    the window was still coming up started a second copy: the mark counted it
    as a run that never finished, so the next start was softened, and the one
    after opened the browser.

    How: a named mutex (Microsoft, CreateMutexW: "If the mutex is a named mutex
    and the object existed before this function call, the return value is a
    handle to the existing object, and the GetLastError function returns
    ERROR_ALREADY_EXISTS"). The first copy keeps its handle for its whole life
    (in _single_instance); "the system closes the handle automatically when
    the process terminates", so a crash never leaves the name behind. A
    second copy closes its own handle at once (CloseHandle), so its search
    for the window, or a message it leaves open, never keeps the name alive
    after the first copy has gone.

    Windows only. Anything that goes wrong here starts the app as usual: this
    must never be the reason it does not open.
    """
    if not sys.platform.startswith("win"):
        return False
    try:
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
        kernel32.CreateMutexW.restype = wintypes.HANDLE
        handle = kernel32.CreateMutexW(None, False, SINGLE_INSTANCE_NAME)
        err = ctypes.get_last_error()
        if not handle:
            log_note("single copy: no guard on this PC (error %d); opening as usual" % err)
            return False
        if err == 183:   # ERROR_ALREADY_EXISTS
            # Another copy owns the name. This copy lets go of its own handle
            # to it at once, so that while it looks for the window, or shows
            # its message below, the name lives only as long as the open
            # copy: once that one closes, the next click opens the app.
            try:
                kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
                kernel32.CloseHandle(handle)
            except Exception:
                pass
        else:
            _single_instance.append(handle)
            return False
    except Exception as exc:
        log_note("single copy: no guard on this PC (%s); opening as usual" % (exc,))
        return False
    try:
        if _bring_window_forward():
            log_note("start: already open; brought its window forward")
        else:
            log_note("start: already open, but its window has not appeared yet")
            tell_user("The Forge is still opening.\n\n"
                      "Its window will appear in a moment.")
    except Exception as exc:
        log_note("start: already open; its window could not be brought forward (%s)" % (exc,))
    return True


_single_instance = []


def _bring_window_forward(wait_s=30.0):
    """Find the open copy's window by its title and bring it forward.

    FindWindowExW walks the top-level windows with this title (Microsoft:
    "if both hwndParent and hwndChildAfter are NULL, the function searches all
    top-level and message-only windows"). A folder or another program can
    carry the same title, so only the app's own window class counts: the
    WinForms window pywebview makes (WindowsForms...) or one of its message
    boxes (#32770). The first copy may still be making its window, so this
    looks again for up to wait_s seconds.

    A minimised window is restored (SW_RESTORE: "An application should specify
    this flag when restoring a minimized window"); any other is shown as it is
    (SW_SHOW: "in its current size and position"), so a maximised window
    stays maximised. SetForegroundWindow is allowed here because this copy was
    just started by the person's click ("The calling process was started by
    the foreground process"); if Windows refuses, it flashes the taskbar
    button instead, which is calm too.
    """
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.FindWindowExW.argtypes = (wintypes.HWND, wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR)
    user32.FindWindowExW.restype = wintypes.HWND
    user32.GetClassNameW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
    user32.GetClassNameW.restype = ctypes.c_int
    user32.IsIconic.argtypes = (wintypes.HWND,)
    user32.IsIconic.restype = wintypes.BOOL
    user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
    user32.ShowWindow.restype = wintypes.BOOL
    user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
    user32.SetForegroundWindow.restype = wintypes.BOOL

    def find():
        after = None
        for _ in range(64):
            hwnd = user32.FindWindowExW(None, after, None, WINDOW_TITLE)
            if not hwnd:
                return None
            name = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, name, 256)
            if name.value.startswith("WindowsForms") or name.value == "#32770":
                return hwnd
            after = hwnd
        return None

    end = time.monotonic() + wait_s
    hwnd = find()
    while not hwnd and time.monotonic() < end:
        time.sleep(0.25)
        hwnd = find()
    if not hwnd:
        return False
    user32.ShowWindow(hwnd, 9 if user32.IsIconic(hwnd) else 5)   # SW_RESTORE or SW_SHOW
    user32.SetForegroundWindow(hwnd)
    return True


WEBVIEW2_CLIENT_KEY = r"Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"


def _webview2_runtime():
    """9s57: where the Edge WebView2 Runtime was found, or "" when it was not.

    Microsoft's documented test, "Detect if a WebView2 Runtime is already
    installed" (https://learn.microsoft.com/en-us/microsoft-edge/webview2/
    concepts/distribution#detect-if-a-webview2-runtime-is-already-installed):
    read the pv (REG_SZ) value at
      HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Microsoft\\EdgeUpdate\\Clients\\
        {F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}   (per machine, 64-bit Windows)
      HKEY_CURRENT_USER\\Software\\Microsoft\\EdgeUpdate\\Clients\\
        {F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}   (per user)
    "at least one of these regkeys must be present and defined with a version
    greater than 0.0.0.0. If neither regkey exists, or if only one of these
    regkeys exists but its value is null, an empty string, or 0.0.0.0, this
    means that the WebView2 Runtime isn't installed." (The page's 32-bit
    Windows paths are not needed: this program is 64-bit only.)

    The old test, an msedgewebview2.exe under Program Files, saw per-machine
    installs only, so a per-user runtime sent the app to the browser for no
    reason. It stays as a second witness. Any error means "present": the
    window is then tried, and its own fallback to the browser stays.
    """
    try:
        import winreg
        for root, kind, sub in (
                (winreg.HKEY_LOCAL_MACHINE, "per machine", "SOFTWARE\\WOW6432Node\\" + WEBVIEW2_CLIENT_KEY),
                (winreg.HKEY_CURRENT_USER, "per user", "Software\\" + WEBVIEW2_CLIENT_KEY)):
            try:
                with winreg.OpenKey(root, sub) as key:
                    pv = str(winreg.QueryValueEx(key, "pv")[0] or "").strip()
            except FileNotFoundError:
                continue
            if pv and pv != "0.0.0.0":
                return "version %s (registry, %s)" % (pv, kind)
    except Exception as exc:
        return "assumed present (the registry could not be read: %s)" % (exc,)
    try:
        import glob as _glob
        _pf = [os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles"),
               r"C:\Program Files (x86)", r"C:\Program Files"]
        for _p in _pf:
            if not _p:
                continue
            _hits = _glob.glob(os.path.join(_p, "Microsoft", "EdgeWebView", "Application", "*", "msedgewebview2.exe"))
            if _hits:
                return "found under Program Files (%s)" % _hits[0]
    except Exception as exc:
        return "assumed present (%s)" % (exc,)
    return ""


# 9s58: safe graphics, the two browser arguments that stopped the AMD Radeon
# first-click crash (see _prepare_windows_graphics). Chromium's own words for
# the first: "Prevent the compositor from using its GPU implementation."
SAFE_GRAPHICS_ARGS = "--disable-gpu-compositing --disable-features=CalculateNativeWinOcclusion"
_MONTHS = ("January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December")


def _safe_graphics_file():
    """9s58: the small note that keeps safe graphics on for this PC.

    It sits beside the session flag, in the folder that holds the work
    (%LOCALAPPDATA%\\TheForge\\storage), so an update or a new install
    keeps it; the installer clears only the session flag. Deleting it is
    how safe graphics are switched off again, and the note says so inside.
    """
    d = storage_dir() or os.path.expanduser("~")
    return os.path.join(d, "the_forge_safe_graphics.txt")


def _when(t=None):
    """A date and time in plain words, the same in every language setting."""
    lt = time.localtime(time.time() if t is None else t)
    return "%d %s %d at %02d:%02d" % (lt.tm_mday, _MONTHS[lt.tm_mon - 1], lt.tm_year, lt.tm_hour, lt.tm_min)


def _remember_safe_graphics(path, prior_failures):
    """9s58: write the note that keeps safe graphics on. True when written."""
    try:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(
                "Safe graphics are on for The Forge on this PC.\n"
                "\n"
                "The Forge switched them on by itself on %s, because a run\n"
                "before that did not finish (%d unfinished run%s found). With safe\n"
                "graphics the window is drawn without the graphics chip's help and with\n"
                "simpler effects: a little less smooth, and safe on this PC.\n"
                "\n"
                "To try full graphics again: close The Forge, delete this file,\n"
                "and open The Forge. If its window ever closes by itself again,\n"
                "safe graphics switch back on by themselves.\n"
                % (_when(), prior_failures, "" if prior_failures == 1 else "s"))
        return True
    except Exception as exc:
        log_note("graphics: safe graphics could not be remembered on this PC (%s)" % (exc,))
        return False


def _prepare_windows_graphics(prior_failures):
    """Choose the browser arguments Edge WebView2 starts with, on Windows only.

    Returns (arguments, soft): soft is True whenever safe graphics are used, so
    the page is opened with ?softgpu=1 and sheds its heaviest paint
    (html[data-softgpu] and the app's own smooth mode).

    Reported from the field: on an HP with AMD Radeon graphics the window died on
    the very first click, while an Intel machine ran until a second window was
    opened. The first is the signature of a crash inside the graphics process,
    which is why nothing was ever written to the log. These arguments must be set
    BEFORE the web view is created, because that is when the environment is read.

    9s58: FULL GRAPHICS BY DEFAULT, SAFE GRAPHICS REMEMBERED. Until now every run
    was handed the safe arguments, so on every PC the window's moving, shadowed
    and blurred parts were composited by the processor on every frame, while
    the page was told to shed its heavy paint only after a failed run. Now:
      - a PC that has never had a run end badly gets full graphics, as Inkwell
        does (no extra arguments: the graphics chip helps draw the window);
      - the first start that finds an unfinished run (the session flag) switches
        safe graphics on by itself and REMEMBERS it in a small note beside the
        work (_safe_graphics_file), so every later start on that PC uses them,
        with ?softgpu=1. One bad ending is enough, and they stay on: the AMD
        first-click crash can happen at most once on a PC;
      - 9s58 win_like_ink: a second unfinished run no longer opens the browser;
        the window is always tried, as in Inkwell (see main);
      - deleting the note (the README says how) tries full graphics again.
    Every start writes one plain line saying which it used ("graphics: full"
    or "graphics: safe ..."), and the page says so in About while it is on.
    """
    import os
    if not sys.platform.startswith("win"):
        return None, False
    # 9s42: the all-software renderer is RETIRED from the ladder. After any run
    # that did not finish (including a force-quit of a hung window), every later
    # run was forced onto pure-CPU painting, and an eleven-megabyte crafted page
    # under it hung into an empty window: the bars drew, the body never did, the
    # force-quit counted as another bad run, and the app locked itself onto the
    # renderer that paints nothing. Safe graphics are the mild arguments only.
    existing = os.environ.get("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS", "").strip()
    path = _safe_graphics_file()
    remembered = os.path.isfile(path)
    if not remembered and prior_failures < 1:
        if "--disable-gpu-compositing" in existing:
            # Set from outside this program (a test, or by hand): the page is
            # still told, so it sheds the paint the processor would carry.
            log_note("graphics: safe, set from outside the app (%s)" % existing)
            return existing, True
        log_note("graphics: full (the graphics chip helps draw the window)")
        return (existing or None), False
    if remembered:
        try:
            since = " since " + _when(os.path.getmtime(path))
        except Exception:
            since = ""
        why = ("safe graphics are on for this PC%s, after a run that did not finish. "
               "To try full graphics again, close The Forge and delete %s" % (since, path))
    elif _remember_safe_graphics(path, prior_failures):
        why = ("safe graphics switched on for this PC by themselves, because the last run did "
               "not finish; they stay on. To try full graphics again, close The Forge and delete %s" % path)
    else:
        why = "safe graphics for this run, because the last run did not finish"
    args = SAFE_GRAPHICS_ARGS
    if existing:
        args = existing + " " + args
    os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = args
    log_note("graphics: %s (%s)" % (why, args))
    return args, True


class CarpeApiSingle:
    """The API offered on Windows by default: no second native window.

    Why: a second web view in the same process is what killed the Intel machine
    the moment a studio was opened. The page asks Python for a native window only
    because open_app exists here; with it absent the app uses ITS OWN floating
    window instead, which it draws inside the page. Those windows are no longer a
    poor relation: they resize from every edge, remember their size and place,
    fold into the dock and answer the desk tabs. Nothing is lost except the crash.

    Anyone who wants the old behaviour can set CARPE_DIEM_NATIVE_WINDOWS=1.
    """

    def __init__(self, app_url):
        self._app_url = app_url
        self._main_window = None

    def save_file(self, name, mime, data_b64):
        return save_bytes(None, name, mime, data_b64)

    def read_clipboard(self):
        """9s58: the clipboard, for the page's own Paste (see clipboard_read)."""
        return clipboard_read()

    def write_clipboard(self, text, html=""):
        """9s58: the page's own Copy and Cut (see clipboard_write)."""
        return clipboard_write(text, html)

    def broadcast_theme(self, dark):
        js = "try{window.cdApplyThemeExternal&&window.cdApplyThemeExternal(%s);}catch(e){}" % (
            "true" if dark else "false",)
        try:
            if self._main_window is not None:
                self._main_window.evaluate_js(js)
        except Exception:
            pass
        _remember_theme(dark=bool(dark))   # 9s57: the window colour of the next start
        return True


class CarpeApi:
    """JS API exposed to the main window as window.pywebview.api.

    Opens Tabula, Abacus, or Imago in its own native window (the in-app floating
    button calls open_app). The windows share the same on-disk localStorage where
    the platform web view allows it; each app re-reads its saved work on load.
    """

    APP_TITLES = {"tabula": "Tabula", "abacus": "Abacus", "slides": "Imago", "scriba": "Scriba", "fontes": "Fontes"}
    APP_COLORS = {"tabula": "#2A2622", "abacus": "#1E3D2C", "slides": "#7A2530", "scriba": "#22304A", "fontes": "#F1EBE1"}

    def __init__(self, app_url):
        import threading
        self._app_url = app_url
        # Every window reference on an API object starts with an underscore.
        # pywebview walks each public attribute of the API on every page load,
        # and a public window led it through the whole native window and web
        # view (on Windows: errors, a slower start, and native controls offered
        # to the page). It skips names that start with an underscore.
        self._main_window = None
        self._wins = {}
        # Creating two native windows at once, or twice for the same studio
        # because the float button was pressed again while the first was still
        # opening, is a real way to destabilise the platform web view. One
        # creation at a time, and never a duplicate.
        self._lock = threading.RLock()
        self._creating = set()

    def _alive(self, which):
        w = self._wins.get(which)
        if w is None:
            return False
        try:
            _ = w.title
            return True
        except Exception:
            self._wins.pop(which, None)
            return False

    def save_file(self, name, mime, data_b64):
        return save_bytes(None, name, mime, data_b64)

    def read_clipboard(self):
        """9s58: the clipboard, for the page's own Paste (see clipboard_read)."""
        return clipboard_read()

    def write_clipboard(self, text, html=""):
        """9s58: the page's own Copy and Cut (see clipboard_write)."""
        return clipboard_write(text, html)

    def close_app(self, which):
        """Close a native studio window, so the desk bar's cross can reach it.
        Without this the cross could only ever close a desk frame, which is why it
        looked ornamental on the desktop builds."""
        if which not in self.APP_TITLES:
            return False
        with self._lock:
            w = self._wins.get(which)
        if w is None:
            return False
        try:
            w.destroy()
        except Exception:
            log_problem("close_app(%r): destroy failed" % (which,), sys.exc_info())
        finally:
            with self._lock:
                self._wins.pop(which, None)
        return True

    def focus_app(self, which):
        """Return True if that app window is open (and try to bring it forward)."""
        if which not in self.APP_TITLES or not self._alive(which):
            return False
        w = self._wins[which]
        try:
            w.restore()
        except Exception:
            pass
        try:
            w.show()
        except Exception:
            pass
        return True

    def open_app(self, which):
        """Open (or focus) a separate native window for the app. True on success."""
        if which not in self.APP_TITLES:
            return False
        with self._lock:
            if self._alive(which):
                return self.focus_app(which)
            if which in self._creating:
                log_problem("open_app(%r): already opening, ignored" % (which,))
                return False
            self._creating.add(which)
        try:
            import webview
            win_api = TabulaWindowApi(host=self)
            win = webview.create_window(
                self.APP_TITLES[which],
                url=self._app_url + "#cd=" + which,
                width=1050,
                height=760,
                min_size=(MIN_WIDTH, MIN_HEIGHT),
                background_color=self.APP_COLORS[which],
                confirm_close=False,
                text_select=True,
                js_api=win_api,
            )
            win_api._win = win
            self._wins[which] = win
            try:
                win.events.closed += (lambda *a, w=which: self._wins.pop(w, None))
            except Exception:
                pass
            return True
        except Exception:
            log_problem("open_app(%r)" % (which,))
            self._wins.pop(which, None)
            return False
        finally:
            with self._lock:
                self._creating.discard(which)

    # Backward compatible names kept for older builds of the app HTML.
    def broadcast_theme(self, dark):
        """Carry a theme change to every other native window of this app.

        Separate webviews do not reliably observe one another's localStorage
        writes, so the main window asks Python to relay the change directly.
        """
        js = "try{window.cdApplyThemeExternal&&window.cdApplyThemeExternal(%s);}catch(e){}" % (
            "true" if dark else "false",
        )
        targets = []
        try:
            targets.append(self._main_window)
        except Exception:
            pass
        with self._lock:
            targets.extend(list(self._wins.values()))
        for w in targets:
            if w is None:
                continue
            try:
                w.evaluate_js(js)
            except Exception:
                pass
        _remember_theme(dark=bool(dark))   # 9s57: the window colour of the next start
        return True

    def open_tabula(self):
        return self.open_app("tabula")

    def focus_tabula(self):
        return self.focus_app("tabula")


# 644 (forge_guard_644.py): the Forge's own address answers the Forge's own window only. pywebview serves the page from
# 127.0.0.1; a request that names any other host (a page that has pointed its own name at 127.0.0.1) is refused before any
# file is read.
def _guard_local_server():
    try:
        import webview.http as _wh
    except Exception:
        return False
    b = getattr(_wh, "bottle", None)
    if b is None or getattr(b.run, "_forge_guard", False):
        return bool(b)
    orig = b.run

    def run(app=None, *a, **kw):
        # the port as pywebview gives it (by name), or in its place (bottle.run(app, server, host, port))
        port, inner = kw.get("port") or (a[2] if len(a) > 2 else None), app

        def guarded(environ, start_response):
            host = (environ.get("HTTP_HOST") or "").strip().lower()
            name = host if host.endswith("]") else host.rsplit(":", 1)[0]
            # with the port known, the window's own address exactly; were a later pywebview to start its server some
            # other way, the computer's own name alone (a page that rebinds a name always names its own), never a blank window
            if (port and host in ("127.0.0.1:%s" % port, "localhost:%s" % port, "[::1]:%s" % port)) or                     (not port and name in ("127.0.0.1", "localhost", "[::1]")):
                return inner(environ, _forge_no_store(start_response))  # 647 (forge_shell_647b.py)
            body = b"This address answers only the Forge's own window."
            start_response("421 Misdirected Request", [("Content-Type", "text/plain; charset=utf-8"),
                                                       ("Content-Length", str(len(body)))])
            return [body]
        return orig(guarded, *a, **kw)   # the app first, in its place, however the rest is given
    run._forge_guard = True
    b.run = run
    return True


def _make_window(webview, api, app_url, background):
    """The main window, in one place so its creation can be guarded.

    It is handed a proper file:// URI, not a bare path. Every studio window
    already used one; this window did not, and on Windows a bare path like
    C:\\Users\\...\\the_forge.html is turned into file://C:\\Users..., which is
    not a valid URL. Edge WebView2 fails that navigation inside the backend,
    before any Python error can be raised, which is why the window died with
    nothing written down.
    """
    _guard_local_server()
    return webview.create_window(
        WINDOW_TITLE,
        url=app_url,
        width=DEFAULT_WIDTH,
        height=DEFAULT_HEIGHT,
        min_size=(MIN_WIDTH, MIN_HEIGHT),
        background_color=background,
        confirm_close=False,
        text_select=True,
        js_api=api,
    )


def _guard_bridge_frames():
    """647 (forge_shell_647.py): on a Mac, answer a call from the page only when it comes from the main frame of the Forge's
    own page, never from a frame inside it (pywebview's message handler is defined in every frame and does not check)."""
    if sys.platform != "darwin":
        return
    try:
        import objc
        from webview.platforms import cocoa as _pc
        base = _pc.BrowserView.JSBridge
        if getattr(base, "_forge_guarded", False):
            return

        class ForgeFrameGuardedJSBridge(base):
            def userContentController_didReceiveScriptMessage_(self, controller, message):
                try:
                    info = message.frameInfo()
                    if info is None or not info.isMainFrame():
                        return
                    origin = info.securityOrigin()
                    host = str(origin.host() or "") if origin is not None else ""
                    proto = str(origin.protocol() or "").lower() if origin is not None else ""
                    # the Forge's own page: from its file, or from pywebview's own address; never a website
                    if not (host in ("127.0.0.1", "localhost") or proto in ("file", "about") or (proto == "" and host == "")):
                        return
                except Exception:
                    return
                objc.super(ForgeFrameGuardedJSBridge, self).userContentController_didReceiveScriptMessage_(controller, message)

        ForgeFrameGuardedJSBridge._forge_guarded = True
        _pc.BrowserView.JSBridge = ForgeFrameGuardedJSBridge
    except Exception:
        log_problem("guard of the page's calls to the program could not be set", sys.exc_info())


_CARE = {"attached": False, "reloads": [], "told": False, "gpu": 0, "refs": []}


def _care_say(text):
    if not _CARE["told"]:
        _CARE["told"] = True
        import threading as _th
        _th.Thread(target=tell_user, args=(text,), daemon=True).start()


def _forge_care_attach(window):
    """647 (forge_shell_647.py), Windows: listen for the web view's processes stopping. Once, from the first page load (the web
    view exists by then); the listening itself is set up on the window's own thread."""
    if _CARE["attached"] or not sys.platform.startswith("win"):
        return
    _CARE["attached"] = True
    try:
        import time as _t
        import clr  # noqa: F401  (pythonnet, already loaded by the window)
        from System import Func, Type
        from Microsoft.Web.WebView2.Core import CoreWebView2ProcessFailedKind as K
        form = getattr(window, "native", None)
        wv = getattr(form, "webview", None) if form is not None else None
        if wv is None:
            log_problem("care: the web view could not be reached; a page whose process stops will not come back by itself")
            return

        def failed(_sender, args):
            try:
                kind = args.ProcessFailedKind
                more = ""
                try:
                    more = " (%s, exit code %s)" % (args.Reason, args.ExitCode)
                except Exception:
                    pass
                now = _t.time()
                if kind == K.RenderProcessExited:
                    recent = [x for x in _CARE["reloads"] if now - x < 120]
                    if len(recent) >= 3:
                        log_note("page: its process stopped again%s, after three new starts in two minutes; left as it is" % more)
                        _care_say("The Forge's page stopped working several times in a row.\n\nYour work is saved as you go. "
                                  "Please close The Forge and open it again.\n\nDetails were written to:\n  %s" % crash_log_path())
                        return
                    recent.append(now)
                    _CARE["reloads"] = recent
                    log_note("page: its process stopped%s; the page is loaded again" % more)
                    wv.CoreWebView2.Reload()
                elif kind == K.RenderProcessUnresponsive:
                    log_note("page: its process is not answering%s; left to finish what it is doing" % more)
                elif kind == K.GpuProcessExited:
                    _CARE["gpu"] += 1
                    log_note("graphics: the graphics process stopped%s (%d this run)" % (more, _CARE["gpu"]))
                    path = _safe_graphics_file()
                    if _CARE["gpu"] >= 2 and not os.path.isfile(path) and _remember_safe_graphics(path, 1):
                        log_note("graphics: safe graphics kept for the next start (%s)" % path)
                elif kind == K.BrowserProcessExited:
                    log_note("web view: its own process stopped%s; the window cannot show the page until The Forge is opened again" % more)
                    _care_say("The Forge's window stopped working (its web view closed).\n\nYour work is saved as you go. "
                              "Please close The Forge and open it again.")
                else:
                    log_note("web view: a helper process stopped (%s)%s" % (kind, more))
            except BaseException:
                log_problem("care: a stopped process could not be handled", sys.exc_info())

        def attach():
            core = wv.CoreWebView2
            if core is None:
                log_problem("care: the web view is not ready; a page whose process stops will not come back by itself")
                return None
            core.ProcessFailed += failed
            _CARE["refs"].append(failed)
            ver = ""
            try:
                ver = str(core.Environment.BrowserVersionString)
            except Exception:
                pass
            log_note("care: listening for the page's processes stopping (web view %s)" % (ver or "version unknown"))
            return None
        form.Invoke(Func[Type](attach))
    except BaseException:
        log_problem("care: could not listen to the web view", sys.exc_info())


def _forge_no_store(start_response):
    """647 (forge_shell_647b.py): every answer from the Forge's own address says it is not to be kept."""
    def sr(status, headers, exc_info=None):
        keep = [(k, v) for (k, v) in headers if k.lower() not in ("cache-control", "expires", "pragma", "etag", "last-modified")]
        keep += [("Cache-Control", "no-store, max-age=0"), ("Pragma", "no-cache"), ("Expires", "0")]
        if exc_info is not None:
            return start_response(status, keep, exc_info)
        return start_response(status, keep)
    return sr


def _page_build(path):
    """The build the Forge's page names (window.CD_BUILD's pass and stamp), read from the file, or ''."""
    import re as _re
    try:
        with open(path, "rb") as fh:
            data = fh.read()
        m = _re.search(rb'window\.CD_BUILD=\{date:"[^"]*",pass:"(\d+)",stamp:"([^"]*)"', data)
        return (m.group(1) + b" " + m.group(2)).decode("ascii", "replace") if m else ""
    except Exception:
        return ""


def _forget_old_pages(app_html):
    """647 (forge_shell_647b.py): the first time a build starts, the web view's cache of pages is emptied, so the window shows
    this build's page and not one kept from an earlier build at the same address. The work (local storage, the databases) is
    never touched."""
    build = _page_build(app_html)
    store = storage_dir()
    if not build or not store:
        return
    note = os.path.join(os.path.dirname(store), "page_build.txt")
    try:
        with open(note, encoding="utf-8") as fh:
            before = fh.read().strip()
    except Exception:
        before = ""
    if before == build:
        return
    emptied = False
    try:
        if sys.platform == "darwin":
            import time as _t
            import WebKit
            from Foundation import NSDate, NSRunLoop, NSSet
            kinds = NSSet.setWithArray_([WebKit.WKWebsiteDataTypeDiskCache, WebKit.WKWebsiteDataTypeMemoryCache])
            done = {"ok": False}

            def _done():
                done["ok"] = True
            WebKit.WKWebsiteDataStore.defaultDataStore().removeDataOfTypes_modifiedSince_completionHandler_(
                kinds, NSDate.dateWithTimeIntervalSince1970_(0), _done)
            end = _t.time() + 5
            while not done["ok"] and _t.time() < end:
                NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.05))
            emptied = done["ok"]
        elif sys.platform.startswith("win"):
            import shutil as _sh
            for rel in (("EBWebView", "Default", "Cache"), ("EBWebView", "Default", "Code Cache")):
                p = os.path.join(store, *rel)
                if os.path.isdir(p):
                    _sh.rmtree(p, ignore_errors=True)
            emptied = True
    except Exception:
        log_problem("page cache: could not be emptied", sys.exc_info())
    log_note("page: build %s starts (the build before: %s); the web view's cache of pages %s"
             % (build, before or "none noted", "emptied" if emptied else "NOT emptied"))
    if emptied:
        try:
            with open(note, "w", encoding="utf-8") as fh:
                fh.write(build)
        except Exception:
            pass


def main():
    # 9s57: one copy at a time. First of all, and before the session mark is
    # read or written: a second click brings the open window forward and ends.
    if _another_copy_is_open():
        return

    app_html = find_app_html()
    if not app_html:
        tell_user(
            "Could not find the app file, the_forge.html.\n\n"
            "If you are running from the source folder, keep the_forge.html\n"
            "beside this program. The installed program keeps it in its\n"
            "_internal folder: The Forge.exe must stay in its own folder,\n"
            "beside _internal. If it was moved out on its own, install\n"
            "The Forge again with its installer (the Setup .exe on the\n"
            "Releases page), or open it from the Start menu.\n\n"
            "You can also open the_forge.html on its own. That file is the\n"
            "whole app, offline."
        )
        sys.exit(1)

    _prior = _begin_session()
    # 9s58 win_like_ink: the window is ALWAYS tried, as in Inkwell 7.36. Two
    # unfinished runs used to open the browser instead; Inkwell dropped the
    # same rung after it left Inkwell stuck, and an installed program does not
    # open the browser by itself. An unfinished run still switches safe
    # graphics on for this PC (_prepare_windows_graphics), and a real failure
    # to draw the window is still handled below, by the error it raises.
    _gfx_args, _gfx_soft = _prepare_windows_graphics(_prior)
    try:
        _forget_old_pages(app_html)  # 647 (forge_shell_647b.py)
    except Exception:
        log_problem("page cache: the check failed", sys.exc_info())
    log_problem("start: locating the window component")
    try:
        import webview  # pywebview
    except BaseException:
        # Not ImportError alone. On Windows pywebview loads pythonnet, and a
        # runtime that will not start raises RuntimeError, OSError or worse.
        # This was a crash before the window ever appeared.
        log_problem("import webview failed", sys.exc_info())
        _missing = isinstance(sys.exc_info()[1], ImportError)
        if open_in_browser(app_html):
            if _missing:
                tell_user(
                    "The Forge has opened in your browser, because the component\n"
                    "that draws its own window is not installed.\n\n"
                    "Everything works exactly the same there, and nothing is sent\n"
                    "anywhere."
                )
            else:
                tell_user(
                    "The Forge has opened in your browser, because the component\n"
                    "that draws its own window would not start on this PC.\n\n"
                    "Everything works exactly the same there, and nothing is sent\n"
                    "anywhere.\n\n"
                    "Details were written to:\n  %s" % crash_log_path()
                )
            return
        tell_user(friendly_missing_dependency_message())
        sys.exit(1)

    # Create the native window pointing at the local HTML file. Because the file
    # is loaded from disk, everything runs offline with no server involved.
    # background_color tints the native window behind the page. It is what shows
    # during load, so since 9s57 it is the colour the page itself paints first
    # (learned from the page at ready, see _remember_theme; WINDOW_COLORS, in
    # the look the page last showed, until one has been learned): no flash of
    # another colour. Note: this is NOT the same as the title bar colour you get from
    # installing as a web app, which comes from the manifest's theme_color and
    # is applied by the browser.
    # File URI form so a query flag can be appended for the Tabula window.
    # 9s58: ?softgpu=1 goes with safe graphics EVERY time they are used, not
    # only on the start after a bad ending: with the processor compositing,
    # the page sheds its dearest paint (html[data-softgpu]) and says in About
    # that safe graphics are on. The query does not change where the work is
    # kept (a file page's storage does not depend on it).
    try:
        from pathlib import Path
        app_url = Path(app_html).as_uri()
        if _gfx_soft:
            app_url = app_url + "?softgpu=1"
    except Exception:
        app_url = app_html

    # Recorded once at startup so a crash report says what it was running on.
    try:
        import platform
        log_problem("start: python %s on %s %s | pywebview %s" % (
            platform.python_version(), platform.system(), platform.release(),
            getattr(webview, "__version__", "unknown")))
    except Exception:
        pass

    if sys.platform.startswith("win") and not os.environ.get("CARPE_DIEM_NATIVE_WINDOWS"):
        api = CarpeApiSingle(app_url)
        log_problem("windows: one window, the app draws its own floating windows")
    else:
        api = CarpeApi(app_url)
    _look, _colour = _remembered_theme()
    _background = _colour or WINDOW_COLORS.get(_look, WINDOW_COLORS["day"])
    log_note("start: window colour %s (%s)" % (_background, _look))
    try:
        window = _make_window(webview, api, app_url, _background)
    except BaseException:
        # Creating the window can fail on its own, before start() is reached.
        log_problem("create_window failed", sys.exc_info())
        if open_in_browser(app_html):
            tell_user(
                "The Forge could not open its own window on this PC, so it has\n"
                "opened in your browser instead. Everything works the same there,\n"
                "offline.\n\n"
                "The cure for the app's own window is the free Microsoft Edge\n"
                "WebView2 Runtime, installed once from Microsoft's website.\n"
                "Details were written to:\n  %s" % crash_log_path())
            return
        tell_user(
            "The Forge could not open a window on this PC.\n\n"
            "Open the_forge.html by hand: that file IS the whole app.\n\n"
            "Details were written to:\n  %s" % crash_log_path())
        sys.exit(1)
    try:
        api._main_window = window
    except Exception:
        pass
    # A close or a shutdown is a clean ending (see _closing_is_clean); a crash
    # still is not.
    try:
        window.events.closing += _closing_is_clean
    except Exception:
        log_problem("could not watch the window closing")
    try:
        window.events.loaded += _page_loaded
        window.events.loaded += lambda *_a, **_k: _forge_care_attach(window)  # 647 (forge_shell_647.py)
        _guard_bridge_frames()
    except Exception:
        pass
    # 9s57: how long the start takes, in the log on every start: the window
    # shown, the page loaded, and the page ready (_watch_start, started below,
    # just before the window).
    try:
        window.events.shown += _window_shown
    except Exception:
        pass

    # gui=None lets pywebview pick the best native backend for the platform
    # (Edge WebView2 on Windows, WKWebView on macOS, WebKitGTK/Qt on Linux).
    # debug=False keeps developer tools hidden for a clean, app-like feel.
    def _hook(exc_type, exc, tb):
        log_problem("uncaught", (exc_type, exc, tb))
        sys.__excepthook__(exc_type, exc, tb)
    sys.excepthook = _hook
    try:
        import threading
        if hasattr(threading, "excepthook"):
            threading.excepthook = lambda a: log_problem(
                "uncaught in thread", (a.exc_type, a.exc_value, a.exc_traceback))
    except Exception:
        pass

    # private_mode=False is what makes the work survive closing the app.
    # storage_path keeps it in the user's profile rather than in a temporary
    # unpack directory. An older pywebview may not accept either, so the failure
    # is caught and RECORDED rather than passing silently, because passing
    # silently is exactly how the data loss went unnoticed.
    _store = storage_dir()

    def _try_start(gui, with_storage):
        """One attempt, recorded either way. Returns True if the window ran."""
        kw = {"debug": False}
        if gui is not None:
            kw["gui"] = gui
        if with_storage:
            kw["private_mode"] = False
            if _store:
                kw["storage_path"] = _store
        try:
            log_problem("start attempt: gui=%r storage=%s" % (gui, bool(with_storage and _store)))
            webview.start(**kw)
            return True
        except TypeError:
            # An older pywebview refuses private_mode or storage_path. Recorded
            # rather than passed over, because passing it over silently is how
            # the data loss went unnoticed once before.
            log_problem("webview.start refused private_mode or storage_path")
            return False
        except Exception:
            log_problem("webview.start failed with gui=%r" % (gui,), sys.exc_info())
            return False

    # On Windows the backend is edgechromium or nothing. 9s43: the old order
    # had a gui=None road beyond them, and pywebview picks MSHTML down that road
    # when the WebView2 runtime is absent. MSHTML is the Internet Explorer
    # engine: it paints a top bar and a rail from plain markup but cannot run
    # this page at all, which is the "chrome only, body empty" failure. Rather
    # than walk a machine down it, the runtime is checked first; absent, the
    # page opens in the browser, which cannot be MSHTML and cannot lose.
    # 9s57: the runtime is looked for the way Microsoft documents it (the
    # registry), as well as under Program Files; see _webview2_runtime.
    _rt_missing = False
    if sys.platform.startswith("win"):
        try:
            _rt = _webview2_runtime()
            _rt_missing = not _rt
            if _rt_missing:
                log_note("webview2 runtime: not in the registry and not under Program Files")
            else:
                log_note("webview2 runtime: %s" % _rt)
        except Exception:
            _rt_missing = False
        if _rt_missing:
            if open_in_browser(app_html):
                _end_session()
                tell_user(
                    "The Forge has opened in your browser.\n\n"
                    "Its own window needs the Microsoft Edge WebView2 Runtime, which\n"
                    "is not present on this PC. It is free from Microsoft; once it is\n"
                    "installed, the app's own window will work.\n\n"
                    "Until then, everything runs here, offline, exactly the same.\n"
                    "(Double-clicking the_forge.html does the same thing at any time.)")
                return
    _order = [("edgechromium", True), ("edgechromium", False)] \
        if sys.platform.startswith("win") else [(None, True), (None, False)]

    # 9s57: the watch on the page (see _watch_start). A daemon thread, so it
    # never holds the program open after the window closes.
    try:
        import threading
        threading.Thread(target=_watch_start, args=(window, app_html),
                         name="start-watch", daemon=True).start()
    except Exception:
        log_note("start: the ready watch could not start")

    _ran = False
    for _gui, _with_storage in _order:
        if _try_start(_gui, _with_storage):
            _ran = True
            _end_session()
            if not _with_storage:
                log_problem("started WITHOUT persistent storage: work may not survive closing")
            break

    if not _ran:
        # No native window could be created at all: a missing WebView2 runtime
        # on Windows is the usual reason. The page still is the application, so
        # it opens in the browser rather than the program dying in silence.
        log_problem("every backend refused to start")
        if open_in_browser(app_html):
            tell_user(
                "The Forge could not open a native window on this PC, so it has\n"
                "opened in your browser instead. Everything works the same there.\n\n"
                "The usual cause is a missing Microsoft Edge WebView2 runtime.\n"
                "Details were written to:\n  %s" % crash_log_path()
            )
        else:
            tell_user(
                "The Forge could not open a window, and could not reach a browser\n"
                "either. Open the_forge.html by hand: that file IS the whole app.\n\n"
                "Details were written to:\n  %s" % crash_log_path()
            )


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        # A crash now leaves a file to read instead of a window that vanishes.
        log_problem("fatal")
        tell_user(
            "The Forge stopped unexpectedly.\n\n"
            "Details were written to:\n  %s\n\n"
            "the_forge.html still opens the whole app in a browser: it is in the\n"
            "package you downloaded, and in the _internal folder beside\n"
            "this program." % crash_log_path())
        sys.exit(1)
