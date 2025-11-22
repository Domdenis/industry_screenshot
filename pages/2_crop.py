import streamlit as st
from PIL import Image
from io import BytesIO
from datetime import datetime
import pandas as pd
import zipfile
from streamlit_cropper import st_cropper

# ⚠️ Ne pas ajouter st.set_page_config() - déjà fait dans app.py
# st.set_page_config(page_title="✂️ Recadrage + Suppression", layout="wide")

st.title("✂️ Recadrage puis suppression d'une zone (traitement par lot)")

# -----------------------------
# INIT SESSION
# -----------------------------
if "step" not in st.session_state:
    st.session_state.step = 1
if "cropped_images" not in st.session_state:
    st.session_state.cropped_images = None
if "crop_box" not in st.session_state:
    st.session_state.crop_box = None

# -----------------------------
# Restart bouton
# -----------------------------
if st.button("🔄 Recommencer depuis zéro"):
    for k in ["step", "cropped_images", "crop_box"]:
        st.session_state.pop(k, None)
    st.session_state.step = 1
    st.rerun()

# -----------------------------
# UPLOAD IMAGES
# -----------------------------
uploaded_files = st.file_uploader(
    "📁 Charge une ou plusieurs images PNG (même taille)",
    type=["png"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("📥 Charge au moins une image.")
    st.stop()

ref_file = uploaded_files[0]
ref_img_orig = Image.open(ref_file).convert("RGBA")
orig_w, orig_h = ref_img_orig.size

# ==========================================================
# ÉTAPE 1 : RECADRAGE
# ==========================================================
if st.session_state.step == 1:

    st.markdown("## 1️⃣ Étape 1 : Recadrer les images")
    st.write("🎯 Recadre la première image. Ce recadrage sera appliqué à toutes les images.")

    # Zone de recadrage
    crop_box = st_cropper(
        ref_img_orig,
        realtime_update=True,
        box_color='#00FF00',
        aspect_ratio=None,
        return_type="box",
        should_resize_image=False
    )

    if crop_box:
        left_c = int(crop_box["left"])
        top_c = int(crop_box["top"])
        width_c = int(crop_box["width"])
        height_c = int(crop_box["height"])

        st.success(f"✂️ Zone de recadrage : x={left_c}, y={top_c}, w={width_c}, h={height_c}")

        # Preview
        preview_crop = ref_img_orig.crop((left_c, top_c, left_c + width_c, top_c + height_c))
        st.image(preview_crop, caption="Prévisualisation recadrée", use_container_width=True)

        # -----------------------------------------
        # Appliquer le recadrage à toutes les images
        # -----------------------------------------
        if st.button("✅ Valider le recadrage et générer les images recadrées"):
            cropped_images = []

            for f in uploaded_files:
                img = Image.open(f).convert("RGBA")
                cropped = img.crop((left_c, top_c, left_c + width_c, top_c + height_c))

                buf = BytesIO()
                cropped.save(buf, format="PNG")
                cropped_images.append({
                    "name": f.name,
                    "bytes": buf.getvalue()
                })

            st.session_state.cropped_images = cropped_images
            st.session_state.crop_box = (left_c, top_c, width_c, height_c)

            st.success("🎉 Recadrage appliqué à toutes les images !")

    # -----------------------------------------
    # Télécharger uniquement les images recadrées
    # -----------------------------------------
    if st.session_state.cropped_images:
        st.markdown("### 📥 Télécharger les images recadrées (sans suppression)")
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for item in st.session_state.cropped_images:
                zipf.writestr(item["name"].replace(".png", "_recadre.png"), item["bytes"])
        zip_buffer.seek(0)
        st.download_button(
            "📦 Télécharger uniquement les images recadrées",
            zip_buffer.getvalue(),
            file_name="images_recadrees.zip"
        )

        # Passer à l'étape 2
        if st.button("➡️ Passer à l'étape 2 : suppression d'une zone"):
            st.session_state.step = 2
            st.rerun()

# ==========================================================
# ÉTAPE 2 : SUPPRESSION D'UNE ZONE
# ==========================================================
elif st.session_state.step == 2:

    st.markdown("## 2️⃣ Étape 2 : Suppression d'une zone horizontale")
    st.write("Dessine une zone à supprimer sur la première image recadrée.")

    first_crop = st.session_state.cropped_images[0]
    ref_cropped_img = Image.open(BytesIO(first_crop["bytes"])).convert("RGBA")
    cw, ch = ref_cropped_img.size

    # Zone à supprimer
    box = st_cropper(
        ref_cropped_img,
        realtime_update=True,
        box_color='#FF0000',
        aspect_ratio=None,
        return_type="box",
        should_resize_image=False
    )

    if box:
        left = int(box["left"])
        top = int(box["top"])
        width = int(box["width"])
        height = int(box["height"])

        st.success(f"🚨 Zone à supprimer : x={left}, y={top}, w={width}, h={height}")

        # Preview suppression
        top_part = ref_cropped_img.crop((0, 0, cw, top))
        bottom_part = ref_cropped_img.crop((0, top + height, cw, ch))
        new_h_prev = top_part.height + bottom_part.height

        preview_clean = Image.new("RGBA", (cw, new_h_prev))
        preview_clean.paste(top_part, (0, 0))
        preview_clean.paste(bottom_part, (0, top_part.height))

        st.image(preview_clean, caption="Prévisualisation après suppression", use_container_width=True)

        # Traitement
        if st.button("🚀 Supprimer cette zone sur toutes les images recadrées"):
            zip_buffer = BytesIO()
            logs = []

            with zipfile.ZipFile(zip_buffer, "w") as zipf:

                for item in st.session_state.cropped_images:
                    img = Image.open(BytesIO(item["bytes"])).convert("RGBA")
                    W, H = img.size

                    top_part = img.crop((0, 0, W, top))
                    bottom_part = img.crop((0, top + height, W, H))
                    new_h = top_part.height + bottom_part.height

                    out_img = Image.new("RGBA", (W, new_h))
                    out_img.paste(top_part, (0, 0))
                    out_img.paste(bottom_part, (0, top_part.height))

                    out_name = item["name"].replace(".png", "_recadre_cleaned.png")
                    img_bytes = BytesIO()
                    out_img.save(img_bytes, "PNG")
                    img_bytes.seek(0)
                    zipf.writestr(out_name, img_bytes.getvalue())

                    logs.append({
                        "Image source": item["name"],
                        "Image finale": out_name,
                        "Recadrage": str(st.session_state.crop_box),
                        "Zone supprimée": f"{left},{top},{width},{height}",
                        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })

                # Log Excel
                df = pd.DataFrame(logs)
                excel_bytes = BytesIO()
                df.to_excel(excel_bytes, index=False)
                excel_bytes.seek(0)
                zipf.writestr("log_operations.xlsx", excel_bytes.getvalue())

            zip_buffer.seek(0)

            st.success("🎉 Traitement terminé.")
            st.download_button(
                "📦 Télécharger les images finales (ZIP)",
                zip_buffer.getvalue(),
                file_name="images_recadrees_et_nettoyees.zip"
            )
