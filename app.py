import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Any Budget Bleed Tool", layout="centered")

# --- APP INTERFACE ---
try:
    st.image("Any Budget Logo.png", width=300)
except:
    st.warning("Logo not found. Make sure 'Any Budget Logo.png' is in your GitHub folder.")

st.title("Any Budget PDF Bleed Tool")

st.write("""
1. **Upload** a file (PDF, PNG, or JPG).
2. The tool **automatically creates** perfect bleeds.
3. **Download** your new print-ready PDF.
""")

def add_pixel_stretch_bleed(image, bleed_px):
    """
    Takes a PIL image and adds a 'smeared' pixel bleed to all sides.
    This preserves the center quality perfectly.
    """
    w, h = image.size
    new_w = w + 2 * bleed_px
    new_h = h + 2 * bleed_px
    
    # Create new canvas
    new_img = Image.new("RGB", (new_w, new_h))
    
    # Paste original in the center
    new_img.paste(image, (bleed_px, bleed_px))
    
    # --- 1. STRETCH TOP EDGE ---
    # Crop the top 1px row
    top_row = image.crop((0, 0, w, 1))
    # Resize it to fill the top bleed area
    top_fill = top_row.resize((w, bleed_px), resample=Image.NEAREST)
    new_img.paste(top_fill, (bleed_px, 0))
    
    # --- 2. STRETCH BOTTOM EDGE ---
    # Crop the bottom 1px row
    bottom_row = image.crop((0, h-1, w, h))
    # Resize it to fill the bottom bleed area
    bottom_fill = bottom_row.resize((w, bleed_px), resample=Image.NEAREST)
    new_img.paste(bottom_fill, (bleed_px, h + bleed_px))
    
    # --- 3. STRETCH LEFT EDGE ---
    # Crop the left 1px column
    left_col = image.crop((0, 0, 1, h))
    # Resize it to fill the left bleed area
    left_fill = left_col.resize((bleed_px, h), resample=Image.NEAREST)
    new_img.paste(left_fill, (0, bleed_px))
    
    # --- 4. STRETCH RIGHT EDGE ---
    # Crop the right 1px column
    right_col = image.crop((w-1, 0, w, h))
    # Resize it to fill the right bleed area
    right_fill = right_col.resize((bleed_px, h), resample=Image.NEAREST)
    new_img.paste(right_fill, (w + bleed_px, bleed_px))
    
    # --- 5. FILL CORNERS ---
    # We take the corner pixels and stretch them into the empty corner blocks
    
    # Top-Left
    tl_pixel = image.crop((0, 0, 1, 1)).resize((bleed_px, bleed_px), resample=Image.NEAREST)
    new_img.paste(tl_pixel, (0, 0))
    
    # Top-Right
    tr_pixel = image.crop((w-1, 0, w, 1)).resize((bleed_px, bleed_px), resample=Image.NEAREST)
    new_img.paste(tr_pixel, (w + bleed_px, 0))
    
    # Bottom-Left
    bl_pixel = image.crop((0, h-1, 1, h)).resize((bleed_px, bleed_px), resample=Image.NEAREST)
    new_img.paste(bl_pixel, (0, h + bleed_px))
    
    # Bottom-Right
    br_pixel = image.crop((w-1, h-1, w, h)).resize((bleed_px, bleed_px), resample=Image.NEAREST)
    new_img.paste(br_pixel, (w + bleed_px, h + bleed_px))
    
    return new_img

# --- FILE UPLOADER ---
uploaded_file = st.file_uploader("Upload File", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    
    processed_images = []
    
    # Load input as Image list
    if uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
        img = Image.open(uploaded_file)
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        # We assume 600 DPI for uploaded images
        processed_images.append(img)
        
    else:
        # It is a PDF -> Render pages to Images
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        for page in doc:
            # --- CHANGE 1: Render at 600 DPI (High Resolution) ---
            pix = page.get_pixmap(dpi=600)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            processed_images.append(img)

    # PROCESS BLEEDS
    # --- CHANGE 2: Update bleed pixels for 600 DPI ---
    # 0.0625 inches * 600 DPI = 37.5 -> Round to 38
    BLEED_PX = 38
    
    final_pdf_images = []
    
    with st.spinner("Generating High-Res Pixel-Stretched Bleeds..."):
        for img in processed_images:
            final_img = add_pixel_stretch_bleed(img, BLEED_PX)
            final_pdf_images.append(final_img)

    # SAVE TO PDF
    output_buffer = io.BytesIO()
    if final_pdf_images:
        final_pdf_images[0].save(
            output_buffer, 
            "PDF", 
            resolution=600.0, # --- CHANGE 3: Save as 600 DPI ---
            save_all=True, 
            append_images=final_pdf_images[1:]
        )
    
    st.success("Success! Download PDF with Bleeds.")
    
    st.download_button(
        label="Download Print-Ready PDF",
        data=output_buffer.getvalue(),
        file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}WITH_BLEEDS.pdf",
        mime="application/pdf"
    )

