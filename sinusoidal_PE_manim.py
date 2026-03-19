from manim import *
import numpy as np

# ── Casanovo positional-encoding parameters ───────────────────────────────────
D_SIN      = 256
LAMBDA_MIN = 0.001
LAMBDA_MAX = 10_000

_i = np.arange(D_SIN)
WAVELENGTHS = (LAMBDA_MIN / (2 * np.pi)) * (LAMBDA_MAX / LAMBDA_MIN) ** (_i / (D_SIN - 1))
PERIODS     = LAMBDA_MIN * (LAMBDA_MAX / LAMBDA_MIN) ** (_i / (D_SIN - 1))

# Five representative waves: (wavelength_index, approx_period_Th, label, color)
WAVES = [
    (44,  0.016, "~0.016 Th",  RED),
    (87,  0.25,  "~0.25 Th",   GREEN),
    (131, 3.98,  "~3.98 Th",   PURPLE),
    (175, 63.1,  "~63 Th",     YELLOW),
    (219, 1000., "~1000 Th",   BLUE_C),
]


def sin_enc(wave_idx: int, x):
    """sin(x / lambda_i) — the positional encoding for one dimension."""
    return float(np.sin(x / WAVELENGTHS[wave_idx]))


# ─────────────────────────────────────────────────────────────────────────────

