import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from shapely.geometry import Polygon

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Sistem Ukur & Pemetaan Geomatik",
    page_icon="📐",
    layout="wide"
)

def kira_galas_jarak(x, y):
    """Fungsi untuk mengira jarak dan galas antara titik-titik koordinat"""
    n = len(x)
    data_bearing_jarak = []
    
    for i in range(n):
        x1, y1 = x[i], y[i]
        x2, y2 = x[(i + 1) % n], y[(i + 1) % n]  # Titik seterusnya (gelung)
        
        dx = x2 - x1
        dy = y2 - y1
        
        # Jarak Euclidean (Pythagoras)
        jarak = np.sqrt(dx**2 + dy**2)
        
        # Pengiraan Galas (Bearing dalam darjah 0° - 360°)
        sudut_rad = np.arctan2(dx, dy)
        sudut_deg = np.degrees(sudut_rad)
        if sudut_deg < 0:
            sudut_deg += 360
            
        # Tukar ke darjah, minit, saat (DMS)
        d = int(sudut_deg)
        m = int((sudut_deg - d) * 60)
        s = ((sudut_deg - d) * 60 - m) * 60
        dms_str = f"{d}° {m:02d}' {s:05.2f}''"
        
        data_bearing_jarak.append({
            "Dari Stesen": f"STN {i+1}",
            "Ke Stesen": f"Ke STN {(i+1)%n + 1}",
            "ΔE (m)": dx,
            "ΔN (m)": dy,
            "Jarak (m)": jarak,
            "Galas (°' \")": dms_str
        })
        
    return pd.DataFrame(data_bearing_jarak)

def main_dashboard():
    st.title("📐 Sistem Pemprosesan Data Ukur & Lot Tanah")
    st.markdown("Aplikasi web interaktif untuk memproses koordinat, mengira luas, dan memaparkan pelan lot ukur.")

    # Bahagian Sidebar
    st.sidebar.header("Tetapan Data")
    
    # Pilihan sumber data
    pilihan_input = st.sidebar.radio("Pilih Kaedah Masukan Data:", ["Muat Naik CSV", "Contoh Data Automatik"])
    
    df = None
    
    if pilihan_input == "Muat Naik CSV":
        uploaded_file = st.sidebar.file_uploader("Muat naik fail CSV (Lajur: Stesen, Easting, Northing)", type=["csv"])
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
    else:
        # Data contoh (Contoh Lot Ujian)
        data_contoh = {
            "Stesen": ["1", "2", "3", "4"],
            "Easting": [805000.0, 805100.0, 805100.0, 805000.0],
            "Northing": [350000.0, 350000.0, 350100.0, 350100.0]
        }
        df = pd.DataFrame(data_contoh)
        st.sidebar.info("Menggunakan data contoh koordinat piawai.")

    if df is not None:
        st.subheader("📋 Jadual Koordinat Stesen Ukur")
        st.dataframe(df, use_container_width=True)
        
        # Memastikan lajur wujud
        if all(col in df.columns for col in ["Stesen", "Easting", "Northing"]):
            stesen_nama = df["Stesen"].astype(str).tolist()
            x = df["Easting"].values
            y = df["Northing"].values
            
            # Maklumat Tambahan Lot
            col1, col2 = st.columns(2)
            with col1:
                no_lot_input = st.text_input("Nombor Lot", "Lot 2001")
            with col2:
                nama_pemilik = st.text_input("Nama Pemilik / Hakmilik", "Pemilik Berdaftar")

            try:
                # Kira Luas menggunakan Shapely
                polygon_coords = list(zip(x, y))
                poly = Polygon(polygon_coords)
                luas_sqm = poly.area
                luas_hectare = luas_sqm / 10000.0
                
                # Paparan Keputusan Luas
                st.markdown("---")
                mcol1, mcol2 = st.columns(2)
                mcol1.metric("Luas Kawasan (Meter Persegi)", f"{luas_sqm:,.2f} m²")
                mcol2.metric("Luas Kawasan (Hektar)", f"{luas_hectare:,.4f} hektar")
                
                # Jadual Galas dan Jarak
                st.subheader("📏 Jadual Pengiraan Galas & Jarak")
                df_bj = kira_galas_jarak(x, y)
                st.dataframe(df_bj, use_container_width=True)

                # Paparan Peta Folium
                st.subheader("🗺️ Pelan Interaktif Peta Lot")
                
                pusat_y = np.mean(y)
                pusat_x = np.mean(x)
                
                m = folium.Map(location=[pusat_y, pusat_x], zoom_start=18)
                lat_lon_coords = [[yi, xi] for yi, xi in zip(y, x)]
                
                folium.Polygon(
                    locations=lat_lon_coords,
                    color="blue",
                    weight=3,
                    fill=True,
                    fill_color="cyan",
                    fill_opacity=0.4,
                    popup=folium.Popup(
                        f"<b>No. Lot:</b> {no_lot_input}<br>"
                        f"<b>Pemilik:</b> {nama_pemilik}<br>"
                        f"<b>Luas:</b> {luas_sqm:,.2f} m²",
                        max_width=300
                    )
                ).add_to(m)

                for i in range(len(x)):
                    folium.CircleMarker(
                        location=[y[i], x[i]],
                        radius=5,
                        color='darkred',
                        fill=True,
                        fill_color='yellow',
                        fill_opacity=1.0,
                        popup=f"STN {stesen_nama[i]}<br>E: {x[i]}<br>N: {y[i]}"
                    ).add_to(m)

                st_folium(m, width=800, height=500)

            except Exception as e:
                st.error(f"Ralat semasa memproses geometri lot: {e}")
        else:
            st.error("Fail CSV mesti mengandungi lajur bernama: 'Stesen', 'Easting', dan 'Northing'.")

if __name__ == "__main__":
    main_dashboard()
