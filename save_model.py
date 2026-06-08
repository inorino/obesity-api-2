"""
save_model.py — Obesity Risk Prediction v3 (3-class)
資料集：CDC BRFSS 2022 (data/brfss2022_clean.csv)
═══════════════════════════════════════════════════════════
目標：bmi_cat（3 類）
  Normal(0) / Overweight(1) / Obese(2)

三組特徵集 × 3演算法 × 3抽樣策略 = 27 模型實驗
  Group 1  Full_25feat   — 完整特徵（生活+健康+慢性病+人口）
  Group 2  Behav_15feat  — 行為健康（無慢性病史）
  Group 3  Core_6feat    — 核心行為（純可控習慣）

執行：python save_model.py
輸出：models/  outputs/plots/  outputs/report.html
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
MODEL_DIR = "models"
PLOT_DIR  = "outputs/plots"
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(PLOT_DIR,  exist_ok=True)

# ════════════════════════════════════════════════════════════
# 1. 讀資料
# ════════════════════════════════════════════════════════════
df = pd.read_csv(DATA_PATH)
print(f"資料載入：{df.shape[0]:,} 筆, {df.shape[1]} 欄")

class_dist = df["bmi_cat"].value_counts().sort_index()
print(f"類別分佈: {dict(class_dist)}")
print(f"  0=Normal, 1=Overweight, 2=Obese\n")

# ════════════════════════════════════════════════════════════
# 2. 三組特徵集定義
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
                                          eval_metric="mlogloss", random_state=42),
}
SAMPLINGS = {
    "Raw Data":               None,
    "SMOTE":                  SMOTE(random_state=42),
    "Random\nUnder-sampling": RandomUnderSampler(random_state=42),
}
ALGO_KEYS = list(ALGORITHMS.keys())
SAMP_KEYS = list(SAMPLINGS.keys())

CLASS_NAMES = ["Normal", "Overweight", "Obese"]
COLORS = {"Full_25feat": "#2563EB", "Behav_15feat": "#16A34A", "Core_6feat": "#DC2626"}

# ════════════════════════════════════════════════════════════
# 4. 繪圖函式
# ════════════════════════════════════════════════════════════
def plot_heatmap(df_f, features, set_name, label):
    cols = features + ["bmi_cat"]
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
    y = df["bmi_cat"].values

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
# 6. 摘要
# ════════════════════════════════════════════════════════════
print(f"\n{'='*62}")
print("  最終模型摘要")
print(f"{'='*62}")
print(f"  {'特徵集':22s} {'特徵數':6s} {'最佳演算法':24s} {'最佳抽樣':26s} F1")
for k, v in all_best.items():
    print(f"  {k:22s} {v['n_features']:<6d} {v['algorithm']:24s} {v['sampling']:26s} {v['f1']:.4f}")
print(f"\n  models/        -> {len(os.listdir(MODEL_DIR))} files")
print(f"  outputs/plots/ -> {len(os.listdir(PLOT_DIR))} images")

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

today   = date.today().strftime("%Y-%m-%d")
n_total = len(df)
dist_html = "".join(
    f"<tr><td>{i}</td><td>{n:,}</td><td>{['Normal (BMI < 25)','Overweight (25-29.9)','Obese (BMI >= 30)'][i]}</td>"
    f"<td>{class_dist[i]/n_total*100:.1f}%</td></tr>"
    for i, n in class_dist.items()
)

summary_rows = "".join(
    f"<tr style='background:{'#f0f7ff' if i%2==0 else 'white'}'>"
    f"<td><b>{k}</b></td><td style='text-align:center'>{v['n_features']}</td>"
    f"<td>{v['algorithm']}</td><td>{v['sampling']}</td>"
    f"<td style='text-align:center;font-weight:bold;color:{'#16a34a' if v['f1']==max(x['f1'] for x in all_best.values()) else '#1d4ed8'}'>{v['f1']:.4f}</td></tr>"
    for i, (k, v) in enumerate(all_best.items())
)

SET_COLORS = {"Full_21feat": "#2563EB", "Habit_10feat": "#16A34A", "Slim_5feat": "#DC2626"}
sections = ""
for set_name, v in all_best.items():
    color = SET_COLORS.get(set_name, "#333")
    heatmap_img   = html_img(f"{PLOT_DIR}/{set_name}_heatmap.png",  "heatmap",  "90%")
    f1grid_img    = html_img(f"{PLOT_DIR}/{set_name}_f1_grid.png",  "f1 grid",  "90%")
    confusion_img = html_img(f"{PLOT_DIR}/{set_name}_confusion.png","confusion","60%")
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
    </section>"""

