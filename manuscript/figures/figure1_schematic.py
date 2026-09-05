"""Figure 1 (aug28 revision): task-side axes schematic.

Replaces the previous Figure 1, which drew isotropic zone bands labeled with
AR thresholds (review finding F11). This version shows only the task-side
coordinate system: three ordinal axes, levels 1-3. The envelope is measured,
not drawn.

Sept 2026: rendered in black and grey only (no color), for journals that
charge for color figures.
"""
import matplotlib.pyplot as plt
import numpy as np

INK = "#171717"; MUT = "#666666"; FAINT = "#bfbfbf"; ACC = INK   # grayscale-only palette (no color)

AXES = [
    (90,  "Reasoning\nComplexity ($r$)", ["Extraction", "Interpretation", "Synthesis"]),
    (210, "Knowledge\nBoundedness ($k$)", ["Closed-domain", "Domain-specific", "Open-domain"]),
    (330, "Output\nStructure ($o$)", ["Deterministic", "Templated", "Creative"]),
]

fig, ax = plt.subplots(figsize=(6.4, 6.0))
ax.set_aspect("equal"); ax.axis("off")

for ang, name, levels in AXES:
    a = np.radians(ang)
    ux, uy = np.cos(a), np.sin(a)
    ax.plot([0, 3.18*ux], [0, 3.18*uy], lw=1.4, color=INK, zorder=3)
    ax.annotate("", xy=(3.34*ux, 3.34*uy), xytext=(3.05*ux, 3.05*uy),
                arrowprops=dict(arrowstyle="-|>", lw=1.2, color=INK), zorder=3)
    nr = 3.72 if ang == 90 else 4.05
    ax.text(nr*ux, nr*uy, name, ha="center", va="center",
            fontsize=10.5, fontweight="bold", color=INK)
    for lev, lab in zip((1, 2, 3), levels):
        x, y = lev*ux, lev*uy
        ax.plot([x], [y], marker="o", ms=4.5, color=ACC, zorder=4)
        if ang == 90:
            ax.text(x - 0.22, y, f"{lev}  {lab}", ha="right", va="center",
                    fontsize=8.2, color=MUT, zorder=4)
        elif ang == 210:
            ax.text(x - 0.13, y + 0.20, str(lev), ha="center", va="bottom",
                    fontsize=8.4, color=MUT, zorder=4)
        else:
            ax.text(x + 0.13, y + 0.20, str(lev), ha="center", va="bottom",
                    fontsize=8.4, color=MUT, zorder=4)
    if ang != 90:
        sub = "   ".join(f"{i} {lab}" for i, lab in zip((1, 2, 3), levels))
        ax.text(nr*ux, nr*uy - 0.72, sub, ha="center", va="center",
                fontsize=7.8, color=MUT, zorder=4)

# JMIR: no notes embedded in the image; this explanatory text lives in the figure caption instead.
ax.set_xlim(-5.0, 5.0); ax.set_ylim(-3.55, 4.5)
fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(f"figure1_axes_schematic.{ext}", dpi=300, bbox_inches="tight")
print("figure 1 written")
