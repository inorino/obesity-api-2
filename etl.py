"""
etl.py — BRFSS 2022 ETL Pipeline
輸入：D:/07_Claude/01_Master_Report/LLCP2022.XPT
輸出：
  data/brfss2022_clean.csv    (主要使用，Python 跑模型用)
  data/brfss2022_clean.xlsx   (人工檢視用)
"""

import pandas as pd
import numpy as np
import os
import sys
import warnings
sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

os.makedirs("data", exist_ok=True)

# ─────────────────────────────────────────────
# 1. 讀取原始 XPT
# ─────────────────────────────────────────────
XPT_PATH = "D:/07_Claude/01_Master_Report/LLCP2022.XPT"
COLS_NEEDED = [
    "_BMI5CAT",
    "SLEPTIM1",
    "_SMOKER3",
    "DRNKANY6", "_DRNKWK2",
    "EXERANY2",
    "GENHLTH", "MENTHLTH", "PHYSHLTH", "DIFFWALK", "ADDEPEV3",
    "DIABETE4", "CVDCRHD4", "CVDSTRK3", "CHCCOPD3", "HAVARTH4", "CHCKDNY2",
    "ASTHMA3",
    "_SEX", "_AGEG5YR", "EDUCA", "INCOME3", "MARITAL",
    "EMPLOY1", "RENTHOM1", "_DENVST3",
]

print("載入 LLCP2022.XPT（約需 30-60 秒）...")
chunks = []
reader = pd.read_sas(XPT_PATH, format="xport", chunksize=50000)
for i, chunk in enumerate(reader):
    chunks.append(chunk[COLS_NEEDED])
    print(f"  {(i+1)*50000:,} rows loaded...", end="\r")
df = pd.concat(chunks, ignore_index=True)
print(f"\n原始筆數：{len(df):,}  ×  {df.shape[1]} 欄")

# ─────────────────────────────────────────────
# 2. 目標變數：_BMI5CAT
# ─────────────────────────────────────────────
# 刪除 missing
df = df[df["_BMI5CAT"].notna()].copy()
print(f"刪除 BMI 缺值後：{len(df):,}")

# Underweight (1) 併入 Normal (2)
df["_BMI5CAT"] = df["_BMI5CAT"].replace(1.0, 2.0)

# 3 類重新編碼：Normal=0, Overweight=1, Obese=2
df["bmi_cat"] = df["_BMI5CAT"].map({2.0: 0, 3.0: 1, 4.0: 2}).astype("Int64")
df = df.drop(columns=["_BMI5CAT"])

# ─────────────────────────────────────────────
# 3. 生活習慣
# ─────────────────────────────────────────────
# SLEPTIM1：77/99 → NaN；>16 小時 cap 至 16
df["SLEPTIM1"] = df["SLEPTIM1"].where(~df["SLEPTIM1"].isin([77, 99]))
df["SLEPTIM1"] = df["SLEPTIM1"].clip(upper=16)
df = df.rename(columns={"SLEPTIM1": "sleep_hours"})

# _SMOKER3：1/2/3/4 有效；9 → NaN
df["_SMOKER3"] = df["_SMOKER3"].where(~df["_SMOKER3"].isin([9]))
df = df.rename(columns={"_SMOKER3": "smoking_status"})

# DRNKANY6：1→1, 2→0, 7/9→NaN
df["DRNKANY6"] = df["DRNKANY6"].replace({1.0: 1, 2.0: 0})
df["DRNKANY6"] = df["DRNKANY6"].where(df["DRNKANY6"].isin([0, 1]))
df = df.rename(columns={"DRNKANY6": "drank_any"})

# _DRNKWK2：SAS 零值 5.4e-79 → 0；除以 100 得到實際飲酒次數/週；77777/99900→NaN
SAX_ZERO = 5.397605346934028e-79
df["_DRNKWK2"] = df["_DRNKWK2"].replace(SAX_ZERO, 0)
df["_DRNKWK2"] = df["_DRNKWK2"].where(~df["_DRNKWK2"].isin([77777, 99900]))
df["_DRNKWK2"] = df["_DRNKWK2"] / 100
df = df.rename(columns={"_DRNKWK2": "drinks_per_week"})

# EXERANY2：1→1, 2→0, 7/9→NaN
df["EXERANY2"] = df["EXERANY2"].replace({1.0: 1, 2.0: 0})
df["EXERANY2"] = df["EXERANY2"].where(df["EXERANY2"].isin([0, 1]))
df = df.rename(columns={"EXERANY2": "exercised"})

