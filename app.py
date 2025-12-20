# app.py - Streamlit PDF Merger

import streamlit as st
import os
import tempfile
from pathlib import Path
from PyPDF2 import PdfMerger, PdfReader
import io
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="PDF Merger Pro",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .file-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    .success-box {
        background-color: #D1FAE5;
        border: 1px solid #10B981;
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
    }
    .error-box {
        background-color: #FEE2E2;
        border: 1px solid #EF4444;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .stButton button {
        width: 100%;
    }
    .valid-pdf {
        border-left: 4px solid #10B981;
    }
    .invalid-pdf {
        border-left: 4px solid #EF4444;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'merged_pdf' not in st.session_state:
    st.session_state.merged_pdf = None
if 'merge_status' not in st.session_state:
    st.session_state.merge_status = ""
if 'valid_files' not in st.session_state:
    st.session_state.valid_files = []

# ========== STEP 1: PDF VALIDATION FUNCTION ==========
def validate_pdf(file_path):
    """Validate if a PDF file is readable and not corrupted"""
    try:
        with open(file_path, 'rb') as f:
            reader = PdfReader(f)
            num_pages = len(reader.pages)
            # Try to read some metadata to ensure it's truly valid
            _ = reader.metadata
            _ = reader.trailer
            return True, num_pages, "Valid PDF"
    except Exception as e:
        error_msg = str(e)
        if "startxref" in error_msg:
            return False, 0, "Corrupted PDF: Invalid file structure"
        elif "EOF" in error_msg:
            return False, 0, "Incomplete or corrupted PDF"
        elif "encrypted" in error_msg.lower():
            return False, 0, "Password-protected PDF"
        else:
            return False, 0, f"Invalid PDF: {error_msg[:100]}"

def repair_pdf(input_path, output_path):
    """Try to repair a corrupted PDF by re-writing it"""
    try:
        from pypdf import PdfReader as PyPdfReader, PdfWriter
        
        reader = PyPdfReader(input_path)
        writer = PdfWriter()
        
        # Copy all pages
        for page in reader.pages:
            writer.add_page(page)
        
        # Copy metadata if available
        if reader.metadata:
            writer.add_metadata(reader.metadata)
        
        # Save repaired version
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        return True, "PDF repaired successfully"
    except Exception as e:
        return False, f"Could not repair: {str(e)}"

def merge_pdfs(file_list, output_path):
    """Merge multiple PDF files into one"""
    merger = PdfMerger()
    
    for file in file_list:
        merger.append(file)
    
    with open(output_path, 'wb') as output_file:
        merger.write(output_file)
    
    merger.close()
    return output_path

def get_file_size(file_path):
    """Get file size in readable format"""
    size_bytes = os.path.getsize(file_path)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def main():
    # Header
    st.markdown('<h1 class="main-header">📄 PDF Merger Pro</h1>', unsafe_allow_html=True)
    st.markdown("Merge multiple PDF files into a single document")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # REMOVED output_name from sidebar - MOVED TO MAIN AREA
        st.info("**📝 Name your file** in the main area below the uploaded files")
        
        # Merge options
        st.subheader("Merge Options")
        compress = st.checkbox("Compress output PDF", value=True)
        linearize = st.checkbox("Optimize for web viewing", value=True)
        
        # PDF Validation options
        st.subheader("PDF Validation")
        auto_validate = st.checkbox("Validate PDFs automatically", value=True)
        attempt_repair = st.checkbox("Attempt to repair corrupted PDFs", value=False)
        
        # Page order
        page_order = st.radio(
            "Page Order",
            ["Sequential (File1, File2, File3)", "Alternating (Page1, Page1, Page2, Page2)"]
        )
        
        st.divider()
        
        # Clear button
        if st.button("🗑️ Clear All Files", use_container_width=True):
            st.session_state.uploaded_files = []
            st.session_state.merged_pdf = None
            st.session_state.valid_files = []
            st.rerun()
    
    # Main content area - Two columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📁 Upload PDF Files")
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Drag and drop PDF files here",
            type=['pdf'],
            accept_multiple_files=True,
            help="Select multiple PDF files to merge"
        )
        
        # Process uploaded files
        if uploaded_files:
            temp_files = []
            validation_results = []
            
            for uploaded_file in uploaded_files:
                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                
                # Save uploaded file
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                
                # Validate PDF if enabled
                is_valid = True
                page_count = 0
                validation_msg = "Not validated"
                
                if auto_validate:
                    is_valid, page_count, validation_msg = validate_pdf(temp_path)
                    
                    # Attempt repair if invalid and repair is enabled
                    if not is_valid and attempt_repair:
                        repair_path = temp_path + "_repaired.pdf"
                        repair_success, repair_msg = repair_pdf(temp_path, repair_path)
                        if repair_success:
                            # Validate the repaired version
                            is_valid, page_count, validation_msg = validate_pdf(repair_path)
                            if is_valid:
                                temp_path = repair_path  # Use repaired version
                                validation_msg = f"Repaired: {validation_msg}"
                
                temp_files.append({
                    'name': uploaded_file.name,
                    'path': temp_path,
                    'size': uploaded_file.size,
                    'is_valid': is_valid,
                    'page_count': page_count,
                    'validation_msg': validation_msg
                })
            
            st.session_state.uploaded_files = temp_files
            
            # Separate valid and invalid files
            valid_files = [f for f in temp_files if f['is_valid']]
            invalid_files = [f for f in temp_files if not f['is_valid']]
            st.session_state.valid_files = valid_files
            
            # Show validation summary
            if invalid_files and auto_validate:
                st.error(f"⚠️ {len(invalid_files)} invalid PDF file(s) detected")
                for invalid in invalid_files:
                    with st.expander(f"❌ {invalid['name']} - {invalid['validation_msg']}", expanded=False):
                        st.write(f"**Issue:** {invalid['validation_msg']}")
                        st.write(f"**Size:** {get_file_size(invalid['path'])}")
                        if attempt_repair:
                            st.info("Repair was attempted but unsuccessful")
        
        # Display uploaded files
        if st.session_state.uploaded_files:
            st.subheader(f"📋 Selected Files ({len(st.session_state.uploaded_files)} files)")
            
            for i, file_info in enumerate(st.session_state.uploaded_files):
                with st.expander(f"{'✅' if file_info['is_valid'] else '❌'} {i+1}. {file_info['name']}", expanded=not file_info['is_valid']):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.write(f"**Size:** {get_file_size(file_info['path'])}")
                        
                        if file_info['page_count'] > 0:
                            st.write(f"**Pages:** {file_info['page_count']}")
                        else:
                            st.write("**Pages:** Unknown")
                        
                        if not file_info['is_valid'] and auto_validate:
                            st.error(f"**Status:** {file_info['validation_msg']}")
                        elif auto_validate:
                            st.success(f"**Status:** {file_info['validation_msg']}")
                    
                    with col_b:
                        if st.button(f"Remove", key=f"remove_{i}"):
                            st.session_state.uploaded_files.pop(i)
                            if i < len(st.session_state.valid_files):
                                st.session_state.valid_files.pop(i)
                            st.rerun()
        
        # ======== NEW: OUTPUT FILENAME SECTION (Right below files) ========
        if st.session_state.uploaded_files:
            st.markdown("---")
            st.header("📝 Name Your Merged File")
            
            col_name1, col_name2 = st.columns([3, 1])
            
            with col_name1:
                output_name = st.text_input(
                    "**Filename for merged PDF:**",
                    value=f"merged_document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    help="Enter any name you want for the merged PDF file",
                    key="output_filename"
                )
                
                # Auto-add .pdf if missing
                if output_name and not output_name.lower().endswith('.pdf'):
                    output_name = output_name + ".pdf"
                    st.success(f"✅ Added .pdf extension: **{output_name}**")
                elif output_name:
                    st.info(f"📄 File will be saved as: **{output_name}**")
            
            with col_name2:
                st.markdown("**Quick Options:**")
                quick_col1, quick_col2 = st.columns(2)
                with quick_col1:
                    if st.button("📅", help="Date-based name", use_container_width=True):
                        st.session_state.output_filename = f"merged_{datetime.now().strftime('%Y%m%d')}.pdf"
                        st.rerun()
                with quick_col2:
                    if st.button("📄", help="Simple name", use_container_width=True):
                        st.session_state.output_filename = "merged_documents.pdf"
                        st.rerun()
                
                if st.button("🔄 Reset", type="secondary", use_container_width=True):
                    st.session_state.output_filename = f"merged_document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    st.rerun()
            
            st.caption("💡 This name will be used when you click 'Merge PDFs Now'")

    with col2:
        st.header("🔄 Merge Action")
        
        # Get valid file count
        valid_count = len(st.session_state.valid_files)
        
        if valid_count > 1:
            # Show file count
            st.metric("📊 Ready to Merge", f"{valid_count} valid PDFs")
            
            # Make sure output_name is defined
            if 'output_name' not in locals():
                output_name = f"merged_document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            if st.button("✨ **Merge PDFs Now**", type="primary", use_container_width=True, key="merge_button"):
                with st.spinner("Merging PDFs..."):
                    try:
                        # Create output path
                        temp_dir = tempfile.gettempdir()
                        output_path = os.path.join(temp_dir, output_name)
                        
                        # Get only valid file paths
                        valid_file_paths = [f['path'] for f in st.session_state.valid_files]
                        
                        if not valid_file_paths:
                            st.error("No valid PDF files to merge!")
                            return
                        
                        # Try different PDF libraries if PyPDF2 fails
                        try:
                            # Try with PyPDF2 first
                            from PyPDF2 import PdfMerger
                            merger = PdfMerger()
                            for file_path in valid_file_paths:
                                merger.append(file_path)
                            
                            with open(output_path, 'wb') as output_file:
                                merger.write(output_file)
                            merger.close()
                            
                        except Exception as pdf_error:
                            # Fallback to pypdf library
                            try:
                                st.info("Trying alternative PDF library...")
                                from pypdf import PdfMerger as PyPdfMerger
                                merger = PyPdfMerger()
                                for file_path in valid_file_paths:
                                    merger.append(file_path)
                                
                                with open(output_path, 'wb') as output_file:
                                    merger.write(output_file)
                                merger.close()
                                
                            except Exception as fallback_error:
                                raise Exception(f"Both PDF libraries failed:\n1. {pdf_error}\n2. {fallback_error}")
                        
                        # Store in session state
                        st.session_state.merged_pdf = output_path
                        st.session_state.merge_status = "success"
                        
                        st.success(f"✅ Successfully merged {valid_count} PDF files!")
                        st.balloons()
                        
                        # Show file info
                        file_size = get_file_size(output_path)
                        total_pages = sum(f['page_count'] for f in st.session_state.valid_files)
                        st.info(f"**Output:** {output_name}\n**Size:** {file_size}\n**Total Pages:** {total_pages}")
                        
                    except Exception as e:
                        error_msg = str(e)
                        if "startxref" in error_msg or "incorrect startxref" in error_msg:
                            st.error("""
                            ❌ PDF File Error: One or more PDF files are corrupted.
                            
                            **Solutions:**
                            1. Try different PDF files
                            2. Re-download the PDFs from original source
                            3. Use PDFs created from Word/Google Docs
                            4. Check if PDFs are password-protected
                            5. Enable 'Attempt to repair' in settings
                            """)
                        elif "encrypted" in error_msg.lower():
                            st.error("""
                            ❌ Password-protected PDF detected.
                            
                            **Solution:**
                            1. Remove password protection from PDFs before uploading
                            2. Use PDFs without security restrictions
                            """)
                        else:
                            st.error(f"❌ Error merging PDFs: {error_msg}")
                        st.session_state.merge_status = "error"
        
        elif valid_count == 1:
            if auto_validate:
                st.warning(f"Need at least 2 valid PDF files to merge. You have 1 valid PDF.")
            else:
                st.warning("Upload at least 2 PDF files to merge")
        elif len(st.session_state.uploaded_files) > 0 and valid_count == 0:
            st.error("No valid PDF files detected! Check file validation above.")
        else:
            st.info("Upload PDF files to begin")
        
        # Download section
        if st.session_state.merged_pdf and os.path.exists(st.session_state.merged_pdf):
            st.markdown("---")
            st.header("📥 Download")
            
            # Make sure output_name is defined for download
            if 'output_name' not in locals():
                output_name = os.path.basename(st.session_state.merged_pdf)
            
            # Show download info
            col_d1, col_d2 = st.columns([2, 1])
            with col_d1:
                st.success(f"**Ready to download:** {output_name}")
                st.caption(f"Size: {get_file_size(st.session_state.merged_pdf)}")
            with col_d2:
                with open(st.session_state.merged_pdf, "rb") as file:
                    st.download_button(
                        label="⬇️ Download",
                        data=file,
                        file_name=output_name,
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary"
                    )
            
            # Clear merge button
            if st.button("🗑️ Clear & Start Over", type="secondary", use_container_width=True):
                st.session_state.merged_pdf = None
                st.rerun()
    
    # Footer (OUTSIDE the columns, at the very bottom)
    st.divider()
    with st.expander("ℹ️ How to Use & Tips"):
        st.markdown("""
        ### Step-by-Step:
        1. **📁 Upload PDFs** - Select your PDF files
        2. **✅ Check validation** - See which files are valid
        3. **📝 Name your file** - Enter filename (right above this section)
        4. **🔄 Merge** - Click 'Merge PDFs Now' button
        5. **📥 Download** - Get your merged PDF
        
        ### Quick Tips:
        - Name your file before merging
        - Invalid files won't be merged
        - Enable 'Attempt to repair' for corrupted PDFs
        - All processing happens locally
        """)

if __name__ == "__main__":
    main()