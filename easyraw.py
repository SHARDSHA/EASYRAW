import rawpy
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk

# =============================================================================
# CONFIG
# =============================================================================

RAW_PATH = "DSCF5184.RAF"
WINDOW_TITLE = "EASYRAW"

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
    font=("Courier", 14)
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
# EXPOSURE SLIDER (NEW)
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
# START
# =============================================================================

refresh()
root.mainloop()

