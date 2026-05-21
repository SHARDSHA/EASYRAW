import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk

# =============================================================================
# CONFIG
# =============================================================================

RAW_PATH = "DSCF5184.RAF"
WINDOW_TITLE = "EASYRAW Pre-lpha"

# =============================================================================
# WHITE BALANCE PRESETS
# =============================================================================

WB_PRESETS = {
    "Auto":        (1.0, 1.0, 1.0),
    "Sunny":       (2.0, 1.0, 1.6),
    "Cloudy":      (2.1, 1.0, 1.5),
    "Shade":       (2.3, 1.0, 1.8),
    "Tungsten":    (1.2, 1.0, 2.5),
    "Fluorescent": (1.5, 1.0, 2.0),
}

# =============================================================================
# RAW LOADING
# =============================================================================

def load_raw(path):

    global raw_info

    # --- Lectura EXIF amb Pillow ---
    # Els tags EXIF estan identificats per números estàndard:
    # 33434 = ExposureTime, 33437 = FNumber, 34855 = ISOSpeedRatings, 37386 = FocalLength

    EXIF_TAGS = {
        33434: "ExposureTime",
        33437: "FNumber",
        34855: "ISO",
        37386: "FocalLength",
    }

    def read_exif_pillow(path):
        try:
            img = Image.open(path)
            exif_raw = img._getexif()
            if not exif_raw:
                return {}
            return {EXIF_TAGS[k]: v for k, v in exif_raw.items() if k in EXIF_TAGS}
        except Exception:
            return {}

    def fmt_rational(v):
        """Pillow retorna valors racionals com a tuples (numerador, denominador)."""
        if isinstance(v, tuple):
            return v[0] / v[1] if v[1] != 0 else 0
        return float(v)

    def fmt_shutter(v):
        if v is None:
            return "—"
        s = fmt_rational(v)
        if s == 0:
            return "—"
        if s >= 1:
            return f"{s:.1f}s"
        return f"1/{round(1/s)}s"

    def fmt_aperture(v):
        if v is None:
            return "—"
        a = fmt_rational(v)
        return f"f/{a:.1f}" if a else "—"

    def fmt_focal(v):
        if v is None:
            return "—"
        f = fmt_rational(v)
        return f"{f:.0f}mm" if f else "—"

    def fmt_iso(v):
        if v is None:
            return "—"
        return f"ISO {int(v)}"

    tags = read_exif_pillow(path)

    raw_info = {
        "ISO":       fmt_iso(tags.get("ISO")),
        "Obturador": fmt_shutter(tags.get("ExposureTime")),
        "Obertura":  fmt_aperture(tags.get("FNumber")),
        "Focal":     fmt_focal(tags.get("FocalLength")),
    }

    # --- Lectura del RAW amb rawpy ---
    with rawpy.imread(path) as raw:
        rgb = raw.postprocess(
            use_camera_wb=False,
            no_auto_bright=False,
            gamma=(1, 1),
            output_bps=16
        )

    rgb = rgb.astype(np.float32) / 65535.0
    return rgb

# =============================================================================
# UTILS
# =============================================================================

def clamp(img):
    return np.clip(img, 0.0, 1.0)

# =============================================================================
# EXPOSURE
# =============================================================================

def apply_exposure(img, value):
    # value range: -5 .. +5
    ev = value / 2.0
    return clamp(img * (2.0 ** ev))

# =============================================================================
# WHITE BALANCE
# =============================================================================

def apply_white_balance(img, preset):

    m = WB_PRESETS[preset]

    out = img.copy()
    out[:, :, 0] *= m[0]
    out[:, :, 1] *= m[1]
    out[:, :, 2] *= m[2]

    return clamp(out)

# =============================================================================
# PROCESS PIPELINE
# =============================================================================

def process(img):

    out = img.copy()

    out = apply_exposure(out, exposure_var.get())
    out = apply_white_balance(out, wb_var.get())

    return clamp(out)

# =============================================================================
# DISPLAY
# =============================================================================

