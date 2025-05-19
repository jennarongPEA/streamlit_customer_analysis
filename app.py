import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io
from datetime import datetime

# ------------------ Page Config ------------------
apptitle = 'BB_customer_analysis'
st.set_page_config(page_title=apptitle, page_icon="⚡", layout="wide")
st.title("📊 Customer Risk Summary Dashboard")

file_path = os.path.join("data", "customer_risk_summary.csv")

try:
    df = pd.read_csv(file_path)
    df["กฟฟ."] = df["TRSG"].str[:3]

    # สร้างความน่าจะเป็น (%) ทศนิยม 1 ตำแหน่ง
    df["ความน่าจะเป็น (%)"] = (df["ความน่าจะเป็น"] * 100).round(1)
    df.drop(columns=["ความน่าจะเป็น"], inplace=True)

    # ------------------ Sidebar ------------------
    


    with st.sidebar:
        st.image("assets/pea_logo.png", use_container_width=True)
        
        menu = st.sidebar.radio("เลือกหน้า", ["📊 สรุป Dashboard", "🔍 ดูข้อมูลรายละเอียดราย CA"])

    
        st.markdown("## 🗺️ ตัวกรองพื้นที่")

        selected_gfo = st.selectbox("เลือก กฟฟ.", options=["ทั้งหมด"] + sorted(df["กฟฟ."].unique()))
        if selected_gfo != "ทั้งหมด":
            filtered_trsg = df[df["กฟฟ."] == selected_gfo]["TRSG"].unique()
        else:
            filtered_trsg = df["TRSG"].unique()
        selected_trsg = st.selectbox("เลือก กฟส.", options=["ทั้งหมด"] + sorted(filtered_trsg))

        if selected_trsg != "ทั้งหมด":
            filtered_mru_options = df[df["TRSG"] == selected_trsg]["MRU"].unique()
        elif selected_gfo != "ทั้งหมด":
            filtered_mru_options = df[df["กฟฟ."] == selected_gfo]["MRU"].unique()
        else:
            filtered_mru_options = df["MRU"].unique()
        selected_mru = st.selectbox("เลือกสายการอ่านหน่วย (MRU)", options=["ทั้งหมด"] + sorted(filtered_mru_options))

        st.markdown("## 📋 แนวทางดำเนินการ")
        selected_action_dropdown = st.selectbox(
            "เลือกแนวทางดำเนินการ",
            options=["ทั้งหมด"] + sorted(df["แนวทางดำเนินการ"].dropna().unique())
        )

        st.markdown("## ⚠️ ตัวกรองระดับความเสี่ยง")
        risk_levels_all = sorted(df['ระดับความเสี่ยง'].dropna().unique())
        selected_risk = []
        for level in risk_levels_all:
            if st.checkbox(f"ระดับ: {level}", value=True):
                selected_risk.append(level)

        st.markdown("## 🔎 ฟิลเตอร์เสริม")
        selected_usage = st.multiselect(
            "ลักษณะการใช้ไฟฟ้า",
            options=sorted(df["ลักษณะการใช้ไฟฟ้า"].dropna().unique()),
            default=None
        )
        st.markdown("---")
        st.markdown("""
<div style='font-size: 13px; line-height: 1.6;'>
📌 <strong>จัดทำโดย</strong><br><br>
📈 <strong>กองบัญชีและเศรษฐกิจพลังงานไฟฟ้า<br>ฝ่ายสนับสนุนการบริหารงาน</strong><br><br>
🛠️ <strong>กองบริการลูกค้า<br>ฝ่ายวิศวกรรมและบริการ</strong><br><br>
🟣 <strong>การไฟฟ้าส่วนภูมิภาค เขต 3 (ภาคตะวันออกเฉียงเหนือ) จังหวัดนครราชสีมา</strong>
</div>
""", unsafe_allow_html=True)
        
    # ------------------ Filtering ------------------
    filtered_df = df.copy()
    if selected_gfo != "ทั้งหมด":
        filtered_df = filtered_df[filtered_df["กฟฟ."] == selected_gfo]
    if selected_trsg != "ทั้งหมด":
        filtered_df = filtered_df[filtered_df["TRSG"] == selected_trsg]
    if selected_mru != "ทั้งหมด":
        filtered_df = filtered_df[filtered_df["MRU"] == selected_mru]
    if selected_action_dropdown != "ทั้งหมด":
        filtered_df = filtered_df[filtered_df["แนวทางดำเนินการ"] == selected_action_dropdown]
    if selected_risk:
        filtered_df = filtered_df[filtered_df["ระดับความเสี่ยง"].isin(selected_risk)]
    if selected_usage:
        filtered_df = filtered_df[filtered_df["ลักษณะการใช้ไฟฟ้า"].isin(selected_usage)]

    # ------------------ Summary ------------------
    st.markdown("### 📊 สรุปตัวชี้วัด (Summary Metrics)")

    total_customers = len(filtered_df)
    analysis_counts = filtered_df["ผลการวิเคราะห์"].value_counts().to_dict()
    risk_counts = filtered_df["ระดับความเสี่ยง"].value_counts().to_dict()

    st.metric("🔢 จำนวนลูกค้า", total_customers)

    col_analysis = st.columns(len(analysis_counts))
    for i, (label, count) in enumerate(analysis_counts.items()):
        col_analysis[i].metric(f"📘 {label}", count)

    col_risk = st.columns(len(risk_counts))
    for i, (level, count) in enumerate(risk_counts.items()):
        col_risk[i].metric(f"⚠️ ความเสี่ยง: {level}", count)

    # ------------------ Bar Chart by กฟฟ. ------------------
    st.markdown("### 📊 กราฟแท่งแนวตั้ง: จำนวนลูกค้าตามระดับความเสี่ยง (Grouped by กฟฟ.)")
    grouped_gfo = filtered_df.groupby(["กฟฟ.", "ระดับความเสี่ยง"]).size().reset_index(name='count')
    fig_gfo = px.bar(
        grouped_gfo,
        x='กฟฟ.', y='count', color='ระดับความเสี่ยง',
        barmode='stack', text_auto=True,
        title="จำนวนลูกค้าตามระดับความเสี่ยง (กฟฟ.)"
    )
    st.plotly_chart(fig_gfo, use_container_width=True)

    # ------------------ Bar Chart by กฟส. ------------------
    st.markdown("### 📊 กราฟแท่งแนวนอน: จำนวนลูกค้าตามระดับความเสี่ยง (Grouped by กฟส.)")
    grouped_trsg = filtered_df.groupby(["TRSG", "ระดับความเสี่ยง"]).size().reset_index(name='count')
    grouped_trsg = grouped_trsg.sort_values(by="count", ascending=False)
    fig_trsg = px.bar(
        grouped_trsg,
        y='TRSG', x='count', color='ระดับความเสี่ยง',
        orientation='h', text_auto=True,
        title="จำนวนลูกค้าตามระดับความเสี่ยง (กฟส.)"
    )
    st.plotly_chart(fig_trsg, use_container_width=True)

    # ------------------ Bar Chart: แนวทางดำเนินการ ------------------
    st.markdown("### 📊 กราฟแท่ง: จำนวนตามแนวทางดำเนินการ")
    action_df = filtered_df["แนวทางดำเนินการ"].value_counts().reset_index()
    action_df.columns = ["แนวทางดำเนินการ", "จำนวน"]
    fig_action = px.bar(
        action_df,
        x="แนวทางดำเนินการ",
        y="จำนวน",
        text_auto=True,
        color="แนวทางดำเนินการ",
        title="จำนวนลูกค้าตามแนวทางดำเนินการ"
    )
    st.plotly_chart(fig_action, use_container_width=True)

    # ------------------ 3D Scatter Plot ------------------
    st.markdown("### 📈 การกระจายตัวแบบ 3 มิติ: ความน่าจะเป็น vs เดือนใช้งาน vs หมายเลข CA")
    fig_scatter_3d = px.scatter_3d(
        filtered_df,
        x="ความน่าจะเป็น (%)",
        y="num_valid_months",
        z="CA",
        color="ระดับความเสี่ยง",
        hover_data=["แนวทางดำเนินการ", "ลักษณะการใช้ไฟฟ้า"],
        title="การกระจาย 3 มิติ: ความน่าจะเป็น (%) / เดือน / CA",
        opacity=0.7
    )
    st.plotly_chart(fig_scatter_3d, use_container_width=True)

    # ------------------ Pivot Table ------------------
    st.markdown("### 📊 สรุปตาราง Pivot")
    pivot = pd.pivot_table(
        filtered_df,
        index='ระดับความเสี่ยง',
        columns='แนวทางดำเนินการ',
        values='CA',
        aggfunc='count',
        fill_value=0
    )
    st.dataframe(pivot, use_container_width=True)

    # ------------------ Data Preview ------------------
    st.markdown("### 👀 ตัวอย่างข้อมูล (Data Preview)")
    col_order = ['กฟฟ.', 'TRSG', 'MRU'] + [c for c in filtered_df.columns if c not in ['กฟฟ.', 'TRSG', 'MRU']]
    styled_df = filtered_df[col_order].head(10).style.set_properties(**{'text-align': 'left'}).apply(
        lambda x: ['background-color: #565656; color: white' if i % 2 == 0 else '' for i in range(len(x))], axis=0
    )
    st.dataframe(styled_df, use_container_width=True)

    # ------------------ Download ------------------
    st.markdown("### 📥 ดาวน์โหลดข้อมูล (Excel)")
    towrite = io.BytesIO()
    filtered_df.to_excel(towrite, index=False, sheet_name='Filtered Data')
    towrite.seek(0)
    st.download_button(
        label="📥 Download Excel",
        data=towrite,
        file_name=f"customer_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

except FileNotFoundError:
    st.error(f"❌ ไม่พบไฟล์: {file_path}")