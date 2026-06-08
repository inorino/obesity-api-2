"""
test_api.py v3 — 6場景 × 16週 × 2端點
- 改善男/女、惡化男/女、穩定健康、穩定高風險
- 雙Y軸：Behav_15=藍色、Core_6=橘色（固定，不隨場景變色）
- BMI 跨越25毛點：紅色大圓點 + 紅色標注
- 新增圖型：熱圖 / 斜率圖 / 差值圖 / 散點圖
"""
import base64, io, sys, time
from datetime import date
sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import requests
from scipy.signal import savgol_filter

plt.rcParams["font.family"] = ["Microsoft JhengHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

API   = "https://obesity-api-2-2ro4.onrender.com"
N     = 16
WEEKS = list(range(1, N + 1))

# ── 模型固定色 ─────────────────────────────────────────────
COL_B15 = "#2563eb"   # Behav_15feat 永遠藍色
COL_C6  = "#f97316"   # Core_6feat  永遠橘色

# ════════════════════════════════════════════════════════════
# 共用行為週序列
# ════════════════════════════════════════════════════════════

def _bmi(kg, cm):
    h = cm / 100
    return round(kg / h / h, 1)

# 改善型 core6（16週，S曲線）：差 → 好
IMPROVE_C6 = [
    dict(sleep_hours=5.0, smoking_status=1, drank_any=1, drinks_per_week=20, exercised=0, general_health=5),
    dict(sleep_hours=5.0, smoking_status=1, drank_any=1, drinks_per_week=19, exercised=0, general_health=5),
    dict(sleep_hours=5.5, smoking_status=1, drank_any=1, drinks_per_week=17, exercised=0, general_health=5),
    dict(sleep_hours=5.5, smoking_status=2, drank_any=1, drinks_per_week=15, exercised=0, general_health=5),
    dict(sleep_hours=6.0, smoking_status=2, drank_any=1, drinks_per_week=13, exercised=0, general_health=4),
    dict(sleep_hours=6.0, smoking_status=2, drank_any=1, drinks_per_week=11, exercised=1, general_health=4),
    dict(sleep_hours=6.5, smoking_status=2, drank_any=1, drinks_per_week=9,  exercised=1, general_health=4),
    dict(sleep_hours=6.5, smoking_status=3, drank_any=1, drinks_per_week=7,  exercised=1, general_health=3),
    dict(sleep_hours=7.0, smoking_status=3, drank_any=1, drinks_per_week=6,  exercised=1, general_health=3),
    dict(sleep_hours=7.0, smoking_status=3, drank_any=1, drinks_per_week=5,  exercised=1, general_health=3),
    dict(sleep_hours=7.5, smoking_status=4, drank_any=1, drinks_per_week=4,  exercised=1, general_health=2),
    dict(sleep_hours=7.5, smoking_status=4, drank_any=1, drinks_per_week=3,  exercised=1, general_health=2),
    dict(sleep_hours=8.0, smoking_status=4, drank_any=0, drinks_per_week=2,  exercised=1, general_health=2),
    dict(sleep_hours=8.0, smoking_status=4, drank_any=0, drinks_per_week=1,  exercised=1, general_health=1),
    dict(sleep_hours=8.0, smoking_status=4, drank_any=0, drinks_per_week=0,  exercised=1, general_health=1),
    dict(sleep_hours=8.0, smoking_status=4, drank_any=0, drinks_per_week=0,  exercised=1, general_health=1),
]

# 惡化型 core6（16週，S曲線）：好 → 差
WORSEN_C6 = [
    dict(sleep_hours=8.0, smoking_status=4, drank_any=0, drinks_per_week=0,  exercised=1, general_health=1),
    dict(sleep_hours=8.0, smoking_status=4, drank_any=0, drinks_per_week=1,  exercised=1, general_health=1),
    dict(sleep_hours=7.5, smoking_status=4, drank_any=1, drinks_per_week=2,  exercised=1, general_health=2),
    dict(sleep_hours=7.5, smoking_status=4, drank_any=1, drinks_per_week=3,  exercised=1, general_health=2),
    dict(sleep_hours=7.0, smoking_status=3, drank_any=1, drinks_per_week=5,  exercised=1, general_health=2),
    dict(sleep_hours=7.0, smoking_status=3, drank_any=1, drinks_per_week=7,  exercised=0, general_health=3),
    dict(sleep_hours=6.5, smoking_status=3, drank_any=1, drinks_per_week=9,  exercised=0, general_health=3),
    dict(sleep_hours=6.5, smoking_status=2, drank_any=1, drinks_per_week=11, exercised=0, general_health=3),
    dict(sleep_hours=6.0, smoking_status=2, drank_any=1, drinks_per_week=13, exercised=0, general_health=4),
    dict(sleep_hours=6.0, smoking_status=2, drank_any=1, drinks_per_week=14, exercised=0, general_health=4),
    dict(sleep_hours=5.5, smoking_status=1, drank_any=1, drinks_per_week=16, exercised=0, general_health=4),
    dict(sleep_hours=5.5, smoking_status=1, drank_any=1, drinks_per_week=17, exercised=0, general_health=5),
    dict(sleep_hours=5.0, smoking_status=1, drank_any=1, drinks_per_week=18, exercised=0, general_health=5),
    dict(sleep_hours=5.0, smoking_status=1, drank_any=1, drinks_per_week=19, exercised=0, general_health=5),
    dict(sleep_hours=4.5, smoking_status=1, drank_any=1, drinks_per_week=20, exercised=0, general_health=5),
    dict(sleep_hours=4.5, smoking_status=1, drank_any=1, drinks_per_week=21, exercised=0, general_health=5),
]

# ════════════════════════════════════════════════════════════
# 場景定義
# ════════════════════════════════════════════════════════════
SCENARIOS = {
    "改善男": {
        "emoji": "💪", "subtitle": "肥胖男性 → 16週全面改善",
        "color": "#16a34a", "group": "improve",
        "desc": "男性 178cm，BMI 31.6（肥胖）出發，16 週減重並改善全部行為習慣",
        "persona": dict(sex="男", height_cm=178, sex_code=1,
                        age_group=6, education=4, income=4, employment=1),
        "weights_kg": [100,99,98,97,95,92.5,90,87.5,84.5,81.5,79,77,75,74,73,71.5],
        "diff_walking": 0, "depression": 0,
        "weeks_core6": IMPROVE_C6,
        "b15_delta": [(0,0)]*16,
    },
    "改善女": {
        "emoji": "🌸", "subtitle": "過重女性 → 16週全面改善",
        "color": "#059669", "group": "improve",
        "desc": "女性 162cm，BMI 28.2（過重）出發，16 週減重並改善行為習慣",
        "persona": dict(sex="女", height_cm=162, sex_code=0,
                        age_group=4, education=5, income=5, employment=1),
        "weights_kg": [74,72.5,71,69.5,68,66.5,65.5,64,63,61.5,60,58.5,57.5,57,56.5,56],
        "diff_walking": 0, "depression": 0,
        "weeks_core6": IMPROVE_C6,
        "b15_delta": [(0,0)]*16,
    },
    "惡化男": {
        "emoji": "📉", "subtitle": "正常男性 → 16週逐步惡化",
        "color": "#dc2626", "group": "worsen",
        "desc": "男性 176cm，BMI 22.6（正常）出發，16 週增重並逐步放棄健康習慣",
        "persona": dict(sex="男", height_cm=176, sex_code=1,
                        age_group=3, education=5, income=4, employment=1),
        "weights_kg": [70,70.5,71,72,73,74,75,76,77,78.5,80,81.5,82.5,83.5,84.5,85.5],
        "diff_walking": 0, "depression": 0,
        "weeks_core6": WORSEN_C6,
        "b15_delta": [(0,0)]*16,
    },
    "惡化女": {
        "emoji": "⚠️", "subtitle": "正常女性 → 16週逐步惡化",
        "color": "#b91c1c", "group": "worsen",
        "desc": "女性 163cm，BMI 20.7（正常）出發，16 週增重並逐步惡化行為習慣",
        "persona": dict(sex="女", height_cm=163, sex_code=0,
                        age_group=3, education=5, income=4, employment=1),
        "weights_kg": [55,56.5,57.5,58.5,59.5,61,62.5,64,66,68,69.5,70.5,71.5,72,72.5,73],
        "diff_walking": 0, "depression": 0,
        "weeks_core6": WORSEN_C6,
        "b15_delta": [(0,0)]*16,
    },
    "穩定健康": {
        "emoji": "✅", "subtitle": "16週穩定健康",
        "color": "#2563eb", "group": "stable",
        "desc": "女性 160cm，BMI 21.5（正常），全程維持良好習慣，驗證低機率零波動",
        "persona": dict(sex="女", height_cm=160, sex_code=0,
                        age_group=3, education=6, income=6, employment=1),
        "weights_kg": [55.0] * N,
        "diff_walking": 0, "depression": 0,
        "weeks_core6": [dict(sleep_hours=7.5, smoking_status=4, drank_any=0,
                             drinks_per_week=0, exercised=1, general_health=1)] * N,
        "b15_delta": [(0, 0)] * N,
    },
    "穩定高風險": {
        "emoji": "🔴", "subtitle": "16週持續高風險",
        "color": "#f59e0b", "group": "stable",
        "desc": "男性 172cm，BMI 33.8（肥胖），全程維持不良習慣，驗證高機率零波動",
        "persona": dict(sex="男", height_cm=172, sex_code=1,
                        age_group=8, education=3, income=2, employment=7),
        "weights_kg": [100.0] * N,
        "diff_walking": 1, "depression": 1,
        "weeks_core6": [dict(sleep_hours=5.0, smoking_status=1, drank_any=1,
                             drinks_per_week=14, exercised=0, general_health=5)] * N,
        "b15_delta": [(0, 0)] * N,
    },
}

for sc in SCENARIOS.values():
    h = sc["persona"]["height_cm"]
    sc["bmi_list"] = [_bmi(w, h) for w in sc["weights_kg"]]

# ════════════════════════════════════════════════════════════
# API 呼叫
# ════════════════════════════════════════════════════════════

def call_api(endpoint, payload, retries=3):
    url = f"{API}/{endpoint}"
    for i in range(retries):
        try:
            r = requests.post(url, json=payload, timeout=60)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if i < retries - 1:
                time.sleep(3)
            else:
                print(f"  ERROR {url}: {e}")
                return None

# ════════════════════════════════════════════════════════════
# 收集結果
# ════════════════════════════════════════════════════════════
results = {}
for name, sc in SCENARIOS.items():
    p = sc["persona"]
    print(f"\n{'='*55}\nScenario: {sc['emoji']} {name}  ({p['sex']} {p['height_cm']}cm)")
    r_c6, r_b15 = [], []
    for wk in range(N):
        c6 = sc["weeks_core6"][wk]
        resp_c = call_api("predict/core6", c6)
        p_c = resp_c["probability"]["overweight_obese"] if resp_c else None
        r_c6.append(p_c)

        mh, ph = sc["b15_delta"][wk]
        b15 = {**c6,
               "sex": p["sex_code"], "age_group": p["age_group"],
               "education": p["education"], "income": p["income"],
               "employment": p["employment"],
               "diff_walking": sc["diff_walking"], "depression": sc["depression"],
               "mental_health_days": mh, "physical_health_days": ph}
        resp_b = call_api("predict/behav15", b15)
        p_b = resp_b["probability"]["overweight_obese"] if resp_b else None
        r_b15.append(p_b)

        c6_str  = f"{p_c:.4f}" if p_c is not None else "ERR"
        b15_str = f"{p_b:.4f}" if p_b is not None else "ERR"
        print(f"  W{wk+1:02d}  Core6={c6_str}  Behav15={b15_str}")

    results[name] = {**sc, "core6": r_c6, "behav15": r_b15}

# ════════════════════════════════════════════════════════════
# 工具函式
# ════════════════════════════════════════════════════════════

def sg_smooth(vals, window=7, poly=2):
    arr = np.array([v if v is not None else np.nan for v in vals], dtype=float)
    n_valid = int(np.sum(~np.isnan(arr)))
    w = window if (window <= n_valid and window % 2 == 1) else max(3, n_valid - (1 - n_valid % 2))
    if w < 3:
        return arr
    return savgol_filter(arr, window_length=w, polyorder=min(poly, w - 1))

def fig_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode()

BMI_BANDS = [(0, 18.5,"#dbeafe"),(18.5,25.0,"#dcfce7"),(25.0,30.0,"#fef9c3"),(30.0,45.0,"#fee2e2")]
BMI_YMIN, BMI_YMAX = 15, 42

def find_bmi25_crossing(bmi_list):
    """回傳 (interpolated_week_float, direction) 或 None"""
    for i in range(1, len(bmi_list)):
        prev, curr = bmi_list[i-1], bmi_list[i]
        if (prev > 25 >= curr) or (prev < 25 <= curr):
            frac = (25 - prev) / (curr - prev)
            return WEEKS[i-1] + frac * (WEEKS[i] - WEEKS[i-1]), "down" if prev > 25 else "up"
    return None, None

# ════════════════════════════════════════════════════════════
# 圖 1：個人雙Y軸圖（Behav_15=藍, Core_6=橘, BMI25毛點）
# ════════════════════════════════════════════════════════════

def make_dual_chart(name, data, mode="both"):
    show_b15 = mode in ("both", "b15")
    show_c6  = mode in ("both", "c6")
    bmi_list = data["bmi_list"]
    cross_w, cross_dir = find_bmi25_crossing(bmi_list)

    fig, ax1 = plt.subplots(figsize=(12, 5.2))
    ax2 = ax1.twinx()

    # ── 右軸：BMI ──
    for lo, hi, bg in BMI_BANDS:
        ax2.axhspan(max(lo, BMI_YMIN), min(hi, BMI_YMAX), alpha=0.13, color=bg, zorder=0)
    ax2.axhline(25.0, color="#d97706", lw=1.2, ls="-.", alpha=0.9, zorder=1)
    ax2.axhline(30.0, color="#b91c1c", lw=1.2, ls="-.", alpha=0.9, zorder=1)
    ax2.plot(WEEKS, bmi_list, "D-", color="#78716c", lw=1.8, ms=5,
             alpha=0.85, label="模擬 BMI（假設值）", zorder=3)

    # BMI 25 跨越毛點（紅色大圓點）
    if cross_w is not None:
        ax2.scatter([cross_w], [25], color="red", s=220, zorder=16,
                    edgecolors="darkred", linewidths=2, marker="o")
        arrow_x = min(cross_w + 1.8, N - 1)
        arrow_y = 27.5 if cross_dir == "up" else 22.5
        ax2.annotate(
            f"BMI 跨越 25！{'↑' if cross_dir=='up' else '↓'}",
            xy=(cross_w, 25),
            xytext=(arrow_x, arrow_y),
            fontsize=9, color="red", fontweight="bold",
            arrowprops=dict(arrowstyle="->", color="red", lw=1.8),
            bbox=dict(boxstyle="round,pad=0.3", fc="#fff0f0", ec="red", alpha=0.85),
            zorder=17
        )
        ax2.axvline(cross_w, color="red", lw=1.0, ls="--", alpha=0.35, zorder=4)

    ax2.set_ylabel("模擬 BMI（假設值）", fontsize=10, color="#6b7280")
    ax2.tick_params(axis="y", labelcolor="#6b7280", labelsize=9)
    ax2.set_ylim(BMI_YMIN, BMI_YMAX)
    ax2.text(N + 0.3, 25.4, "BMI 25", fontsize=7.5, color="#d97706", va="bottom", clip_on=False)
    ax2.text(N + 0.3, 30.4, "BMI 30", fontsize=7.5, color="#b91c1c", va="bottom", clip_on=False)

    # ── 左軸：機率 ──
    ax1.axhline(0.5, color="#94a3b8", lw=1.4, ls=":", zorder=2)
    ax1.fill_between(WEEKS, 0.5, 1.0, alpha=0.03, color="#ef4444", zorder=1)
    ax1.fill_between(WEEKS, 0.0, 0.5, alpha=0.03, color="#22c55e", zorder=1)

    if show_b15 and any(v is not None for v in data["behav15"]):
        ax1.plot(WEEKS, sg_smooth(data["behav15"]),
                 "-", color=COL_B15, lw=6, alpha=0.15, zorder=3)
        ax1.plot(WEEKS, data["behav15"], "o-", color=COL_B15,
                 lw=2.2, ms=7, zorder=5, label="Behav_15feat")
    if show_c6 and any(v is not None for v in data["core6"]):
        ax1.plot(WEEKS, sg_smooth(data["core6"]),
                 "--", color=COL_C6, lw=6, alpha=0.12, zorder=3)
        ax1.plot(WEEKS, data["core6"], "s--", color=COL_C6,
                 lw=2.0, ms=7, alpha=0.85, zorder=5, label="Core_6feat")

    ax1.set_xlabel("週次", fontsize=11)
    ax1.set_ylabel("Overweight+Obese 機率", fontsize=11)
    ax1.set_xlim(0.5, N + 0.8)
    ax1.set_ylim(-0.02, 1.05)
    ax1.set_xticks(WEEKS)
    ax1.set_xticklabels([f"W{w}" for w in WEEKS], fontsize=8.5)
    ax1.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax1.text(0.01, 0.52, "決策邊界 0.5", transform=ax1.get_yaxis_transform(),
             fontsize=8, color="#94a3b8", va="bottom")
    ax1.set_title(f"{data['emoji']} {name}　{data['subtitle']}",
                  fontsize=13, fontweight="bold", pad=10)

    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, fontsize=9, loc="upper right", framealpha=0.93)
    ax1.grid(axis="y", alpha=0.2)
    ax1.set_zorder(ax2.get_zorder() + 1)
    ax1.patch.set_visible(False)
    fig.tight_layout(rect=[0, 0, 0.95, 1])
    return fig_b64(fig)

