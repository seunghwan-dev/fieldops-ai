"""
Figure generation for FieldOps-AI dummy papers.

WHY: High-quality figures (300 DPI) for VLM extraction testing.
     VLM must read axis labels, annotations, and trend patterns.
RISK: Low-resolution or unclear labels -> VLM extraction failure.
INTERVIEW: "Designed figures specifically to test VLM's ability to
           interpret scientific charts -- not just OCR text."
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "figures")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_fig1_decomposition():
    """
    Figure 1: Temperature vs Decomposition Rate (sigmoid curve).

    WHY: Tests VLM extraction of trend patterns and annotations.
         Sharp rise at ~180C, thermal runaway zone above 200C.
    """
    plt.rcParams["font.family"] = "serif"
    fig, ax = plt.subplots(figsize=(8, 5))

    temp = np.linspace(150, 250, 500)
    # Sigmoid centered at 200C with steepness factor
    rate = 100 / (1 + np.exp(-0.15 * (temp - 200)))

    ax.plot(temp, rate, "b-", linewidth=2, label="Decomposition Rate")

    # Shaded thermal runaway zone above 200C
    ax.axvspan(200, 250, alpha=0.15, color="red", label="Thermal runaway zone")

    # Annotation arrow at inflection point (~180C)
    rate_at_180 = 100 / (1 + np.exp(-0.15 * (180 - 200)))
    ax.annotate(
        "Inflection point\n(~180\u00b0C)",
        xy=(180, rate_at_180),
        xytext=(155, 55),
        fontsize=10,
        arrowprops=dict(arrowstyle="->", color="black", lw=1.5),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", edgecolor="black"),
    )

    # Annotation for thermal runaway zone
    ax.annotate(
        "Thermal runaway\nzone (>200\u00b0C)",
        xy=(220, 85),
        fontsize=10,
        color="darkred",
        fontweight="bold",
        ha="center",
    )

    ax.set_xlabel("Temperature (\u00b0C)", fontsize=12)
    ax.set_ylabel("Decomposition Rate (%)", fontsize=12)
    ax.set_title("Figure 1: Temperature vs Decomposition Rate of Material X", fontsize=13)
    ax.set_xlim(150, 250)
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", fontsize=10)

    output_path = os.path.join(OUTPUT_DIR, "fig1_decomposition.png")
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Figure 1 saved: {output_path}")


def generate_fig2_rpm_vs_temp():
    """
    Figure 2: RPM vs Discharge Temperature for different jacket temps.

    WHY: Plots actual data from Report-A Table 4.
         Tests VLM extraction of multi-line charts with safety threshold.
    """
    plt.rcParams["font.family"] = "serif"
    fig, ax = plt.subplots(figsize=(8, 5))

    # Data from Report-A Table 4
    rpm_jacket25 = [30, 60, 90, 120]
    temp_jacket25 = [68, 112, 158, 175]

    rpm_jacket100 = [90, 120]
    temp_jacket100 = [182, 205]

    rpm_jacket150 = [90, 120]
    temp_jacket150 = [198, 228]

    ax.plot(rpm_jacket25, temp_jacket25, "bo-", linewidth=2, markersize=8,
            label="Jacket = 25\u00b0C")
    ax.plot(rpm_jacket100, temp_jacket100, "gs-", linewidth=2, markersize=8,
            label="Jacket = 100\u00b0C")
    ax.plot(rpm_jacket150, temp_jacket150, "r^-", linewidth=2, markersize=8,
            label="Jacket = 150\u00b0C")

    # Safety limit line
    ax.axhline(y=200, color="red", linestyle="--", linewidth=1.5, alpha=0.8)
    ax.text(35, 203, "Safety Limit (200\u00b0C)", color="red", fontsize=10,
            fontweight="bold")

    ax.set_xlabel("RPM", fontsize=12)
    ax.set_ylabel("Discharge Temperature (\u00b0C)", fontsize=12)
    ax.set_title("Figure 2: RPM vs Discharge Temperature by Jacket Temperature",
                 fontsize=13)
    ax.set_xlim(20, 130)
    ax.set_ylim(40, 250)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper left", fontsize=10)

    output_path = os.path.join(OUTPUT_DIR, "fig2_rpm_vs_temp.png")
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] Figure 2 saved: {output_path}")


if __name__ == "__main__":
    print("=== FieldOps-AI: Generating figures ===")
    generate_fig1_decomposition()
    generate_fig2_rpm_vs_temp()
    print("=== Done ===")
