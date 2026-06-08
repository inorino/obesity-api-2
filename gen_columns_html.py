"""gen_columns_html.py — 產生 BRFSS 2022 全欄位說明 HTML"""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")

with open("outputs/col_stats.json", encoding="utf-8") as f:
    stats = {d["col"]: d for d in json.load(f)}

# ── 已使用欄位 ─────────────────────────────────────────────
USED = {
    "_BMI5CAT": "bmi_cat（目標變數）",
    "SLEPTIM1": "sleep_hours",
    "_SMOKER3": "smoking_status",
    "DRNKANY6": "drank_any",
    "_DRNKWK2": "drinks_per_week",
    "EXERANY2": "exercised",
    "GENHLTH":  "general_health",
    "MENTHLTH": "mental_health_days",
    "PHYSHLTH": "physical_health_days",
    "DIFFWALK": "diff_walking",
    "ADDEPEV3": "depression",
    "DIABETE4": "diabetes",
    "CVDCRHD4": "heart_disease",
    "CVDSTRK3": "stroke",
    "CHCCOPD3": "copd",
    "HAVARTH4": "arthritis",
    "CHCKDNY2": "kidney_disease",
    "_SEX":     "sex",
    "_AGEG5YR": "age_group",
    "EDUCA":    "education",
    "INCOME3":  "income",
    "MARITAL":  "marital_status",
}