# ════════════════════════════════════════════════════════════
# 圖 2：四場景整體比較折線圖
# ════════════════════════════════════════════════════════════

def make_cmp_chart(model="core6"):
    fig, ax = plt.subplots(figsize=(13, 5))
    for name, data in results.items():
        vals = data[model]
        ax.plot(WEEKS, sg_smooth(vals), "-", color=data["color"], lw=6, alpha=0.15, zorder=3)
        ax.plot(WEEKS, vals, "o-", color=data["color"], lw=2.5, ms=6,
                label=f"{data['emoji']} {name}", zorder=5)
    ax.axhline(0.5, color="#94a3b8", lw=1.5, ls=":", label="決策邊界 0.5", zorder=2)
    ax.fill_between(WEEKS, 0.5, 1.0, alpha=0.04, color="#ef4444")
    ax.fill_between(WEEKS, 0.0, 0.5, alpha=0.04, color="#22c55e")
    label = "Core_6feat（6特徵）" if model == "core6" else "Behav_15feat（15特徵）"
    ax.set_title(f"六場景 × 16週  OW+Obese 機率趨勢（{label}）",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("週次", fontsize=11)
    ax.set_ylabel("OW+Obese 機率", fontsize=11)
    ax.set_xlim(0.5, N + 0.5)
    ax.set_ylim(-0.02, 1.05)
    ax.set_xticks(WEEKS)
    ax.set_xticklabels([f"W{w}" for w in WEEKS], fontsize=9)
    ax.legend(fontsize=9, loc="center right", framealpha=0.93, ncol=1)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    return fig_b64(fig)

# ════════════════════════════════════════════════════════════
# 圖 3：機率熱圖 Heatmap
# ════════════════════════════════════════════════════════════

def make_heatmap():
    names = list(results.keys())
    fig, axes = plt.subplots(1, 2, figsize=(16, 4.5))
    fig.suptitle("OW+Obese 機率熱圖（每格 = 一週預測值）",
                 fontsize=13, fontweight="bold", y=1.02)

    for ax, model, title in zip(
        axes,
        ["core6", "behav15"],
        ["Core_6feat（6特徵）", "Behav_15feat（15特徵）"]
    ):
        matrix = np.array([
            [results[n][model][w] if results[n][model][w] is not None else np.nan
             for w in range(N)]
            for n in names
        ])
        im = ax.imshow(matrix, aspect="auto", cmap="RdYlGn_r", vmin=0, vmax=1)
        ax.set_xticks(range(N))
        ax.set_xticklabels([f"W{i+1}" for i in range(N)], fontsize=8)
        ax.set_yticks(range(len(names)))
        ax.set_yticklabels(
            [f"{results[n]['emoji']} {n}" for n in names], fontsize=9)
        ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
        plt.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
        # 每格數值
        for i in range(len(names)):
            for j in range(N):
                val = matrix[i, j]
                if not np.isnan(val):
                    clr = "white" if val > 0.65 or val < 0.25 else "#1a1a1a"
                    ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                            fontsize=6.5, color=clr)
        # BMI 25 crossing marker
        for i, n in enumerate(names):
            _, cross_dir = find_bmi25_crossing(results[n]["bmi_list"])
            if cross_dir:
                cross_wk, _ = find_bmi25_crossing(results[n]["bmi_list"])
                ax.axvline(cross_wk - 1, color="red", lw=1.5, ls="--", alpha=0.5)

    fig.tight_layout()
    return fig_b64(fig)

