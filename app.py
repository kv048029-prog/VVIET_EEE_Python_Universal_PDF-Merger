import streamlit as st
import io
from PIL import Image
from pypdf import PdfWriter, PdfReader
import docx
from fpdf import FPDF
import fitz  # PyMuPDF

# --- Helper Functions ---

def image_to_pdf_bytes(image_bytes):
    """Converts an uploaded image (PNG/JPG) to a single-page PDF in memory."""
    image = Image.open(io.BytesIO(image_bytes))
    # Convert RGBA (PNGs with transparency) to RGB so it can be saved as PDF
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    pdf_buffer = io.BytesIO()
    image.save(pdf_buffer, format="PDF")
    return pdf_buffer.getvalue()

def docx_to_pdf_bytes(docx_bytes):
    """
    Extracts text from a DOCX file and creates a basic PDF.
    (Excludes complex formatting/images for cloud compatibility).
    """
    doc = docx.Document(io.BytesIO(docx_bytes))
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    
    for para in doc.paragraphs:
        # Replace characters that might break standard encoding
        clean_text = para.text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, text=clean_text)
        
    return bytes(pdf.output())

def render_pdf_page_by_page(pdf_bytes):
    """Renders a PDF byte stream into Streamlit images page by page."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # Increase resolution slightly with a matrix
        zoom_matrix = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=zoom_matrix)
        
        # Convert PyMuPDF pixmap to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        st.markdown(f"**Page {page_num + 1}**")
        st.image(img, use_column_width=True)
        st.divider()

# --- Main Streamlit App ---

st.set_page_config(page_title="Universal PDF Merger", page_icon="📄", layout="centered")

st.title("📄 Universal PDF Merger")
st.write("Upload PDFs, Images (JPG, PNG), and Word Documents (.docx). They will be merged into a single PDF which you can preview and download.")

# File uploader allowing multiple files
uploaded_files = st.file_uploader(
    "Upload your files here", 
    type=["pdf", "png", "jpg", "jpeg", "docx"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.info(f"{len(uploaded_files)} file(s) selected. Drag and drop in the uploader to reorder them before merging.")
    
    if st.button("Merge Files", type="primary"):
        with st.spinner("Processing and merging files..."):
            pdf_writer = PdfWriter()
            
            try:
                for uploaded_file in uploaded_files:
                    file_name = uploaded_file.name.lower()
                    file_bytes = uploaded_file.read()
                    
                    # 1. Handle PDFs
                    if file_name.endswith(".pdf"):
                        reader = PdfReader(io.BytesIO(file_bytes))
                        for page in reader.pages:
                            pdf_writer.add_page(page)
                            
                    # 2. Handle Images
                    elif file_name.endswith((".png", ".jpg", ".jpeg")):
                        converted_pdf = image_to_pdf_bytes(file_bytes)
                        reader = PdfReader(io.BytesIO(converted_pdf))
                        pdf_writer.add_page(reader.pages[0])
                        
                    # 3. Handle Word Documents
                    elif file_name.endswith(".docx"):
                        converted_pdf = docx_to_pdf_bytes(file_bytes)
                        reader = PdfReader(io.BytesIO(converted_pdf))
                        for page in reader.pages:
                            pdf_writer.add_page(page)
                
                # Save the merged PDF to a bytes buffer
                merged_pdf_buffer = io.BytesIO()
                pdf_writer.write(merged_pdf_buffer)
                merged_pdf_bytes = merged_pdf_buffer.getvalue()
                
                st.success("Files merged successfully!")
                
                # Provide Download Button
                st.download_button(
                    label="⬇️ Download Merged PDF",
                    data=merged_pdf_bytes,
                    file_name="merged_document.pdf",
                    mime="application/pdf"
                )
                
                # Display Page by Page
                st.subheader("Preview: Page by Page")
                render_pdf_page_by_page(merged_pdf_bytes)

            except Exception as e:
                st.error(f"An error occurred during merging: {e}")
