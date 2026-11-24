"""Rebuild the lecture figures from the two bundled dispatch CSVs.

Run: python data/build_charts.py
Dependencies used for the supplied figures: pandas 2.2.3 and matplotlib 3.11.2.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


DATA = Path(__file__).resolve().parent
IMAGES = DATA.parent / "images"
NAVY = "#162b43"
BLUE = "#2864a3"
TEAL = "#087c7c"
PALE_BLUE = "#b8d1ec"
AMBER = "#c77b3e"
GRID = "#dbe4ee"
SLATE = "#48627b"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "axes.labelcolor": NAVY,
    "axes.titlecolor": NAVY,
    "text.color": NAVY,
    "xtick.color": SLATE,
    "ytick.color": SLATE,
    "figure.facecolor": "white",
})


def save(fig, name):
    fig.savefig(IMAGES / name, dpi=200, facecolor="white")
    plt.close(fig)


def horizontal_bars(series, title, axis_label, filename, colors=BLUE, labels=None):
    fig, ax = plt.subplots(figsize=(8, 4.2), layout="constrained")
    bars = ax.barh(series.index, series, color=colors, height=0.58, zorder=2)
    ax.bar_label(bars, labels=labels, padding=6, color=NAVY, weight="bold")
    ax.invert_yaxis()
    ax.set_xlim(0, series.max() * (1.31 if labels else 1.17))
    ax.set_title(title, loc="left", pad=16, weight="bold")
    ax.set_xlabel(axis_label, loc="right")
    ax.grid(axis="x", color=GRID, zorder=0)
    ax.tick_params(axis="both", length=0)
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    save(fig, filename)


def join_counts(matched_count, unmatched_count):
    fig, ax = plt.subplots(figsize=(8, 3.1), layout="constrained")
    labels = ["Left join", "Inner join"]
    kept = ax.barh(labels, [matched_count, matched_count], color=BLUE, height=0.42)
    unknown = ax.barh(labels, [unmatched_count, 0], left=matched_count, color=AMBER, height=0.42)
    ax.bar_label(kept, label_type="center", color="white", weight="bold")
    ax.annotate(str(unmatched_count), xy=(matched_count + unmatched_count / 2, 0),
                xytext=(11, 13), textcoords="offset points", ha="left", va="bottom",
                weight="bold", arrowprops={"arrowstyle": "-", "color": SLATE, "lw": 1})
    ax.invert_yaxis()
    ax.set_xlim(0, (matched_count + unmatched_count) * 1.17)
    ax.set_title("A left join keeps shipments with unknown codes", loc="left", weight="bold", pad=14)
    ax.set_xlabel("Shipment rows", loc="right")
    ax.legend([kept, unknown], ["Catalog match", "No catalog match"], loc="lower left",
              bbox_to_anchor=(0, -0.35), ncols=2, frameon=False, fontsize=10)
    ax.tick_params(axis="both", length=0)
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.set_axisbelow(True)
    ax.grid(axis="x", color=GRID)
    save(fig, "02_join_audit.png")


def channel_comparison(wide):
    fig, ax = plt.subplots(figsize=(8, 4.3), layout="constrained")
    positions = range(len(wide))
    for channel, offset, color in [("Home", -0.19, TEAL), ("Store", 0.19, BLUE)]:
        bars = ax.bar([x + offset for x in positions], wide[channel], width=0.34, label=channel, color=color, zorder=2)
        ax.bar_label(bars, padding=5, weight="bold")
    ax.set_xticks(positions, wide.index)
    ax.set_ylim(0, wide.to_numpy().max() * 1.27)
    ax.set_ylabel("Packs")
    ax.set_title("Packs by category and channel", loc="left", weight="bold", pad=16)
    ax.legend(loc="upper right", ncols=2, frameon=False)
    ax.grid(axis="y", color=GRID)
    ax.tick_params(axis="both", length=0)
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    save(fig, "03_category_by_channel.png")


def coverage(reported, unassigned):
    total = reported + unassigned
    fig, ax = plt.subplots(figsize=(8, 2.5), layout="constrained")
    ax.barh([0], [reported], height=0.35, color=BLUE)
    ax.barh([0], [unassigned], height=0.35, left=reported, color=AMBER)
    ax.text(reported / 2, 0, f"{reported:,} in named categories",
            ha="center", va="center", color="white", weight="bold")
    ax.annotate(f"{unassigned:,} unassigned", (reported + unassigned / 2, 0.16),
                (total, 0.51), ha="right", va="bottom", weight="bold",
                arrowprops={"arrowstyle": "-", "color": SLATE, "lw": 1})
    ax.text(0, -0.42, f"{total:,} packs in the full log", va="center", color=SLATE)
    ax.set_xlim(0, total * 1.04)
    ax.set_ylim(-0.65, 0.83)
    ax.set_title("The report accounts for every logged pack", loc="left", weight="bold", pad=10)
    ax.set_axis_off()
    save(fig, "05_report_coverage.png")


def main():
    IMAGES.mkdir(exist_ok=True)
    shipments = pd.read_csv(DATA / "shipments.csv")
    catalog = pd.read_csv(DATA / "product_catalog.csv")
    linked = shipments.merge(catalog, on="product_code", how="left",
                             validate="many_to_one", indicator=True)
    matched = linked.loc[linked["_merge"].eq("both")]
    unmatched = linked.loc[linked["_merge"].eq("left_only")]

    by_product = shipments.groupby("product_code")["units"].sum().sort_values(ascending=False)
    horizontal_bars(by_product, "Pack volume by product code", "Packs",
                    "01_packs_by_product.png")
    join_counts(len(matched), len(unmatched))

    wide = matched.pivot_table(index="category", columns="channel", values="units",
                              aggfunc="sum", fill_value=0)
    channel_comparison(wide)

    report = matched.groupby("category", as_index=False)["units"].sum().sort_values(
        ["units", "category"], ascending=[False, True]
    ).set_index("category")
    reported = report["units"].sum()
    labels = [f"{units:,}  ({units / reported:.1%})" for units in report["units"]]
    rank_colors = [BLUE] + [PALE_BLUE] * (len(report) - 1)
    horizontal_bars(report["units"], "Category ranking by matched pack volume", "Packs",
                    "04_ranked_categories.png", colors=rank_colors, labels=labels)
    coverage(reported, unmatched["units"].sum())


if __name__ == "__main__":
    main()