# ── 欄位描述（中文） ─────────────────────────────────────────
DESC = {
    # 調查管理
    "_STATE":"受訪者所在州別（FIPS代碼）","FMONTH":"受訪月份","IDATE":"訪問日期",
    "IMONTH":"訪問月份","IDAY":"訪問日","IYEAR":"訪問年份",
    "DISPCODE":"問卷完成狀態（1100=完成/1200=部分）","SEQNO":"序列號",
    "_PSU":"抽樣單位","CTELENM1":"電話號碼是否匹配","PVTRESD1":"是否私人住宅",
    "COLGHOUS":"是否大學宿舍","STATERE1":"是否州內居民","CELPHON1":"是否手機號碼",
    "LADULT1":"是否為成人","COLGSEX1":"大學受訪者性別","NUMADULT":"家中成人數",
    "LANDSEX1":"市話受訪者性別","NUMMEN":"家中男性人數","NUMWOMEN":"家中女性人數",
    "NUMHHOL4":"家戶電話線數","NUMPHON4":"受訪者可用電話數","CELLFON5":"手機使用狀況",
    "CELLSEX1":"手機受訪者性別","CAGEG":"受訪年齡分組（粗略）","QSTLANG":"問卷語言",
    "QSTVER":"問卷版本","MSCODE":"都市化代碼","_METSTAT":"都會區狀態",
    "_URBSTAT":"城鄉狀態","_LLCPWT":"受訪者抽樣權重","_LLCPWT2":"抽樣權重2",
    "_STRWT":"地層抽樣權重","_RAWRAKE":"原始rake權重","_WT2RAKE":"第二次rake權重",
    "_STSTR":"地層","_CLLCPWT":"合併手機權重","_DUALCOR":"雙框架修正因子",
    "_DUALUSE":"是否同時使用手機和市話","RESPSLCT":"受訪者選取方式",
    "CSTATE1":"受訪州別確認","LOADULK2":"受訪資格確認","SDNATES1":"SDH原生州",
    "CPDEMO1C":"人口統計控制","RRATWRK2":"調整加權","RRCLASS3":"調整分類",
    "RRCOGNT2":"認知調整","RRHCARE4":"醫療照護調整","RRPHYSM2":"身體健康調整",
    "RRTREAT":"治療調整",
    # 健康狀態
    "GENHLTH":"自評整體健康（1=優秀 5=差）","PHYSHLTH":"過去30天身體不適天數",
    "MENTHLTH":"過去30天心理不適天數","POORHLTH":"健康不佳影響正常活動天數",
    "PERSDOC3":"是否有固定就診醫師","MEDCOST1":"過去12個月因費用無法就醫",
    "CHECKUP1":"上次常規健康檢查時間","LSATISFY":"生活整體滿意度",
    "EMTSUPRT":"情緒支持頻率","_RFHLTH":"自評健康是否良好（計算）",
    "_HLTHPLN":"是否有健康保險（計算）","_HCVU652":"65歲以下保險狀態",
    "PRIMINSR":"主要保險來源","WHEREGET":"主要就醫場所","HLTHPLN":"是否有健康保險",
    # 體重/BMI
    "WEIGHT2":"體重（磅）","HEIGHT3":"身高（英尺英寸）","WTKG3":"體重（公斤×100）",
    "HTM4":"身高（公分）","HTIN4":"身高（英寸）",
    "_BMI5":"BMI值×100","_BMI5CAT":"BMI分類（目標變數）","_RFBMI5":"是否過重（BMI≥25）",
    # 生活習慣
    "SLEPTIM1":"平均睡眠時數","EXERANY2":"過去30天是否有運動","_TOTINDA":"是否有休閒體力活動",
    "SMOKE100":"一生中是否吸過100根菸","SMOKDAY2":"目前每天還是偶爾抽菸",
    "STOPSMK2":"過去12個月是否嘗試戒菸","LASTSMK2":"最後一次吸菸是多久以前",
    "USENOW3":"目前是否使用無煙菸草","ECIGNOW2":"目前是否使用電子菸",
    "MENTCIGS":"過去30天使用傳統菸草天數","MENTECIG":"過去30天使用電子菸天數",
    "DRNKANY6":"過去30天是否喝酒","ALCDAY4":"過去30天喝酒天數",
    "AVEDRNK3":"飲酒時平均幾杯","MAXDRNKS":"過去30天最多一次喝幾杯",
    "DRNK3GE5":"過去30天喝5杯以上的天數","DROCDY4_":"每天飲酒次數（計算）",
    "SMALSTOL":"是否告知醫師飲酒量",
    # 菸草計算
    "_SMOKER3":"吸菸狀態（計算：1=每天/2=偶爾/3=曾抽/4=從不）",
    "_RFSMOK3":"是否為現在吸菸者（計算）","_SMOKGRP":"吸菸分組（計算）",
    "_CURECI2":"是否目前使用電子菸（計算）","_YRSQUIT":"戒菸年數",
    "_YRSSMOK":"吸菸年數","_PACKYRS":"包年（累積吸菸量）",
    "_PACKDAY":"每天吸幾包","HEATTBCO":"加熱型菸草使用",
    # 飲酒計算
    "_DRNKWK2":"每週平均飲酒次數（計算）","_RFBING6":"是否為暴飲者（計算）",
    "_RFDRHV8":"是否重度飲酒（計算）","ASBIBING":"哮喘+暴飲",
    "ASBIDRNK":"哮喘+飲酒","ASBIALCH":"哮喘+酒精","ASBIRDUC":"哮喘+戒酒建議",
    "ASBIADVC":"哮喘+飲酒建議",
    # 慢性病
    "CVDINFR4":"曾發生心肌梗塞","CVDCRHD4":"曾診斷冠狀動脈心臟病",
    "CVDSTRK3":"曾診斷中風","ASTHMA3":"曾診斷氣喘","ASTHNOW":"目前仍有氣喘",
    "CHCSCNC1":"曾診斷皮膚癌","CHCOCNC1":"曾診斷其他癌症","CHCCOPD3":"曾診斷COPD",
    "HAVARTH4":"曾診斷關節炎","ADDEPEV3":"曾診斷憂鬱症","CHCKDNY2":"曾診斷腎臟病",
    "DIABETE4":"糖尿病狀態（無/前期/確診）","DIABAGE4":"確診糖尿病年齡",
    "DIABEDU1":"是否接受糖尿病管理教育","DIABEYE1":"過去12個月眼睛檢查",
    "FEETSORE":"過去12個月足部潰瘍","INSULIN1":"是否使用胰島素",
    "PDIABTS1":"醫師是否告知前期糖尿病","PREDIAB2":"前期糖尿病狀態","DIABTYPE":"糖尿病類型",
    "COPDBRTH":"COPD導致呼吸困難","COPDBTST":"COPD肺功能測試",
    "COPDCOGH":"COPD慢性咳嗽","COPDFLEM":"COPD咳痰","COPDSMOK":"COPD+吸菸",
    "_DRDXAR2":"關節炎醫師診斷（計算）","_MICHD":"心臟病計算欄","_ASTHMS1":"氣喘狀態計算",
    "_CASTHM1":"目前氣喘計算","_LTASTH1":"終身氣喘計算",
    "CASTHDX2":"童年氣喘診斷","CASTHNO2":"童年氣喘現況",
    "CHKHEMO3":"血色素A1C檢測","CNCRTYP2":"癌症類型","CNCRAGE":"癌症診斷年齡",
    "CNCRDIFF":"癌症治療困難","HAVECFS":"是否有慢性疲勞症候群","TOLDCFS":"醫師診斷CFS",
    "WORKCFS":"CFS影響工作","CDASSIST":"CFS需要協助","CDDISCUS":"CFS討論",
    "CDHELP":"CFS獲得幫助","CDHOUSE":"CFS家庭支持","CDSOCIAL":"CFS社交影響",
    # 行動/失能
    "DIFFWALK":"行走或爬樓梯有困難","DIFFDRES":"自我穿著或洗澡有困難",
    "DIFFALON":"獨立處理事務有困難","BLIND":"視力障礙","DEAF":"聽力障礙",
    "DECIDE":"認知/記憶困難","CIMEMLOS":"記憶力問題",
    # 人口統計
    "_SEX":"性別（計算：1=男/2=女）","SEXVAR":"性別變數","BIRTHSEX":"出生性別",
    "TRNSGNDR":"跨性別認同","RCSGEND1":"性別認同","RCSRLTN2":"關係狀態",
    "RCSXBRTH":"出生性別詳細","_AGEG5YR":"年齡組別（5歲一組）",
    "_AGE65YR":"是否65歲以上","_AGE80":"是否80歲以上","_AGE_G":"年齡分組",
    "EDUCA":"最高教育程度","_EDUCAG":"教育程度分組",
    "INCOME3":"家庭年收入","_INCOMG1":"收入分組",
    "MARITAL":"婚姻狀態","CHILDREN":"家中18歲以下兒童數",
    "EMPLOY1":"就業狀態（在職/退休/無法工作等）","VETERAN3":"退伍軍人身份",
    "HHADULT":"家中成人數（版本2）","RENTHOM1":"租屋或自有","PREGNANT":"是否懷孕",
    "SOFEMALE":"女性樣本","SOMALE":"男性樣本",
    # 種族
    "_HISPANC":"是否西班牙裔","_IMPRACE":"歸因種族（計算）","_MRACE2":"多種族（計算）",
    "_PRACE2":"偏好種族","_CRACE2":"合併種族","_RACEPR1":"種族偏好1",
    "_RACEG22":"種族分組","_RACEGR4":"種族4分組","_RACE1":"種族1",
    "_CHISPNC":"西班牙裔計算","_CPRACE2":"合併種族2",
    # SDH
    "SDHBILLS":"難以支付帳單","SDHEMPLY":"就業問題","SDHFOOD1":"食物不安全",
    "SDHISOLT":"社會孤立","SDHSTRE1":"壓力程度","SDHTRNSP":"交通問題",
    "SDHUTILS":"水電瓦斯難以負擔","FOODSTMP":"是否使用食物券","SAFETIME":"安全感",
    # 篩檢
    "HADMAM":"是否做過乳房攝影","CERVSCRN":"是否做過子宮頸抹片",
    "CRVCLPAP":"最近抹片時間","CRVCLHPV":"HPV篩檢","HPVADSHT":"HPV疫苗接種",
    "HPVADVC4":"HPV疫苗建議","PSATEST1":"PSA攝護腺檢查","PSASUGST":"醫師建議PSA",
    "PSATIME1":"PSA檢查時間","PCSTALK1":"與醫師討論PSA","PCPSARS2":"PSA決策",
    "COLNSIGM":"乙狀結腸鏡","COLNCNCR":"大腸鏡（癌症）","COLNTES1":"大腸鏡時間",
    "HADSIGM4":"是否做過直腸鏡","VCLNTES2":"大腸檢查2","VIRCOLO1":"虛擬大腸鏡",
    "SIGMTES1":"直腸鏡時間","STOLTEST":"糞便潛血","STOOLDN2":"糞便潛血時間",
    "BLDSTFIT":"糞便免疫測試","LCSCTSC1":"肺癌CT篩檢","LCSCTWHN":"CT篩檢時間",
    "LCSFIRST":"第一次CT","LCSLAST":"最近CT","LCSNUMCG":"CT次數","LCSSCNCR":"CT發現",
    "_MAM5023":"乳房攝影計算","_RFMAM22":"乳房攝影建議","_CRCREC2":"大腸癌篩檢建議",
    "_CLNSCP1":"大腸鏡計算","_HADSIGM":"直腸鏡計算","_SGMS101":"直腸鏡1",
    "_SGMSCP1":"直腸鏡計算2","_SBONTI1":"糞便計算","_RFBLDS5":"糞便篩檢建議",
    "_LCSREC":"肺癌篩檢建議","_HADCOLN":"是否做過大腸鏡","_AIDTST4":"HIV檢測計算",
    "EYEEXAM1":"眼科檢查","LASTDEN4":"上次看牙醫時間","RMVTETH4":"拔牙顆數",
    "_DENVST3":"過去一年是否看牙醫","_ALTETH3":"全口假牙","_EXTETH3":"拔牙計算",
    "FLUSHOT7":"流感疫苗","PNEUVAC4":"肺炎鏈球菌疫苗","TETANUS1":"破傷風疫苗",
    "SHINGLE2":"帶狀疱疹疫苗","_FLSHOT7":"流感疫苗計算","_PNEUMO3":"肺炎疫苗計算",
    "IMFVPLA3":"COVID疫苗接種地點",
    # 癌症存活者
    "CSRVCLIN":"治療臨床試驗","CSRVCTL2":"癌症控制計畫","CSRVDEIN":"診斷資訊",
    "CSRVDOC1":"後續醫療文件","CSRVINSR":"癌後保險問題","CSRVINST":"治療機構",
    "CSRVPAIN":"癌後疼痛管理","CSRVRTRN":"重返工作","CSRVSUM":"治療摘要",
    "CSRVTRT3":"治療類型",
    # HIV
    "HIVTST7":"是否曾做HIV檢測","HIVTSTD3":"最近HIV檢測地點","HIVRISK5":"HIV風險行為",
    "HADSEX":"是否曾有性行為","HADHYST2":"是否做過子宮切除",
    "NOBCUSE8":"不使用避孕的原因","TYPCNTR9":"使用避孕方式","HOWLONG":"關係持續時間",
    "BRTHCNT4":"過去12個月生育控制",
    # 大麻
    "USEMRJN4":"過去30天大麻使用","MARIJAN1":"過去30天大麻使用天數",
    "MARJSMOK":"吸食大麻","MARJVAPE":"電子菸大麻","MARJEAT":"食用大麻",
    "MARJDAB":"濃縮大麻","MARJOTHR":"其他大麻使用方式",
    # 槍支
    "FIREARM5":"家中是否有槍","GUNLOAD":"槍是否已上膛",
    # 照護者
    "CAREGIV1":"是否為照護者","CRGVALZD":"照護情況","CRGVEXPT":"照護經驗",
    "CRGVHOU1":"照護場所","CRGVHRS1":"每週照護時數","CRGVLNG1":"照護持續時間",
    "CRGVPER1":"被照護人身份","CRGVPRB3":"照護問題","CRGVREL4":"照護關係",
    # ACE
    "ACEADNED":"童年家長學歷不足","ACEADSAF":"童年不安全感","ACEDEPRS":"童年家長憂鬱",
    "ACEDIVRC":"童年父母離婚","ACEDRINK":"童年家長酗酒","ACEDRUGS":"童年家長吸毒",
    "ACEHURT1":"童年被打","ACEHVSEX":"童年家庭暴力（性）","ACEPRISN":"童年家長坐牢",
    "ACEPUNCH":"童年被毆打","ACESWEAR":"童年被辱罵","ACETOUCH":"童年不當觸碰",
    "ACETTHEM":"童年ACE總分",
    # COVID
    "COVIDPOS":"是否曾確診COVID","COVIDINT":"是否曾自我隔離","COVIDFS1":"COVID症狀",
    "COVIDSE1":"COVID嚴重程度","COVIDNU1":"COVID住院","COVACGET":"COVID疫苗取得",
    "COVIDVA1":"COVID疫苗接種","COVIDPRM":"COVID後遺症","COVIDSMP":"COVID症狀嚴重",
    # 其他
    "HOWLONG":"目前關係持續時間","HADSEX":"是否有過性行為",
    "FLSHTMY3":"冬季流感疫苗","POORHLTH":"健康不佳阻礙日常天數",
    "COPDFLEM":"COPD咳痰",
}

