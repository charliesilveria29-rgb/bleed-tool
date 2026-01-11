import streamlit as st
import fitz  # This is PyMuPDF
from PIL import Image
import io

def add_bleed(page_pixmap):
    # Convert to PIL Image
    mode = "RGBA" if page_pixmap.alpha else "RGB"
    img = Image.frombytes(mode, [page_pixmap.width, page_pixmap.height], page_pixmap.samples)
    
    # Settings
    DPI = 300 
    BLEED_PX = int(0.0625 * DPI)
    w, h = img.size
    
    # Create larger canvas
    new_w = w + (BLEED_PX * 2)
    new_h = h + (BLEED_PX * 2)
    new_img = Image.new("RGB", (new_w, new_h), "white")
    
    # Paste original in center
    new_img.paste(img, (BLEED_PX, BLEED_PX))
    
    # --- PIXEL STRETCH METHOD ---
    # 1. TOP
    top_row = img.crop((0, 0, w, 1))
    top_stretch = top_row.resize((w, BLEED_PX))
    new_img.paste(top_stretch, (BLEED_PX, 0))
    
    # 2. BOTTOM
    bot_row = img.crop((0, h-1, w, h))
    bot_stretch = bot_row.resize((w, BLEED_PX))
    new_img.paste(bot_stretch, (BLEED_PX, new_h - BLEED_PX))
    
    # 3. LEFT
    left_col = img.crop((0, 0, 1, h))
    left_stretch = left_col.resize((BLEED_PX, h))
    new_img.paste(left_stretch, (0, BLEED_PX))
    
    # 4. RIGHT
    right_col = img.crop((w-1, 0, w, h))
    right_stretch = right_col.resize((BLEED_PX, h))
    new_img.paste(right_stretch, (new_w - BLEED_PX, BLEED_PX))
    
    # --- CORNERS ---
    # Top-Left
    tl_pixel = img.crop((0, 0, 1, 1))
    tl_fill = tl_pixel.resize((BLEED_PX, BLEED_PX))
    new_img.paste(tl_fill, (0, 0))
    
    # Top-Right
    tr_pixel = img.crop((w-1, 0, w, 1))
    tr_fill = tr_pixel.resize((BLEED_PX, BLEED_PX))
    new_img.paste(tr_fill, (new_w - BLEED_PX, 0))
    
    # Bottom-Left
    bl_pixel = img.crop((0, h-1, 1, h))
    bl_fill = bl_pixel.resize((BLEED_PX, BLEED_PX))
    new_img.paste(bl_fill, (0, new_h - BLEED_PX))
    
    # Bottom-Right
    br_pixel = img.crop((w-1, h-1, w, h))
    br_fill = br_pixel.resize((BLEED_PX, BLEED_PX))
    new_img.paste(br_fill, (new_w - BLEED_PX, new_h - BLEED_PX))

    return new_img

# --- APP INTERFACE ---
st.image("Any Budget Logo.png", width=300)
st.title("Any Budget PDF Bleed Tool")
st.write("""
1. **Upload** a PDF file without bleeds.
2. The tool **automatically creates** bleeds by stretching the edges.
3. **Download** your new print-ready file.
""")

uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file:
    # This "with" block creates a temporary spinner that vanishes when done
    with st.spinner("Processing... please wait."):
        try:
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            processed_pages = []
            
            for page in doc:
                pix = page.get_pixmap(dpi=300)
                new_page = add_bleed(pix)
                processed_pages.append(new_page)
                
            pdf_bytes = io.BytesIO()
            processed_pages[0].save(pdf_bytes, format="PDF", save_all=True, append_images=processed_pages[1:], resolution=300)
            
            # Set flag to show success message outside the spinner
            success = True
            
        except Exception as e:
            st.error(f"Error: {e}")
            success = False

    # This code runs AFTER the spinner has disappeared
    if success:
        st.success("Done!")

        st.download_button("Download Print-Ready PDF", data=pdf_bytes.getvalue(), file_name="bleed_added_stretched.pdf", mime="application/pdf")





