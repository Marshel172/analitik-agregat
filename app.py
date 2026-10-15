import streamlit as st
import pandas as pd
import plotly.express as px

# Konfigurasi Halaman
st.set_page_config(
    page_title="Analitik Perencanaan Agregat Produksi",
    layout="wide"
)

st.title("🏭 Aplikasi Analitik Perencanaan Agregat Produksi")
st.caption("Simulasi dan Komparasi Strategi Perencanaan Agregat (Studi Kasus: Jason Enterprises)")

# ---------------------------------------------------------
# SIDEBAR: INPUT PARAMETER BIAYA & TENAGA KERJA
# ---------------------------------------------------------
st.sidebar.header("⚙️ Parameter Biaya & Tenaga Kerja")

cost_material = st.sidebar.number_input("Biaya Material / Unit ($)", value=100.0)
cost_holding = st.sidebar.number_input("Holding Cost / Unit / Bulan ($)", value=10.0)
cost_backorder = st.sidebar.number_input("Backorder Cost / Unit / Bulan ($)", value=20.0)
cost_subcontract = st.sidebar.number_input("Subcontracting Cost / Unit ($)", value=100.0)
cost_hiring = st.sidebar.number_input("Biaya Hiring / Pekerja ($)", value=50.0)
cost_layoff = st.sidebar.number_input("Biaya Layoff / Pekerja ($)", value=100.0)
wage_rate = st.sidebar.number_input("Upah / Jam ($)", value=12.50)
hours_per_unit = st.sidebar.number_input("Jam Kerja / Unit", value=4.0)
hours_per_day = st.sidebar.number_input("Jam Kerja / Hari / Pekerja", value=8.0)

st.sidebar.header("⚙️ Parameter Strategi B & C")
initial_inventory = st.sidebar.number_input("Persediaan Awal (Unit)", value=200)
constant_workers = st.sidebar.number_input("Jumlah Pekerja Konstan", value=10)

# ---------------------------------------------------------
# TABEL INPUT UTAMA: PERMINTAAN & HARI KERJA
# ---------------------------------------------------------
st.subheader("📅 Data Permintaan & Hari Kerja Bulanan")
st.write("Silakan sesuaikan data permintaan dan hari kerja pada tabel di bawah ini:")

default_data = pd.DataFrame({
    "Bulan": ["Januari", "Februari", "Maret", "April", "Mei", "Juni"],
    "Hari Kerja": [22, 18, 22, 21, 22, 20],
    "Permintaan (Demand)": [900, 700, 800, 1200, 1500, 1100]
})

edited_df = st.data_editor(default_data, num_rows="dynamic", use_container_width=True)

# ---------------------------------------------------------
# LOGIKA PERHITUNGAN STRATEGI
# ---------------------------------------------------------

# Total Kebutuhan Produksi
total_demand = edited_df["Permintaan (Demand)"].sum()
net_demand = max(0, total_demand - initial_inventory)

# --- STRATEGY A: Chase / Vary Workforce ---
labor_hours_a = net_demand * hours_per_unit
cost_labor_a = labor_hours_a * wage_rate

workers_needed_list = []
for idx, row in edited_df.iterrows():
    req_units = row["Permintaan (Demand)"] - (initial_inventory if idx == 0 else 0)
    req_units = max(0, req_units)
    req_hours = req_units * hours_per_unit
    avail_hours_per_worker = row["Hari Kerja"] * hours_per_day
    workers = req_hours / avail_hours_per_worker if avail_hours_per_worker > 0 else 0
    workers_needed_list.append(round(workers))

hiring_cost_a = 0
layoff_cost_a = 0
current_workers = constant_workers

for w in workers_needed_list:
    diff = w - current_workers
    if diff > 0:
        hiring_cost_a += diff * cost_hiring
    else:
        layoff_cost_a += abs(diff) * cost_layoff
    current_workers = w

total_hl_a = hiring_cost_a + layoff_cost_a
total_cost_a = cost_labor_a + total_hl_a