# ════════════════════════════════════════════════════════════
# 圖 4：斜率圖 Slope Chart（W1 → W16）
# ════════════════════════════════════════════════════════════

def make_slope_chart():
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), sharey=True)
    fig.suptitle("W1 vs W16：機率變化斜率圖",
                 fontsize=13, fontweight="bold", y=1.01)

    for ax, model, title in zip(
        axes,
        ["core6", "behav15"],
        ["Core_6feat", "Behav_15feat"]
    ):
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.axhline(0.5, color="#94a3b8", lw=1, ls=":", alpha=0.7)
        ax.set_xlim(-0.5, 1.5)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["W1（起始）", "W16（結束）"], fontsize=10)
        ax.set_ylabel("OW+Obese 機率", fontsize=10)
        ax.set_ylim(-0.05, 1.08)
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
        ax.fill_between([-0.5, 1.5], 0.5, 1.0, alpha=0.04, color="#ef4444")
        ax.fill_between([-0.5, 1.5], 0.0, 0.5, alpha=0.04, color="#22c55e")
        ax.grid(axis="y", alpha=0.2)

        for name, data in results.items():
            v1 = data[model][0]
            v16 = data[model][-1]
            if v1 is None or v16 is None:
                continue
            color = data["color"]
            ax.plot([0, 1], [v1, v16], "o-", color=color, lw=2.5, ms=9,
                    zorder=5, label=f"{data['emoji']} {name}")
            ax.text(-0.08, v1, f"{v1:.3f}", ha="right", va="center",
                    fontsize=8.5, color=color, fontweight="bold")
            ax.text(1.08, v16, f"{v16:.3f}", ha="left", va="center",
                    fontsize=8.5, color=color, fontweight="bold")
            delta = v16 - v1
            mid_x = 0.5
            mid_y = (v1 + v16) / 2
            ax.text(mid_x, mid_y + 0.025,
                    f"{'▼' if delta < 0 else '▲'}{abs(delta):.3f}",
                    ha="center", va="bottom", fontsize=8, color=color, alpha=0.85)

        ax.legend(fontsize=8.5, loc="center left", framealpha=0.9)
        ax.set_facecolor("#fafafa")

    fig.tight_layout()
    return fig_b64(fig)

