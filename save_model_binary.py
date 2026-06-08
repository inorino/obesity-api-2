"""
save_model_binary.py — Obesity Risk Prediction v3 (Binary)
資料集：CDC BRFSS 2022 (data/brfss2022_clean.csv)
═══════════════════════════════════════════════════════════
目標：binary_cat（2 類）
  Normal(0)：BMI < 25   /   Overweight+Obese(1)：BMI >= 25

三組特徵集 × 3演算法 × 3抽樣策略 = 27 模型實驗
  Group 1  Full_25feat   — 完整特徵（生活+健康+慢性病+人口）
  Group 2  Behav_15feat  — 行為健康（無慢性病史）
  Group 3  Core_6feat    — 核心行為（純可控習慣）

執行：python save_model_binary.py
輸出：models_binary/  outputs/plots_binary/  outputs/report_binary.html
═══════════════════════════════════════════════════════════
"""

import os, sys, copy, warnings, base64
from datetime import date
sys.stdout.reconfigure(encoding="utf-8")
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, classification_report, confusion_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler

warnings.filterwarnings("ignore")
plt.rcParams["font.family"] = ["Microsoft JhengHei", "DejaVu Sans"]

# ════════════════════════════════════════════════════════════
# 0. 路徑
# ════════════════════════════════════════════════════════════
DATA_PATH = "data/brfss2022_clean.csv"
MODEL_DIR = "models_binary"
PLOT_DIR  = "outputs/plots_binary"
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(PLOT_DIR,  exist_ok=True)

# ════════════════════════════════════════════════════════════
# 1. 讀資料 & 建立二元目標
# ════════════════════════════════════════════════════════════
df = pd.read_csv(DATA_PATH)
print(f"資料載入：{df.shape[0]:,} 筆, {df.shape[1]} 欄")

# 二元轉換：Normal=0, Overweight+Obese=1
df["binary_cat"] = df["bmi_cat"].apply(lambda x: 0 if x == 0 else 1)

class_dist = df["binary_cat"].value_counts().sort_index()
n_total = len(df)
print(f"二元類別分佈:")
print(f"  0 Normal          : {class_dist[0]:,} ({class_dist[0]/n_total*100:.1f}%)")
print(f"  1 Overweight+Obese: {class_dist[1]:,} ({class_dist[1]/n_total*100:.1f}%)\n")

# ════════════════════════════════════════════════════════════
# 2. 三組特徵集（與 3-class 版本相同，方便比較）
# ════════════════════════════════════════════════════════════
# Group 1：完整特徵（25 feat）
FULL25 = [
    # 生活習慣 (5)
    "sleep_hours", "smoking_status", "drank_any", "drinks_per_week", "exercised",
    # 健康狀態 (5)
    "general_health", "mental_health_days", "physical_health_days",
    "diff_walking", "depression",
    # 慢性病史 (7)
    "diabetes", "heart_disease", "stroke", "copd", "asthma", "arthritis", "kidney_disease",
    # 人口統計 (7) + 健康行為 (1)
    "sex", "age_group", "education", "income", "marital_status",
    "employment", "rent_or_own", "dental_visit",
]

# Group 2：行為健康組（15 feat）— 去掉慢性病史
BEHAV15 = [
    # 生活習慣 (5)
    "sleep_hours", "smoking_status", "drank_any", "drinks_per_week", "exercised",
    # 健康狀態 (5)
    "general_health", "mental_health_days", "physical_health_days",
    "diff_walking", "depression",
    # 人口統計 (5)
    "sex", "age_group", "education", "income", "employment",
]

# Group 3：核心行為組（6 feat）— 只留可控習慣
CORE6 = [
    "sleep_hours", "smoking_status", "drank_any", "drinks_per_week",
    "exercised", "general_health",
]

FEATURE_SETS = {
    "Full_25feat": {
        "label":    "完整特徵（25 feat：生活習慣+健康狀態+慢性病史+人口統計）",
        "features": FULL25,
        "save_as":  "model_full.pkl",
    },
    "Behav_15feat": {
        "label":    "行為健康（15 feat：生活習慣+健康狀態+人口統計，無慢性病）",
        "features": BEHAV15,
        "save_as":  "model_behav.pkl",
    },
    "Core_6feat": {
        "label":    "核心行為（6 feat：睡眠+吸菸+飲酒+運動+自評健康）",
        "features": CORE6,
        "save_as":  "model_core.pkl",
    },
}

