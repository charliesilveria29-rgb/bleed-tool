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

st.title("Any Budget PDF Bleed Creator")

st.write("""
1. **Upload** a file (PDF, PNG, JPG, or TIF).
2. **Automatically create** perfect bleeds.
3. **Download** your new print-ready PDF.
4. Place your order at [anybudget.com](https://anybudget.com)
""")

def get_stretched_background(page, bleed_pts):
    """
    Generates a pixel-stretched image of the page to use as a background.
    """
    # 1. Render page to image (DPI 150 is fine for the blurry edge effect)
    pix = page.get_pixmap(dpi=150)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    # 2. Calculate pixel bleed amount based on the 150 DPI
    # (bleed_pts / 72 inch) * 150 dpi
    bleed_px = int((bleed_pts / 72) * 150)
    
    w, h = img.size
    new_w = w + 2 * bleed_px
    new_h = h + 2 * bleed_px
    
    # 3. Create the stretched canvas
    new_img = Image.new("RGB", (new_w, new_h))
    new_img.paste(img, (bleed_px, bleed_px))
    
    # Stretch Top
    top = img.crop((0, 0, w, 1)).resize((w, bleed_px), resample=Image.NEAREST)
    new_img.paste(top, (bleed_px, 0))
    
    # Stretch Bottom
    bot = img.crop((0, h-1, w, h)).resize((w, bleed_px), resample=Image.NEAREST)
    new_img.paste(bot, (bleed_px, h + bleed_px))
    
    # Stretch Left
    left = img.crop((0, 0, 1, h)).resize((bleed_px, h), resample=Image.NEAREST)
    new_img.paste(left, (0, bleed_px))
    
    # Stretch Right
    right = img.crop((w-1, 0, w, h)).resize((bleed_px, h), resample=Image.NEAREST)
    new_img.paste(right, (w + bleed_px, bleed_px))
    
    # Corners
    tl = img.crop((0, 0, 1, 1)).resize((bleed_px, bleed_px), resample=Image.NEAREST)
    new_img.paste(tl, (0, 0))
    
    tr = img.crop((w-1, 0, w, 1)).resize((bleed_px, bleed_px), resample=Image.NEAREST)
    new_img.paste(tr, (w + bleed_px, 0))
    
    bl = img.crop((0, h-1, 1, h)).resize((bleed_px, bleed_px), resample=Image.NEAREST)
    new_img.paste(bl, (0, h + bleed_px))
    
    br = img.crop((w-1, h-1, w, h)).resize((bleed_px, bleed_px), resample=Image.NEAREST)
    new_img.paste(br, (w + bleed_px, h + bleed_px))
    
    return new_img

# --- FILE UPLOADER ---
# Added 'tif' and 'tiff' to the allowed types list
uploaded_file = st.file_uploader("Upload File", type=["pdf", "png", "jpg", "jpeg", "tif", "tiff"])

if uploaded_file is not None:
    
    # 1. PREPARE SOURCE DOCUMENT
    # If image, convert to PDF in memory first so we can treat everything as a PDF
    # Added .tif and .tiff to the check below
    if uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff')):
        img = Image.open(uploaded_file)
        
        # Convert RGBA (transparent) or CMYK (often used in TIF) to RGB so it saves as PDF
        if img.mode in ('RGBA', 'CMYK'):
            img = img.convert('RGB')
            
        pdf_stream = io.BytesIO()
        img.save(pdf_stream, format="PDF", resolution=300)
        pdf_stream.seek(0)
        doc = fitz.open(stream=pdf_stream.read(), filetype="pdf")
    else:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

    # 2. CREATE NEW PDF WITH BLEEDS
    # 0.0625 inches = 4.5 points
    BLEED_PTS = 4.5
    
    new_doc = fitz.open()
    
    with st.spinner("Generating Hybrid Vector Bleeds..."):
        for page in doc:
            original_rect = page.rect
            width = original_rect.width
            height = original_rect.height
            
            # Create new page with bleed dimensions
            new_page = new_doc.new_page(width = width + (2 * BLEED_PTS),
                                        height = height + (2 * BLEED_PTS))
            
            # STEP A: Draw the "Stretched" Background Image
            # We generate the smeared image and insert it to fill the WHOLE new page
            bg_img = get_stretched_background(page, BLEED_PTS)
            with io.BytesIO() as f:
                bg_img.save(f, format="JPEG", quality=95)
                new_page.insert_image(new_page.rect, stream=f.getvalue())
            
            # STEP B: Overlay the ORIGINAL Vector Page in the center
            # This keeps text 100% sharp because we are pasting the vector PDF, not an image
            target_rect = fitz.Rect(BLEED_PTS, BLEED_PTS, 
                                    width + BLEED_PTS, height + BLEED_PTS)
            
            new_page.show_pdf_page(target_rect, doc, page.number)

    # 3. SAVE & DOWNLOAD
    output_buffer = io.BytesIO()
    new_doc.save(output_buffer)
    new_doc.close()
    
    st.success("Success!")
    
    st.download_button(
        label="Download Print-Ready PDF",
        data=output_buffer.getvalue(),
        file_name=f"{uploaded_file.name.rsplit('.', 1)[0]}_WITH_BLEEDS.pdf",
        mime="application/pdf"
    )