# --- STRATEGY B: Level Workforce + Backorder ---
total_working_days = edited_df["Hari Kerja"].sum()
total_avail_hours_b = total_working_days * hours_per_day * constant_workers
cost_labor_b = total_avail_hours_b * wage_rate

inv_balance = initial_inventory
cost_holding_b = 0
cost_backorder_b = 0
details_b = []

for idx, row in edited_df.iterrows():
    prod_cap = (row["Hari Kerja"] * hours_per_day * constant_workers) / hours_per_unit
    inv_balance = inv_balance + prod_cap - row["Permintaan (Demand)"]
    if inv_balance >= 0:
        h_cost = inv_balance * cost_holding
        b_cost = 0
    else:
        h_cost = 0
        b_cost = abs(inv_balance) * cost_backorder
    
    cost_holding_b += h_cost
    cost_backorder_b += b_cost
    details_b.append({
        "Bulan": row["Bulan"],
        "Kapasitas Produksi": prod_cap,
        "Permintaan": row["Permintaan (Demand)"],
        "Sisa Stok / (Backorder)": inv_balance,
        "Biaya Holding ($)": h_cost,
        "Biaya Backorder ($)": b_cost
    })

total_hb_b = cost_holding_b + cost_backorder_b
total_cost_b = cost_labor_b + total_hb_b

# --- STRATEGY C: Level Workforce + Subcontracting ---
cost_labor_c = cost_labor_b
regular_prod_capacity = total_avail_hours_b / hours_per_unit
subcontract_units = max(0, net_demand - regular_prod_capacity)
cost_subcontract_c = subcontract_units * cost_subcontract
total_cost_c = cost_labor_c + cost_subcontract_c

# ---------------------------------------------------------
# DISPLAY HASIL & RINGKASAN BIAYA
# ---------------------------------------------------------
st.markdown("---")
st.subheader("📊 Ringkasan Hasil Perbandingan Biaya")

summary_df = pd.DataFrame({
    "Komponen Biaya ($)": [
        "Biaya Tenaga Kerja (Labor)",
        "Biaya Hiring & Layoff",
        "Biaya Holding & Backorder",
        "Biaya Subcontracting",
        "TOTAL BIAYA"
    ],
    "Strategy A (Chase / Vary)": [
        f"${cost_labor_a:,.2f}",
        f"${total_hl_a:,.2f}",
        "$0.00",
        "$0.00",
        f"${total_cost_a:,.2f}"
    ],
    "Strategy B (Level + Backorder)": [
        f"${cost_labor_b:,.2f}",
        "$0.00",
        f"${total_hb_b:,.2f}",
        "$0.00",
        f"${total_cost_b:,.2f}"
    ],
    "Strategy C (Level + Subcontract)": [
        f"${cost_labor_c:,.2f}",
        "$0.00",
        "$0.00",
        f"${cost_subcontract_c:,.2f}",
        f"${total_cost_c:,.2f}"
    ]
})

col1, col2 = st.columns([1, 1])

with col1:
    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    costs = {"Strategy A": total_cost_a, "Strategy B": total_cost_b, "Strategy C": total_cost_c}
    best_strategy = min(costs, key=costs.get)
    st.success(f"💡 **Rekomendasi Strategi Optimal:** **{best_strategy}** dengan Total Biaya Terendah sebesar **${costs[best_strategy]:,.2f}**")

with col2:
    chart_data = pd.DataFrame({
        "Strategi": ["Strategy A (Chase)", "Strategy B (Level + Backorder)", "Strategy C (Level + Subcontract)"],
        "Total Biaya ($)": [total_cost_a, total_cost_b, total_cost_c]
    })
    fig = px.bar(
        chart_data, 
        x="Strategi", 
        y="Total Biaya ($)", 
        color="Strategi",
        title="Perbandingan Total Biaya Antar Strategi",
        text_auto=".2s"
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# RINCIAN HITUNGAN
# ---------------------------------------------------------
st.markdown("---")
with st.expander("🔍 Lihat Rincian Hitungan Bulanan Strategy B (Level + Backorder)"):
    st.dataframe(pd.DataFrame(details_b), use_container_width=True, hide_index=True)