# ════════════════════════════════════════════════════════════
# 3. 演算法 & 抽樣策略
# ════════════════════════════════════════════════════════════
ALGORITHMS = {
    "Logistic\nRegression": LogisticRegression(max_iter=1000, random_state=42),
    "Random\nForest":       RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42),
    "XGBoost":              XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.08,
                                          subsample=0.8, colsample_bytree=0.8,
                                          eval_metric="logloss", random_state=42),
}
SAMPLINGS = {
    "Raw Data":               None,
    "SMOTE":                  SMOTE(random_state=42),
    "Random\nUnder-sampling": RandomUnderSampler(random_state=42),
}
ALGO_KEYS = list(ALGORITHMS.keys())
SAMP_KEYS = list(SAMPLINGS.keys())

CLASS_NAMES = ["Normal", "Overweight+Obese"]
COLORS = {"Full_25feat": "#2563EB", "Behav_15feat": "#16A34A", "Core_6feat": "#DC2626"}

# ════════════════════════════════════════════════════════════
# 4. 繪圖函式
# ════════════════════════════════════════════════════════════
def plot_heatmap(df_f, features, set_name, label):
    cols = features + ["binary_cat"]
    corr = df_f[cols].corr()
    n = len(cols)
    fig, ax = plt.subplots(figsize=(max(8, n*0.75), max(7, n*0.7)))
    mask = np.zeros_like(corr, dtype=bool)
    mask[np.triu_indices_from(mask, k=1)] = True
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r",
                center=0, linewidths=0.3, ax=ax, annot_kws={"size": 7.5},
                cbar_kws={"shrink": 0.8})
    ax.set_title(f"Correlation Heatmap\n{label}", fontsize=12, fontweight="bold", pad=10)
    ax.tick_params(axis="x", rotation=45, labelsize=8)
    ax.tick_params(axis="y", rotation=0,  labelsize=8)
    plt.tight_layout()
    path = f"{PLOT_DIR}/{set_name}_heatmap.png"
    plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
    print(f"   Heatmap      -> {path}")

def plot_f1_grid(records, set_name, label, best_algo, best_samp):
    rdf   = pd.DataFrame(records)
    pivot = rdf.pivot(index="Sampling", columns="Algorithm", values="F1")
    pivot = pivot.reindex(index=SAMP_KEYS, columns=ALGO_KEYS)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    sns.heatmap(pivot, annot=True, fmt=".4f", cmap="YlGn",
                vmin=0.45, vmax=1.0, linewidths=0.6, linecolor="white",
                ax=ax, annot_kws={"size": 12, "weight": "bold"})
    best_col = ALGO_KEYS.index(best_algo)
    best_row = SAMP_KEYS.index(best_samp)
    ax.add_patch(plt.Rectangle((best_col, best_row), 1, 1,
                 fill=False, edgecolor="red", lw=3, zorder=5))
    ax.set_title(f"F1-Score Grid (3x3)\n{label}", fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("Algorithm", fontsize=10)
    ax.set_ylabel("Sampling Strategy", fontsize=10)
    ax.tick_params(labelsize=9)
    plt.tight_layout()
    path = f"{PLOT_DIR}/{set_name}_f1_grid.png"
    plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
    print(f"   F1 Grid      -> {path}")

def plot_confusion(cm, set_name, label, algo, samp, f1):
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES,
                linewidths=0.4, ax=ax, annot_kws={"size": 13})
    ax.set_xlabel("Predicted", fontsize=10)
    ax.set_ylabel("Actual",    fontsize=10)
    ax.set_title(
        f"Confusion Matrix - {label}\n"
        f"Best: {algo.replace(chr(10),' ')} + {samp.replace(chr(10),' ')}  (F1={f1:.4f})",
        fontsize=10, fontweight="bold", pad=10)
    plt.tight_layout()
    path = f"{PLOT_DIR}/{set_name}_confusion.png"
    plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
    print(f"   Confusion    -> {path}")