# ════════════════════════════════════════════════════════════
# 圖 5：差值折線圖（Behav_15 − Core_6）
# ════════════════════════════════════════════════════════════

def make_diff_chart():
    fig, ax = plt.subplots(figsize=(13, 4.8))
    ax.axhline(0, color="#94a3b8", lw=1.2, ls="--", alpha=0.8)
    ax.fill_between(WEEKS, 0, 0.15, alpha=0.06, color="#3b82f6", zorder=1)
    ax.fill_between(WEEKS, -0.15, 0, alpha=0.04, color="#f97316", zorder=1)

    for name, data in results.items():
        diff = [
            (b - c) if (b is not None and c is not None) else np.nan
            for b, c in zip(data["behav15"], data["core6"])
        ]
        ax.plot(WEEKS, diff, "o-", color=data["color"], lw=2.0, ms=6,
                label=f"{data['emoji']} {name}", zorder=5)

    ax.set_title("Behav_15 − Core_6 機率差值（正值 = 加入人口統計後風險評估更高）",
                 fontsize=12, fontweight="bold")
    ax.set_xlabel("週次", fontsize=11)
    ax.set_ylabel("機率差值（Behav_15 − Core_6）", fontsize=11)
    ax.set_xlim(0.5, N + 0.5)
    ax.set_xticks(WEEKS)
    ax.set_xticklabels([f"W{w}" for w in WEEKS], fontsize=9)
    ax.legend(fontsize=9, loc="upper right", framealpha=0.93, ncol=2)
    ax.grid(axis="y", alpha=0.2)
    ax.text(0.01, 0.97, "Behav_15 > Core_6", transform=ax.transAxes,
            fontsize=9, color="#3b82f6", va="top", alpha=0.7)
    ax.text(0.01, 0.03, "Core_6 > Behav_15", transform=ax.transAxes,
            fontsize=9, color="#f97316", va="bottom", alpha=0.7)
    fig.tight_layout()
    return fig_b64(fig)

