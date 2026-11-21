# 0003: Show the monthly art comparison as a generated HTML page in the browser

- Status: accepted
- Date: 2026-11-21

## Decision (Y-statement)

In the context of **R5's monthly "open an old piece next to a recent one" in a
command-line app that may only use the Python standard library**, facing **the fact that
a terminal cannot show images, and that the standard library has no image decoding
(tkinter's PhotoImage reads only PNG/GIF, not JPEG or WebP, and tkinter is not always
installed)**, we decided for **writing `drawplan_art/compare.html` with the oldest piece
on the left and the newest on the right, each labelled with its date, and opening it
with `webbrowser`**, and neglected **opening both files in the operating system's image
viewer (`os.startfile` / `open` / `xdg-open`: two separate windows that aren't side by
side, with platform-specific code), and a tkinter window (no JPEG/WebP, and a GUI
dependency that can be missing)**, to achieve **a true side-by-side view with dates,
working on every OS and for every accepted image format, while the page-building logic
stays plain, testable text with no GUI**, accepting **that the app depends on a default
browser being set, that each comparison overwrites the one page, and that the CLI cannot
tell whether the page actually opened. To cover that, the CLI also prints the page path.**
