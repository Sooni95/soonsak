import os
from datetime import datetime
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO
import platform

# ----
# 폰트 설정 (Windows / macOS 지원)
# ----
plt.rcParams['axes.unicode_minus'] = False
if platform.system() == 'Darwin':
    plt.rcParams['font.family'] = 'AppleGothic'
else:
    plt.rcParams['font.family'] = 'Malgun Gothic'

# ----
# 파일 설정
# ----
EXCEL_FILE = 'wedding_budget.xlsx'
REQUIRED_COLUMNS = ["날짜", "품목명", "총금액", "계약금", "1차결제", "2차결제", "계약취소", "계약금확변", "실지\uc출", "잔금"]

# ----
# 금액 계산기
# ----
def calculate_amounts(total_price, deposit, pay1, pay2, canceled, refunded):
    if canceled:
        actual = pay1 + pay2 if refunded else deposit + pay1 + pay2
    else:
        actual = deposit + pay1 + pay2
    balance = total_price - (deposit + pay1 + pay2)
    return actual, balance

# ----
# ì# \xec# \xec\x97# \xec\x97\x91셀 파일 파일지 심설
# ----
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# ----
# 기본 설정
# ----
st.set_page_config(page_title="결항 예산 관리기", layout="centered")
st.title("💒 결항 예산 관리기")

# ----
# ì# \xec# \xec\x97# \xec\x97\x91셀 업로드
# ----
uploaded = st.file_uploader("📤 업로드한 예산 파일 (.xlsx)", type=["xlsx"])
if 'uploaded_df' not in st.session_state:
    st.session_state.uploaded_df = None

if uploaded:
    try:
        df_temp = pd.read_excel(uploaded)
        if list(df_temp.columns) == REQUIRED_COLUMNS:
            st.session_state.uploaded_df = df_temp
            st.success("✅ 업로드한 파일이 정상 다운로드되었습니다.")
            if st.button("📥 반영하기"):
                df_temp.to_excel(EXCEL_FILE, index=False)
                st.success("💾 예산 데이터가 반영되었습니다!")
        else:
            st.error("❌ 필요한 연산이 못된 파일 구조입니다.")
    except:
        st.error("❌ 파일 읽기에서 오류가 발생했습니다.")

# ----
# 기존 데이터 로드
# ----
if os.path.exists(EXCEL_FILE):
    df = pd.read_excel(EXCEL_FILE)
else:
    df = pd.DataFrame(columns=REQUIRED_COLUMNS)

item_list = df["품목명"].tolist()
mode = st.radio("모드 선택", ["🆕 신규 품목 등록", "♻ 기존 품목 업데이트", "❌ 품목 삭제"])

# 신규 품목 등록
if mode == "🆕 신규 품목 등록":
    with st.form("new_form"):
        item = st.text_input("📌 품목명")
        total = st.number_input("💰 총금액", min_value=0, step=10000)
        deposit = st.number_input("🔐 계약금", min_value=0, step=10000)
        submit = st.form_submit_button("➕ 등록")
        if submit and item:
            actual, balance = calculate_amounts(total, deposit, 0, 0, False, False)
            new_row = pd.DataFrame([{
                "날짜": datetime.now().strftime("%Y-%m-%d"),
                "품목명": item,
                "총금액": total,
                "계약금": deposit,
                "1차결제": 0,
                "2차결제": 0,
                "계약취소": "X",
                "계약금환불": "X",
                "실지출": actual,
                "잔금": balance
            }])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_excel(EXCEL_FILE, index=False)
            st.success(f"✅ '{item}' 이(가) 추가되었습니다!")

# 기존 품목 업데이트
elif mode == "♻ 기존 품목 업데이트":
    if item_list:
        selected = st.selectbox("✏ 수정할 품목", item_list)
        row = df[df["품목명"] == selected].iloc[0]
        with st.form("update_form"):
            pay1 = st.number_input("💳 1차 결제", value=int(row["1차결제"]), step=10000)
            pay2 = st.number_input("💳 2차 결제", value=int(row["2차결제"]), step=10000)
            canceled = st.checkbox("❌ 계약 취소", value=(row["계약취소"] == "O"))
            refunded = st.checkbox("💸 계약금 환불 받음", value=(row["계약금환불"] == "O"))
            actual, balance = calculate_amounts(row["총금액"], row["계약금"], pay1, pay2, canceled, refunded)
            st.info(f"💰 현재 잔금: {balance:,} 원")
            submit = st.form_submit_button("✅ 업데이트")
            if submit:
                df.loc[df["품목명"] == selected, ["1차결제", "2차결제", "계약취소", "계약금환불", "실지출", "잔금"]] = [
                    pay1, pay2, "O" if canceled else "X", "O" if refunded else "X", actual, balance
                ]
                df.to_excel(EXCEL_FILE, index=False)
                st.success(f"🔁 '{selected}' 항목이 업데이트되었습니다!")
    else:
        st.info("등록된 품목이 없습니다.")

# 품목 삭제
elif mode == "❌ 품목 삭제":
    if item_list:
        target = st.selectbox("🗑 삭제할 항목", item_list)
        if st.button("❌ 삭제하기"):
            df = df[df["품목명"] != target]
            df.to_excel(EXCEL_FILE, index=False)
            st.success(f"🗑 '{target}' 항목이 삭제되었습니다!")
    else:
        st.info("삭제할 항목이 없습니다.")

# 요약 지표
st.divider()
total_spent = df["실지출"].sum()
total_balance = df["잔금"].sum()
col1, col2 = st.columns(2)
col1.metric("📦 총 누적 실지출", f"{total_spent:,} 원")
col2.metric("💸 총 잔금", f"{total_balance:,} 원")

# 시각화 - 파이 차트
if not df.empty:
    st.subheader("📊 품목별 실지출 비율")
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(df["실지출"], labels=df["품목명"], autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)

# 다운로드
st.divider()
st.subheader("📥 전체 예산 내역 다운로드")
st.download_button(
    label="💾 엑셀로 다운로드",
    data=to_excel(df),
    file_name="wedding_budget.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
