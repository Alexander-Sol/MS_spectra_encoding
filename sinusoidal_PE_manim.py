from manim import *
import numpy as np

# ── Constants ─────────────────────────────────────────────────────────
# Target values at m/z = 600 from the "Low-Dimensional Numerical Example"
# in 03_Casanovo.ipynb (λ0..λ5). We build visually nice waves that hit these
# exact values at x=600, even if the periods are "fake."
TARGET_VALUES_600 = np.array([-0.000, 0.364, -0.782, -0.973, -0.059, -0.588])
D_SIN = len(TARGET_VALUES_600)

# Choose visually reasonable periods (shortest still visible, then longer).
PERIODS = np.logspace(np.log10(10), np.log10(10000.0), num=D_SIN)
WAVELENGTHS = PERIODS / (2 * np.pi)

def _phase_for_value(y, wl, x0=600.0):
    base = np.arcsin(np.clip(y, -1.0, 1.0))
    phase = base - (x0 / wl)
    return (phase + np.pi) % (2 * np.pi) - np.pi

PHASES = np.array([_phase_for_value(y, wl) for y, wl in zip(TARGET_VALUES_600, WAVELENGTHS)])

WAVE_COLORS = [PURPLE, RED, ORANGE, YELLOW, GREEN, BLUE]
WAVE_X_RANGE = [0, 1000, 100]


def sin_enc(wi, x):
    return np.sin(x / WAVELENGTHS[wi] + PHASES[wi])


