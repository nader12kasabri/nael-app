
import streamlit as st
from reportlab.pdfgen import canvas
from tempfile import NamedTemporaryFile
import json
import os
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import arabic_reshaper
from bidi.algorithm import get_display

# تسجيل خط Open Sans
font_path = "fonts/OpenSans-Regular.ttf"
pdfmetrics.registerFont(TTFont("OpenSans", font_path))

# اسم ملف التخزين
DATA_FILE = "workers_data.json"

# تحميل البيانات من الملف
def load_workers():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# حفظ البيانات للملف
def save_workers(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# تنسيق النص العبري/العربي
def reshape_text(text):
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

# تحميل/تهيئة البيانات
if "workers" not in st.session_state:
    st.session_state.workers = load_workers()

st.set_page_config(page_title="نظام برامج الشغيلة", layout="centered")

# CSS للتصميم
st.markdown("""<style>
.stApp {
    background-color: #F4F4F4;
    color: #111111;
}
html, body, [class*="css"] {
    color: #111111 !important;
    font-weight: 500;
}
h1, h2, h3, h4 {
    color: #023E8A;
}
.stButton > button {
    background-color: #0077B6;
    color: white;
    font-weight: bold;
    border-radius: 8px;
    height: 45px;
}
.stButton > button:hover {
    background-color: #023E8A;
}
</style>""", unsafe_allow_html=True)

st.title("نظام إدارة برامج الشغيلة")
page = st.sidebar.radio("انتقل إلى:", ["إدارة الشغيلة", "إعداد البرامج وتوليد PDF"])

if page == "إدارة الشغيلة":
    st.header("إضافة شغيل جديد")
    col1, col2 = st.columns([2, 1])
    with col1:
        new_worker = st.text_input("اسم الشغيل")
    with col2:
        if st.button("أضف شغيل"):
            if new_worker.strip() == "":
                st.warning("يرجى إدخال اسم.")
            elif new_worker in st.session_state.workers:
                st.warning("الشغيل موجود مسبقًا.")
            else:
                st.session_state.workers[new_worker] = ""
                save_workers(st.session_state.workers)
                st.success(f"تمت إضافة {new_worker}")

    st.markdown("---")
    st.header("قائمة الشغيلة")
    if st.session_state.workers:
        col1, col2 = st.columns([2, 1])
        with col1:
            to_delete = st.selectbox("اختر شغيل للحذف:", list(st.session_state.workers.keys()))
        with col2:
            if st.button("احذف الشغيل"):
                st.session_state.workers.pop(to_delete)
                save_workers(st.session_state.workers)
                st.success(f"تم حذف {to_delete}")
    else:
        st.info("لا يوجد شغيلة حاليًا.")

elif page == "إعداد البرامج وتوليد PDF":
    st.header("إعداد البرامج")
    if not st.session_state.workers:
        st.warning("لا يوجد شغيلة.")
    else:
        selected_worker = st.selectbox("اختر الشغيل لتعديل برنامجه:", list(st.session_state.workers.keys()))
        current_program = st.session_state.workers[selected_worker]
        updated_program = st.text_area("برنامج العمل", value=current_program, height=250)

        if st.button("احفظ البرنامج"):
            st.session_state.workers[selected_worker] = updated_program
            save_workers(st.session_state.workers)
            st.success(f"تم حفظ البرنامج لـ {selected_worker}")

    st.markdown("---")
    st.header("توليد ملف PDF")

    if st.button("أنشئ PDF"):
        if not st.session_state.workers:
            st.warning("لا يوجد بيانات.")
        else:
            with NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                c = canvas.Canvas(tmp_file.name, pagesize=(595, 842))
                for i, name in enumerate(st.session_state.workers.keys()):
                    # استخدم آخر ما كتبه المستخدم
                    program = updated_program if name == selected_worker else st.session_state.workers[name]

                    if i != 0:
                        c.showPage()

                    c.setFont("OpenSans", 16)
                    c.drawCentredString(297.5, 800, reshape_text("פרויקט חלוקת משימות יומי"))

                    reshaped_name = reshape_text(f"שם העובד: {name}")
                    c.setFont("OpenSans", 14)
                    c.drawRightString(545, 760, reshaped_name)

                    c.setFont("OpenSans", 12)
                    y = 730
                    for line in program.split("\n"):
                        if line.strip():
                            reshaped_line = reshape_text(line)
                            c.drawRightString(545, y, reshaped_line)
                            y -= 20

                    c.setLineWidth(0.5)
                    c.line(50, 80, 545, 80)

                    c.setFont("OpenSans", 8)
                    c.setFillGray(0.4)
                    c.drawRightString(545, 65, "© 2025 Kasabri Nader App")
                    c.setFillGray(0)

                c.save()

                st.success("تم إنشاء ملف PDF بنجاح!")
                with open(tmp_file.name, "rb") as f:
                    st.download_button(
                        label="تحميل PDF",
                        data=f,
                        file_name="programs.pdf",
                        mime="application/pdf"
                    )