# ── 分類定義 ─────────────────────────────────────────────
CATEGORIES = [
  ("survey",    "📋 調查管理", "#64748b", [
    "_STATE","FMONTH","IDATE","IMONTH","IDAY","IYEAR","DISPCODE","SEQNO","_PSU",
    "CTELENM1","PVTRESD1","COLGHOUS","STATERE1","CELPHON1","LADULT1","COLGSEX1",
    "NUMADULT","LANDSEX1","NUMMEN","NUMWOMEN","NUMHHOL4","NUMPHON4","CELLFON5",
    "CELLSEX1","CAGEG","QSTLANG","QSTVER","MSCODE","_METSTAT","_URBSTAT",
    "_LLCPWT","_LLCPWT2","_STRWT","_RAWRAKE","_WT2RAKE","_STSTR","_CLLCPWT",
    "_DUALCOR","_DUALUSE","RESPSLCT","CSTATE1","LOADULK2","SDNATES1",
    "CPDEMO1C","RRATWRK2","RRCLASS3","RRCOGNT2","RRHCARE4","RRPHYSM2","RRTREAT",
  ]),
  ("bmi_weight","⚖️ 體重/BMI","#0ea5e9",[
    "WEIGHT2","HEIGHT3","WTKG3","HTM4","HTIN4","_BMI5","_BMI5CAT","_RFBMI5",
  ]),
  ("lifestyle",  "🏃 生活習慣", "#2563eb", [
    "SLEPTIM1","EXERANY2","_TOTINDA",
    "SMOKE100","SMOKDAY2","STOPSMK2","LASTSMK2","USENOW3","ECIGNOW2",
    "MENTCIGS","MENTECIG",
    "DRNKANY6","ALCDAY4","AVEDRNK3","MAXDRNKS","DRNK3GE5","DROCDY4_","SMALSTOL",
  ]),
  ("tobacco_calc","🚬 菸草（計算欄）","#78716c",[
    "_SMOKER3","_RFSMOK3","_SMOKGRP","_CURECI2","_YRSQUIT","_YRSSMOK",
    "_PACKYRS","_PACKDAY","HEATTBCO",
  ]),
  ("alcohol_calc","🍺 飲酒（計算欄）","#b45309",[
    "_DRNKWK2","_RFBING6","_RFDRHV8",
    "ASBIBING","ASBIDRNK","ASBIALCH","ASBIRDUC","ASBIADVC",
  ]),
  ("health_status","💚 健康狀態","#16a34a",[
    "GENHLTH","PHYSHLTH","MENTHLTH","POORHLTH","PERSDOC3","MEDCOST1","CHECKUP1",
    "LSATISFY","EMTSUPRT","_RFHLTH","_HLTHPLN","_HCVU652","PRIMINSR","WHEREGET",
    "HLTHPLN",
  ]),
  ("chronic",    "❤️ 慢性病史", "#dc2626", [
    "CVDINFR4","CVDCRHD4","CVDSTRK3","ASTHMA3","ASTHNOW",
    "CHCSCNC1","CHCOCNC1","CHCCOPD3","HAVARTH4","ADDEPEV3","CHCKDNY2",
    "DIABETE4","DIABAGE4","DIABEDU1","DIABEYE1","FEETSORE","INSULIN1",
    "PDIABTS1","PREDIAB2","DIABTYPE",
    "COPDBRTH","COPDBTST","COPDCOGH","COPDFLEM","COPDSMOK",
    "_DRDXAR2","_MICHD","_ASTHMS1","_CASTHM1","_LTASTH1",
    "CASTHDX2","CASTHNO2","CHKHEMO3","CNCRTYP2","CNCRAGE","CNCRDIFF",
    "HAVECFS","TOLDCFS","WORKCFS","CDASSIST","CDDISCUS","CDHELP","CDHOUSE","CDSOCIAL",
  ]),
  ("disability", "♿ 行動/失能", "#7c3aed", [
    "DIFFWALK","DIFFDRES","DIFFALON","BLIND","DEAF","DECIDE","CIMEMLOS",
  ]),
  ("demographics","👤 人口統計","#0891b2",[
    "_SEX","SEXVAR","BIRTHSEX","TRNSGNDR","RCSGEND1","RCSRLTN2","RCSXBRTH",
    "_AGEG5YR","_AGE65YR","_AGE80","_AGE_G",
    "EDUCA","_EDUCAG","INCOME3","_INCOMG1",
    "MARITAL","CHILDREN","EMPLOY1","VETERAN3","HHADULT","RENTHOM1","PREGNANT",
    "SOFEMALE","SOMALE",
  ]),
  ("race",       "🌍 種族/民族","#0d9488",[
    "_HISPANC","_IMPRACE","_MRACE2","_PRACE2","_CRACE2","_RACEPR1",
    "_RACEG22","_RACEGR4","_RACE1","_CHISPNC","_CPRACE2",
  ]),
  ("sdh",        "🏘️ 社會決定因素(SDH)","#d97706",[
    "SDHBILLS","SDHEMPLY","SDHFOOD1","SDHISOLT","SDHSTRE1","SDHTRNSP","SDHUTILS",
    "FOODSTMP","SAFETIME",
  ]),
  ("screening",  "🔬 癌症/健康篩檢","#be185d",[
    "HADMAM","CERVSCRN","CRVCLPAP","CRVCLHPV","HPVADSHT","HPVADVC4",
    "PSATEST1","PSASUGST","PSATIME1","PCSTALK1","PCPSARS2",
    "COLNSIGM","COLNCNCR","COLNTES1","HADSIGM4","VCLNTES2","VIRCOLO1",
    "SIGMTES1","STOLTEST","STOOLDN2","BLDSTFIT",
    "LCSCTSC1","LCSCTWHN","LCSFIRST","LCSLAST","LCSNUMCG","LCSSCNCR",
    "_MAM5023","_RFMAM22","_CRCREC2","_CLNSCP1","_HADSIGM","_SGMS101",
    "_SGMSCP1","_SBONTI1","_RFBLDS5","_LCSREC","_HADCOLN","_AIDTST4",
    "EYEEXAM1","FLUSHOT7","PNEUVAC4","TETANUS1","SHINGLE2","_FLSHOT7",
    "_PNEUMO3","IMFVPLA3","FLSHTMY3",
  ]),
  ("oral_health","🦷 口腔健康","#a16207",[
    "LASTDEN4","RMVTETH4","_DENVST3","_ALTETH3","_EXTETH3",
  ]),
  ("cancer_surv","🎗️ 癌症存活者","#9f1239",[
    "CSRVCLIN","CSRVCTL2","CSRVDEIN","CSRVDOC1","CSRVINSR","CSRVINST",
    "CSRVPAIN","CSRVRTRN","CSRVSUM","CSRVTRT3",
  ]),
  ("hiv_sex",    "🔴 HIV/性健康","#c2410c",[
    "HIVTST7","HIVTSTD3","HIVRISK5","HADSEX","HADHYST2","NOBCUSE8",
    "TYPCNTR9","HOWLONG","BRTHCNT4",
  ]),
  ("marijuana",  "🌿 大麻使用","#4d7c0f",[
    "USEMRJN4","MARIJAN1","MARJSMOK","MARJVAPE","MARJEAT","MARJDAB","MARJOTHR",
  ]),
  ("firearms",   "🔫 槍支","#57534e",["FIREARM5","GUNLOAD"]),
  ("caregiving", "🤝 照護者","#0369a1",[
    "CAREGIV1","CRGVALZD","CRGVEXPT","CRGVHOU1","CRGVHRS1","CRGVLNG1",
    "CRGVPER1","CRGVPRB3","CRGVREL4",
  ]),
  ("ace",        "😔 童年逆境(ACE)","#7e22ce",[
    "ACEADNED","ACEADSAF","ACEDEPRS","ACEDIVRC","ACEDRINK","ACEDRUGS",
    "ACEHURT1","ACEHVSEX","ACEPRISN","ACEPUNCH","ACESWEAR","ACETOUCH","ACETTHEM",
  ]),
  ("covid",      "😷 COVID-19","#0f766e",[
    "COVIDPOS","COVIDINT","COVIDFS1","COVIDSE1","COVIDNU1","COVACGET",
    "COVIDVA1","COVIDPRM","COVIDSMP",
  ]),
]

