import os
os.makedirs('D:/07_Claude/01_Master_Report/obesity_project_3/outputs', exist_ok=True)

html = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BRFSS 2022 - 資料探索報告</title>
<style>
  :root{--blue:#1d4ed8;--green:#15803d;--bg:#f8fafc;--card:#fff}
  body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--bg);color:#1a1a2e;margin:0;padding:24px}
  .container{max-width:1120px;margin:0 auto}
  h1{font-size:24px;margin-bottom:4px;color:#0f172a}
  h2{font-size:18px;margin:36px 0 12px;padding-left:12px;border-left:5px solid #1d4ed8;color:#1e3a5f}
  h3{font-size:15px;margin:18px 0 8px;color:#334155}
  .meta{color:#64748b;font-size:13px;margin-bottom:28px}
  .card{background:var(--card);border-radius:10px;padding:20px 24px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,.08)}
  table{border-collapse:collapse;width:100%;font-size:13px}
  th{background:#1e3a5f;color:#fff;padding:9px 12px;text-align:left;font-weight:600}
  td{padding:8px 12px;border-bottom:1px solid #e2e8f0;vertical-align:top;line-height:1.5}
  tr:hover td{background:#f8fafc}
  .tag{display:inline-block;padding:2px 9px;border-radius:10px;font-size:12px;font-weight:700;margin-right:6px}
  .t-habit{background:#dbeafe;color:#1d4ed8}
  .t-health{background:#dcfce7;color:#15803d}
  .t-chronic{background:#fee2e2;color:#b91c1c}
  .t-demo{background:#fef3c7;color:#92400e}
  .t-sdh{background:#ede9fe;color:#5b21b6}
  .t-target{background:#fce7f3;color:#9d174d}
  .step{display:flex;align-items:center;gap:16px;margin:8px 0;padding:12px 16px;background:#f8fafc;border-radius:8px;border-left:4px solid #cbd5e1}
  .step.drop{border-left-color:#ef4444}
  .step.keep{border-left-color:#22c55e}
  .step.info{border-left-color:#3b82f6}
  .step.opt{border-left-color:#a855f7;opacity:.8}
  .step-n{font-size:20px;font-weight:700;color:#0f172a;min-width:100px}
  .step-desc{color:#475569;font-size:13px;flex:1}
  .step-delta{font-size:12px;color:#ef4444;white-space:nowrap}
  .step-delta.pos{color:#16a34a}
  .warn{background:#fef9c3;border:1px solid #fde047;border-radius:6px;padding:10px 14px;font-size:13px;color:#713f12;margin:10px 0}
  .note{background:#eff6ff;border:1px solid #bfdbfe;border-radius:6px;padding:10px 14px;font-size:13px;color:#1e40af;margin:10px 0}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
  code{background:#f1f5f9;padding:2px 6px;border-radius:4px;font-family:monospace;font-size:12px;color:#0f172a}
  .bar-row{display:flex;align-items:center;gap:10px;margin:6px 0;font-size:13px}
  .bar-label{min-width:130px;color:#334155;font-size:12px}
  .bar{height:24px;border-radius:4px;display:flex;align-items:center;padding:0 10px;font-size:12px;font-weight:700;color:#fff}
  .bar-pct{min-width:50px;color:#64748b;font-size:12px}
  .bar-n{color:#94a3b8;font-size:11px}
  .sdh-badge{background:#7c3aed;color:#fff;border-radius:4px;padding:2px 7px;font-size:11px;font-weight:700}
  .good{color:#16a34a;font-weight:700}
  .warn-val{color:#d97706;font-weight:700}
  .bad-val{color:#dc2626;font-weight:700}
  footer{text-align:center;color:#94a3b8;font-size:12px;margin-top:48px;padding-top:20px;border-top:1px solid #e2e8f0}
</style>
</head>
<body>
<div class="container">

<h1>BRFSS 2022 — 資料探索 &amp; ETL 分析報告</h1>
<p class="meta">資料來源：CDC BRFSS 2022 (LLCP2022.XPT) &nbsp;|&nbsp; 生成日期：2026-05-24 &nbsp;|&nbsp; 專案：obesity_project_3</p>

<!-- ===== SECTION 1: BASIC INFO + ETL FLOW ===== -->
<h2>一、資料集基本資訊 &amp; ETL 逐步篩選</h2>
<div class="card">
  <div class="grid2">
    <div>
      <h3>資料基本資訊</h3>
      <table>
        <tr><td><b>原始筆數</b></td><td>445,132 筆</td></tr>
        <tr><td><b>變數數</b></td><td>328 個</td></tr>
        <tr><td><b>睡眠變數 SLEPTIM1</b></td><td>✅ 存在（這是選 2022 的核心理由）</td></tr>
        <tr><td><b>目標變數</b></td><td><code>_BMI5CAT</code>（WHO 4 級 BMI 分類）</td></tr>
        <tr><td><b>資料年份</b></td><td>2022（COVID 後第 2 年，資料穩定）</td></tr>
      </table>
      <br>
      <h3>年度比較（為何選 2022）</h3>
      <table>
        <tr><th>年份</th><th>筆數</th><th>SLEPTIM1</th></tr>
        <tr><td>2019</td><td>418,268</td><td style="color:#dc2626">無（OFF 年）</td></tr>
        <tr><td>2020-21</td><td>—</td><td style="color:#dc2626">跳過（COVID）</td></tr>
        <tr style="background:#f0fdf4"><td><b>2022 ✅</b></td><td><b>445,132</b></td><td style="color:#16a34a"><b>有</b></td></tr>
        <tr><td>2023</td><td>433,323</td><td style="color:#dc2626">無（OFF 年）</td></tr>
        <tr><td>2024</td><td>457,670</td><td style="color:#dc2626">無（OFF 年）</td></tr>
      </table>
    </div>
    <div>
      <h3>逐步 ETL 篩選（筆數變化）</h3>
      <div class="step info"><div class="step-n">445,132</div><div class="step-desc"><b>Step 0</b> 原始資料（Raw）</div></div>
      <div class="step drop"><div class="step-n">396,326</div><div class="step-desc"><b>Step 1</b> 刪除 <code>_BMI5CAT</code> 缺值</div><div class="step-delta">-48,806</div></div>
      <div class="step info"><div class="step-n">396,326</div><div class="step-desc"><b>Step 2</b> Underweight (1.7%) 併入 Normal，不刪行、改標籤</div><div class="step-delta pos">relabel 6,778</div></div>
      <div class="step drop"><div class="step-n">392,216</div><div class="step-desc"><b>Step 3</b> 刪除 <code>SLEPTIM1</code> 無效（77/99）</div><div class="step-delta">-4,110</div></div>
      <div class="step drop"><div class="step-n" style="color:#16a34a">338,666</div><div class="step-desc"><b>Step 4 ✅ 主分析資料集</b><br>刪除核心特徵（生活習慣/健康/慢性病/人口統計）無效值</div><div class="step-delta">-53,550</div></div>
      <div class="step opt"><div class="step-n">206,136</div><div class="step-desc"><b>Step 5* 選用</b> 額外刪除 SDH 缺值（含社會決定因素版本）</div><div class="step-delta">-132,530</div></div>
    </div>
  </div>
  <div class="note">✅ <b>主要實驗使用 338,666 筆</b>（原始的 76.1%）。SDH 模型使用 206,136 筆子集。</div>
</div>

<!-- ===== SECTION 2: TARGET VARIABLE ===== -->
<h2>二、目標變數 <code>_BMI5CAT</code></h2>
<div class="card">
  <div class="grid2">
    <div>
      <h3>BMI 計算方式（CDC 官方公式）</h3>
      <table>
        <tr><th colspan="2">計算流程</th></tr>
        <tr><td>①</td><td>受訪者提供英制身高 <code>HEIGHT3</code>（如 504 = 5ft 4in）</td></tr>
        <tr><td>②</td><td>CDC 轉公制：<code>HTM4</code>（公分）、<code>WTKG3</code>（kg × 100）</td></tr>
        <tr><td>③</td><td>公式：<b>BMI = 體重(kg) ÷ 身高(m)²</b></td></tr>
        <tr><td>④</td><td><code>_BMI5</code> = BMI × 100 儲存（2658 = BMI 26.58）</td></tr>
        <tr><td>⑤</td><td>按 WHO 標準轉為 <code>_BMI5CAT</code></td></tr>
      </table>
      <br>
      <table>
        <tr><th>_BMI5CAT</th><th>名稱</th><th>BMI 範圍</th><th>本專案</th></tr>
        <tr><td>1</td><td>Underweight</td><td>&lt; 18.50</td><td>→ 併入 Normal</td></tr>
        <tr style="background:#f0fdf4"><td><b>2</b></td><td><b>Normal weight</b></td><td>18.50 – 24.99</td><td><b>類別 0</b></td></tr>
        <tr style="background:#fefce8"><td><b>3</b></td><td><b>Overweight</b></td><td>25.00 – 29.99</td><td><b>類別 1</b></td></tr>
        <tr style="background:#fff1f2"><td><b>4</b></td><td><b>Obese</b></td><td>≥ 30.00</td><td><b>類別 2</b></td></tr>
      </table>
    </div>
    <div>
      <h3>分佈（Step 4 後，338,666 筆）</h3>
      <div class="bar-row">
        <div class="bar-label">Normal (0) 含Underweight</div>
        <div class="bar" style="width:185px;background:#22c55e">30.9%</div>
        <div class="bar-pct">30.9%</div>
        <div class="bar-n">104,654</div>
      </div>
      <div class="bar-row">
        <div class="bar-label">Overweight (1)</div>
        <div class="bar" style="width:212px;background:#f59e0b">35.4%</div>
        <div class="bar-pct">35.4%</div>
        <div class="bar-n">119,957</div>
      </div>
      <div class="bar-row">
        <div class="bar-label">Obese (2)</div>
        <div class="bar" style="width:202px;background:#ef4444">33.7%</div>
        <div class="bar-pct">33.7%</div>
        <div class="bar-n">114,055</div>
      </div>
      <div class="note" style="margin-top:16px">
        ✅ 三類分佈 <b>30.9% / 35.4% / 33.7%</b> 相當均衡！<br>
        對比 Project 2 的二元目標（91% vs 9%），本次無嚴重不平衡問題。<br>
        仍可比較 Raw Data vs SMOTE vs Under-sampling 的效果差異。
      </div>
    </div>
  </div>
</div>

<!-- ===== SECTION 3: FEATURE CATALOG ===== -->
<h2>三、特徵完整目錄（5 大類）</h2>

<div class="card">
  <h3><span class="tag t-habit">生活習慣 Life Habits</span> 最核心的可改變行為指標</h3>
  <table>
    <tr><th>變數</th><th>中文名稱</th><th>英文說明</th><th>有效值範圍</th><th>特殊碼 ETL</th><th>有效率</th></tr>
    <tr>
      <td><code>SLEPTIM1</code></td>
      <td>每晚睡眠時數 ⭐</td>
      <td>Avg hours of sleep per 24-hr period</td>
      <td>1 – 24 小時（整數）</td>
      <td>77=不知道 → NaN<br>99=拒答 → NaN<br><b>注意：7=7小時（有效！）</b><br>&gt;16hr → cap 或 drop</td>
      <td class="good">99.0%</td>
    </tr>
    <tr>
      <td><code>_SMOKER3</code></td>
      <td>吸菸狀態（4級計算值）</td>
      <td>Computed smoking status (4 levels)</td>
      <td>1=每日, 2=偶爾<br>3=曾吸, 4=從不</td>
      <td>9=不知道 → NaN</td>
      <td class="good">96.3%</td>
    </tr>
    <tr>
      <td><code>DRNKANY6</code></td>
      <td>過去30天有無飲酒</td>
      <td>Drank any alcohol in past 30 days</td>
      <td>1=Yes → 1<br>2=No → 0</td>
      <td>7=不知道, 9=拒答 → NaN</td>
      <td class="good">93.9%</td>
    </tr>
    <tr>
      <td><code>_DRNKWK2</code></td>
      <td>每週飲酒次數（計算值）</td>
      <td>Computed drinks consumed per week</td>
      <td>連續值（× 100 儲存）<br>e.g. 100 = 1.0 drink/week</td>
      <td><b>5.4e-79 = SAS 零值 → 0</b><br>77777=不知道 → NaN</td>
      <td class="good">100%</td>
    </tr>
    <tr>
      <td><code>EXERANY2</code></td>
      <td>過去30天有無運動</td>
      <td>Any physical activity in past 30 days</td>
      <td>1=Yes → 1<br>2=No → 0</td>
      <td>7=不知道, 9=拒答 → NaN</td>
      <td class="good">99.8%</td>
    </tr>
  </table>
</div>

<div class="card">
  <h3><span class="tag t-health">健康狀態 Health Status</span> 自評健康感受與功能限制</h3>
  <table>
    <tr><th>變數</th><th>中文名稱</th><th>英文說明</th><th>有效值範圍</th><th>特殊碼 ETL</th><th>有效率</th></tr>
    <tr>
      <td><code>GENHLTH</code></td>
      <td>自評整體健康（5級）</td>
      <td>General health condition (self-reported)</td>
      <td>1=Excellent, 2=Very good<br>3=Good, 4=Fair, 5=Poor</td>
      <td>7=不知道, 9=拒答 → NaN<br><b>⚠ 數值越大越不健康（反向）</b></td>
      <td class="good">99.8%</td>
    </tr>
    <tr>
      <td><code>MENTHLTH</code></td>
      <td>心理不健康天數（近30天）</td>
      <td>Days mental health was not good (past 30 days)</td>
      <td>1–30 天（連續）</td>
      <td><b>88 = 0天 → 重新編碼為 0 ⚠</b><br>77=不知道, 99=拒答 → NaN</td>
      <td class="good">98.1%</td>
    </tr>
    <tr>
      <td><code>PHYSHLTH</code></td>
      <td>身體不健康天數（近30天）</td>
      <td>Days physical health was not good (past 30 days)</td>
      <td>1–30 天（連續）</td>
      <td><b>88 = 0天 → 重新編碼為 0 ⚠</b><br>77=不知道, 99=拒答 → NaN</td>
      <td class="good">97.8%</td>
    </tr>
    <tr>
      <td><code>DIFFWALK</code></td>
      <td>行走或爬樓梯困難</td>
      <td>Serious difficulty walking or climbing stairs</td>
      <td>1=Yes → 1<br>2=No → 0</td>
      <td>7=不知道, 9=拒答, NaN → 全部 drop</td>
      <td class="warn-val">98.7%</td>
    </tr>
    <tr>
      <td><code>ADDEPEV3</code></td>
      <td>曾被診斷憂鬱症</td>
      <td>Ever told had a depressive disorder</td>
      <td>1=Yes → 1<br>2=No → 0</td>
      <td>7=不知道, 9=拒答 → NaN</td>
      <td class="good">99.5%</td>
    </tr>
  </table>
</div>

<div class="card">
  <h3><span class="tag t-chronic">慢性病史 Chronic Disease History</span> 醫師曾診斷的既有疾病</h3>
  <table>
    <tr><th>變數</th><th>中文名稱</th><th>英文說明</th><th>有效值 / ETL 編碼</th><th>有效率</th></tr>
    <tr>
      <td><code>DIABETE4</code></td>
      <td>糖尿病（含前期/妊娠）</td>
      <td>Ever told had diabetes (4 levels in 2022)</td>
      <td>原始：1=Yes, 2=妊娠期, 3=No, 4=前期<br><b>→ 編碼：0=No(3) / 1=前期(4) / 2=Yes(1,2)</b><br>7/9 → NaN</td>
      <td class="good">99.8%</td>
    </tr>
    <tr><td><code>CVDCRHD4</code></td><td>冠狀動脈心臟病</td><td>Ever had coronary heart disease (CHD)</td><td>1=Yes→1, 2=No→0 / 7,9→NaN</td><td class="good">99.1%</td></tr>
    <tr><td><code>CVDSTRK3</code></td><td>中風</td><td>Ever had a stroke</td><td>1=Yes→1, 2=No→0 / 7,9→NaN</td><td class="good">99.7%</td></tr>
    <tr><td><code>CHCCOPD3</code></td><td>慢性肺阻塞 COPD</td><td>Ever told had COPD or chronic bronchitis</td><td>1=Yes→1, 2=No→0 / 7,9→NaN</td><td class="good">99.6%</td></tr>
    <tr><td><code>HAVARTH4</code></td><td>關節炎</td><td>Ever told had some form of arthritis</td><td>1=Yes→1, 2=No→0 / 7,9→NaN</td><td class="good">99.5%</td></tr>
    <tr><td><code>CHCKDNY2</code></td><td>慢性腎臟病</td><td>Ever told had kidney disease</td><td>1=Yes→1, 2=No→0 / 7,9→NaN</td><td class="good">99.6%</td></tr>
  </table>
</div>

<div class="card">
  <h3><span class="tag t-demo">人口統計 Demographics</span> 個人基本屬性</h3>
  <table>
    <tr><th>變數</th><th>中文名稱</th><th>英文說明</th><th>有效值 / ETL 編碼</th><th>有效率</th></tr>
    <tr><td><code>_SEX</code></td><td>性別</td><td>Sex of respondent (computed)</td><td>1=Male→1, 2=Female→0</td><td class="good">100%</td></tr>
    <tr>
      <td><code>_AGEG5YR</code></td>
      <td>年齡組（5歲區間）</td>
      <td>Age group in five-year intervals</td>
      <td>1=18-24, 2=25-29, 3=30-34<br>4=35-39, ..., 13=80+, 14=DK→NaN</td>
      <td class="good">98.8%</td>
    </tr>
    <tr>
      <td><code>EDUCA</code></td>
      <td>最高教育程度</td>
      <td>Highest grade or year of school completed</td>
      <td>1=未受教育, 2=小學(1-8年級)<br>3=國高中(9-11年級), 4=高中畢/GED<br>5=大學1-3年, 6=大學4年以上 / 9→NaN</td>
      <td class="good">99.7%</td>
    </tr>
    <tr>
      <td><code>INCOME3</code></td>
      <td>家庭年收入（8級）</td>
      <td>Annual household income from all sources</td>
      <td>1=&lt;$15k, 2=$15-25k, 3=$25-35k<br>4=$35-50k, 5=$50-75k, 6=$75-100k<br>7=$100-200k, 8=≥$200k<br>77/99 → 建議保留為類別 9</td>
      <td class="warn-val">83.1%（16.9%拒答）</td>
    </tr>
    <tr>
      <td><code>MARITAL</code></td>
      <td>婚姻狀況</td>
      <td>Marital status</td>
      <td>1=已婚, 2=離婚, 3=喪偶<br>4=分居, 5=未婚, 6=同居伴侶 / 9→NaN</td>
      <td class="good">99.4%</td>
    </tr>
  </table>
  <div class="warn">⚠️ <b>INCOME3</b> 有 16.9% 拒答（最高單一缺值率）。建議做法：77/99 不刪除，改歸為第 9 類「未回答」，保留樣本量。</div>
</div>

<div class="card">
  <h3><span class="tag t-sdh">社會決定因素 SDH</span> <span class="sdh-badge">2022 新增</span> 前兩次資料集完全沒有的維度</h3>
  <table>
    <tr><th>變數</th><th>中文名稱</th><th>英文說明</th><th>有效值範圍</th><th>缺值率</th></tr>
    <tr>
      <td><code>SDHFOOD1</code></td>
      <td>食物安全感（擔心沒食物）</td>
      <td>How often worried about having enough food</td>
      <td>1=總是, 2=通常, 3=有時<br>4=很少, 5=從不</td>
      <td class="bad-val">40.6% missing</td>
    </tr>
    <tr>
      <td><code>SDHBILLS</code></td>
      <td>財務壓力（無法付帳單）</td>
      <td>Had problems paying bills in past 12 months</td>
      <td>1=Yes→1, 2=No→0</td>
      <td class="bad-val">40.7% missing</td>
    </tr>
    <tr>
      <td><code>SDHISOLT</code></td>
      <td>社會孤立感</td>
      <td>How often felt isolated from others</td>
      <td>1=總是, 2=通常, 3=有時<br>4=很少, 5=從不</td>
      <td class="bad-val">40.4% missing</td>
    </tr>
    <tr>
      <td><code>EMTSUPRT</code></td>
      <td>情緒支持來源</td>
      <td>How often can get emotional support when needed</td>
      <td>1=總是, 2=通常, 3=有時<br>4=很少, 5=從不</td>
      <td class="bad-val">40.3% missing</td>
    </tr>
    <tr>
      <td><code>LSATISFY</code></td>
      <td>生活整體滿意度</td>
      <td>Satisfied with life in general</td>
      <td>1=非常滿意, 2=滿意<br>3=不滿意, 4=非常不滿意</td>
      <td class="bad-val">40.2% missing</td>
    </tr>
  </table>
  <div class="warn">
    ⚠️ <b>SDH 缺值高達 ~40%</b>，原因：這些問題屬 Optional Module，各州自行決定是否收集，並非全美強制。<br>
    <br>
    <b>➡ 建議：SDH 作為第四組特徵集（附加實驗）</b><br>
    主實驗（Full/Habit/Slim）在 <b>338,666 筆</b> 上進行（不含 SDH）。<br>
    額外實驗「Full+SDH」在 <b>206,136 筆</b> 子集上進行。<br>
    簡報討論：「加入社會決定因素後，是否能提升預測準確率？」→ 增加比較深度。
  </div>
</div>

<!-- ===== SECTION 4: ETL RULES ===== -->
<h2>四、ETL 關鍵編碼規則速查</h2>
<div class="card">
  <table>
    <tr><th>變數</th><th>原始 BRFSS 特殊值</th><th>ETL 處理方式</th><th>重要備註</th></tr>
    <tr>
      <td><code>SLEPTIM1</code></td>
      <td>77=不知道<br>99=拒答</td>
      <td>77/99 → NaN（刪除行）<br>值 &gt; 16hr → cap 至 16 或 drop</td>
      <td>⚠ 值 7 = 7小時（有效！），值 9 = 9小時（有效！）<br>不可將 7/9 當成特殊碼</td>
    </tr>
    <tr style="background:#fefce8">
      <td><code>MENTHLTH</code><br><code>PHYSHLTH</code></td>
      <td><b>88 = 0天（近30天完全健康）</b><br>77=不知道, 99=拒答</td>
      <td><b>88 → 0（最關鍵！）</b><br>77/99 → NaN</td>
      <td>最多人回答 88（約 60% 以上）。若直接 drop 88 會刪掉大量健康人群，造成嚴重偏差</td>
    </tr>
    <tr>
      <td><code>ALCDAY4</code></td>
      <td>101-107 = 每週 1-7 天<br>201-230 = 每月 1-30 天<br>888 = 近30天不喝</td>
      <td>101-107 → 值-100 天/週<br>201-230 → (值-200)/4.3 天/週<br>888 → 0 / 777/999 → NaN</td>
      <td>建議直接使用計算值 <code>_DRNKWK2</code> 更方便</td>
    </tr>
    <tr>
      <td><code>_DRNKWK2</code></td>
      <td>5.4e-79（SAS XPT 格式的零）<br>77777 = 不知道</td>
      <td>5.4e-79 → 0（不喝酒）<br>77777 → NaN</td>
      <td>儲存值為「每週飲酒次數 × 100」</td>
    </tr>
    <tr style="background:#fefce8">
      <td><code>DIABETE4</code></td>
      <td>1=糖尿病, 2=妊娠糖尿病<br>3=無, 4=前期糖尿病<br>7=不知道, 9=拒答</td>
      <td>3 → 0（No）<br>4 → 1（Pre-diabetes）<br>1, 2 → 2（Yes，含妊娠）<br>7/9 → NaN</td>
      <td>2022 年 DIABETE4 的編碼與 2020 年不同！<br>（2020 年 1=Yes, 2=gestational, 3=No, 4=borderline）</td>
    </tr>
    <tr>
      <td><code>GENHLTH</code></td>
      <td>1=Excellent, 2=Very good<br>3=Good, 4=Fair, 5=Poor<br>7=不知道, 9=拒答</td>
      <td>保留原始 1-5 值<br>7/9 → NaN</td>
      <td>⚠ 方向反直覺：數值越大 = 健康越差<br>建議在 README / codebook 明確標注</td>
    </tr>
    <tr>
      <td>所有二元 Yes/No 變數</td>
      <td>1=Yes, 2=No<br>7=不知道, 9=拒答</td>
      <td>1 → 1，2 → 0<br>7/9 → NaN（刪除行）</td>
      <td>包含：EXERANY2, DIFFWALK, ADDEPEV3,<br>CVDCRHD4, CVDSTRK3, CHCCOPD3, HAVARTH4, CHCKDNY2</td>
    </tr>
    <tr>
      <td><code>INCOME3</code></td>
      <td>1-8 = 有效收入等級<br>77=不知道, 99=拒答（16.9%）</td>
      <td><b>建議：77/99 → 9（保留為獨立類別）</b><br>而非刪除（會損失大量樣本）</td>
      <td>拒答收入很常見（隱私顧慮）。「拒答收入」本身可能對 BMI 有預測意義</td>
    </tr>
  </table>
</div>

<!-- ===== SECTION 5: FEATURE SETS ===== -->
<h2>五、建議特徵集設計（三主 + 一附加）</h2>
<div class="card">
  <table>
    <tr><th>特徵集</th><th>包含特徵</th><th>特徵數</th><th>設計理念</th><th>樣本數</th></tr>
    <tr style="background:#eff6ff">
      <td><b>Full</b></td>
      <td>SLEPTIM1, _SMOKER3, DRNKANY6, _DRNKWK2, EXERANY2,<br>GENHLTH, MENTHLTH, PHYSHLTH, DIFFWALK, ADDEPEV3,<br>DIABETE4, CVDCRHD4, CVDSTRK3, CHCCOPD3, HAVARTH4, CHCKDNY2,<br>_SEX, _AGEG5YR, EDUCA, INCOME3, MARITAL</td>
      <td>21</td>
      <td>全特徵，最高準確度</td>
      <td>338,666</td>
    </tr>
    <tr style="background:#f0fdf4">
      <td><b>Habit</b></td>
      <td>SLEPTIM1, _SMOKER3, DRNKANY6, EXERANY2,<br>GENHLTH, MENTHLTH, PHYSHLTH, DIFFWALK, ADDEPEV3, DIABETE4</td>
      <td>10</td>
      <td>純生活習慣 + 健康感受，不需人口統計/疾病史</td>
      <td>338,666</td>
    </tr>
    <tr style="background:#fff7ed">
      <td><b>Slim</b></td>
      <td>SLEPTIM1, _SMOKER3, DRNKANY6, EXERANY2, GENHLTH</td>
      <td>5</td>
      <td>最精簡可改變行為，前端互動易輸入</td>
      <td>338,666</td>
    </tr>
    <tr style="background:#fdf4ff">
      <td><b>Full+SDH</b><br><span class="sdh-badge">附加</span></td>
      <td>Full 的 21 個 +<br>SDHFOOD1, SDHBILLS, SDHISOLT, EMTSUPRT, LSATISFY</td>
      <td>26</td>
      <td>含社會決定因素，探索社經條件對 BMI 影響</td>
      <td><b>206,136</b>（SDH 子集）</td>
    </tr>
  </table>
  <div class="note" style="margin-top:14px">
    <b>主實驗矩陣：3 特徵集 × 3 演算法 × 3 抽樣策略 = 27 組合</b><br>
    演算法：Logistic Regression / Random Forest / XGBoost<br>
    抽樣：Raw Data / SMOTE / Random Under-sampling<br>
    指標：Weighted F1-score<br><br>
    <b>附加實驗：Full+SDH × 3 演算法 × 3 抽樣 = 9 組合</b>（討論社會因素的貢獻）
  </div>
</div>

<footer>
  Generated 2026-05-24 &nbsp;|&nbsp; CDC BRFSS 2022 (LLCP2022.XPT) &nbsp;|&nbsp; obesity_project_3
</footer>
</div>
</body>
</html>"""

out_path = 'D:/07_Claude/01_Master_Report/obesity_project_3/outputs/data_exploration_report.html'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'Done: {out_path}')
print(f'Size: {os.path.getsize(out_path):,} bytes')