def to_tk(img):

    img = clamp(img)
    img = (img * 255).astype(np.uint8)

    pil = Image.fromarray(img)
    pil.thumbnail((800, 800))

    return ImageTk.PhotoImage(pil)

# =============================================================================
# REFRESH
# =============================================================================

def refresh():

    global current_view

    if show_after.get():
        img = process(original)
    else:
        img = original

    current_view = to_tk(img)

    image_label.configure(image=current_view)
    image_label.image = current_view

# =============================================================================
# LOAD
# =============================================================================

raw_info = {}
print("Welcome to EasyRaw. The RAW developer with a soul")
print("Loading RAW...")

original = load_raw(RAW_PATH)
original = original[::2, ::2]

# =============================================================================
# GUI
# =============================================================================

root = tk.Tk()
root.title(WINDOW_TITLE)
root.configure(bg="#111111")

main_frame = tk.Frame(root, bg="#111111")
main_frame.pack()

image_frame = tk.Frame(main_frame, bg="#111111")
image_frame.pack(side="left", padx=10, pady=10)

control_frame = tk.Frame(main_frame, bg="#111111")
control_frame.pack(side="right", fill="y", padx=10, pady=10)

# =============================================================================
# IMAGE
# =============================================================================

current_view = to_tk(original)

image_label = tk.Label(image_frame, image=current_view, bg="#111111")
image_label.pack()

# =============================================================================
# TITLE
# =============================================================================

tk.Label(
    control_frame,
    text="EASYRAW",
    fg="white",
    bg="#111111",
    font=("Monospace", 13)
).pack(pady=10)

# =============================================================================
# TOGGLE
# =============================================================================

show_after = tk.BooleanVar(value=True)

tk.Checkbutton(
    control_frame,
    text="Show processed",
    variable=show_after,
    command=refresh,
    fg="white",
    bg="#111111",
    selectcolor="#333333"
).pack(pady=10)

# =============================================================================
# EXPOSURE SLIDER
# =============================================================================

tk.Label(
    control_frame,
    text="Exposure",
    fg="white",
    bg="#111111"
).pack()

exposure_var = tk.DoubleVar(value=0)

tk.Scale(
    control_frame,
    from_=-5,
    to=5,
    resolution=0.1,
    orient="horizontal",
    variable=exposure_var,
    command=lambda _: refresh(),
    fg="white",
    bg="#111111",
    highlightthickness=0
).pack(fill="x", padx=10)

# =============================================================================
# WHITE BALANCE
# =============================================================================

wb_var = tk.StringVar(value="Auto")

tk.Label(
    control_frame,
    text="White Balance",
    fg="white",
    bg="#111111"
).pack()

ttk.OptionMenu(
    control_frame,
    wb_var,
    "Auto",
    *WB_PRESETS.keys(),
    command=lambda _: refresh()
).pack(pady=5)

# =============================================================================
# EXIF PANEL (a baix de tot dels controls)
# =============================================================================

# Separador visual
tk.Frame(
    control_frame,
    bg="#333333",
    height=1
).pack(fill="x", padx=5, pady=15)

tk.Label(
    control_frame,
    text="EXIF",
    fg="#888888",
    bg="#111111",
    font=("Monospace", 9)
).pack()

# Mostra cada camp EXIF com una fila etiqueta + valor
EXIF_LABELS = {
    "ISO":       "ISO",
    "Obturador": "Shutter",
    "Obertura":  "Aperture",
    "Focal":     "Focal",
}

for key, label in EXIF_LABELS.items():
    row = tk.Frame(control_frame, bg="#111111")
    row.pack(fill="x", padx=8, pady=1)

    tk.Label(
        row,
        text=label,
        fg="#666666",
        bg="#111111",
        font=("Monospace", 9),
        width=9,
        anchor="w"
    ).pack(side="left")

    tk.Label(
        row,
        text=raw_info.get(key, "—"),
        fg="#cccccc",
        bg="#111111",
        font=("Monospace", 9),
        anchor="w"
    ).pack(side="left")

# =============================================================================
# START
# =============================================================================

refresh()
root.mainloop()