# ════════════════════════════════════════════════════════════
# 圖 6：散點圖（BMI × 機率）
# ════════════════════════════════════════════════════════════

def make_scatter():
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)
    fig.suptitle("模擬 BMI × 預測機率散點圖（每點 = 一場景一週）",
                 fontsize=13, fontweight="bold", y=1.01)

    for ax, model, title in zip(
        axes,
        ["core6", "behav15"],
        ["Core_6feat", "Behav_15feat"]
    ):
        ax.axvline(25, color="#d97706", lw=1.5, ls="-.", alpha=0.9, label="BMI 25 超重線")
        ax.axvline(30, color="#b91c1c", lw=1.5, ls="-.", alpha=0.9, label="BMI 30 肥胖線")
        ax.axhline(0.5, color="#94a3b8", lw=1.2, ls=":", alpha=0.8, label="決策邊界 0.5")
        ax.fill_between([25, 30], 0, 1.05, alpha=0.05, color="#f59e0b")
        ax.fill_between([30, 50], 0, 1.05, alpha=0.06, color="#ef4444")

        for name, data in results.items():
            xs, ys = [], []
            for w in range(N):
                bmi = data["bmi_list"][w]
                p = data[model][w]
                if p is not None:
                    xs.append(bmi)
                    ys.append(p)
            sc = ax.scatter(xs, ys, color=data["color"], s=55, alpha=0.75,
                            label=f"{data['emoji']} {name}", zorder=5, edgecolors="white",
                            linewidths=0.5)
            # 標出 W1 和 W16
            if xs:
                ax.annotate("W1", (xs[0], ys[0]), fontsize=7, color=data["color"],
                            xytext=(2, 3), textcoords="offset points")
                ax.annotate("W16", (xs[-1], ys[-1]), fontsize=7, color=data["color"],
                            xytext=(2, -8), textcoords="offset points")

        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.set_xlabel("模擬 BMI（假設值）", fontsize=10)
        if model == "core6":
            ax.set_ylabel("OW+Obese 機率", fontsize=10)
        ax.set_xlim(14, 40)
        ax.set_ylim(-0.02, 1.05)
        ax.legend(fontsize=8, loc="upper left", framealpha=0.9, ncol=1)
        ax.grid(alpha=0.18)
        ax.set_facecolor("#fafafa")

    fig.tight_layout()
    return fig_b64(fig)

# ════════════════════════════════════════════════════════════
# 生成所有圖表
# ════════════════════════════════════════════════════════════
print("\n\n生成圖表中...")

indiv_imgs = {}
for n, d in results.items():
    print(f"  [{n}] dual chart...", end=" ", flush=True)
    indiv_imgs[n] = {m: make_dual_chart(n, d, m) for m in ("both", "b15", "c6")}
    print("done")

print("  [比較] overview...", end=" ", flush=True)
cmp_c6  = make_cmp_chart("core6")
cmp_b15 = make_cmp_chart("behav15")
print("done")

print("  [熱圖] heatmap...", end=" ", flush=True)
img_heatmap = make_heatmap()
print("done")

