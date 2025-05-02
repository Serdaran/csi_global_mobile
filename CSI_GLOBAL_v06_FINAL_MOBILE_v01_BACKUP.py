import streamlit as st
from datetime import datetime
import uuid
import os
from PIL import Image
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import gspread
import pillow_heif

def convert_heic_to_jpg(uploaded_file):
    heif_file = pillow_heif.read_heif(uploaded_file.getvalue())
    image = Image.frombytes(
        heif_file.mode,
        heif_file.size,
        heif_file.data,
        "raw"
    )
    jpg_filename = str(uuid.uuid4()) + ".jpg"
    image.save(jpg_filename, format="JPEG")
    return jpg_filename


# ============ SAYFA AYARLARI (Mobil için) ============
st.set_page_config(
    page_title="CSI:GLOBAL Mobil Kayıt",
    page_icon="🛠️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    input, select, textarea {
        font-size: 18px !important;
    }
    button[kind="primary"] {
        font-size: 18px !important;
        padding: 0.75em 2em;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
# 📋 CSI:GLOBAL Kayıt Formu
Mobil cihazınızdan kolayca form doldurabilirsiniz. Lütfen tüm alanları eksiksiz doldurun.
""")

# ============ GÖRSEL YÜKLEME FONKSİYONU ============
def upload_image_to_drive(image_file, folder_id):
    if image_file is None:
        return ""
    if image_file.name.lower().endswith(".heic"):
        unique_filename = convert_heic_to_jpg(image_file)
    else:
        unique_filename = str(uuid.uuid4()) + "_" + image_file.name
        with open(unique_filename, "wb") as f:
            f.write(image_file.getbuffer())
    

    scopes = ['https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_file(
        "csi-global-render-e90cef81204f.json",
        scopes=scopes
    )
    drive_service = build('drive', 'v3', credentials=credentials)
    media = MediaFileUpload(unique_filename, resumable=True)
    file_metadata = {
        'name': unique_filename,
        'parents': ['1Dsny6OO-JshEfAqStBe_4YerIWkK8hRZ']  # 👈 Bunu birazdan gerçek ID ile değiştireceğiz
    }
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    file_id = file.get('id')
    drive_service.permissions().create(
        fileId=file_id,
        body={'type': 'anyone', 'role': 'reader'},
    ).execute()
    file_url = f"https://drive.google.com/uc?id={file_id}"
    os.remove(unique_filename)
    return file_url

# ============ FORM ============
material_options = [
    "P-01_Alaşımsız Çelik (Unalloyed Steel) | HB110 | C15 ; C45 ; C60",
    "P-02_Düşük Alaşımlı Çelik (Low Alloyed Steel) | HB180 | 21NiCrMo2 ; 36CrNiMo4 ; 34CrMo4",
    "P-03_Yüksek Alaşımlı Çelik (High Alloyed Steel) | HB200 | 34CrNiMo6 ; 42CrMo4",
    "P-04_Yüksek Alaşımlı Çelik (High Alloyed Steel) | HB400 | X40CrMoV5 ; X45GrSi93",
    "M-01_Ferritik/Martensitik Paslanmaz Çelik (Ferritic/Martensitic Stainless Steel) | X12CrMoS17 ; X6CrMo17",
    "M-02_Östenitik Paslanmaz Çelik (Austenitic Stainless Steel) | X5CrNi189 ; X5CrNiMo18 ; X15CrNiSi20",
    "M-03_Duplex Paslanmaz Çelik (Duplex Stainless Steel) | X2CrNiMoSi19 ; X8CrNiMo27 ; X2CrNiMoN22",
    "K-01_Gri Dökme Demir (Grey Cast Iron) | HB220 | GG15 ; GG25 ; GG35",
    "K-02_Sfero Dökme Demir (Nodular Cast Iron) | HB180 | GGG40 ; GGG50 ; GGG70",
    "S-01_Titanyum Alaşımları (Titanium Alloys) | TiAl5Sn2.5 ; TiAl6V4 ; TiAl6V4ELI",
    "S-02_Titanyum Alaşımları (Titanium Alloys) | NiCr19Co11MoTi ; NiFe35Cr14MoTi ; CoCr20W15Ni ; Inconel",
    "N-01_Alüminyum Alaşımları (Aluminium Alloys) | AW7075 ; AlSi12 ; CuZn37",
    "H-01_Sertleştirilmiş Çelikler (Hardened Steels) | 50-60 HRc"
]

with st.form("tool_form"):
    st.subheader("🛠️ Takım Bilgileri")
    customer_name = st.text_input("Müşteri Adı (Customer Name)")
    tool_code = st.text_input("Takım Kodu (Tool Code)")
    chipbreaker = st.text_input("Talaş Kırıcı Formu (Chipbreaker Code)")
    insert_grade = st.text_input("Uç Kalitesi (Insert Grade)")

    st.subheader("📏 Kesme Parametreleri")
    diameter = st.number_input("Parça ya da Takım Çapı (Part or Tool Diameter) [mm]", min_value=0.0)
    cutting_speed = st.number_input("Kesme Hızı (Cutting Speed) [m/dak]", min_value=0.0)
    feed_rate = st.number_input("İlerleme (Feed Rate) [mm/dev veya mm/diş]", min_value=0.0)
    depth_of_cut = st.number_input("Kesme Derinliği (Depth of Cut) [mm]", min_value=0.0)
    tool_teeth = st.number_input("Takım Ağız Sayısı (Number of Tool Teeth)", min_value=1, step=1)

    material = st.selectbox("Malzeme (Material)", material_options)

    st.subheader("📸 Görseller (Opsiyonel)")
    insert_image = st.file_uploader("Aşınmış Uç Görseli (Weared Insert Corner Image)", type=["jpg", "jpeg", "png", "heic"])
    chip_image = st.file_uploader("Talaş Görseli (Chip Image)", type=["jpg", "jpeg", "png", "heic"])

    st.subheader("🧠 Değerlendirme")
    wear_type = st.text_input("Uç Aşınma Tipi (Wear Type Estimation)")
    advice = st.text_area("Tavsiye (Advice)")
    form_filler = st.text_input("Formu Dolduran Kişi (Person Filling Out The Form)")

    submitted = st.form_submit_button("Kaydet")

    if submitted:
        # Görselleri Drive'a yükle
        insert_img_url = upload_image_to_drive(insert_image, "1Dsny6OO-JshEfAqStBe_4YerIWkK8hRZ")
        chip_img_url = upload_image_to_drive(chip_image, "1Dsny6OO-JshEfAqStBe_4YerIWkK8hRZ")

        # Google Sheet bağlantısı
        credentials = Credentials.from_service_account_file(
            "csi-global-render-e90cef81204f.json",
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        gc = gspread.authorize(credentials)
        sh = gc.open_by_key("1OOI0ICueR95VBB98cwaDq3AeunpXtaUyA7-LOQ4N6Dc")
        worksheet = sh.worksheet("Wear_Records")

        new_row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            customer_name, tool_code, chipbreaker, insert_grade,
            diameter, cutting_speed, feed_rate, depth_of_cut, tool_teeth,
            material,  # 👈 bunu buraya ekle
            wear_type, advice, insert_img_url, chip_img_url, form_filler
        ]


        # Yeni satır
        new_row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # timestamp
            customer_name,          # customer_name
            tool_code,              # tool_code
            chipbreaker,            # chipbreaker
            insert_grade,           # tool_grade
            material,               # material
            diameter,               # Part or Tool Diameter
            cutting_speed,          # cutting_speed
            feed_rate,              # feed_rate
            depth_of_cut,           # depth_of_cut
            tool_teeth,             # Number of Tool Teeth
            wear_type,              # wear_type_estimation
            advice,                 # advice_given
            insert_img_url,         # Weared Insert Corner Image
            chip_img_url,           # chip_image_link
            form_filler             # Person Filling Out Form
        ]

        worksheet.append_row(new_row)

        st.success("✅ Kayıt başarıyla yapıldı!")
        st.markdown(f"[🖼️ Aşınmış Uç Görseli]({insert_img_url})")
        st.markdown(f"[🖼️ Talaş Görseli]({chip_img_url})")
        st.stop()