class SinusoidalPE(MovingCameraScene):
    """
    Seven-act animated explainer for sinusoidal positional encoding
    as used in Casanovo (λ_min=0.001, λ_max=10 000, d=512).

    Replaces static images in 03_Casanovo.ipynb sections 3.6 – 3.9.
    """

    # ── utilities ─────────────────────────────────────────────────────────────

    def clear_scene(self, rt: float = 0.5):
        mobs = list(self.mobjects)
        if mobs:
            self.play(FadeOut(*mobs), run_time=rt)
        self.clear()

    def _reset_camera(self, rt: float = 1.8):
        self.play(
            self.camera.frame.animate
                .set_width(self._orig_w)
                .move_to(ORIGIN),
            run_time=rt,
        )

    def _make_axes(self):
        ax = Axes(
            x_range=[0, 1500, 200],
            y_range=[-1.4, 1.4, 0.5],
            x_length=11,
            y_length=3.8,
        ).shift(DOWN * 0.3)
        xl = ax.get_x_axis_label("m/z", direction=RIGHT)
        yl = ax.get_y_axis_label(r"\sin(m/\lambda_i)")
        return ax, VGroup(ax, xl, yl)

    # ── Act 1: Spectrum Peak ──────────────────────────────────────────────────

    def act1_spectrum_peak(self):
        ax = Axes(
            x_range=[0, 1200, 200], y_range=[0, 1.1, 0.5],
            x_length=9, y_length=3.2,
        ).shift(DOWN * 0.6)
        xl = ax.get_x_axis_label("m/z")
        yl = ax.get_y_axis_label("Intensity")

        mz_vals  = [126, 300, 450, 600, 780, 950, 1100]
        int_vals = [0.40, 0.55, 0.30, 0.90, 0.45, 0.60, 0.35]

        bars = VGroup(*[
            Line(ax.c2p(mz, 0), ax.c2p(mz, h), color=WHITE, stroke_width=3)
            for mz, h in zip(mz_vals, int_vals)
        ])

        self.play(Create(VGroup(ax, xl, yl)), run_time=0.8)
        self.play(LaggedStart(*[Create(b) for b in bars], lag_ratio=0.12))

        # Highlight the peak at m/z = 600
        highlight = Line(ax.c2p(600, 0), ax.c2p(600, 0.9),
                         color=YELLOW, stroke_width=7)
        peak_dot  = Dot(ax.c2p(600, 0.9), color=YELLOW, radius=0.10)
        peak_lbl  = MathTex(r"m/z = 600", font_size=26, color=YELLOW)
        peak_lbl.next_to(ax.c2p(600, 0.9), UP, buff=0.15)
        self.play(Create(highlight), FadeIn(peak_dot, peak_lbl))

        question = Text(
            "How does a neural network know this peak is at m/z = 600?",
            font_size=25, color=WHITE,
        ).to_edge(UP, buff=0.35)
        self.play(Write(question), run_time=1.5)
        self.wait(2.5)
        self.clear_scene()

    # ── Act 2: Formula + Wavelength Range ────────────────────────────────────

    def act2_formula(self):
        f_eq = MathTex(
            r"f_i(m_j) = \sin\!\left(\frac{m_j}{\lambda_i}\right)",
            font_size=46,
        ).shift(UP * 1.9)
        lam_eq = MathTex(
            r"\lambda_i \;=\; \frac{\lambda_{\min}}{2\pi}"
            r"\cdot\left(\frac{\lambda_{\max}}{\lambda_{\min}}"
            r"\right)^{\!\frac{i}{\,d_{\sin}-1\,}}",
            font_size=36,
        ).next_to(f_eq, DOWN, buff=0.5)
        vals = MathTex(
            r"\lambda_{\min}=0.001,\quad\lambda_{\max}=10{,}000,\quad d=512",
            font_size=28, color=YELLOW,
        ).next_to(lam_eq, DOWN, buff=0.45)

        self.play(Write(f_eq), run_time=1.2)
        self.play(Write(lam_eq), run_time=1.5)
        self.play(FadeIn(vals))
        self.wait(0.6)

        caption = Text(
            "256 wavelengths span 0.001 → 10,000 exponentially",
            font_size=22, color=TEAL_B,
        ).next_to(vals, DOWN, buff=0.4)
        self.play(Write(caption))

        # Log-scale number line showing all 256 periods
        log_line = NumberLine(
            x_range=[-3, 4, 1], length=9,
            color=GRAY, include_numbers=False,
        ).to_edge(DOWN, buff=0.5)

        tick_lbls = VGroup(*[
            MathTex(f"10^{{{e}}}", font_size=16, color=GRAY)
              .next_to(log_line.n2p(e), DOWN, buff=0.08)
            for e in range(-3, 5)
        ])

        self.play(Create(log_line), FadeIn(tick_lbls))

        # 256 dots appearing one by one
        dots = VGroup(*[
            Dot(log_line.n2p(np.log10(PERIODS[i])), radius=0.035, color=YELLOW)
            for i in range(D_SIN)
        ])
        self.play(
            LaggedStart(*[FadeIn(d) for d in dots], lag_ratio=0.015),
            run_time=1.8,
        )
        self.wait(2.0)
        self.clear_scene()

    # ── Act 3: Five Sine Waves (macro view) ───────────────────────────────────

    def act3_five_waves(self):
        ax, ax_grp = self._make_axes()
        self.play(Create(ax_grp), run_time=0.9)

        title = Text("5 representative wavelengths (out of 256)",
                     font_size=24, color=WHITE).to_edge(UP, buff=0.25)
        self.play(FadeIn(title))

        legend = VGroup()
        wave_mobs = []

        for wi, period, lbl_txt, color in WAVES:
            # Step size: ~40 samples per period; fine waves alias visually
            step = max(period / 40.0, 0.5)
            wave = ax.plot(
                lambda x, wi=wi: sin_enc(wi, x),
                x_range=[0, 1500, step],
                color=color, stroke_width=2,
                use_smoothing=(period > 1.0),
            )
            wave_mobs.append(wave)

            row = VGroup(
                Line(ORIGIN, RIGHT * 0.45, color=color, stroke_width=3),
                Text(lbl_txt, font_size=18, color=color),
            ).arrange(RIGHT, buff=0.12)
            legend.add(row)

        legend.arrange(DOWN, buff=0.22, aligned_edge=LEFT)
        legend.to_edge(RIGHT, buff=0.25).shift(UP * 0.3)

        for wave, row in zip(wave_mobs, legend):
            self.play(Create(wave), FadeIn(row), run_time=0.9)

        footnote = Text(
            "Red & green cycle too fast to see at this scale →",
            font_size=17, color=GRAY,
        ).to_edge(DOWN, buff=0.18)
        self.play(FadeIn(footnote))
        self.wait(1.8)

        # Persist for Acts 4 – 6
        self._ax         = ax
        self._ax_grp     = ax_grp
        self._wave_mobs  = wave_mobs
        self._legend     = legend
        self._title3     = title
        self._footnote3  = footnote

    # ── Act 4: Zoom to Reveal Fine Waves ─────────────────────────────────────

    def act4_zoom(self):
        ax = self._ax
        self.play(FadeOut(self._footnote3))

        # High-resolution fine-wave plots (revealed only at zoom scale)
        hi_res = VGroup(*[
            ax.plot(
                lambda x, wi=wi: sin_enc(wi, x),
                x_range=[594, 608, 0.0004],
                color=color, stroke_width=1.8,
                use_smoothing=False,
            )
            for wi, _, _, color in WAVES[:2]   # red & green only
        ])
        self.add(hi_res)

        zoom_txt = Text("Zooming in to m/z ∈ [594, 608]…",
                        font_size=22, color=YELLOW).to_edge(UP, buff=0.25)
        self.play(FadeIn(zoom_txt))

        zoom_center = ax.c2p(601, 0)
        zoom_width  = ax.c2p(608, 0)[0] - ax.c2p(594, 0)[0]
        self.play(
            self.camera.frame.animate
                .set_width(zoom_width * 1.75)
                .move_to(zoom_center),
            run_time=2.5,
        )
        self.play(FadeOut(zoom_txt))

        # Caption scaled to the current (zoomed) frame
        fw = self.camera.frame.get_width()
        caption = Text("Fine waves cycle many times per m/z unit",
                       font_size=22).set(width=fw * 0.75)
        caption.move_to(zoom_center + UP * self.camera.frame.get_height() * 0.37)
        self.play(FadeIn(caption))
        self.wait(2.5)
        self.play(FadeOut(caption))

        self._reset_camera()
        self._hi_res = hi_res

    # ── Act 5: Encoding m/z = 600 ─────────────────────────────────────────────

    def act5_encode_600(self):
        ax = self._ax

        # Vertical dashed line at 600
        vline = DashedLine(
            ax.c2p(600, -1.3), ax.c2p(600, 1.3),
            color=WHITE, stroke_width=2, dash_length=0.14,
        )
        lbl = MathTex(r"m/z = 600", font_size=24, color=WHITE)
        lbl.next_to(ax.c2p(600, 1.3), UP, buff=0.10)
        self.play(Create(vline), FadeIn(lbl))
        self.wait(0.3)

        # Dot on each wave at x = 600
        dots = VGroup()
        for wi, _, _, color in WAVES:
            y = sin_enc(wi, 600)
            d = Dot(ax.c2p(600, y), color=color, radius=0.10)
            dots.add(d)
            self.play(FadeIn(d), run_time=0.32)

        # Encoding vector panel
        entries = VGroup(*[
            Text(
                f"period ≈ {period:>7.3g} Th  →  {sin_enc(wi, 600):+.3f}",
                font_size=18, color=color,
            )
            for wi, period, _, color in WAVES
        ])
        entries.arrange(DOWN, buff=0.16, aligned_edge=LEFT)
        more   = Text("⋮  (256 values total)", font_size=16, color=GRAY)
        header = Text("Encoding of  m/z = 600", font_size=20, color=YELLOW)
        panel  = VGroup(header, entries, more).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
        panel.to_edge(RIGHT, buff=0.22).shift(UP * 0.4)

        self.play(FadeIn(panel), run_time=1.0)
        self.wait(2.0)

        self._vline600 = vline
        self._lbl600   = lbl
        self._dots600  = dots
        self._panel600 = panel

    # ── Act 6: Fine vs. Coarse  (600 vs. 601) ────────────────────────────────

    def act6_compare_601(self):
        ax = self._ax
        self.play(FadeOut(self._panel600))

        # Dashed line at 601
        vline2 = DashedLine(
            ax.c2p(601, -1.3), ax.c2p(601, 1.3),
            color=YELLOW, stroke_width=2, dash_length=0.14,
        )
        lbl2 = MathTex(r"m/z = 601", font_size=24, color=YELLOW)
        lbl2.next_to(ax.c2p(601, 1.3), UP, buff=0.10)
        self.play(Create(vline2), FadeIn(lbl2))

        dots2 = VGroup(*[
            Dot(ax.c2p(601, sin_enc(wi, 601)), color=color, radius=0.10)
            for wi, _, _, color in WAVES
        ])
        self.play(FadeIn(dots2), run_time=0.8)
        self.wait(0.5)

        # Zoom into [597, 605] so both lines and all 5 dot pairs are visible
        center  = ax.c2p(601, 0)
        frame_w = ax.c2p(605, 0)[0] - ax.c2p(597, 0)[0]
        self.play(
            self.camera.frame.animate
                .set_width(frame_w * 2.0)
                .move_to(center),
            run_time=2.0,
        )
        self.wait(0.5)

        # Sensitivity table sized to current frame
        rows_data = [
            (RED,    "~0.016 Th", "~63 cycles  →  huge shift"),
            (GREEN,  "~0.25 Th",  "~4 cycles   →  large shift"),
            (PURPLE, "~3.98 Th",  "~0.25 cycles → moderate"),
            (YELLOW, "~63 Th",    "~0.016 cycles → tiny"),
            (BLUE_C, "~1000 Th",  "~0.001 cycles → almost 0"),
        ]
        table_rows = VGroup(*[
            Text(f"Period {p:>10}  |  {desc}", font_size=16, color=c)
            for c, p, desc in rows_data
        ])
        table_rows.arrange(DOWN, buff=0.08, aligned_edge=LEFT)
        hdr = Text("1 Th step:  600 → 601", font_size=17, color=WHITE)
        table = VGroup(hdr, table_rows).arrange(DOWN, buff=0.12, aligned_edge=LEFT)
        table.set(width=self.camera.frame.get_width() * 0.44)
        table.move_to(
            self.camera.frame.get_right() + LEFT * table.get_width() * 0.55
        )

        self.play(FadeIn(table))
        self.wait(3.5)

        self._reset_camera()

    # ── Act 7: Why Sine AND Cosine ────────────────────────────────────────────

    def act7_rotation(self):
        self.clear_scene()

        title = Text("Why sine AND cosine?", font_size=36, color=YELLOW)
        title.to_edge(UP, buff=0.35)
        self.play(FadeIn(title))

        # Unit circle centred at left side
        cx, cy = -3.2, -0.2
        circle  = Circle(radius=2.0, color=BLUE_B, stroke_width=2).move_to([cx, cy, 0])
        x_arrow = Arrow([cx - 0.3, cy, 0], [cx + 2.7, cy, 0],
                        buff=0, color=GRAY, stroke_width=2)
        y_arrow = Arrow([cx, cy - 0.3, 0], [cx, cy + 2.7, 0],
                        buff=0, color=GRAY, stroke_width=2)
        cos_lbl = MathTex(r"\cos", font_size=20, color=TEAL_B).next_to([cx+2.7, cy, 0], RIGHT, buff=0.06)
        sin_lbl = MathTex(r"\sin", font_size=20, color=RED).next_to([cx, cy+2.7, 0], UP, buff=0.06)

        self.play(Create(circle), Create(x_arrow), Create(y_arrow),
                  FadeIn(cos_lbl, sin_lbl))

        # Rotating point driven by ValueTracker (m/z value)
        tracker = ValueTracker(0.0)
        wi_circ = 131   # purple wavelength, period ≈ 3.98 Th

        def get_pt():
            angle = tracker.get_value() / WAVELENGTHS[wi_circ]
            return np.array([cx + 2.0 * np.cos(angle),
                             cy + 2.0 * np.sin(angle), 0])

        dot      = always_redraw(lambda: Dot(get_pt(), color=YELLOW, radius=0.13))
        sin_line = always_redraw(lambda: DashedLine(
            [get_pt()[0], cy, 0], get_pt(), color=RED, stroke_width=2))
        cos_line = always_redraw(lambda: DashedLine(
            [cx, get_pt()[1], 0], get_pt(), color=TEAL_B, stroke_width=2))

        self.add(sin_line, cos_line, dot)

        # Explanation panel on the right
        expl = VGroup(
            MathTex(
                r"\text{PE}_i(m) = \begin{bmatrix}\sin(m/\lambda_i)\\\cos(m/\lambda_i)\end{bmatrix}",
                font_size=26,
            ),
            Text(
                "Shifting  m → m + k\nrotates this point by k/λᵢ,\nregardless of starting position.",
                font_size=20, color=GRAY,
            ),
            MathTex(
                r"A^{(k)}\,\mathrm{PE}(m) \;=\; \mathrm{PE}(m+k)",
                font_size=24, color=TEAL_B,
            ),
        ).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        expl.to_edge(RIGHT, buff=0.45).shift(DOWN * 0.3)
        self.play(FadeIn(expl))

        self.play(tracker.animate.set_value(600), run_time=5, rate_func=linear)
        self.wait(0.8)
        self.play(tracker.animate.set_value(1200), run_time=4, rate_func=linear)
        self.wait(1.0)

        # ── Closing slide ─────────────────────────────────────────────────────
        self.clear_scene()

        closing = VGroup(
            Text("One peak  ↦  512 numbers", font_size=34, color=YELLOW),
            Text("Nearby peaks  ↦  similar encodings", font_size=28, color=WHITE),
            Text(
                "The Transformer now attends to peaks\n"
                "based on their m/z relationships.",
                font_size=22, color=GRAY,
            ),
        ).arrange(DOWN, buff=0.55)

        self.play(Write(closing[0]), run_time=1.0)
        self.play(FadeIn(closing[1]))
        self.play(FadeIn(closing[2]))
        self.wait(3.0)

    # ── Entry point ───────────────────────────────────────────────────────────

    def construct(self):
        self._orig_w = self.camera.frame.get_width()

        self.act1_spectrum_peak()
        self.act2_formula()
        self.act3_five_waves()
        self.act4_zoom()
        self.act5_encode_600()
        self.act6_compare_601()
        self.act7_rotation()