print("  [斜率] slope...", end=" ", flush=True)
img_slope = make_slope_chart()
print("done")

print("  [差值] diff...", end=" ", flush=True)
img_diff = make_diff_chart()
print("done")

print("  [散點] scatter...", end=" ", flush=True)
img_scatter = make_scatter()
print("done")

# JS 資料物件
_js_parts = []
for idx, name in enumerate(results.keys()):
    imgs = indiv_imgs[name]
    _js_parts.append(
        f'  "sc{idx}":{{"both":"{imgs["both"]}","b15":"{imgs["b15"]}","c6":"{imgs["c6"]}"}}'
    )
_js_parts.append(f'  "_cmp":{{"c6":"{cmp_c6}","b15":"{cmp_b15}"}}')
JS_DATA = "{\n" + ",\n".join(_js_parts) + "\n}"

# ════════════════════════════════════════════════════════════
# HTML 元件
# ════════════════════════════════════════════════════════════
SMOKE  = {1:"每天",2:"偶爾",3:"已戒",4:"從不"}
HEALTH = {1:"非常好",2:"好",3:"普通",4:"差",5:"非常差"}

def bmi_cat(b):
    if b < 18.5: return "過輕","#3b82f6"
    if b < 25.0: return "正常","#16a34a"
    if b < 30.0: return "過重","#d97706"
    return "肥胖","#dc2626"

def prob_badge(p):
    if p is None:
        return '<span style="color:#9ca3af">N/A</span>'
    c = "#dc2626" if p >= 0.5 else "#16a34a"
    lbl = "OW+Obese" if p >= 0.5 else "Normal"
    return (f'<span style="color:{c};font-weight:700">{p:.3f}</span>'
            f'<small style="color:{c};margin-left:3px">({lbl})</small>')

def bmi_badge(b):
    cat, col = bmi_cat(b)
    is_cross_text = " ★" if abs(b - 25) < 0.5 else ""
    cross_style = ";background:#fee2e2;padding:0 3px;border-radius:3px" if is_cross_text else ""
    return (f'<span style="color:{col};font-weight:600{cross_style}">{b}{is_cross_text}</span>'
            f'<small style="color:{col};margin-left:3px">({cat})</small>')

def summary_rows(data):
    rows = ""
    for wk in range(N):
        p_c = data["core6"][wk]
        bg  = "#fff7f7" if (p_c or 0) >= 0.5 else "#f7fff7"
        rows += (
            f'<tr style="background:{bg}">'
            f'<td style="font-weight:600">W{wk+1}</td>'
            f'<td>{bmi_badge(data["bmi_list"][wk])}</td>'
            f'<td>{prob_badge(data["behav15"][wk])}</td>'
            f'<td>{prob_badge(p_c)}</td>'
            f'</tr>\n'
        )
    return rows

def detail_table_html(name, data):
    sc = SCENARIOS[name]
    rows = ""
    for wk in range(N):
        c6 = sc["weeks_core6"][wk]
        mh, ph = sc["b15_delta"][wk]
        bmi = sc["bmi_list"][wk]
        p_c = data["core6"][wk]
        bg = "#fff7f7" if (p_c or 0) >= 0.5 else "#f7fff7"
        rows += (
            f'<tr style="background:{bg}">'
            f'<td style="font-weight:600">W{wk+1}</td>'
            f'<td>{sc["weights_kg"][wk]}</td>'
            f'<td>{bmi_badge(bmi)}</td>'
            f'<td>{c6["sleep_hours"]}</td>'
            f'<td>{SMOKE[c6["smoking_status"]]}</td>'
            f'<td>{"是" if c6["drank_any"] else "否"}</td>'
            f'<td>{c6["drinks_per_week"]}</td>'
            f'<td>{"是" if c6["exercised"] else "否"}</td>'
            f'<td>{HEALTH[c6["general_health"]]}</td>'
            f'<td>{mh}</td><td>{ph}</td>'
            f'<td>{prob_badge(data["behav15"][wk])}</td>'
            f'<td>{prob_badge(p_c)}</td>'
            f'</tr>\n'
        )
    return f"""
<details style="margin-top:14px">
  <summary style="cursor:pointer;color:#2563eb;font-size:13px;font-weight:600;
                  padding:5px 0;user-select:none;list-style:none">
    ▶ 展開完整 16 週模擬輸入資料
  </summary>
  <div style="overflow-x:auto;margin-top:10px">
    <table class="dtbl">
      <thead><tr>
        <th>週</th><th>體重(kg)</th><th>BMI ⚠️</th>
        <th>睡眠(h)</th><th>吸菸</th><th>飲酒</th><th>杯/週</th>
        <th>運動</th><th>自評健康</th>
        <th>心理不適(天)</th><th>身體不適(天)</th>
        <th>Behav_15 機率</th><th>Core_6 機率</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
  <p style="font-size:11px;color:#9ca3af;margin:6px 0 0">
    ⚠️ BMI 為情境假設值，非模型輸出。★ 標記接近 BMI 25 臨界點。
  </p>
</details>"""