# ─────────────────────────────────────────────
# 4. 健康狀態
# ─────────────────────────────────────────────
# GENHLTH：7/9→NaN（1=Excellent 最好, 5=Poor 最差）
df["GENHLTH"] = df["GENHLTH"].where(~df["GENHLTH"].isin([7, 9]))
df = df.rename(columns={"GENHLTH": "general_health"})

# MENTHLTH / PHYSHLTH：88=0天 → 0；77/99→NaN
for col, newcol in [("MENTHLTH", "mental_health_days"), ("PHYSHLTH", "physical_health_days")]:
    df[col] = df[col].replace(88.0, 0)
    df[col] = df[col].where(~df[col].isin([77, 99]))
    df = df.rename(columns={col: newcol})

# DIFFWALK：1→1, 2→0, 7/9→NaN
df["DIFFWALK"] = df["DIFFWALK"].replace({1.0: 1, 2.0: 0})
df["DIFFWALK"] = df["DIFFWALK"].where(df["DIFFWALK"].isin([0, 1]))
df = df.rename(columns={"DIFFWALK": "diff_walking"})

# ADDEPEV3：1→1, 2→0, 7/9→NaN
df["ADDEPEV3"] = df["ADDEPEV3"].replace({1.0: 1, 2.0: 0})
df["ADDEPEV3"] = df["ADDEPEV3"].where(df["ADDEPEV3"].isin([0, 1]))
df = df.rename(columns={"ADDEPEV3": "depression"})

# ─────────────────────────────────────────────
# 5. 慢性病史
# ─────────────────────────────────────────────
# DIABETE4：3→0(No), 4→1(Pre), 1/2→2(Yes)；7/9→NaN
df["DIABETE4"] = df["DIABETE4"].replace({3.0: 0, 4.0: 1, 1.0: 2, 2.0: 2})
df["DIABETE4"] = df["DIABETE4"].where(df["DIABETE4"].isin([0, 1, 2]))
df = df.rename(columns={"DIABETE4": "diabetes"})

# 二元慢性病：1→1, 2→0, 7/9→NaN
for col, newcol in [
    ("CVDCRHD4", "heart_disease"),
    ("CVDSTRK3", "stroke"),
    ("CHCCOPD3", "copd"),
    ("HAVARTH4", "arthritis"),
    ("CHCKDNY2", "kidney_disease"),
    ("ASTHMA3",  "asthma"),
]:
    df[col] = df[col].replace({1.0: 1, 2.0: 0})
    df[col] = df[col].where(df[col].isin([0, 1]))
    df = df.rename(columns={col: newcol})

# ─────────────────────────────────────────────
# 6. 人口統計
# ─────────────────────────────────────────────
# _SEX：1=Male→1, 2=Female→0
df["_SEX"] = df["_SEX"].replace({1.0: 1, 2.0: 0})
df = df.rename(columns={"_SEX": "sex"})

# _AGEG5YR：14=DK→NaN
df["_AGEG5YR"] = df["_AGEG5YR"].where(~df["_AGEG5YR"].isin([14]))
df["_AGEG5YR"] = df["_AGEG5YR"].astype("Int64")
df = df.rename(columns={"_AGEG5YR": "age_group"})

# EDUCA：9=Refused→NaN
df["EDUCA"] = df["EDUCA"].where(~df["EDUCA"].isin([9]))
df["EDUCA"] = df["EDUCA"].astype("Int64")
df = df.rename(columns={"EDUCA": "education"})

# INCOME3：77/99/NaN → 9（保留為「未回答」獨立類別，不刪除行）
df["INCOME3"] = df["INCOME3"].replace({77.0: 9, 99.0: 9})
df["INCOME3"] = df["INCOME3"].fillna(9)
df["INCOME3"] = df["INCOME3"].astype("Int64")
df = df.rename(columns={"INCOME3": "income"})

# MARITAL：9=Refused→NaN
df["MARITAL"] = df["MARITAL"].where(~df["MARITAL"].isin([9]))
df["MARITAL"] = df["MARITAL"].astype("Int64")
df = df.rename(columns={"MARITAL": "marital_status"})

# EMPLOY1：1-8 有效（在職/自雇/失業/家管/學生/退休/無法工作）；9=Refused→NaN
df["EMPLOY1"] = df["EMPLOY1"].where(~df["EMPLOY1"].isin([9]))
df["EMPLOY1"] = df["EMPLOY1"].astype("Int64")
df = df.rename(columns={"EMPLOY1": "employment"})

