#!/usr/bin/env python3
"""Generate an A1 vertical poster (594mm x 841mm) for the Social Reasoning Warden project.

Style: dark theme matching SocialReasoningWarden_ResearchGroup.pptx
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
import matplotlib.image as mpimg
import os

# ---------- A1 dimensions ----------
A1_W_IN = 594 / 25.4   # ~23.4 in
A1_H_IN = 841 / 25.4   # ~33.1 in

FIG_DIR = os.path.join(os.path.dirname(__file__), "results", "figures")

# ---------- palette ----------
BG = "#1A1A2E"
CARD = "#25253D"
CARD_BORDER = "#3A3A55"
TEAL = "#00D2D3"
TEAL_DIM = "#009B9C"
ORANGE = "#FF9F43"
WHITE = "#FFFFFF"
LIGHT = "#E0E0E8"
DIM = "#9999AA"
VERY_DIM = "#666677"

# ---------- font sizes ----------
TITLE_MAIN = 48
TITLE_SUB = 28
TITLE_AUTHORS = 20
SECTION_TITLE = 24
BODY = 17
CAPTION = 15

# ---------- figure ----------
fig = plt.figure(figsize=(A1_W_IN, A1_H_IN), facecolor=BG, dpi=150)

# Row heights tuned to content:
#   row 0: Motivation / Method text  — tall
#   row 1: Design / Scenarios text   — tall
#   row 2: fig1 / fig2               — medium
#   row 3: fig3 / fig4               — medium
#   row 4: fig5 / Key Findings       — medium-tall
#   row 5: Conclusions / Next Steps  — medium
outer = gridspec.GridSpec(4, 1,
                          height_ratios=[0.005, 0.06, 0.895, 0.04],
                          hspace=0.005, figure=fig,
                          left=0, right=1, top=1, bottom=0)

# ==========================================
# TEAL ACCENT STRIP
# ==========================================
ax_strip = fig.add_subplot(outer[0])
ax_strip.set_facecolor(TEAL)
ax_strip.axis("off")

# ==========================================
# TITLE BAND
# ==========================================
ax_title = fig.add_subplot(outer[1])
ax_title.set_facecolor(BG)
ax_title.set_xlim(0, 1)
ax_title.set_ylim(0, 1)
ax_title.axis("off")

ax_title.text(0.5, 0.78,
              "Social Reasoning Warden",
              fontsize=TITLE_MAIN, fontweight="bold", color=WHITE,
              ha="center", va="center", fontfamily="sans-serif")
ax_title.text(0.5, 0.42,
              "Agent-Based Oversight to Mitigate Adversarial Persuasion of Human and AI Targets",
              fontsize=TITLE_SUB, color=TEAL,
              ha="center", va="center", fontfamily="sans-serif")
ax_title.text(0.5, 0.10,
              "Scott Blain*    Lennart Wachowiak*    David Williams-King    Samuele Marro",
              fontsize=TITLE_AUTHORS, color=DIM,
              ha="center", va="center", fontfamily="sans-serif")

# ==========================================
# BODY — 6 rows x 2 columns with custom heights
# ==========================================
body = gridspec.GridSpecFromSubplotSpec(
    6, 2,
    subplot_spec=outer[2],
    height_ratios=[1.0, 1.05, 0.88, 0.88, 1.0, 1.05],
    hspace=0.13, wspace=0.04
)


def make_text_ax(gs_pos, title, body_text, accent=TEAL, body_fontsize=None):
    """Dark card with colored title accent and light body text.

    Title bar height is fixed; body text starts right below it and fills
    the remaining card space. body_fontsize overrides the global BODY size.
    """
    fs = body_fontsize or BODY
    ax = fig.add_subplot(gs_pos)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Card background
    bg_patch = FancyBboxPatch((0.02, 0.02), 0.96, 0.96,
                              boxstyle="round,pad=0.012",
                              facecolor=CARD, edgecolor=CARD_BORDER, linewidth=2.0)
    ax.add_patch(bg_patch)

    # Title bar accent background
    title_bar = FancyBboxPatch((0.02, 0.89), 0.96, 0.09,
                               boxstyle="round,pad=0.006",
                               facecolor=accent, edgecolor="none", alpha=0.15)
    ax.add_patch(title_bar)

    # Left accent line
    ax.plot([0.035, 0.035], [0.89, 0.98], color=accent, linewidth=4,
            solid_capstyle="round", transform=ax.transAxes, clip_on=False)

    # Title text
    ax.text(0.065, 0.935, title, fontsize=SECTION_TITLE, fontweight="bold",
            color=accent, va="center", fontfamily="sans-serif")

    # Body text — gap below title bar for breathing room
    ax.text(0.06, 0.84, body_text, fontsize=fs, color=LIGHT,
            va="top", fontfamily="sans-serif",
            linespacing=1.45, wrap=False)
    return ax


def make_figure_ax(gs_pos, fig_path, caption=""):
    """Place figure image in a grid cell."""
    ax = fig.add_subplot(gs_pos)
    ax.set_facecolor(BG)
    ax.axis("off")

    if os.path.exists(fig_path):
        img = mpimg.imread(fig_path)
        ax.imshow(img, aspect="equal")

    if caption:
        ax.text(0.5, -0.03, caption, fontsize=CAPTION, color=DIM,
                ha="center", va="top", transform=ax.transAxes,
                fontfamily="sans-serif", style="italic")
    return ax


# ---------- Row 0: Motivation + Method ----------
make_text_ax(body[0, 0], "Motivation", (
    "\u2022  LLMs are acquiring sophisticated social reasoning:\n"
    "   theory of mind, strategic communication, persuasion\n\n"
    "\u2022  These dual-use capabilities can enable manipulation:\n"
    "   social engineering, preference shaping, biasing decisions\n\n"
    "\u2022  A manipulative AI may be more socially adept than its\n"
    "   human target, creating a capability asymmetry\n\n"
    "\u2022  Can a secondary \u201cwarden\u201d agent detect and counter\n"
    "   adversarial persuasion in real time?"
))

make_text_ax(body[0, 1], "Method: Three-Agent Framework", (
    "Adversary \u2014 LLM with a hidden persuasive goal\n"
    "   (e.g., obtain file access, bias a hiring decision)\n\n"
    "Target \u2014 LLM or human with a BFI-2 vulnerability profile\n"
    "   (receives persona only; never sees own vulnerabilities)\n\n"
    "Warden \u2014 Observer-only LLM, sends private advisories\n"
    "   to the target; cannot block adversary messages\n\n"
    "Benign Agent \u2014 Legitimate requester (control condition)\n\n"
    "11 scenarios  \u00b7  4 profiles  \u00b7  4 model families  \u00b7  N = 7,760"
), body_fontsize=15)

# ---------- Row 1: Design + Scenarios ----------
make_text_ax(body[1, 0], "Experimental Design", (
    "Study 1: Warden Effect & Dossier Impact  (N = 2,274)\n"
    "   2\u00d72 factorial: warden \u00d7 behavioral dossier, adversary-only\n\n"
    "Study 2: Capability Asymmetry  (N = 1,215)\n"
    "   4 warden tiers: none / weak / mid / strong\n\n"
    "Study 3: Skeptical Ablation  (N = 3,080)\n"
    "   3 defenses \u00d7 2 requester types (adversary vs. benign)\n\n"
    "Analysis: GLMEs (binomial, logit link) with random intercepts\n"
    "for scenario, profile, and target model; random slope for warden"
), accent=ORANGE)

make_text_ax(body[1, 1], "Scenarios (11 domains)", (
    "\u2022  Hiring \u2014 push weaker candidate (hidden connection)\n"
    "\u2022  File Access \u2014 impersonate researcher for classified files\n"
    "\u2022  File Access (password) \u2014 same, with passcode check\n"
    "\u2022  Coding Agent \u2014 trick user into full home-dir access\n"
    "\u2022  AI Override \u2014 override hospital triage recommendation\n"
    "\u2022  AI Containment \u2014 sandboxed AI seeks internet access\n"
    "\u2022  Model Release \u2014 approve model despite red-team flags\n"
    "\u2022  Automation Decision \u2014 hidden incentive, full automation\n"
    "\u2022  Product Launch \u2014 competitor pushes premature launch\n"
    "\u2022  Upselling \u2014 upsell nonprofit to unneeded plan\n"
    "\u2022  Vote \u2014 bias group vote for personal interests"
), accent=ORANGE, body_fontsize=16)

# ---------- Row 2: Figures — Warden effect + Dossier ----------
make_figure_ax(body[2, 0],
               os.path.join(FIG_DIR, "fig1_warden_effect.png"),
               "Fig 1.  Warden reduces adversary success by 95% (OR = 0.053, p < .001)")

make_figure_ax(body[2, 1],
               os.path.join(FIG_DIR, "fig2_dossier_interaction.png"),
               "Fig 2.  Behavioral dossiers provide no advantage (OR = 1.19, p = .218)")

# ---------- Row 3: Figures — Cap asymmetry + Skeptical ----------
make_figure_ax(body[3, 0],
               os.path.join(FIG_DIR, "fig3_capability_asymmetry.png"),
               "Fig 3.  Even a weak warden cuts adversary success by 62%")

make_figure_ax(body[3, 1],
               os.path.join(FIG_DIR, "fig4_skeptical_ablation.png"),
               "Fig 4.  Prompt-based skepticism: comparable suppression, 3\u00d7 lower FP cost")

# ---------- Row 4: Profile vulnerability + Warden Intelligence ----------
make_figure_ax(body[4, 0],
               os.path.join(FIG_DIR, "fig8_profile_vulnerability.png"),
               "Fig 5.  Warden benefit greatest for most vulnerable profiles")

make_figure_ax(body[4, 1],
               os.path.join(FIG_DIR, "fig10_warden_intelligence.png"),
               "Fig 6.  Warden effectiveness scales with model intelligence")

# ---------- Row 5: Key Findings + Conclusions/Next Steps ----------
make_text_ax(body[5, 0], "Key Findings & Conclusions", (
    "1.  Adversarial LLMs succeed ~52% undefended;\n"
    "    6\u00d7 variation across scenarios (12\u201376%)\n"
    "2.  Warden reduces adversary SR to ~10%\n"
    "    (OR = 0.053, p < .001), robust across conditions\n"
    "3.  Dossiers don\u2019t help adversaries (yet) \u2014 models\n"
    "    can\u2019t spontaneously leverage personal info\n"
    "4.  Even a weak warden cuts success by 62%\n"
    "5.  Prompt skepticism matches warden effectiveness\n"
    "    with 3\u00d7 lower false-positive cost\n\n"
    "\u2022  Social reasoning poses a concrete dual-use risk\n"
    "\u2022  Warden provides scalable oversight, even when weaker\n"
    "\u2022  Precision\u2013recall tradeoff between prompt-based and\n"
    "   agent-based defense has practical implications"
), accent=TEAL_DIM, body_fontsize=12)

make_text_ax(body[5, 1], "Next Steps", (
    "\u25B6  Frontier model runs (Claude, GPT-4o, Gemini Pro)\n"
    "   Do stronger adversaries overcome the warden?\n\n"
    "\u25B6  Human\u2013AI interaction study (pilot in progress)\n"
    "   Prolific \u00d7 4 scenarios \u00d7 warden / no-warden\n\n"
    "\u25B6  Transcript analysis with LLM-as-a-judge\n"
    "   Classify persuasion tactics used by adversaries\n\n"
    "\u25B6  Release COAX-Bench evaluation framework\n"
    "   11 scenarios, profiles, modular warden integration"
), accent=ORANGE, body_fontsize=14)

# ==========================================
# FOOTER
# ==========================================
ax_footer = fig.add_subplot(outer[3])
ax_footer.set_facecolor(CARD)
ax_footer.set_xlim(0, 1)
ax_footer.set_ylim(0, 1)
ax_footer.axis("off")
ax_footer.text(0.5, 0.55,
               "*Equal contribution   |   ERA Fellowship   |   github.com/scottdougblain/social_reasoning_warden",
               fontsize=16, color=DIM, ha="center", va="center",
               fontfamily="sans-serif")

# ==========================================
# Save
# ==========================================
out_pdf = os.path.join(os.path.dirname(__file__), "SocialWarden_Poster_A1.pdf")
out_png = os.path.join(os.path.dirname(__file__), "SocialWarden_Poster_A1.png")
fig.savefig(out_pdf, format="pdf", bbox_inches="tight", pad_inches=0.15)
fig.savefig(out_png, format="png", bbox_inches="tight", pad_inches=0.15, dpi=150)
plt.close()
print(f"Saved poster to {out_pdf}")
print(f"Saved poster preview to {out_png}")