def plot_feature_importance(model, feature_names, set_name, label, algo_name):
    algo_clean = algo_name.replace("\n", " ")
    n = len(feature_names)

    # 取得重要度
    if hasattr(model, "coef_"):
        # Logistic Regression：取係數，絕對值排序，保留正負方向
        coef = model.coef_[0]
        importance = coef
        method_note = "Coefficient (+ = higher obesity risk)"
        colors = ["#dc2626" if v > 0 else "#2563eb" for v in importance]
        sort_idx = np.argsort(np.abs(importance))  # 由小到大，橫向圖底部最重要
    else:
        # Random Forest / XGBoost：feature_importances_
        importance = model.feature_importances_
        method_note = "Feature Importance (Gini/Gain)"
        colors = ["#16a34a"] * n
        sort_idx = np.argsort(importance)

    sorted_feats = [feature_names[i] for i in sort_idx]
    sorted_vals  = [importance[i] for i in sort_idx]
    sorted_colors = [colors[i] for i in sort_idx]

    fig, ax = plt.subplots(figsize=(8, max(4, n * 0.38)))
    bars = ax.barh(sorted_feats, sorted_vals, color=sorted_colors, edgecolor="white", height=0.7)

    # 數值標籤
    for bar, val in zip(bars, sorted_vals):
        x_pos = val + (max(np.abs(sorted_vals)) * 0.02) if val >= 0 else val - (max(np.abs(sorted_vals)) * 0.02)
        ha = "left" if val >= 0 else "right"
        ax.text(x_pos, bar.get_y() + bar.get_height()/2,
                f"{val:.4f}", va="center", ha=ha, fontsize=8)

    if hasattr(model, "coef_"):
        ax.axvline(0, color="black", linewidth=0.8, linestyle="--")

    ax.set_title(f"Feature Importance — {label}\n{algo_clean}  |  {method_note}",
                 fontsize=11, fontweight="bold", pad=10)
    ax.set_xlabel(method_note.split("(")[0].strip(), fontsize=9)
    ax.tick_params(axis="y", labelsize=9)
    ax.tick_params(axis="x", labelsize=8)
    plt.tight_layout()
    path = f"{PLOT_DIR}/{set_name}_importance.png"
    plt.savefig(path, dpi=150, bbox_inches="tight"); plt.close()
    print(f"   Importance   -> {path}")

# ════════════════════════════════════════════════════════════
# 5. 主實驗迴圈
# ════════════════════════════════════════════════════════════
all_best    = {}
all_records = {}

for set_name, cfg in FEATURE_SETS.items():
    print(f"\n{'='*62}")
    print(f"  {cfg['label']}")
    print(f"{'='*62}")

    feats = cfg["features"]
    X = df[feats].values
    y = df["binary_cat"].values

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y)

    plot_heatmap(df, feats, set_name, cfg["label"])

    records = []
    best_f1, best_model, best_algo, best_samp, best_pred = -1, None, None, None, None

    for samp_name, sampler in SAMPLINGS.items():
        for algo_name, algo_proto in ALGORITHMS.items():
            model = copy.deepcopy(algo_proto)
            if sampler is not None:
                try:
                    Xs, ys = copy.deepcopy(sampler).fit_resample(X_tr, y_tr)
                except Exception:
                    Xs, ys = X_tr, y_tr
            else:
                Xs, ys = X_tr, y_tr

            model.fit(Xs, ys)
            y_pred = model.predict(X_te)
            f1 = f1_score(y_te, y_pred, average="weighted")
            records.append({"Algorithm": algo_name, "Sampling": samp_name, "F1": f1})
            star  = " *" if f1 > best_f1 else ""
            a_s   = algo_name.replace("\n", " ")
            s_s   = samp_name.replace("\n", " ")
            print(f"   {s_s:26s} | {a_s:22s} | F1={f1:.4f}{star}")

            if f1 > best_f1:
                best_f1, best_model  = f1, model
                best_algo, best_samp = algo_name, samp_name
                best_pred            = y_pred

    plot_f1_grid(records, set_name, cfg["label"], best_algo, best_samp)
    cm = confusion_matrix(y_te, best_pred)
    plot_confusion(cm, set_name, cfg["label"], best_algo, best_samp, best_f1)
    plot_feature_importance(best_model, feats, set_name, cfg["label"], best_algo)

    joblib.dump(best_model, f"{MODEL_DIR}/{cfg['save_as']}")
    joblib.dump(feats,      f"{MODEL_DIR}/feature_cols_{set_name}.pkl")

    a_s = best_algo.replace("\n", " ")
    s_s = best_samp.replace("\n", " ")
    print(f"\n  最佳：{a_s} + {s_s}  F1={best_f1:.4f}")
    print(classification_report(y_te, best_pred, target_names=CLASS_NAMES, digits=4))

    all_best[set_name]    = {"label": cfg["label"], "algorithm": a_s, "sampling": s_s,
                              "f1": best_f1, "n_features": len(feats), "cm": cm}
    all_records[set_name] = records