html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Obesity Risk Prediction v3 - Experiment Report</title>
<style>
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:1200px;margin:0 auto;padding:32px 24px;color:#1a1a1a;background:#fafafa}}
  h1{{font-size:26px;margin-bottom:4px}} h2{{font-size:20px;margin-top:40px}}
  table{{border-collapse:collapse;width:100%;margin:12px 0}}
  th{{background:#1e3a5f;color:white;padding:10px 14px;text-align:left;font-size:13px}}
  td{{padding:9px 14px;border-bottom:1px solid #e5e7eb;font-size:13px}}
  .meta{{color:#6b7280;font-size:14px;margin-bottom:32px}}
  hr{{border:none;border-top:1px solid #e5e7eb;margin:40px 0}}
</style>
</head>
<body>
<h1>生活習慣與肥胖風險預測 v3 — 實驗報告</h1>
<p class="meta">
  生成日期：{today} &nbsp;|&nbsp;
  資料集：CDC BRFSS 2022 &nbsp;|&nbsp;
  樣本數：{n_total:,} &nbsp;|&nbsp;
  實驗數：27（3 特徵集 × 3 演算法 × 3 抽樣）
</p>

<h2>目標類別分佈（BMI 衍生）</h2>
<table>
  <tr><th>類別</th><th>筆數</th><th>說明</th><th>比例</th></tr>
  {dist_html}
</table>

<h2>實驗結果摘要</h2>
<table>
  <tr><th>特徵集</th><th style="text-align:center">特徵數</th><th>最佳演算法</th><th>最佳抽樣策略</th><th style="text-align:center">Weighted F1</th></tr>
  {summary_rows}
</table>

<hr>
{sections}
<hr>

<h2>特徵欄位說明</h2>
<table>
  <tr><th>欄位名</th><th>說明</th><th>值域</th></tr>
  <tr><td>sleep_hours</td><td>每晚睡眠時數</td><td>1-16 小時</td></tr>
  <tr><td>smoking_status</td><td>吸菸狀態</td><td>1=每日, 2=偶爾, 3=曾吸, 4=從不</td></tr>
  <tr><td>drank_any</td><td>過去30天有無飲酒</td><td>0=No, 1=Yes</td></tr>
  <tr><td>drinks_per_week</td><td>每週飲酒次數</td><td>連續值</td></tr>
  <tr><td>exercised</td><td>過去30天有無運動</td><td>0=No, 1=Yes</td></tr>
  <tr><td>general_health</td><td>自評整體健康</td><td>1=Excellent, 5=Poor</td></tr>
  <tr><td>mental_health_days</td><td>心理不健康天數</td><td>0-30 天</td></tr>
  <tr><td>physical_health_days</td><td>身體不健康天數</td><td>0-30 天</td></tr>
  <tr><td>diff_walking</td><td>行走困難</td><td>0=No, 1=Yes</td></tr>
  <tr><td>depression</td><td>曾被診斷憂鬱症</td><td>0=No, 1=Yes</td></tr>
  <tr><td>diabetes</td><td>糖尿病</td><td>0=No, 1=前期, 2=Yes</td></tr>
  <tr><td>heart_disease</td><td>冠心病</td><td>0=No, 1=Yes</td></tr>
  <tr><td>stroke</td><td>中風</td><td>0=No, 1=Yes</td></tr>
  <tr><td>copd</td><td>慢性肺阻塞</td><td>0=No, 1=Yes</td></tr>
  <tr><td>arthritis</td><td>關節炎</td><td>0=No, 1=Yes</td></tr>
  <tr><td>kidney_disease</td><td>腎臟病</td><td>0=No, 1=Yes</td></tr>
  <tr><td>sex</td><td>性別</td><td>0=Female, 1=Male</td></tr>
  <tr><td>age_group</td><td>年齡組</td><td>1=18-24, ..., 13=80+</td></tr>
  <tr><td>education</td><td>教育程度</td><td>1=未受教育, ..., 6=大學以上</td></tr>
  <tr><td>income</td><td>家庭年收入</td><td>1=&lt;$15k, ..., 8=&gt;$200k, 9=未回答</td></tr>
  <tr><td>marital_status</td><td>婚姻狀況</td><td>1=已婚, 2=離婚, 3=喪偶, 4=分居, 5=未婚, 6=同居</td></tr>
  <tr><td><b>bmi_cat</b></td><td><b>BMI 類別（目標變數）</b></td><td>0=Normal, 1=Overweight, 2=Obese</td></tr>
</table>

<p style="margin-top:48px;font-size:12px;color:#9ca3af;text-align:center">
  Generated by save_model.py · obesity_project_3 · CDC BRFSS 2022 · {today}
</p>
</body>
</html>"""

report_path = "outputs/report.html"
os.makedirs("outputs", exist_ok=True)
with open(report_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\n  HTML report -> {report_path}")
print("\nDone!")