# 反向索引
col_to_cat = {}
for cat_id, cat_name, color, cols in CATEGORIES:
    for c in cols:
        col_to_cat[c] = (cat_id, cat_name, color)

all_cols = list(stats.keys())
uncategorized = [c for c in all_cols if c not in col_to_cat]
if uncategorized:
    CATEGORIES.append(("other","❓ 其他","#94a3b8", uncategorized))
    for c in uncategorized:
        col_to_cat[c] = ("other","❓ 其他","#94a3b8")

print(f"分類完成。未分類: {len(uncategorized)} 個: {uncategorized[:10]}")

# ── 產生 HTML ──────────────────────────────────────────────
def null_badge(pct):
    if pct == 0:
        return f"<span style='color:#16a34a;font-weight:600'>0%</span>"
    elif pct < 15:
        return f"<span style='color:#d97706;font-weight:600'>{pct}%</span>"
    elif pct < 50:
        return f"<span style='color:#dc2626;font-weight:600'>{pct}%</span>"
    else:
        return f"<span style='color:#7c2d12;font-weight:700;background:#fee2e2;padding:1px 6px;border-radius:4px'>{pct}%</span>"

rows_html = ""
for cat_id, cat_name, color, cols in CATEGORIES:
    visible = [c for c in cols if c in stats]
    if not visible:
        continue
    rows_html += f"""
    <tr class="cat-header" data-cat="{cat_id}">
      <td colspan="7" style="background:{color};color:white;font-weight:700;font-size:14px;padding:10px 16px;cursor:pointer"
          onclick="toggleCat('{cat_id}')">
        {cat_name} &nbsp;<span style="font-size:12px;opacity:.8">({len(visible)} 個欄位)</span>
        <span id="arrow_{cat_id}" style="float:right">▼</span>
      </td>
    </tr>"""
    for c in visible:
        s = stats[c]
        used_label = f"<span style='background:#16a34a;color:white;padding:2px 8px;border-radius:8px;font-size:11px;font-weight:600'>✓ {USED[c]}</span>" if c in USED else ""
        desc = DESC.get(c, "—")
        top3_str = ", ".join(str(v) for v in s["top3"][:3]) if s["top3"] else "—"
        rows_html += f"""
    <tr class="cat-row cat-{cat_id}">
      <td style="font-family:monospace;font-size:12px;white-space:nowrap"><b>{c}</b></td>
      <td>{desc}</td>
      <td style="text-align:center">{null_badge(s['null_pct'])}</td>
      <td style="text-align:center;font-size:12px">{s['nunique']}</td>
      <td style="text-align:center;font-size:12px">{s['min'] if s['min'] is not None else '—'}</td>
      <td style="text-align:center;font-size:12px">{s['max'] if s['max'] is not None else '—'}</td>
      <td>{used_label}</td>
    </tr>"""