# RENTHOM1：1=自有, 2=租屋, 3=其他；7/9→NaN
df["RENTHOM1"] = df["RENTHOM1"].where(~df["RENTHOM1"].isin([7, 9]))
df["RENTHOM1"] = df["RENTHOM1"].astype("Int64")
df = df.rename(columns={"RENTHOM1": "rent_or_own"})

# _DENVST3：1→1(有看牙醫), 2→0(沒有)；9→NaN
df["_DENVST3"] = df["_DENVST3"].replace({1.0: 1, 2.0: 0})
df["_DENVST3"] = df["_DENVST3"].where(df["_DENVST3"].isin([0, 1]))
df = df.rename(columns={"_DENVST3": "dental_visit"})

# ─────────────────────────────────────────────
# 7. 刪除含 NaN 的行（不含 income，已用類別 9 處理）
# ─────────────────────────────────────────────
cols_to_drop_nan = [
    "bmi_cat", "sleep_hours", "smoking_status", "drank_any",
    "drinks_per_week",
    "exercised", "general_health", "mental_health_days",
    "physical_health_days", "diff_walking", "depression",
    "diabetes", "heart_disease", "stroke", "copd", "asthma",
    "arthritis", "kidney_disease",
    "sex", "age_group", "education", "marital_status",
    "employment", "rent_or_own", "dental_visit",
]
before = len(df)
df = df.dropna(subset=cols_to_drop_nan)
print(f"刪除殘餘 NaN 後：{len(df):,}  (dropped {before - len(df):,})")

# 欄位排序（目標欄位放最後）
FINAL_COLS = [
    # 生活習慣 (5)
    "sleep_hours", "smoking_status", "drank_any", "drinks_per_week", "exercised",
    # 健康狀態 (5)
    "general_health", "mental_health_days", "physical_health_days",
    "diff_walking", "depression",
    # 慢性病史 (7)
    "diabetes", "heart_disease", "stroke", "copd", "asthma", "arthritis", "kidney_disease",
    # 人口統計 (7)
    "sex", "age_group", "education", "income", "marital_status",
    "employment", "rent_or_own",
    # 健康行為 (1)
    "dental_visit",
    # 目標變數
    "bmi_cat",
]
df = df[FINAL_COLS]

# ─────────────────────────────────────────────
# 8. 最終分佈確認
# ─────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"最終資料集：{len(df):,} 筆  ×  {df.shape[1]} 欄")
print(f"{'='*50}")
dist = df["bmi_cat"].value_counts().sort_index()
labels = {0: "Normal", 1: "Overweight", 2: "Obese"}
for k, v in dist.items():
    print(f"  {k} {labels[k]:12s}: {v:7,}  ({v/len(df)*100:.1f}%)")

print("\n各欄 NaN 確認：")
nan_check = df.isnull().sum()
nan_check = nan_check[nan_check > 0]
if len(nan_check) == 0:
    print("  全部欄位 NaN = 0 ✅")
else:
    print(nan_check)

# ─────────────────────────────────────────────
# 9. 輸出
# ─────────────────────────────────────────────
CSV_OUT   = "data/brfss2022_clean.csv"
EXCEL_OUT = "data/brfss2022_clean.xlsx"

print(f"\n輸出 CSV → {CSV_OUT} ...")
df.to_csv(CSV_OUT, index=False, encoding="utf-8-sig")
print(f"  完成  ({os.path.getsize(CSV_OUT)/1024/1024:.1f} MB)")

print(f"輸出 Excel → {EXCEL_OUT} ...")
with pd.ExcelWriter(EXCEL_OUT, engine="xlsxwriter") as writer:
    df.to_excel(writer, index=False, sheet_name="BRFSS2022_Clean")
    wb  = writer.book
    ws  = writer.sheets["BRFSS2022_Clean"]
    # 標題欄格式
    hdr_fmt = wb.add_format({"bold": True, "bg_color": "#1e3a5f",
                              "font_color": "white", "border": 1})
    for col_idx, col_name in enumerate(df.columns):
        ws.write(0, col_idx, col_name, hdr_fmt)
        ws.set_column(col_idx, col_idx, max(12, len(col_name) + 2))
    ws.freeze_panes(1, 0)
print(f"  完成  ({os.path.getsize(EXCEL_OUT)/1024/1024:.1f} MB)")

print("\n✅ ETL 完成！")
print(f"   CSV  : {CSV_OUT}")
print(f"   Excel: {EXCEL_OUT}")
