import os
from datetime import datetime
import pandas as pd
import streamlit as st
from io import BytesIO

# 파일명 (로컬 저장 불가, 대신 다운로드)
filename = 'wedding_budget.xlsx'

# 기본 열 구조
columns = [
    "날짜", "품목명", "총금액", "계약금", "1차결제", "2차결제",
    "계약취소", "계약금환불", "실지출", "잔금"
]

# 초기 데이터 불러오기
@st.cache_data
def load_data():
    if os.path.exists(filename):
        df = pd.read_excel(filename)
    else:
        df = pd.DataFrame(columns=columns)
    return df

# 실지출/잔금 계산
def calculate_amounts(total_price, deposit, payment1, payment2, canceled, refunded):
    if canceled:
        actual_spend = payment1 + payment2 if refunded else deposit + payment1 + payment2
    else:
        actual_spend = deposit + payment1 + payment2
    balance = total_price - (deposit + payment1 + payment2)
    return actual_spend, balance

# 저장 또는 업데이트
def save_or_update_item(row_data):
    df = load_data()
    item_name = row_data["품목명"]
    if item_name in df["품목명"].values:
        for key in row_data:
            df.loc[df["품목명"] == item_name, key] = row_data[key]
    else:
        df = pd.concat([df, pd.DataFrame([row_data])], ignore_index=True)
    df.to_excel(filename, index=False)

# 품목 삭제
def delete_item(item_name):
    df = load_data()
    df = df[df["품목명"] != item_name]
    df.to_excel(filename, index=False)

# 다운로드용 엑셀 생성
def to_excel_download(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='예산')
    return output.getvalue()

# Streamlit UI 시작
st.set_page_config(page_title="결혼 예산 관리기", layout="centered")
st.title("💒 결혼 예산 관리기")

# 데이터 불러오기
data = load_data()
item_names = data["품목명"].tolist()

mode = st.radio("모드 선택", ["🆕 신규 품목 등록", "♻ 기존 품목 업데이트", "❌ 품목 삭제"])

# 신규 등록
if mode == "🆕 신규 품목 등록":
    with st.form("new_item_form"):
        item = st.text_input("📌 품목명")
        total_price = st.number_input("💰 총금액", min_value=0, step=10000)
        deposit = st.number_input("🔐 계약금", min_value=0, step=10000)
        submitted = st.form_submit_button("➕ 등록")
        if submitted:
            if not item:
                st.warning("품목명을 입력하세요!")
            else:
                actual_spend, balance = calculate_amounts(total_price, deposit, 0, 0, False, False)
                row = {
                    "날짜": datetime.now().strftime("%Y-%m-%d"),
                    "품목명": item,
                    "총금액": total_price,
                    "계약금": deposit,
                    "1차결제": 0,
                    "2차결제": 0,
                    "계약취소": "X",
                    "계약금환불": "X",
                    "실지출": actual_spend,
                    "잔금": balance
                }
                save_or_update_item(row)
                st.success(f"'{item}' 항목이 등록되었습니다!")

# 기존 수정
elif mode == "♻ 기존 품목 업데이트":
    if item_names:
        selected_item = st.selectbox("✏ 수정할 품목 선택", item_names)
        selected_row = data[data["품목명"] == selected_item].iloc[0]
        with st.form("update_item_form"):
            payment1 = st.number_input("💳 1차 결제", value=int(selected_row["1차결제"]), min_value=0, step=10000)
            payment2 = st.number_input("💳 2차 결제", value=int(selected_row["2차결제"]), min_value=0, step=10000)
            canceled = st.checkbox("❌ 계약 취소", value=(selected_row["계약취소"] == "O"))
            refunded = st.checkbox("💸 계약금 환불 받음", value=(selected_row["계약금환불"] == "O"))
            submitted = st.form_submit_button("✅ 업데이트")
            if submitted:
                actual_spend, balance = calculate_amounts(
                    selected_row["총금액"],
                    selected_row["계약금"],
                    payment1,
                    payment2,
                    canceled,
                    refunded
                )
                updated_row = {
                    "날짜": datetime.now().strftime("%Y-%m-%d"),
                    "품목명": selected_item,
                    "총금액": selected_row["총금액"],
                    "계약금": selected_row["계약금"],
                    "1차결제": payment1,
                    "2차결제": payment2,
                    "계약취소": "O" if canceled else "X",
                    "계약금환불": "O" if refunded else "X",
                    "실지출": actual_spend,
                    "잔금": balance
                }
                save_or_update_item(updated_row)
                st.success(f"'{selected_item}' 항목이 업데이트되었습니다!")
    else:
        st.info("등록된 품목이 없습니다.")

# 품목 삭제
elif mode == "❌ 품목 삭제":
    if item_names:
        selected_item = st.selectbox("🗑 삭제할 품목 선택", item_names)
        if st.button("❌ 삭제하기"):
            delete_item(selected_item)
            st.success(f"'{selected_item}' 항목이 삭제되었습니다!")
    else:
        st.info("삭제할 품목이 없습니다.")

# 총 실지출 표시
data = load_data()
total = data["실지출"].sum()
st.metric(label="📦 총 누적 실지출", value=f"{total:,} 원")

# 엑셀 다운로드
st.subheader("📥 전체 예산 내역 다운로드")
excel_file = to_excel_download(data)
st.download_button(
    label="💾 엑셀로 다운로드",
    data=excel_file,
    file_name="wedding_budget.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