# ════════════════════════════════════════════════════════════
# 6. 摘要 & 與 3-class 對比
# ════════════════════════════════════════════════════════════
THREECLASS_F1 = {
    "Full_25feat":  None,   # 重新設計後需重跑 3-class
    "Behav_15feat": None,
    "Core_6feat":   None,
}

print(f"\n{'='*70}")
print("  Binary vs 3-class F1 對比")
print(f"{'='*70}")
print(f"  {'特徵集':20s} {'3-class F1':>12s} {'Binary F1':>12s} {'提升':>10s}")
print(f"  {'-'*60}")
for k, v in all_best.items():
    old = THREECLASS_F1.get(k)
    if old is None:
        print(f"  {k:20s} {'N/A':>12s} {v['f1']:>12.4f} {'(新增)':>10s}")
    else:
        diff = v['f1'] - old
        print(f"  {k:20s} {old:>12.4f} {v['f1']:>12.4f} {diff:>+10.4f}")

print(f"\n  models_binary/ -> {len(os.listdir(MODEL_DIR))} files")
print(f"  outputs/plots_binary/ -> {len(os.listdir(PLOT_DIR))} images")

# ════════════════════════════════════════════════════════════
# 7. HTML 報告
# ════════════════════════════════════════════════════════════
def b64_img(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return ""

def html_img(path, alt="", width="100%"):
    data = b64_img(path)
    if not data:
        return f"<p style='color:red'>Image not found: {path}</p>"
    return f'<img src="data:image/png;base64,{data}" alt="{alt}" style="width:{width};border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,.15)">'

today = date.today().strftime("%Y-%m-%d")

dist_html = (
    f"<tr><td>0</td><td>{class_dist[0]:,}</td><td>Normal (BMI &lt; 25)</td>"
    f"<td>{class_dist[0]/n_total*100:.1f}%</td></tr>"
    f"<tr><td>1</td><td>{class_dist[1]:,}</td><td>Overweight + Obese (BMI &ge; 25)</td>"
    f"<td>{class_dist[1]/n_total*100:.1f}%</td></tr>"
)

def _compare_row(k, v):
    old = THREECLASS_F1.get(k)
    if old is None:
        return (f"<tr><td><b>{k}</b></td>"
                f"<td style='text-align:center;color:#9ca3af'>N/A（新增）</td>"
                f"<td style='text-align:center;font-weight:bold;color:#16a34a'>{v['f1']:.4f}</td>"
                f"<td style='text-align:center;color:#9ca3af'>—</td></tr>")
    diff = v['f1'] - old
    return (f"<tr><td><b>{k}</b></td>"
            f"<td style='text-align:center'>{old:.4f}</td>"
            f"<td style='text-align:center;font-weight:bold;color:#16a34a'>{v['f1']:.4f}</td>"
            f"<td style='text-align:center;color:{'#16a34a' if diff>=0 else '#dc2626'}'>{diff:+.4f}</td></tr>")

compare_rows = "".join(_compare_row(k, v) for k, v in all_best.items())

summary_rows = "".join(
    f"<tr style='background:{'#f0f7ff' if i%2==0 else 'white'}'>"
    f"<td><b>{k}</b></td><td style='text-align:center'>{v['n_features']}</td>"
    f"<td>{v['algorithm']}</td><td>{v['sampling']}</td>"
    f"<td style='text-align:center;font-weight:bold;color:{'#16a34a' if v['f1']==max(x['f1'] for x in all_best.values()) else '#1d4ed8'}'>{v['f1']:.4f}</td></tr>"
    for i, (k, v) in enumerate(all_best.items())
)

SET_COLORS = {"Full_25feat": "#2563EB", "Behav_15feat": "#16A34A", "Core_6feat": "#DC2626"}
sections = ""
for set_name, v in all_best.items():
    color = SET_COLORS.get(set_name, "#333")
    heatmap_img    = html_img(f"{PLOT_DIR}/{set_name}_heatmap.png",    "heatmap",    "90%")
    f1grid_img     = html_img(f"{PLOT_DIR}/{set_name}_f1_grid.png",    "f1 grid",    "90%")
    confusion_img  = html_img(f"{PLOT_DIR}/{set_name}_confusion.png",  "confusion",  "60%")
    importance_img = html_img(f"{PLOT_DIR}/{set_name}_importance.png", "importance", "90%")
    sections += f"""
    <section style="margin-bottom:48px">
      <h2 style="border-left:5px solid {color};padding-left:12px;color:{color}">{set_name}</h2>
      <p style="color:#555">{v['label']}</p>
      <p><b>最佳組合：</b>{v['algorithm']} + {v['sampling']} &nbsp;|&nbsp; <b>Weighted F1 = {v['f1']:.4f}</b></p>
      <div style="display:flex;gap:24px;flex-wrap:wrap;align-items:flex-start;margin-top:16px">
        <div style="flex:1;min-width:280px"><h3 style="font-size:14px;color:#444">Correlation Heatmap</h3>{heatmap_img}</div>
        <div style="flex:1;min-width:280px"><h3 style="font-size:14px;color:#444">F1 Grid (3x3)</h3>{f1grid_img}</div>
        <div style="flex:0 0 auto;min-width:220px"><h3 style="font-size:14px;color:#444">Confusion Matrix</h3>{confusion_img}</div>
      </div>
      <div style="margin-top:24px">
        <h3 style="font-size:14px;color:#444">Feature Importance（最佳模型）</h3>
        <p style="font-size:12px;color:#6b7280;margin:4px 0 12px">
          Logistic Regression：係數（紅=增加肥胖風險 / 藍=降低風險）｜
          Random Forest / XGBoost：Gini/Gain 貢獻度（越長越重要）
        </p>
        {importance_img}
      </div>
    </section>"""

html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Obesity Risk Prediction v3 - Binary Report</title>
<style>
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:1200px;margin:0 auto;padding:32px 24px;color:#1a1a1a;background:#fafafa}}
  h1{{font-size:26px;margin-bottom:4px}} h2{{font-size:20px;margin-top:40px}}
  table{{border-collapse:collapse;width:100%;margin:12px 0}}
  th{{background:#1e3a5f;color:white;padding:10px 14px;text-align:left;font-size:13px}}
  td{{padding:9px 14px;border-bottom:1px solid #e5e7eb;font-size:13px}}
  .meta{{color:#6b7280;font-size:14px;margin-bottom:32px}}
  .badge{{display:inline-block;background:#dc2626;color:white;padding:2px 10px;border-radius:10px;font-size:12px;font-weight:700;margin-left:8px}}
  hr{{border:none;border-top:1px solid #e5e7eb;margin:40px 0}}
</style>
</head>
<body>
<h1>生活習慣與肥胖風險預測 v3 <span class="badge">Binary</span> — 實驗報告</h1>
<p class="meta">
  生成日期：{today} &nbsp;|&nbsp;
  資料集：CDC BRFSS 2022 &nbsp;|&nbsp;
  樣本數：{n_total:,} &nbsp;|&nbsp;
  目標：Normal vs Overweight+Obese &nbsp;|&nbsp;
  實驗數：27（3特徵集 × 3演算法 × 3抽樣）
</p>

<h2>目標類別分佈（Binary）</h2>
<table>
  <tr><th>類別</th><th>筆數</th><th>說明</th><th>比例</th></tr>
  {dist_html}
</table>

<h2>Binary vs 3-class F1 對比</h2>
<table>
  <tr><th>特徵集</th><th style="text-align:center">3-class F1</th><th style="text-align:center">Binary F1</th><th style="text-align:center">提升幅度</th></tr>
  {compare_rows}
</table>

<h2>Binary 實驗結果摘要</h2>
<table>
  <tr><th>特徵集</th><th style="text-align:center">特徵數</th><th>最佳演算法</th><th>最佳抽樣策略</th><th style="text-align:center">Weighted F1</th></tr>
  {summary_rows}
</table>

<hr>
{sections}

<p style="margin-top:48px;font-size:12px;color:#9ca3af;text-align:center">
  Generated by save_model_binary.py · obesity_project_3 · CDC BRFSS 2022 · {today}
</p>
</body>
</html>"""

report_path = "outputs/report_binary.html"
with open(report_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\n  HTML report -> {report_path}")
print("\nDone!")