total_used = len(USED)
total_cols = len(all_cols)

html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BRFSS 2022 原始資料集 — 全欄位分析</title>
<style>
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:1200px;margin:0 auto;padding:24px;color:#1a1a1a;background:#f8fafc}}
  h1{{font-size:22px;margin-bottom:4px}}
  .meta{{color:#6b7280;font-size:13px;margin-bottom:20px}}
  .summary{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:24px}}
  .card{{background:white;border-radius:8px;padding:16px 20px;box-shadow:0 1px 4px rgba(0,0,0,.08);min-width:140px}}
  .card-num{{font-size:28px;font-weight:700;color:#1e3a5f}}
  .card-label{{font-size:12px;color:#6b7280;margin-top:2px}}
  table{{border-collapse:collapse;width:100%;background:white;border-radius:8px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08);margin-bottom:0}}
  th{{background:#1e3a5f;color:white;padding:10px 12px;text-align:left;font-size:12px;font-weight:600;position:sticky;top:0;z-index:10}}
  td{{padding:8px 12px;border-bottom:1px solid #f1f5f9;font-size:12px;vertical-align:middle}}
  .cat-row:hover td{{background:#f0f9ff}}
  input[type=text]{{width:280px;padding:8px 12px;border:1px solid #d1d5db;border-radius:6px;font-size:13px;margin-bottom:16px}}
  .filter-bar{{display:flex;gap:12px;align-items:center;margin-bottom:16px;flex-wrap:wrap}}
  .btn{{padding:6px 14px;border:1px solid #d1d5db;border-radius:6px;background:white;cursor:pointer;font-size:12px}}
  .btn:hover{{background:#f0f9ff;border-color:#2563eb}}
  .btn.active{{background:#2563eb;color:white;border-color:#2563eb}}
</style>
</head>
<body>
<h1>CDC BRFSS 2022 — 原始資料集全欄位分析</h1>
<p class="meta">原始規模：445,132 筆 × 328 變數 &nbsp;|&nbsp; 缺值率以 50,000 筆樣本估算 &nbsp;|&nbsp; ✓ 標記為已納入清理後資料集的欄位</p>

<div class="summary">
  <div class="card"><div class="card-num">328</div><div class="card-label">原始變數總數</div></div>
  <div class="card"><div class="card-num" style="color:#16a34a">{total_used}</div><div class="card-label">已納入模型 (22欄)</div></div>
  <div class="card"><div class="card-num" style="color:#dc2626">{total_cols - total_used}</div><div class="card-label">未使用變數</div></div>
  <div class="card"><div class="card-num" style="color:#d97706">{len(CATEGORIES)}</div><div class="card-label">分類數</div></div>
  <div class="card"><div class="card-num">338,666</div><div class="card-label">清理後筆數</div></div>
</div>

<div class="filter-bar">
  <input type="text" id="search" placeholder="搜尋欄位名稱或說明..." oninput="filterTable()">
  <button class="btn active" onclick="showAll()">全部顯示</button>
  <button class="btn" onclick="showUsedOnly()">只看已使用</button>
  <button class="btn" onclick="showLowMissing()">低缺值 (&lt;15%)</button>
</div>

<table id="mainTable">
  <thead>
    <tr>
      <th style="width:14%">欄位名稱</th>
      <th style="width:30%">說明</th>
      <th style="width:8%;text-align:center">缺值率</th>
      <th style="width:6%;text-align:center">唯一值數</th>
      <th style="width:7%;text-align:center">最小值</th>
      <th style="width:7%;text-align:center">最大值</th>
      <th style="width:18%">本研究使用</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
  </tbody>
</table>

<p style="margin-top:32px;font-size:11px;color:#9ca3af;text-align:center">
  Generated by gen_columns_html.py · obesity_project_3 · CDC BRFSS 2022 · 445,132 rows × 328 variables
</p>

<script>
function toggleCat(id) {{
  const rows = document.querySelectorAll('.cat-' + id);
  const arrow = document.getElementById('arrow_' + id);
  const hidden = rows[0] && rows[0].style.display === 'none';
  rows.forEach(r => r.style.display = hidden ? '' : 'none');
  arrow.textContent = hidden ? '▼' : '▶';
}}
function filterTable() {{
  const q = document.getElementById('search').value.toLowerCase();
  document.querySelectorAll('tr.cat-row').forEach(r => {{
    const text = r.textContent.toLowerCase();
    r.style.display = text.includes(q) ? '' : 'none';
  }});
}}
function showAll() {{
  document.querySelectorAll('tr.cat-row').forEach(r => r.style.display = '');
  document.querySelectorAll('tr.cat-header').forEach(r => r.style.display = '');
  document.querySelectorAll('[id^=arrow_]').forEach(a => a.textContent = '▼');
  setActive(event.target);
}}
function showUsedOnly() {{
  document.querySelectorAll('tr.cat-row').forEach(r => {{
    r.style.display = r.querySelector('span[style*=16a34a]') ? '' : 'none';
  }});
  setActive(event.target);
}}
function showLowMissing() {{
  document.querySelectorAll('tr.cat-row').forEach(r => {{
    const badge = r.querySelector('td:nth-child(3)');
    if (!badge) return;
    const pct = parseFloat(badge.textContent);
    r.style.display = (pct < 15) ? '' : 'none';
  }});
  setActive(event.target);
}}
function setActive(btn) {{
  document.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}}
</script>
</body>
</html>"""

with open("outputs/brfss2022_all_columns.html", "w", encoding="utf-8") as f:
    f.write(html)
print("Done -> outputs/brfss2022_all_columns.html")