# ════════════════════════════════════════════════════════════
# 各場景 section
# ════════════════════════════════════════════════════════════
scenario_sections = ""
for idx, (name, data) in enumerate(results.items()):
    sc = SCENARIOS[name]
    p  = sc["persona"]
    skey = f"sc{idx}"
    scenario_sections += f"""
<div class="card" style="border-top:4px solid {data['color']}">
  <h3 style="color:{data['color']}">
    {sc['emoji']} {name}
    <span style="font-weight:400;font-size:12px;color:#6b7280;margin-left:10px">
      {p['sex']}性 · {p['height_cm']} cm ·
      起始 {sc['weights_kg'][0]} kg（BMI {sc['bmi_list'][0]}）
    </span>
  </h3>
  <p style="color:#6b7280;font-size:13px;margin:4px 0 12px">{data['desc']}</p>
  <div class="btn-grp" style="margin-bottom:14px">
    <span class="btn-lbl">顯示線條：</span>
    <button class="tbtn on" onclick="sw('img-{skey}','{skey}','both',this.parentElement)">
      兩線並排
    </button>
    <button class="tbtn" onclick="sw('img-{skey}','{skey}','b15',this.parentElement)">
      ● Behav_15feat（藍）
    </button>
    <button class="tbtn" onclick="sw('img-{skey}','{skey}','c6',this.parentElement)">
      ● Core_6feat（橘）
    </button>
  </div>
  <div style="display:grid;grid-template-columns:3fr 2fr;gap:22px;align-items:start">
    <img id="img-{skey}" src="{indiv_imgs[name]['both']}"
         style="width:100%;border-radius:8px;border:1px solid #e5e7eb">
    <table>
      <thead><tr>
        <th>週次</th><th>BMI ⚠️</th>
        <th style="color:{COL_B15}">● Behav_15</th>
        <th style="color:{COL_C6}">● Core_6</th>
      </tr></thead>
      <tbody>{summary_rows(data)}</tbody>
    </table>
  </div>
  {detail_table_html(name, data)}
</div>"""

