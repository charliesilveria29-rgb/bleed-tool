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
    # Define bleed size: 0.0625 inches = 4.5 points
    BLEED_PTS = 4.5 
    
    # Create a new empty PDF to hold the final stretched pages
    new_doc = fitz.open()
    
    for page in doc:
        # Get original size
        rect = page.rect
        
        # Calculate new size (Original + Bleed on all sides)
        new_width = rect.width + (2 * BLEED_PTS)
        new_height = rect.height + (2 * BLEED_PTS)
        
        # Create a new page in the new document with the larger size
        new_page = new_doc.new_page(width=new_width, height=new_height)
        
        # Draw the original page onto the new page, STRETCHING it to fill the new box
        # keep_proportion=False is the magic key to eliminate white strips!
        new_page.show_pdf_page(new_page.rect, doc, page.number, keep_proportion=False)

    # 3. SAVE & DOWNLOAD
    output_buffer = io.BytesIO()
    new_doc.save(output_buffer)
    new_doc.close()
    
    st.success("Success! Bleeds added.")
    
    st.download_button(
        label="Download Print-Ready PDF",
        data=output_buffer.getvalue(),
        file_name=f"BLEED_{uploaded_file.name.rsplit('.', 1)[0]}.pdf",
        mime="application/pdf"
    )

