"""
gen_master_report.py — 生成主分析報告 (master_report.html)
包含：資料集說明、實驗設計、3-class & Binary 結果、特徵重要度、跨組比較
所有圖表以 base64 內嵌
"""

import os, base64
from pathlib import Path

BASE = Path("D:/07_Claude/01_Master_Report/obesity_project_3")
PLOT3  = BASE / "outputs/plots"
PLOTB  = BASE / "outputs/plots_binary"
OUT    = BASE / "outputs/master_report.html"

def img64(path):
    p = Path(path)
    if not p.exists():
        return ""
    data = base64.b64encode(p.read_bytes()).decode()
    return f"data:image/png;base64,{data}"

# ── 載入圖表 ──────────────────────────────────────────────
imgs = {}
for grp in ["Full_25feat", "Behav_15feat", "Core_6feat"]:
    for kind in ["f1_grid", "confusion", "heatmap"]:
        imgs[f"3_{grp}_{kind}"] = img64(PLOT3 / f"{grp}_{kind}.png")
    for kind in ["f1_grid", "confusion", "heatmap", "importance"]:
        imgs[f"b_{grp}_{kind}"] = img64(PLOTB / f"{grp}_{kind}.png")

# ── HTML ──────────────────────────────────────────────────
html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>肥胖風險預測 v3 — 主分析報告</title>
<style>
:root{{
  --blue:#2563eb; --green:#16a34a; --red:#dc2626;
  --navy:#1e3a5f; --bg:#f1f5f9;
}}
*{{box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      background:var(--bg);color:#1a1a1a;margin:0;padding:0}}
.page{{max-width:1180px;margin:0 auto;padding:32px 24px}}

/* ── 標題 ── */
.hero{{background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);
       color:#fff;border-radius:12px;padding:36px 40px;margin-bottom:32px}}
.hero h1{{font-size:26px;margin:0 0 8px}}
.hero .sub{{font-size:13px;opacity:.8;line-height:1.8}}
.hero .pills{{margin-top:16px;display:flex;gap:10px;flex-wrap:wrap}}
.pill{{background:rgba(255,255,255,.18);border-radius:20px;padding:4px 14px;font-size:12px;font-weight:700}}

/* ── Section ── */
h2{{font-size:17px;color:#fff;margin:36px 0 14px;padding:10px 18px;border-radius:8px}}
h3{{font-size:14px;color:#374151;margin:20px 0 8px;font-weight:700}}
h4{{font-size:13px;color:#6b7280;margin:14px 0 6px;font-weight:600;text-transform:uppercase;letter-spacing:.05em}}

/* ── 通用卡片 ── */
.card{{background:#fff;border-radius:10px;padding:20px 24px;
       box-shadow:0 1px 5px rgba(0,0,0,.08);margin-bottom:16px}}

/* ── 表格 ── */
table{{border-collapse:collapse;width:100%;font-size:13px;margin:10px 0}}
th{{background:var(--navy);color:#fff;padding:9px 13px;text-align:left;font-weight:600;font-size:12px}}
td{{padding:8px 13px;border-bottom:1px solid #f1f5f9;vertical-align:middle}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:#f8fafc}}

/* ── Highlight / Warning ── */
.hl{{background:#f0fdf4;border-left:4px solid var(--green);
     padding:12px 16px;border-radius:0 8px 8px 0;margin:14px 0;font-size:13px}}
.warn{{background:#fef3c7;border-left:4px solid #f59e0b;
       padding:12px 16px;border-radius:0 8px 8px 0;margin:14px 0;font-size:13px}}
.info-box{{background:#eff6ff;border-left:4px solid var(--blue);
           padding:12px 16px;border-radius:0 8px 8px 0;margin:14px 0;font-size:13px}}

/* ── Badges ── */
.badge{{display:inline-block;padding:2px 9px;border-radius:10px;font-size:11px;font-weight:700}}
.b-new{{background:#dbeafe;color:#1e40af}}
.b-best{{background:#dcfce7;color:#166534}}
.b-warn{{background:#fef3c7;color:#92400e}}
.b-red{{background:#fee2e2;color:#991b1b}}
.up{{color:var(--green);font-weight:700}}
.down{{color:var(--red);font-weight:700}}

/* ── Grid ── */
.g2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:12px 0}}
.g3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin:12px 0}}
.g-plot{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:12px 0}}

/* ── KPI cards ── */
.kpi-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:14px 0}}
.kpi{{background:#fff;border-radius:10px;padding:16px 18px;
      box-shadow:0 1px 5px rgba(0,0,0,.08);text-align:center}}
.kpi .num{{font-size:28px;font-weight:700;margin-bottom:2px}}
.kpi .lbl{{font-size:11px;color:#6b7280}}

/* ── Group color header ── */
.g-full{{border-top:4px solid var(--blue)}}
.g-behav{{border-top:4px solid var(--green)}}
.g-core{{border-top:4px solid var(--red)}}
.dot-full{{width:10px;height:10px;border-radius:50%;background:var(--blue);display:inline-block;margin-right:5px}}
.dot-behav{{width:10px;height:10px;border-radius:50%;background:var(--green);display:inline-block;margin-right:5px}}
.dot-core{{width:10px;height:10px;border-radius:50%;background:var(--red);display:inline-block;margin-right:5px}}

/* ── Plot image ── */
img{{max-width:100%;border-radius:6px;border:1px solid #e5e7eb}}
.plot-wrap{{background:#fff;border-radius:8px;padding:10px;
            box-shadow:0 1px 4px rgba(0,0,0,.06)}}
.plot-title{{font-size:11px;color:#9ca3af;margin-bottom:6px;text-align:center}}

/* ── F1 bar ── */
.f1-bar-wrap{{margin:6px 0}}
.f1-row{{display:flex;align-items:center;gap:10px;margin:5px 0}}
.f1-label{{min-width:130px;font-size:12px;color:#374151}}
.f1-bar{{height:22px;border-radius:4px;display:flex;align-items:center;
         padding:0 10px;font-size:12px;font-weight:700;color:#fff;min-width:20px}}
.f1-val{{font-size:12px;color:#374151;min-width:45px}}

/* ── ETL step ── */
.etl-step{{display:flex;align-items:center;gap:14px;padding:10px 14px;
           border-radius:8px;margin:4px 0;border-left:4px solid #cbd5e1;background:#f8fafc}}
.etl-step.drop{{border-left-color:#ef4444}}
.etl-step.keep{{border-left-color:#22c55e}}
.etl-n{{font-size:18px;font-weight:700;min-width:90px}}
.etl-d{{font-size:12px;color:#475569;flex:1}}
.etl-delta{{font-size:11px;color:#ef4444;white-space:nowrap}}
.etl-delta.pos{{color:#16a34a}}

footer{{text-align:center;color:#9ca3af;font-size:12px;
        margin-top:60px;padding:20px 0;border-top:1px solid #e5e7eb}}
</style>
</head>
<body>
<div class="page">

<!-- ══ HERO ══════════════════════════════════════════════ -->
<div class="hero">
  <h1>生活習慣與肥胖風險預測 — 研究報告 v3</h1>
  <div class="sub">
    資料來源：CDC BRFSS 2022 (LLCP2022.XPT) &nbsp;｜&nbsp;
    清理後：329,126 筆 × 26 欄 &nbsp;｜&nbsp;
    實驗規模：3 群特徵 × 3 演算法 × 3 抽樣 × 2 任務 = 54 模型 &nbsp;｜&nbsp;
    報告日期：2026-05-24
  </div>
  <div class="pills">
    <span class="pill">XGBoost · RF · LR</span>
    <span class="pill">SMOTE · Under-sampling · Raw</span>
    <span class="pill">3-class + Binary</span>
    <span class="pill">Weighted F1-score</span>
  </div>
</div>

<!-- ══ 一、資料集 ════════════════════════════════════════ -->
<h2 style="background:#1e3a5f">一、資料集說明</h2>

<div class="kpi-grid">
  <div class="kpi"><div class="num" style="color:var(--navy)">445,132</div><div class="lbl">原始筆數</div></div>
  <div class="kpi"><div class="num" style="color:var(--navy)">328</div><div class="lbl">原始變數數</div></div>
  <div class="kpi"><div class="num" style="color:var(--green)">329,126</div><div class="lbl">清理後筆數</div></div>
  <div class="kpi"><div class="num" style="color:var(--green)">25 + 1</div><div class="lbl">特徵 + 目標變數</div></div>
</div>

<div class="card">
  <h3>ETL 逐步篩選</h3>
  <div class="etl-step"><div class="etl-n">445,132</div><div class="etl-d"><b>原始資料</b>（Raw BRFSS 2022）</div></div>
  <div class="etl-step drop"><div class="etl-n">396,326</div><div class="etl-d">刪除 <code>_BMI5CAT</code> 缺值</div><div class="etl-delta">-48,806</div></div>
  <div class="etl-step keep"><div class="etl-n">396,326</div><div class="etl-d">Underweight (1.7%) 併入 Normal（改標籤，不刪行）</div><div class="etl-delta pos">relabel 6,778</div></div>
  <div class="etl-step drop"><div class="etl-n">392,216</div><div class="etl-d">刪除 <code>SLEPTIM1</code> 無效值 (77/99)</div><div class="etl-delta">-4,110</div></div>
  <div class="etl-step drop"><div class="etl-n">338,666</div><div class="etl-d">刪除核心特徵（生活習慣/健康/慢性病/人口統計）無效值</div><div class="etl-delta">-53,550</div></div>
  <div class="etl-step keep"><div class="etl-n" style="color:var(--green)">329,126</div>
    <div class="etl-d"><b>v3 最終資料集</b>：新增特徵 (asthma/employment/rent_or_own/dental_visit) 及修正 drinks_per_week 99900 異常碼後再清理</div>
    <div class="etl-delta pos">✅ 最終使用</div>
  </div>
  <div class="hl" style="margin-top:12px">
    ✅ <b>v3 新增修正</b>：BRFSS _DRNKWK2 的「不知道/拒答」代碼 99900（÷100後=999.0）未被過濾，共 2,114 筆異常值，本版已修正並移除。
  </div>
</div>

<div class="card">
  <h3>目標變數分佈（二元 vs 三類）</h3>
  <div class="g2">
    <div>
      <h4>三類分類（3-class）</h4>
      <div class="f1-bar-wrap">
        <div class="f1-row"><div class="f1-label">Normal (0) — 30.9%</div><div class="f1-bar" style="width:155px;background:#22c55e">101,741</div></div>
        <div class="f1-row"><div class="f1-label">Overweight (1) — 35.5%</div><div class="f1-bar" style="width:178px;background:#f59e0b">116,837</div></div>
        <div class="f1-row"><div class="f1-label">Obese (2) — 33.6%</div><div class="f1-bar" style="width:168px;background:#ef4444">110,548</div></div>
      </div>
      <div class="info-box">三類分佈均衡（30–36%），無嚴重不平衡問題，仍可比較三種抽樣策略效果。</div>
    </div>
    <div>
      <h4>二元分類（Binary）</h4>
      <div class="f1-bar-wrap">
        <div class="f1-row"><div class="f1-label">Normal (0) — 30.9%</div><div class="f1-bar" style="width:120px;background:#22c55e">101,741</div></div>
        <div class="f1-row"><div class="f1-label">OW+Obese (1) — 69.1%</div><div class="f1-bar" style="width:276px;background:#ef4444">227,385</div></div>
      </div>
      <div class="warn">二元任務存在不平衡（30:70），SMOTE 抽樣對 Binary 效果顯著。</div>
    </div>
  </div>
</div>

<!-- ══ 二、實驗設計 ════════════════════════════════════════ -->
<h2 style="background:#374151">二、實驗設計 — 三組特徵集</h2>

<div class="card">
  <div class="g3">
    <div class="card g-full" style="margin:0">
      <span class="dot-full"></span><b style="color:var(--blue)">Group 1：Full_25feat</b>
      <div style="font-size:12px;color:#6b7280;margin:8px 0 10px">加入所有可用資訊，預測上限在哪？</div>
      <table>
        <tr><td style="font-size:12px">生活習慣</td><td style="font-size:12px;color:#6b7280">5 個</td></tr>
        <tr><td style="font-size:12px">健康狀態</td><td style="font-size:12px;color:#6b7280">5 個</td></tr>
        <tr><td style="font-size:12px">慢性病史</td><td style="font-size:12px;color:#6b7280">7 個</td></tr>
        <tr><td style="font-size:12px">人口統計</td><td style="font-size:12px;color:#6b7280">7 個</td></tr>
        <tr><td style="font-size:12px">健康行為</td><td style="font-size:12px;color:#6b7280">1 個</td></tr>
      </table>
      <div class="badge b-new" style="margin-top:10px">25 features</div>
    </div>
    <div class="card g-behav" style="margin:0">
      <span class="dot-behav"></span><b style="color:var(--green)">Group 2：Behav_15feat</b>
      <div style="font-size:12px;color:#6b7280;margin:8px 0 10px">不使用疾病診斷，只看行為與健康感受</div>
      <table>
        <tr><td style="font-size:12px">生活習慣</td><td style="font-size:12px;color:#6b7280">5 個</td></tr>
        <tr><td style="font-size:12px">健康狀態</td><td style="font-size:12px;color:#6b7280">5 個</td></tr>
        <tr><td style="font-size:12px;text-decoration:line-through;color:#9ca3af">慢性病史</td><td style="font-size:12px;color:#9ca3af">移除</td></tr>
        <tr><td style="font-size:12px">人口統計</td><td style="font-size:12px;color:#6b7280">5 個</td></tr>
      </table>
      <div class="badge b-best" style="margin-top:10px">15 features</div>
    </div>
    <div class="card g-core" style="margin:0">
      <span class="dot-core"></span><b style="color:var(--red)">Group 3：Core_6feat</b>
      <div style="font-size:12px;color:#6b7280;margin:8px 0 10px">只問 6 個問題，不需任何病歷</div>
      <table>
        <tr><td style="font-size:12px">睡眠時數</td><td style="font-size:12px;color:#6b7280">1 個</td></tr>
        <tr><td style="font-size:12px">吸菸狀態</td><td style="font-size:12px;color:#6b7280">1 個</td></tr>
        <tr><td style="font-size:12px">飲酒（有無+量）</td><td style="font-size:12px;color:#6b7280">2 個</td></tr>
        <tr><td style="font-size:12px">有無運動</td><td style="font-size:12px;color:#6b7280">1 個</td></tr>
        <tr><td style="font-size:12px">自評健康</td><td style="font-size:12px;color:#6b7280">1 個</td></tr>
      </table>
      <div class="badge b-red" style="margin-top:10px">6 features</div>
    </div>
  </div>
  <div class="info-box" style="margin-top:16px">
    <b>設計理念（階梯式消除）：</b>從 Full_25 → Behav_15（移除慢性病史，消除逆向因果）→ Core_6（僅保留純可控行為），
    驗證「不需疾病診斷記錄，只靠行為習慣，能預測肥胖風險嗎？」
  </div>
</div>

<!-- ══ 三、3-class 結果 ════════════════════════════════════ -->
<h2 style="background:#0891b2">三、三分類結果（Normal / Overweight / Obese）</h2>

<div class="card">
  <h3>最佳模型摘要</h3>
  <table>
    <tr><th>特徵集</th><th>特徵數</th><th>最佳演算法</th><th>最佳抽樣</th><th style="text-align:center">Weighted F1</th><th style="text-align:center">vs v2</th></tr>
    <tr style="background:#eff6ff">
      <td><span class="dot-full"></span><b>Full_25feat</b></td><td>25</td><td>XGBoost</td><td>Raw Data</td>
      <td style="text-align:center"><span class="up">0.4955</span></td>
      <td style="text-align:center"><span style="color:#6b7280;font-size:12px">≈ v2 Full_21 (0.4939)</span></td>
    </tr>
    <tr>
      <td><span class="dot-behav"></span><b>Behav_15feat</b></td><td>15</td><td>XGBoost</td><td>Raw Data</td>
      <td style="text-align:center">0.4831</td>
      <td style="text-align:center"><span class="badge b-new">全新</span></td>
    </tr>
    <tr>
      <td><span class="dot-core"></span><b>Core_6feat</b></td><td>6</td><td>Random Forest</td><td>Raw Data</td>
      <td style="text-align:center">0.4187</td>
      <td style="text-align:center"><span style="color:#6b7280;font-size:12px">≈ v2 Slim_5 (0.4139)</span></td>
    </tr>
  </table>
  <div class="warn">
    ⚠️ <b>3-class F1 仍落在 0.42–0.50 區間</b>：與舊版 Full_21（0.4939）相比幾乎無改善。
    確認瓶頸在於 <b>Normal / Overweight 邊界天然模糊</b>（BMI 24.9 vs 25.0 的受測者生活習慣幾乎相同），
    非特徵選取問題。
  </div>
</div>

<!-- 3-class 圖表 -->
<div class="g3">
  <div class="card g-full">
    <span class="dot-full"></span><b>Full_25feat</b>
    <div class="g-plot" style="grid-template-columns:1fr">
      <div class="plot-wrap"><div class="plot-title">F1-score Grid（演算法 × 抽樣）</div>
        {'<img src="' + imgs['3_Full_25feat_f1_grid'] + '">' if imgs['3_Full_25feat_f1_grid'] else '<p style="color:#9ca3af;text-align:center;padding:20px">圖表未生成</p>'}</div>
      <div class="plot-wrap"><div class="plot-title">混淆矩陣（最佳模型）</div>
        {'<img src="' + imgs['3_Full_25feat_confusion'] + '">' if imgs['3_Full_25feat_confusion'] else ''}</div>
    </div>
  </div>
  <div class="card g-behav">
    <span class="dot-behav"></span><b>Behav_15feat</b>
    <div class="g-plot" style="grid-template-columns:1fr">
      <div class="plot-wrap"><div class="plot-title">F1-score Grid</div>
        {'<img src="' + imgs['3_Behav_15feat_f1_grid'] + '">' if imgs['3_Behav_15feat_f1_grid'] else ''}</div>
      <div class="plot-wrap"><div class="plot-title">混淆矩陣（最佳模型）</div>
        {'<img src="' + imgs['3_Behav_15feat_confusion'] + '">' if imgs['3_Behav_15feat_confusion'] else ''}</div>
    </div>
  </div>
  <div class="card g-core">
    <span class="dot-core"></span><b>Core_6feat</b>
    <div class="g-plot" style="grid-template-columns:1fr">
      <div class="plot-wrap"><div class="plot-title">F1-score Grid</div>
        {'<img src="' + imgs['3_Core_6feat_f1_grid'] + '">' if imgs['3_Core_6feat_f1_grid'] else ''}</div>
      <div class="plot-wrap"><div class="plot-title">混淆矩陣（最佳模型）</div>
        {'<img src="' + imgs['3_Core_6feat_confusion'] + '">' if imgs['3_Core_6feat_confusion'] else ''}</div>
    </div>
  </div>
</div>

<!-- ══ 四、Binary 結果 ════════════════════════════════════ -->
<h2 style="background:#16a34a">四、二元分類結果（Normal vs Overweight+Obese）</h2>

<div class="card">
  <h3>最佳模型摘要</h3>
  <table>
    <tr><th>特徵集</th><th>特徵數</th><th>最佳演算法</th><th>最佳抽樣</th><th style="text-align:center">Binary F1</th><th style="text-align:center">vs 3-class</th><th style="text-align:center">vs v2</th></tr>
    <tr style="background:#f0fdf4">
      <td><span class="dot-full"></span><b>Full_25feat</b></td><td>25</td><td>XGBoost</td><td>SMOTE</td>
      <td style="text-align:center"><b class="up">0.6867</b></td>
      <td style="text-align:center"><span class="up">+0.1912</span></td>
      <td style="text-align:center"><span style="color:#6b7280;font-size:12px">≈ v2 Full_21 (0.6883)</span></td>
    </tr>
    <tr>
      <td><span class="dot-behav"></span><b>Behav_15feat</b></td><td>15</td><td>XGBoost</td><td>SMOTE</td>
      <td style="text-align:center"><b>0.6800</b></td>
      <td style="text-align:center"><span class="up">+0.1969</span></td>
      <td style="text-align:center"><span class="badge b-new">全新</span></td>
    </tr>
    <tr>
      <td><span class="dot-core"></span><b>Core_6feat</b></td><td>6</td><td>XGBoost</td><td>SMOTE</td>
      <td style="text-align:center">0.6082</td>
      <td style="text-align:center"><span class="up">+0.1895</span></td>
      <td style="text-align:center"><span style="color:#6b7280;font-size:12px">≈ v2 Slim_5 (0.6087)</span></td>
    </tr>
  </table>

  <div class="hl">
    🎯 <b>關鍵發現：Behav_15 vs Full_25 差距僅 0.0067（&lt;1%）</b><br>
    去掉全部 7 個慢性病診斷後，F1 從 0.6867 只降至 0.6800。<br>
    → <b>行為習慣與健康感受，幾乎能完全取代疾病診斷記錄</b>，支持以「行為介入」為核心的公衛政策方向。
  </div>
</div>

<!-- Binary 圖表 -->
<div class="g3">
  <div class="card g-full">
    <span class="dot-full"></span><b>Full_25feat — Binary</b>
    <div class="g-plot" style="grid-template-columns:1fr">
      <div class="plot-wrap"><div class="plot-title">F1-score Grid</div>
        {'<img src="' + imgs['b_Full_25feat_f1_grid'] + '">' if imgs['b_Full_25feat_f1_grid'] else ''}</div>
      <div class="plot-wrap"><div class="plot-title">混淆矩陣（最佳模型）</div>
        {'<img src="' + imgs['b_Full_25feat_confusion'] + '">' if imgs['b_Full_25feat_confusion'] else ''}</div>
    </div>
  </div>
  <div class="card g-behav">
    <span class="dot-behav"></span><b>Behav_15feat — Binary</b>
    <div class="g-plot" style="grid-template-columns:1fr">
      <div class="plot-wrap"><div class="plot-title">F1-score Grid</div>
        {'<img src="' + imgs['b_Behav_15feat_f1_grid'] + '">' if imgs['b_Behav_15feat_f1_grid'] else ''}</div>
      <div class="plot-wrap"><div class="plot-title">混淆矩陣（最佳模型）</div>
        {'<img src="' + imgs['b_Behav_15feat_confusion'] + '">' if imgs['b_Behav_15feat_confusion'] else ''}</div>
    </div>
  </div>
  <div class="card g-core">
    <span class="dot-core"></span><b>Core_6feat — Binary</b>
    <div class="g-plot" style="grid-template-columns:1fr">
      <div class="plot-wrap"><div class="plot-title">F1-score Grid</div>
        {'<img src="' + imgs['b_Core_6feat_f1_grid'] + '">' if imgs['b_Core_6feat_f1_grid'] else ''}</div>
      <div class="plot-wrap"><div class="plot-title">混淆矩陣（最佳模型）</div>
        {'<img src="' + imgs['b_Core_6feat_confusion'] + '">' if imgs['b_Core_6feat_confusion'] else ''}</div>
    </div>
  </div>
</div>

<!-- ══ 五、特徵重要度 ════════════════════════════════════ -->
<h2 style="background:#7c3aed">五、特徵重要度分析（Binary XGBoost）</h2>

<div class="g3">
  <div class="card g-full">
    <span class="dot-full"></span><b>Full_25feat</b>
    <div class="plot-wrap" style="margin-top:10px">
      {'<img src="' + imgs['b_Full_25feat_importance'] + '">' if imgs['b_Full_25feat_importance'] else ''}
    </div>
    <h4 style="margin-top:14px">Top 7 特徵</h4>
    <table>
      <tr><th>#</th><th>特徵</th><th>重要度</th></tr>
      <tr><td>1</td><td>arthritis</td><td>0.1207</td></tr>
      <tr><td>2</td><td>exercised</td><td>0.1105</td></tr>
      <tr><td>3</td><td><b>asthma</b> <span class="badge b-new">新</span></td><td>0.0934</td></tr>
      <tr><td>4</td><td>sex</td><td>0.0917</td></tr>
      <tr><td>5</td><td>general_health</td><td>0.0887</td></tr>
      <tr><td>6</td><td><b>dental_visit</b> <span class="badge b-new">新</span></td><td>0.0746</td></tr>
      <tr><td>7</td><td>diabetes</td><td>0.0744</td></tr>
    </table>
  </div>
  <div class="card g-behav">
    <span class="dot-behav"></span><b>Behav_15feat</b>
    <div class="plot-wrap" style="margin-top:10px">
      {'<img src="' + imgs['b_Behav_15feat_importance'] + '">' if imgs['b_Behav_15feat_importance'] else ''}
    </div>
    <h4 style="margin-top:14px">Top 5 特徵（慢性病移除後重排）</h4>
    <table>
      <tr><th>#</th><th>特徵</th><th>重要度</th></tr>
      <tr><td>1</td><td>exercised ▲ 奪回首位</td><td>0.1520</td></tr>
      <tr><td>2</td><td>sex</td><td>0.1460</td></tr>
      <tr><td>3</td><td>general_health ▲</td><td>0.1438</td></tr>
      <tr><td>4</td><td>diff_walking ▲▲ 大幅上升</td><td>0.1195</td></tr>
      <tr><td>5</td><td>depression ▲▲ 大幅上升</td><td>0.1069</td></tr>
    </table>
    <div class="info-box" style="margin-top:10px;font-size:12px">
      diff_walking 和 depression 在完整模型中被慢性病「遮蔽」了。去掉慢性病後，這兩個症狀成為模型重要依據。
    </div>
  </div>
  <div class="card g-core">
    <span class="dot-core"></span><b>Core_6feat</b>
    <div class="plot-wrap" style="margin-top:10px">
      {'<img src="' + imgs['b_Core_6feat_importance'] + '">' if imgs['b_Core_6feat_importance'] else ''}
    </div>
    <h4 style="margin-top:14px">6 個特徵重要度分佈</h4>
    <table>
      <tr><th>#</th><th>特徵</th><th>重要度</th></tr>
      <tr><td>1</td><td>general_health 主導</td><td>0.4180</td></tr>
      <tr><td>2</td><td>exercised</td><td>0.2583</td></tr>
      <tr><td>3</td><td>smoking_status</td><td>0.1198</td></tr>
      <tr><td>4</td><td>drinks_per_week</td><td>0.1195</td></tr>
      <tr><td>5</td><td>sleep_hours</td><td>0.0586</td></tr>
      <tr><td>6</td><td>drank_any（最弱）</td><td>0.0258</td></tr>
    </table>
    <div class="info-box" style="margin-top:10px;font-size:12px">
      6 個特徵時，自評健康獨佔 42% 重要度。「喝多少」比「有沒有喝」更重要。
    </div>
  </div>
</div>

<!-- ══ 六、跨群組比較 ════════════════════════════════════ -->
<h2 style="background:#0f172a">六、跨群組完整比較</h2>

<div class="card">
  <h3>F1-score 對比（3-class vs Binary）</h3>
  <table>
    <tr>
      <th>特徵集</th><th>特徵數</th>
      <th style="text-align:center">3-class F1</th>
      <th style="text-align:center">Binary F1</th>
      <th style="text-align:center">Binary 提升幅度</th>
      <th>最佳演算法</th>
    </tr>
    <tr style="background:#eff6ff">
      <td><span class="dot-full"></span><b>Full_25feat</b></td><td>25</td>
      <td style="text-align:center">0.4955</td>
      <td style="text-align:center"><b class="up">0.6867</b></td>
      <td style="text-align:center"><span class="up">+0.1912</span></td>
      <td>XGBoost (SMOTE)</td>
    </tr>
    <tr>
      <td><span class="dot-behav"></span><b>Behav_15feat</b></td><td>15</td>
      <td style="text-align:center">0.4831</td>
      <td style="text-align:center"><b>0.6800</b></td>
      <td style="text-align:center"><span class="up">+0.1969</span></td>
      <td>XGBoost (SMOTE)</td>
    </tr>
    <tr>
      <td><span class="dot-core"></span><b>Core_6feat</b></td><td>6</td>
      <td style="text-align:center">0.4187</td>
      <td style="text-align:center">0.6082</td>
      <td style="text-align:center"><span class="up">+0.1895</span></td>
      <td>XGBoost (SMOTE)</td>
    </tr>
  </table>

  <div class="hl" style="margin-top:16px">
    <b>結構性發現：三組 Binary 提升幅度均為 +0.19（一致）</b><br>
    無論特徵集多完整或多精簡，切換到 Binary 任務的提升幅度幾乎完全一致。<br>
    → 瓶頸 100% 來自 <b>Normal/Overweight 邊界的天然模糊性</b>，而非特徵選取或演算法選擇問題。
    這是一個有助於論文討論的重要結構性發現。
  </div>
</div>

<div class="card">
  <h3>新增特徵貢獻評估</h3>
  <table>
    <tr><th>新增特徵</th><th>Full_25 重要度排名</th><th>重要度</th><th>評估</th></tr>
    <tr>
      <td><b>asthma</b> <span class="badge b-new">新增</span></td>
      <td>第 3 名</td>
      <td><span class="up">0.0934</span></td>
      <td>✅ 超出預期，氣喘與肥胖的雙向關係非常強，加入正確</td>
    </tr>
    <tr>
      <td><b>dental_visit</b> <span class="badge b-new">新增</span></td>
      <td>第 6 名</td>
      <td><span class="up">0.0746</span></td>
      <td>✅ 高於預期，健康意識代理效果良好，超過 diabetes（0.0744）</td>
    </tr>
    <tr>
      <td><b>employment</b> <span class="badge b-new">新增</span></td>
      <td>第 16 名</td>
      <td>0.0181</td>
      <td>⚠️ 在 Full_25 被壓制；在 Behav_15 達 0.0247，仍有一定貢獻</td>
    </tr>
    <tr>
      <td><b>rent_or_own</b> <span class="badge b-new">新增</span></td>
      <td>第 13 名</td>
      <td>0.0253</td>
      <td>⚠️ 中等，主要捕捉 SES 信號，與 income/education 有重疊</td>
    </tr>
  </table>
</div>

<!-- ══ 七、討論與結論 ════════════════════════════════════ -->
<h2 style="background:#166534">七、討論、結論與限制</h2>

<div class="card">
  <h3>核心論點（建議簡報使用）</h3>
  <div class="hl">
    「本研究以 CDC BRFSS 2022（329,126 筆）驗證生活習慣對肥胖風險的預測效力。
    三群特徵集的階梯式設計揭示：
    <ol>
      <li>完整模型（25 feat, F1=0.687）是預測上限</li>
      <li><b>行為健康模型（15 feat, F1=0.680）不使用任何疾病診斷，與完整模型差距僅 0.007（&lt;1%）</b></li>
      <li>核心行為模型（6 feat, F1=0.608）僅需 6 個問題即可達到基本預測效力</li>
    </ol>
    此結果支持以行為介入為核心的公衛政策方向，且顯示日常生活習慣指標幾乎能完整取代疾病診斷記錄的預測價值。」
  </div>
</div>

<div class="card">
  <h3>研究限制（Limitation）</h3>
  <table>
    <tr><th>限制項目</th><th>說明</th></tr>
    <tr>
      <td><b>無飲食資料</b></td>
      <td>BRFSS 2022 主檔不含 FRUIT2/VEGETAB2 等飲食變數，為最主要特徵缺口。飲食是肥胖最直接相關因子，缺失可能低估模型潛力。</td>
    </tr>
    <tr>
      <td><b>運動僅 Yes/No</b></td>
      <td>EXERANY2 為二元變數，無法區分運動強度、頻率、類型。粗糙的運動指標可能限制其區分能力。</td>
    </tr>
    <tr>
      <td><b>逆向因果（慢性病）</b></td>
      <td>arthritis、diabetes 等為肥胖後果而非原因，Full_25 組具有逆向因果風險。Behav_15 的設計正是為解決此問題。</td>
    </tr>
    <tr>
      <td><b>橫斷面資料</b></td>
      <td>BRFSS 為截面調查，無法建立因果推論，僅能說明相關性。</td>
    </tr>
    <tr>
      <td><b>族群侷限</b></td>
      <td>BRFSS 僅限美國成年人，結果推論至其他族群（尤其亞洲族群，BMI 標準不同）需謹慎。</td>
    </tr>
    <tr>
      <td><b>自報資料偏差</b></td>
      <td>身高體重、飲食行為均由受測者自報，存在社會期許偏差（Social Desirability Bias）。</td>
    </tr>
  </table>
</div>

<div class="card">
  <h3>三次迭代演進摘要</h3>
  <table>
    <tr><th>版本</th><th>資料集</th><th>特徵設計</th><th>最佳 F1</th><th>主要貢獻</th></tr>
    <tr>
      <td>v1</td>
      <td>NHANES 2017-18</td>
      <td>~10 feat</td>
      <td>~0.55 (binary)</td>
      <td>建立基礎流程，FastAPI 部署</td>
    </tr>
    <tr>
      <td>v2</td>
      <td>BRFSS 2022<br>338,666 筆</td>
      <td>Full_21 / Habit_10 / Slim_5<br>21 feat max</td>
      <td>0.6883 (binary)</td>
      <td>大幅擴大資料量，引入 3-class 任務</td>
    </tr>
    <tr style="background:#f0fdf4">
      <td><b>v3 ✅</b></td>
      <td><b>BRFSS 2022<br>329,126 筆</b></td>
      <td><b>Full_25 / Behav_15 / Core_6<br>重新設計 3 群，加入 4 新變數</b></td>
      <td><b>0.6867 (binary)</b></td>
      <td><b>階梯式消除設計，逆向因果分析，Behav_15 關鍵發現</b></td>
    </tr>
  </table>
</div>

<footer>
  obesity_project_3 &nbsp;·&nbsp; CDC BRFSS 2022 &nbsp;·&nbsp; 329,126 rows × 26 cols &nbsp;·&nbsp; 2026-05-24
</footer>
</div>
</body>
</html>"""

OUT.write_text(html, encoding="utf-8")
size_kb = OUT.stat().st_size / 1024
print(f"Done: {OUT}")
print(f"Size: {size_kb:.0f} KB")