class SinusoidalPE(Scene):
    def construct(self):
        self._scene_1()

    # ── Scene 1 ── The Question ───────────────────────────────────────
    def _scene_1(self):
        spectrum_ax = Axes(
            x_range=[0, 1000, 100], y_range=[0, 100, 10],
            x_length=10, y_length=5,
            axis_config={"include_tip": True},
        ).shift(DOWN * 0.3)

        mz_lbl  = Text("m/z",       font_size=24).next_to(spectrum_ax.x_axis, DOWN,  buff=0.2)
        int_lbl = Text("Intensity", font_size=24).next_to(spectrum_ax.y_axis, LEFT, buff=0.2)

        # Realistic-looking spectrum
        np.random.seed(43)
        peak_positions = np.random.uniform(100, 900, 40)
        peak_heights   = np.random.uniform(20, 95, 40)

        # Force a prominent peak at 600 m/z
        peak_positions = np.append(peak_positions, 600)
        peak_heights   = np.append(peak_heights,   95)

        bars = VGroup()
        for x_pos, height in zip(peak_positions, peak_heights):
            bar = Line(
                start=spectrum_ax.c2p(x_pos, 0),
                end=spectrum_ax.c2p(x_pos, height),
                color=WHITE, stroke_width=2,
            )
            bars.add(bar)

        self.play(Create(spectrum_ax), Write(mz_lbl), Write(int_lbl))
        self.play(Create(bars), run_time=1.5)
        self.wait(1)

        # Highlight the 600 m/z bar
        bar_600  = bars[-1]
        dot_600  = Dot(spectrum_ax.c2p(600, 95), color=YELLOW, radius=0.08)
        lbl_600  = Text("m/z = 600", font_size=22, color=YELLOW) \
                       .next_to(dot_600, UP, buff=0.2)
        self.play(
            bar_600.animate.set_color(YELLOW).set_stroke(width=4),
            FadeIn(dot_600), Write(lbl_600),
        )

        question = Text(
            "How does the model know this peak is at m/z = 600?",
            font_size=28,
        ).to_edge(UP, buff=0.3)

        others = VGroup(*[b for b in bars if b != bar_600])
        self.play(Write(question), FadeOut(others, run_time=1.5))
        self.wait(1)

        # ── Transition: spectrum → wave axes ─────────────────────────
        axes_pos = spectrum_ax.get_center()

        wave_ax = Axes(
            x_range=WAVE_X_RANGE,
            y_range=[-1.5, 1.5, 1],
            x_length=10, y_length=3,
            axis_config={"include_tip": False},
        ).move_to(axes_pos)

        x_labels = VGroup(
            MathTex("0", font_size=24).next_to(wave_ax.c2p(0, 0), DOWN),
            MathTex("1000", font_size=24).next_to(wave_ax.c2p(1000, 0), DOWN),
        )
        y_labels = VGroup(
            MathTex("-1", font_size=24).next_to(wave_ax.c2p(0, -1), LEFT),
            MathTex("1", font_size=24).next_to(wave_ax.c2p(0, 1), LEFT),
        )

        self.play(
            FadeOut(spectrum_ax), FadeOut(int_lbl), FadeOut(mz_lbl),
            FadeOut(dot_600), FadeOut(lbl_600),
            Create(wave_ax),
            Write(x_labels), Write(y_labels),
        )
        wl0 = WAVELENGTHS[0]
        y0 = np.sin(600.0 / wl0 + PHASES[0])

        # Build formula from stable parts so only the λ index updates.
        def _frac_mz(idx):
            tex = rf"\frac{{\mathrm{{m/z}}}}{{\lambda_{{{idx}}}}}"
            return MathTex(
                tex,
                font_size=28,
                substrings_to_isolate=[rf"\lambda_{{{idx}}}"],
            )

        def _frac_600(idx):
            tex = rf"\frac{{600}}{{\lambda_{{{idx}}}}}"
            return MathTex(
                tex,
                font_size=28,
                substrings_to_isolate=[rf"\lambda_{{{idx}}}"],
            )

        left_open = MathTex(r"\sin\!\left(", font_size=28)
        left_frac = _frac_mz(0)
        left_close = MathTex(r"\right)", font_size=28)
        arrow = MathTex(r"\Rightarrow", font_size=28)
        right_open = MathTex(r"\sin\!\left(", font_size=28)
        right_frac = _frac_600(0)
        right_close = MathTex(r"\right)", font_size=28)
        equals = MathTex(r"=", font_size=28)
        y_tracker = ValueTracker(0.0)

        def _bound_decimal(font_size):
            dn = DecimalNumber(
                0.0,
                num_decimal_places=3,
                include_sign=True,
                font_size=font_size,
            )
            dn.add_updater(lambda m: m.set_value(y_tracker.get_value()))
            return dn

        y_num = _bound_decimal(32)
        formula_group = VGroup(
            left_open, left_frac, left_close,
            arrow,
            right_open, right_frac, right_close,
            equals, y_num,
        ).arrange(RIGHT, buff=0.1)
        formula_group.next_to(question, DOWN, buff=0.4, aligned_edge=LEFT)
        self.play(FadeIn(formula_group))

        # ── Draw waves: fastest → slowest ──────────────────────────
        zoom_waves = VGroup()
        zoom_dots  = VGroup()
        y_vals     = []

        mz_part = Text("(600, ", font_size=24)
        val_part = _bound_decimal(28)
        rparen = Text(")", font_size=24)
        point_group = VGroup(mz_part, val_part, rparen).arrange(RIGHT, buff=0.05)
        point_group.next_to(formula_group, DOWN, buff=0.3, aligned_edge=LEFT)

        self.play(FadeIn(point_group))

        for idx in range(D_SIN):
            color = WAVE_COLORS[idx]
            wl    = WAVELENGTHS[idx]
            self.play(FadeOut(zoom_waves), FadeOut(zoom_dots), run_time=0.6)
            zoom_waves = VGroup()
            zoom_dots  = VGroup()

            # ── Plot the wave ──
            period = 2 * np.pi * wl
            full_window = WAVE_X_RANGE[1] - WAVE_X_RANGE[0]
            step = min(full_window / 800, period / 80)
            step = max(step, full_window / 5000)

            wave = wave_ax.plot(
                lambda x, _wl=wl, _ph=PHASES[idx]: np.sin(x / _wl + _ph),
                x_range=[WAVE_X_RANGE[0], WAVE_X_RANGE[1], step],
                color=color,
                stroke_width=2,
                use_smoothing=False,
            )

            y_val = np.sin(600.0 / wl + PHASES[idx])

            dot = Dot(wave_ax.c2p(600, y_val), color=color, radius=0.06)

            display_y    = TARGET_VALUES_600[idx]
            y_vals.append(display_y)
            display_idx = idx
            new_left_frac = _frac_mz(display_idx).move_to(left_frac)
            new_right_frac = _frac_600(display_idx).move_to(right_frac)

            left_lambda = new_left_frac.get_parts_by_tex(
                rf"\lambda_{{{display_idx}}}"
            )[0]
            right_lambda = new_right_frac.get_parts_by_tex(
                rf"\lambda_{{{display_idx}}}"
            )[0]
            left_lambda.set_color(color)
            right_lambda.set_color(color)


            highlight_circle = Circle(
                radius=0.15, color=YELLOW, stroke_width=3,
            ).move_to(dot.get_center())

            y_num.set_color(color)
            val_part.set_color(color)

            self.play(
                Create(wave),
                FadeIn(dot),
                FadeTransform(left_frac, new_left_frac),
                FadeTransform(right_frac, new_right_frac),
                y_tracker.animate.set_value(display_y),
                Succession(
                    FadeIn(highlight_circle,  scale=0.5),
                    FadeOut(highlight_circle, scale=1.5),
                ),
                Flash(val_part,     color=color,  line_length=0.1, flash_radius=0.3),
                Flash(dot,          color=YELLOW, line_length=0.1, flash_radius=0.2),
                run_time=2.0,
            )
            formula_group.remove(left_frac, right_frac)
            left_frac = new_left_frac
            right_frac = new_right_frac
            formula_group.add(left_frac, right_frac)
            zoom_waves.add(wave)
            zoom_dots.add(dot)
            self.wait(0.2)

        self.wait(2)

        # ── Final: collapse to vector form ────────────────────────────
        values_str = " \\\\ ".join(
            f"{0.0 if abs(y) < 1e-4 else y:.3f}" for y in y_vals
        )
        vec = MathTex(
            r"\mathbf{p}(600) = \begin{bmatrix}" + values_str + r"\end{bmatrix}",
            font_size=32,
        ).move_to(wave_ax.get_center())

        conclusion = Text(
            "Together, these values form the positional encoding vector.",
            font_size=26,
        ).next_to(vec, DOWN, buff=0.4)

        self.play(
            FadeOut(zoom_waves), FadeOut(zoom_dots),
            FadeOut(formula_group),
            FadeOut(point_group),
            FadeOut(wave_ax),
            FadeOut(question),
            FadeOut(bar_600)
        )
        self.play(Write(vec))
        self.play(FadeIn(conclusion))
        self.wait(2)
