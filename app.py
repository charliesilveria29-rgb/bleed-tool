import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Any Budget Bleed Tool", layout="centered")

# --- APP INTERFACE ---
# Make sure "Any Budget Logo.png" is uploaded to your GitHub folder!
try:
    st.image("Any Budget Logo.png", width=300)
except:
    st.warning("Logo not found. Make sure 'Any Budget Logo.png' is in your GitHub folder.")

st.title("Any Budget PDF Bleed Tool")

st.write("""
1. **Upload** a file (PDF, PNG, or JPG).
2. The tool **automatically converts & adds bleeds** by stretching the content.
3. **Download** your new print-ready PDF.
""")

# --- FILE UPLOADER (Accepts PDF & Images) ---
uploaded_file = st.file_uploader("Upload File", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file is not None:
    
    # 1. PRE-PROCESSING: Convert Image to PDF if needed
    if uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg')):
        # Open the image
        image = Image.open(uploaded_file)
        
        # Convert RGBA (transparent) to RGB so it saves as PDF
        if image.mode == 'RGBA':
            image = image.convert('RGB')
            
        # Save image as PDF into memory
        pdf_stream = io.BytesIO()
        image.save(pdf_stream, format="PDF", resolution=300)
        pdf_stream.seek(0)
        
        # Load this new PDF into PyMuPDF
        doc = fitz.open(stream=pdf_stream.read(), filetype="pdf")
        st.info("Image converted to PDF. Now adding bleeds...")
        
    else:
        # It's already a PDF, just load it
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

    # 2. BLEED GENERATION LOGIC
    # Define bleed size: 0.125 inches = 9 points (Standard Print Bleed)
    BLEED_PTS = 9 
    
    for page in doc:
        # Get current size
        rect = page.rect
        
        # Calculate scale factor to stretch content to fill the new bleed area
        # (New Size / Old Size)
        scale_x = (rect.width + 2 * BLEED_PTS) / rect.width
        scale_y = (rect.height + 2 * BLEED_PTS) / rect.height
        
        # Apply the scaling matrix to the page content
        mat = fitz.Matrix(scale_x, scale_y)
        page.set_transformation_matrix(mat)
        
        # Update the page's visible box (MediaBox) to match the new scaled size
        page.set_mediabox(fitz.Rect(0, 0, rect.width * scale_x, rect.height * scale_y))

    # 3. SAVE & DOWNLOAD
    output_buffer = io.BytesIO()
    doc.save(output_buffer)
    doc.close()
    
    st.success("Success! Bleeds added.")
    
    st.download_button(
        label="Download Print-Ready PDF",
        data=output_buffer.getvalue(),
        file_name=f"BLEED_{uploaded_file.name.rsplit('.', 1)[0]}.pdf",
        mime="application/pdf"
    )
