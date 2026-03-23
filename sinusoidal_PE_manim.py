from manim import *
import numpy as np

# ── Constants ─────────────────────────────────────────────────────────
D_SIN = 6
LAMBDA_MIN = 0.001
LAMBDA_MAX = 10000

# Casanovo wavelength formula (matches make_wavelength_list in 03_Casanovo.ipynb):
#   λ_i = (λ_min / 2π) × (λ_max / λ_min)^(i / (d_sin - 1))
#
# For d_sin = 6, λ_min = 0.001, λ_max = 10000:
#   λ₀ ≈ 0.000159  λ₁ ≈ 0.003998  λ₂ ≈ 0.100420
#   λ₃ ≈ 2.522436  λ₄ ≈ 63.360724  λ₅ ≈ 1591.549431
#
# sin(600 / λ_i) for i=1..5:
#   [0.424, -0.392, -0.781, -0.045, 0.368]
# (λ₀ gives ≈ 0.000 since 600/λ₀ = 1,200,000π)

WAVELENGTHS = np.array([
    (LAMBDA_MIN / (2 * np.pi)) * (LAMBDA_MAX / LAMBDA_MIN) ** (i / (D_SIN - 1))
    for i in range(D_SIN)
])

WAVE_COLORS = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE]

BASE_X_RANGE = [0, 1000, 100]
BASE_WINDOW = BASE_X_RANGE[1] - BASE_X_RANGE[0]
WINDOW_PERIODS = 4


def sin_enc(wi, x):
    return np.sin(x / WAVELENGTHS[wi])


class SinusoidalPE(MovingCameraScene):
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

        # ── Transition: spectrum → zoomed-in wave axes ───────────────
        axes_pos = spectrum_ax.get_center()

        wave_ax = Axes(
            x_range=BASE_X_RANGE,
            y_range=[-1.5, 1.5, 1],
            x_length=10, y_length=3,
            axis_config={"include_tip": False},
        ).move_to(axes_pos)

        self.play(
            FadeOut(spectrum_ax), FadeOut(int_lbl), FadeOut(mz_lbl),
            FadeOut(dot_600), FadeOut(lbl_600), FadeOut(bar_600),
            Create(wave_ax),
        )
        self.camera.frame.set_width(wave_ax.get_width())
        self.camera.frame.move_to(wave_ax.get_center())

        formula_lbl = MathTex(
            r"\sin\!\left(\frac{\mathrm{m/z}}{\lambda_i}\right)",
            font_size=32,
        ).next_to(question, DOWN, buff=0.4)
        self.play(FadeIn(formula_lbl))

        # ── Draw waves: fastest → slowest, zooming via camera ───────
        zoom_waves = VGroup()
        zoom_dots  = VGroup()
        y_vals     = []

        lambda_lbl = MathTex(
            rf"\lambda_{{0}}",
            font_size=30,
        ).next_to(formula_lbl, RIGHT, buff=1.5)

        mz_part  = Text("(600, ", font_size=24).next_to(formula_lbl, DOWN, buff=0.3)
        val_part = Text("0.000)", font_size=24).next_to(mz_part, RIGHT, buff=0.1)

        self.play(FadeIn(lambda_lbl), FadeIn(mz_part), FadeIn(val_part))

        def _window_for_wavelength(wl, center_x=600.0):
            period = 2 * np.pi * wl
            window = WINDOW_PERIODS * period
            if window >= BASE_WINDOW:
                return BASE_X_RANGE[0], BASE_X_RANGE[1]
            left = center_x - window / 2
            right = center_x + window / 2
            if left < BASE_X_RANGE[0]:
                right += BASE_X_RANGE[0] - left
                left = BASE_X_RANGE[0]
            if right > BASE_X_RANGE[1]:
                left -= right - BASE_X_RANGE[1]
                right = BASE_X_RANGE[1]
            return left, right

        def _step_for_window(wl, left, right):
            period = 2 * np.pi * wl
            window = right - left
            step = min(window / 600, period / 80)
            step = min(step, window / 300)
            step = max(step, window / 5000)
            return step

        base_width = wave_ax.get_width()
        base_center = wave_ax.get_center()
        focus_center = wave_ax.c2p(600, 0)

        for idx in range(D_SIN):
            color = WAVE_COLORS[idx]
            wl    = WAVELENGTHS[idx]

            left, right = _window_for_wavelength(wl)
            window = right - left
            target_width = base_width * (window / BASE_WINDOW)
            target_center = base_center if window >= BASE_WINDOW else focus_center

            self.play(
                FadeOut(zoom_waves), FadeOut(zoom_dots),
                self.camera.frame.animate.set_width(target_width).move_to(target_center),
                run_time=1.5,
            )
            zoom_waves = VGroup()
            zoom_dots  = VGroup()

            # ── Plot the wave ──
            step = _step_for_window(wl, left, right)

            wave = wave_ax.plot(
                lambda x, _wl=wl: np.sin(x / _wl),
                x_range=[left, right, step],
                color=color,
                stroke_width=2,
                use_smoothing=False,
            )

            y_val = np.sin(600.0 / wl)
            y_vals.append(y_val)

            dot = Dot(wave_ax.c2p(600, y_val), color=color, radius=0.06)

            # Format wavelength for display
            if wl < 0.01:
                wl_str = f"{wl:.6f}"
            elif wl < 1:
                wl_str = f"{wl:.4f}"
            else:
                wl_str = f"{wl:.1f}"

            new_lambda_lbl = MathTex(
                rf"\lambda_{{{idx}}} = {wl_str}",
                font_size=28,
            ).next_to(formula_lbl, RIGHT, buff=1.5)

            display_y    = 0.0 if abs(y_val) < 1e-4 else y_val
            new_val_part = Text(
                f"{display_y:.3f})", font_size=24, color=color,
            ).next_to(mz_part, RIGHT, buff=0.1)

            highlight_circle = Circle(
                radius=0.15, color=YELLOW, stroke_width=3,
            ).move_to(dot.get_center())

            self.play(
                Create(wave),
                FadeIn(dot),
                Transform(lambda_lbl, new_lambda_lbl),
                FadeOut(val_part,     shift=UP * 0.2),
                FadeIn(new_val_part,  shift=UP * 0.2),
                Succession(
                    FadeIn(highlight_circle,  scale=0.5),
                    FadeOut(highlight_circle, scale=1.5),
                ),
                Flash(new_val_part, color=color,  line_length=0.1, flash_radius=0.3),
                Flash(dot,          color=YELLOW, line_length=0.1, flash_radius=0.2),
                run_time=2.0,
            )
            val_part = new_val_part
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
            FadeOut(lambda_lbl), FadeOut(mz_part), FadeOut(val_part),
            FadeOut(formula_lbl), FadeOut(wave_ax),
            FadeOut(question),
        )
        self.play(Write(vec))
        self.play(FadeIn(conclusion))
        self.wait(2)
