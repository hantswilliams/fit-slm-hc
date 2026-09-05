"""Figure 2 (aug28 revision): AR vs axis sum for the 22 unique snapshot tasks.

Reads analysis/data/tasks_master.csv so the figure cannot drift from the table.
Shape+tone encode adaptation symmetry (black circles vs. grey squares; the
figure uses no color, for journals that charge for color figures); the 4-bit
quantization variant of Pathology IE is shown hollow, linked to its parent.
Selective direct labels only. Thresholds are governance settings, drawn as
reference lines, with AR = 1.0 as parity.
"""
import csv
from collections import defaultdict
import matplotlib.pyplot as plt

INK="#171717"; MUT="#666666"; FAINT="#cfcfcf"; GRID="#e6e6e6"
BLACK="#171717"; GREY="#8c8c8c"   # grayscale-only palette: black vs. mid-grey (no color)

rows = list(csv.DictReader(open("tasks_master.csv")))
tasks = [r for r in rows if r["axis_sum"] != ""]
uniq  = [r for r in tasks if r["is_variant"] == "0"]
var   = [r for r in tasks if r["is_variant"] == "1"]

groups = defaultdict(list)
for r in uniq: groups[int(r["axis_sum"])].append(r)
for s in groups: groups[s].sort(key=lambda r: float(r["ar"]))

def xpos(s, i, n, width=0.46):
    if n == 1: return s
    return s - width/2 + width * i/(n-1)

pos = {}
for s, g in groups.items():
    for i, r in enumerate(g): pos[r["task_id"]] = xpos(s, i, len(g))

fig, ax = plt.subplots(figsize=(7.0, 4.6))
for y in (0.80, 0.95):
    ax.axhline(y, ls=(0,(4,3)), lw=0.9, color=FAINT, zorder=1)
ax.axhline(0.90, ls=(0,(4,3)), lw=1.2, color=MUT, zorder=1)
ax.axhline(1.00, lw=0.9, color=GRID, zorder=1)
for y, lab, c in ((0.80,"AR 0.80 (lenient)",FAINT),(0.90,"AR 0.90 (default)",MUT),
                  (0.95,"AR 0.95 (strict)",FAINT),(1.00,"parity",FAINT)):
    ax.text(7.62, y, lab, fontsize=7.2, color=MUT if y==0.90 else "#919191",
            va="center", ha="left")

# group means as short gray bars
for s, g in groups.items():
    m = sum(float(r["ar"]) for r in g)/len(g)
    ax.plot([s-0.30, s+0.30], [m, m], lw=2.2, color="#a3a3a3", alpha=0.85,
            solid_capstyle="round", zorder=2)

M = {"slm_favored": dict(marker="o", color=BLACK, label="SLM-favored adaptation"),
     "symmetric":   dict(marker="s", color=GREY,  label="Symmetric adaptation")}
seen = set()
for r in uniq:
    st = r["adaptation_symmetry"]; sp = M[st]
    ax.scatter(pos[r["task_id"]], float(r["ar"]), s=46, marker=sp["marker"],
               facecolor=sp["color"], edgecolor="white", linewidth=1.1,
               label=sp["label"] if st not in seen else None, zorder=4)
    seen.add(st)

# 4-bit variant: hollow, linked to its parent (T07)
for r in var:
    x = pos["T07"]
    ax.plot([x, x], [float(r["ar"])+0.012, 0.938-0.012], lw=0.9, color=MUT,
            ls=(0,(2,2)), alpha=0.9, zorder=3)
    ax.scatter(x, float(r["ar"]), s=46, marker="s", facecolor="white",
               edgecolor=BLACK, linewidth=1.4, zorder=4, label="4-bit variant of Pathology IE")

LABELS = {"T07": ("Pathology IE (Vignette A)", (10, 4)),
          "T08": ("4-bit", (10, -2)),
          "T12": ("Suicide detection", (-10, -3)),
          "T14": ("DDXPlus diagnosis", (-8, -3)),
          "T20": ("Clinical triage", (8, 4)),
          "T22": ("Medical exam QA", (-10, 8)),
          "T23": ("Medical QA (USMLE)", (-10, -14))}
for r in tasks:
    if r["task_id"] in LABELS:
        lab, (dx, dy) = LABELS[r["task_id"]]
        x = pos[r["task_id"]] if r["task_id"] != "T08" else pos["T07"]
        ha = "right" if dx < 0 else "left"
        ax.annotate(lab, (x, float(r["ar"])), textcoords="offset points",
                    xytext=(dx, dy), fontsize=7.4, color=INK, ha=ha)

ax.set_xlim(2.5, 7.6); ax.set_ylim(0.62, 1.78)
ax.set_xticks([3,4,5,6,7])
ax.set_xticks([], minor=True)
ax.set_xlabel("Axis sum ($r+k+o$)", fontsize=9.5)
ax.set_ylabel("Accuracy Ratio (SLM $\\div$ reference)", fontsize=9.5)
ax.tick_params(labelsize=8.5, length=0)
for side in ("top","right"): ax.spines[side].set_visible(False)
for side in ("left","bottom"): ax.spines[side].set_color(FAINT)
ax.grid(axis="y", color=GRID, lw=0.6, zorder=0)
ax.set_axisbelow(True)
leg = ax.legend(loc="upper right", fontsize=7.6, frameon=False,
                handletextpad=0.4, borderaxespad=0.2)
ax.plot([], [])  # no-op
# JMIR: no caption text embedded in the image; the gray-bar explanation lives in the figure caption.
fig.tight_layout()
for ext in ("pdf","png"):
    fig.savefig(f"figure2_ar_scatter.{ext}", dpi=300, bbox_inches="tight")
print("figure 2 written; n unique =", len(uniq), "variant =", len(var))