# ════════════════════════════════════════════════════════════
# 最終 HTML
# ════════════════════════════════════════════════════════════
html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<title>Obesity Risk API — 場景測試報告 v3</title>
<style>
:root {{
  --navy: #1e3a5f; --blue: {COL_B15}; --orange: {COL_C6}; --green: #16a34a;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft JhengHei",sans-serif;
     background:#f1f5f9;color:#1a1a1a}}
.page{{max-width:1200px;margin:0 auto;padding:36px 24px}}
.hero{{background:linear-gradient(135deg,#0a1628 0%,#1d4ed8 100%);color:#fff;
       border-radius:14px;padding:30px 38px;margin-bottom:30px}}
.hero h1{{font-size:22px;font-weight:700;margin-bottom:10px}}
.meta{{font-size:13px;opacity:.88;line-height:2.4}}
.badge{{display:inline-block;background:rgba(255,255,255,.18);border-radius:20px;
        padding:2px 12px;font-size:12px;margin:2px 4px 2px 0}}
h2{{font-size:14px;color:#fff;padding:10px 20px;border-radius:8px;
    margin:30px 0 16px;letter-spacing:.5px}}
h3{{font-size:14px;color:#374151;margin-bottom:8px;font-weight:700}}
.card{{background:#fff;border-radius:12px;padding:24px 28px;
       box-shadow:0 1px 6px rgba(0,0,0,.07);margin-bottom:18px}}
table{{border-collapse:collapse;width:100%}}
th{{background:var(--navy);color:#fff;padding:8px 11px;
    text-align:left;font-size:11px;white-space:nowrap}}
td{{padding:7px 11px;border-bottom:1px solid #f1f5f9;font-size:12px;white-space:nowrap}}
tr:last-child td{{border-bottom:none}}
.dtbl th{{background:#374151}}
.hl{{background:#f0fdf4;border-left:4px solid var(--green);
     padding:12px 16px;border-radius:0 8px 8px 0;margin:14px 0;font-size:13px;line-height:1.7}}
.warn{{background:#fffbeb;border-left:4px solid #f59e0b;
       padding:12px 16px;border-radius:0 8px 8px 0;margin:14px 0;font-size:13px;line-height:1.7}}
img{{max-width:100%;height:auto;display:block}}
.btn-grp{{display:flex;align-items:center;gap:7px;flex-wrap:wrap}}
.btn-lbl{{font-size:12px;color:#6b7280;white-space:nowrap;margin-right:2px}}
.tbtn{{padding:5px 15px;border:1.5px solid #d1d5db;border-radius:20px;
       background:#f9fafb;color:#374151;font-size:12px;font-family:inherit;
       cursor:pointer;transition:all .15s ease;white-space:nowrap}}
.tbtn:hover{{border-color:var(--blue);color:var(--blue);background:#eff6ff}}
.tbtn.on{{background:var(--blue);border-color:var(--blue);color:#fff;font-weight:600}}
.legend-pill{{display:inline-flex;align-items:center;gap:5px;
              background:#f8fafc;border:1px solid #e2e8f0;
              padding:4px 12px;border-radius:20px;font-size:12px;margin:0 6px 6px 0}}
footer{{text-align:center;color:#9ca3af;font-size:12px;
        margin-top:52px;padding:18px 0;border-top:1px solid #e5e7eb}}
</style>
</head>
<body>
<div class="page">

<div class="hero">
  <h1>🏥 Obesity Risk API — 場景測試報告 v3</h1>
  <div class="meta">
    <span class="badge">API：{API}</span>
    <span class="badge">6 場景 × 16 週 × 2 端點 = 192 次預測</span>
    <span class="badge">BMI 25 毛點標紅</span>
    <span class="badge">熱圖 / 斜率圖 / 差值圖 / 散點圖</span>
    <br>
    <span class="legend-pill">
      <span style="display:inline-block;width:14px;height:3px;background:{COL_B15};border-radius:2px"></span>
      Behav_15feat（15特徵）
    </span>
    <span class="legend-pill">
      <span style="display:inline-block;width:14px;height:3px;background:{COL_C6};
                   border-radius:2px;border-top:2px dashed {COL_C6}"></span>
      Core_6feat（6特徵）
    </span>
    <span class="badge">生成日期：{date.today()}</span>
  </div>
</div>

<!-- 設計說明 -->
<h2 style="background:var(--navy)">📋 測試設計說明</h2>
<div class="card">
  <table>
    <thead><tr>
      <th>場景</th><th>性別/身高</th><th>起始BMI</th><th>趨勢</th><th>設計目的</th>
    </tr></thead>
    <tbody>
      <tr><td>💪 改善男</td><td>男 178cm</td><td>31.6（肥胖）</td><td>逐週改善</td>
          <td>中年男 + 靜態錨定效應，驗證 Behav_15 反應較鈍</td></tr>
      <tr><td>🌸 改善女</td><td>女 162cm</td><td>28.2（過重）</td><td>逐週改善</td>
          <td>較年輕女性，錨定效應弱，Behav_15 反應較靈敏</td></tr>
      <tr><td>📉 惡化男</td><td>男 176cm</td><td>22.6（正常）</td><td>逐週惡化</td>
          <td>年輕男從健康滑向過重，性別對比用</td></tr>
      <tr><td>⚠️ 惡化女</td><td>女 163cm</td><td>20.7（正常）</td><td>逐週惡化</td>
          <td>與惡化男對稱，驗證性別差異</td></tr>
      <tr><td>✅ 穩定健康</td><td>女 160cm</td><td>21.5（正常）</td><td>12週穩定</td>
          <td>低機率基準，驗證零波動</td></tr>
      <tr><td>🔴 穩定高風險</td><td>男 172cm</td><td>33.8（肥胖）</td><td>16週穩定</td>
          <td>高機率基準，驗證零波動</td></tr>
    </tbody>
  </table>
  <div class="hl" style="margin-top:16px">
    📌 <b>機率 ≥ 0.5 → 預測 Overweight+Obese</b>；機率 &lt; 0.5 → Normal。
    紅色大圓點 = BMI 模擬值跨越 25 的週次。
  </div>
  <div class="warn">
    ⚠️ <b>右軸 BMI 為人物情境假設值，非模型輸出。</b>
    模型為 Binary 分類器，只輸出 OW+Obese 機率（0–1）。
  </div>
</div>

<!-- 整體比較折線圖 -->
<h2 style="background:#374151">📊 六場景整體比較（含 SG 平滑趨勢帶）</h2>
<div class="card">
  <div class="btn-grp" style="margin-bottom:16px">
    <span class="btn-lbl">特徵集：</span>
    <button class="tbtn on" onclick="sw('img-cmp','_cmp','c6',this.parentElement)">
      Core_6feat（橘，6特徵）
    </button>
    <button class="tbtn" onclick="sw('img-cmp','_cmp','b15',this.parentElement)">
      Behav_15feat（藍，15特徵）
    </button>
  </div>
  <img id="img-cmp" src="{cmp_c6}"
       style="width:100%;border-radius:8px;border:1px solid #e5e7eb">
</div>

<!-- 熱圖 -->
<h2 style="background:#0891b2">🌡️ 機率熱圖（6場景 × 16週）</h2>
<div class="card">
  <p style="color:#6b7280;font-size:13px;margin-bottom:12px">
    每格顏色代表當週預測機率：
    <span style="color:#16a34a;font-weight:600">深綠=低風險</span> →
    <span style="color:#d97706;font-weight:600">黃=中等</span> →
    <span style="color:#dc2626;font-weight:600">深紅=高風險</span>。
    紅色虛線 = BMI 跨越 25 的週次。
  </p>
  <img src="{img_heatmap}" style="width:100%;border-radius:8px;border:1px solid #e5e7eb">
</div>

<!-- 斜率圖 -->
<h2 style="background:#7c3aed">📐 W1 vs W16 斜率圖</h2>
<div class="card">
  <p style="color:#6b7280;font-size:13px;margin-bottom:12px">
    每條線代表一個場景從 W1（起始）到 W16（結束）的機率變化。
    中間數字顯示 ▼降低 或 ▲升高 幅度。
  </p>
  <img src="{img_slope}" style="width:100%;border-radius:8px;border:1px solid #e5e7eb">
</div>

<!-- 差值圖 -->
<h2 style="background:#0f766e">🔀 Behav_15 − Core_6 差值圖</h2>
<div class="card">
  <p style="color:#6b7280;font-size:13px;margin-bottom:12px">
    正值 = Behav_15 機率高於 Core_6（加入人口統計後風險評估更高）。<br>
    <b>改善男差值持續正數且大</b>：中年男性人口統計錨定效應強，
    即使行為改善，Behav_15 仍因「中年男」標籤維持高估。
  </p>
  <img src="{img_diff}" style="width:100%;border-radius:8px;border:1px solid #e5e7eb">
</div>

<!-- 散點圖 -->
<h2 style="background:#1d4ed8">⚡ BMI × 機率散點圖</h2>
<div class="card">
  <p style="color:#6b7280;font-size:13px;margin-bottom:12px">
    每個點 = 一個場景的一週資料。W1/W16 有標記。
    驗證模型是否在 BMI 25 附近有機率跳變（理想上應有正相關）。
  </p>
  <img src="{img_scatter}" style="width:100%;border-radius:8px;border:1px solid #e5e7eb">
</div>

<!-- 各場景詳細 -->
<h2 style="background:#374151">🔬 各場景詳細結果（雙 Y 軸圖）</h2>
{scenario_sections}

<footer>
  obesity_project_3 · API Test Report v3 ·
  Behav_15=藍色 / Core_6=橘色 · {date.today()}
</footer>
</div>

<script>
const D = {JS_DATA};
function sw(imgId,key,mode,grp){{
  document.getElementById(imgId).src=D[key][mode];
  grp.querySelectorAll('.tbtn').forEach(function(b){{
    b.classList.toggle('on',b===event.currentTarget);
  }});
}}
</script>
</body></html>"""

OUT = f"outputs/api_test_report_{date.today().strftime('%Y%m%d')}.html"
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\n{'='*55}\nDone  →  {OUT}")
