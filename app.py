# app.py - Clean Minimalist PDF Merger with Size Display

import streamlit as st
import os
import tempfile
from pathlib import Path
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import io
from datetime import datetime
import subprocess
import sys

# Page configuration
st.set_page_config(
    page_title="PDF Merger",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean Minimalist CSS
st.markdown("""
<style>
    /* Clean minimalist styling */
    .main-header {
        font-size: 2rem;
        color: #000000;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    
    /* Clean sidebar - white background, black text */
    [data-testid="stSidebar"] {
        background-color: white !important;
        color: black !important;
    }
    
    [data-testid="stSidebar"] * {
        color: #000000 !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] .st-emotion-cache-16idsys p {
        color: #000000 !important;
        font-weight: 500 !important;
    }
    
    /* Clean buttons */
    .stButton button {
        border-radius: 6px;
        border: 1px solid #ddd;
        transition: all 0.2s ease;
    }
    
    .stButton button:hover {
        border-color: #3B82F6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Size display styling */
    .size-info {
        background: #f8f9fa;
        border-radius: 6px;
        padding: 10px;
        margin: 10px 0;
        border: 1px solid #e9ecef;
    }
    
    .size-original {
        color: #6c757d;
        font-size: 0.9rem;
    }
    
    .size-compressed {
        color: #198754;
        font-weight: 500;
        font-size: 0.9rem;
    }
    
    .size-reduction {
        color: #0d6efd;
        font-weight: 600;
        font-size: 1rem;
    }
    
    /* Clean file list */
    .file-item {
        padding: 10px;
        margin: 5px 0;
        border: 1px solid #eee;
        border-radius: 6px;
        background: white;
    }
    
    /* Mobile responsive */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 0.5rem;
            padding-bottom: 0.5rem;
        }
        
        [data-testid="stSidebar"] {
            padding: 1rem !important;
        }
        
        [data-testid="stSidebar"] button {
            min-height: 44px !important;
            font-size: 1rem !important;
        }
        
        .size-info {
            padding: 8px;
            margin: 8px 0;
        }
    }
    
    /* Desktop sidebar fixed */
    @media (min-width: 769px) {
        [data-testid="stSidebar"] {
            position: fixed;
            height: 100vh;
            overflow-y: auto;
        }
    }
</style>
""", unsafe_allow_html=True)

# ========== HELPER FUNCTIONS ==========

def get_file_size(file_path):
    """Get file size in readable format"""
    try:
        size_bytes = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    except:
        return "0 B"

def get_file_size_bytes(file_path):
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0

def format_size(bytes_size):
    """Format bytes to human readable string"""
    try:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"
    except:
        return "0 B"

def merge_pdfs(file_list, output_path):
    """Merge multiple PDF files into one"""
    merger = PdfMerger()
    for file in file_list:
        merger.append(file)
    with open(output_path, 'wb') as output_file:
        merger.write(output_file)
    merger.close()
    return output_path

def compress_with_ghostscript(input_path, output_path, quality="Medium"):
    """Compress PDF using Ghostscript"""
    try:
        # Quality settings
        dpi_settings = {
            "Low": 300,
            "Medium": 200,
            "High": 150,
            "Maximum": 72
        }
        
        dpi = dpi_settings.get(quality, 200)
        
        gs_command = [
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/ebook",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-dDownsampleColorImages=true",
            f"-dDownsampleGrayImages=true",
            f"-dDownsampleMonoImages=true",
            f"-dColorImageResolution={dpi}",
            f"-dGrayImageResolution={dpi}",
            f"-dMonoImageResolution={dpi}",
            "-sOutputFile=" + output_path,
            input_path
        ]
        
        result = subprocess.run(gs_command, capture_output=True, text=True)
        return result.returncode == 0
        
    except:
        return False

# ========== SESSION STATE ==========

def reset_all():
    """Reset everything to initial state"""
    st.session_state.uploaded_files = []
    st.session_state.merged_pdf = None
    st.session_state.output_filename = f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    st.session_state.compression_stats = {}

# Initialize session state
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []
if 'merged_pdf' not in st.session_state:
    st.session_state.merged_pdf = None
if 'output_filename' not in st.session_state:
    st.session_state.output_filename = f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
if 'compression_stats' not in st.session_state:
    st.session_state.compression_stats = {}

# ========== MAIN APP ==========

def main():
    # Clean minimal header
    st.markdown('<h1 class="main-header">📄 PDF Merger</h1>', unsafe_allow_html=True)
    
    # Check for Ghostscript
    try:
        subprocess.run(["gs", "--version"], capture_output=True, text=True)
        gs_available = True
    except:
        gs_available = False
    
    # ========== CLEAN SIDEBAR ==========
    with st.sidebar:
        # Only compression button - no other text
        st.header("")
        
        # Compression toggle only
        compress = st.checkbox(
            "Compress PDF",
            value=True,
            help="Reduce file size"
        )
        
        # Quality selector - ALWAYS SHOW WHEN COMPRESSION IS ENABLED
        if compress:
            quality = st.selectbox(
                "Quality",
                ["Low", "Medium", "High", "Maximum"],
                index=1,
                help="Higher compression = smaller file"
            )
            
            # Show Ghostscript status only when compression is enabled
            if not gs_available:
                st.info("Note: Install Ghostscript for compression to work")
        
        # Add some spacing
        st.write("")
        st.write("")
        
        # Clear All button
        if st.button(
            "🗑️ Clear All",
            use_container_width=True,
            type="secondary",
            help="Remove all files and reset"
        ):
            reset_all()
            st.rerun()
    
    # ========== MAIN CONTENT ==========
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Upload section
        uploaded_files = st.file_uploader(
            "Upload PDFs",
            type=['pdf'],
            accept_multiple_files=True,
            help="Select PDF files to merge"
        )
        
        # Process uploaded files
        if uploaded_files:
            for uploaded_file in uploaded_files:
                # Skip duplicates
                existing_names = [f['name'] for f in st.session_state.uploaded_files]
                if uploaded_file.name in existing_names:
                    continue
                
                # Save file
                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                
                # Validate
                is_valid = True
                try:
                    reader = PdfReader(temp_path)
                    page_count = len(reader.pages)
                except:
                    is_valid = False
                    page_count = 0
                
                st.session_state.uploaded_files.append({
                    'name': uploaded_file.name,
                    'path': temp_path,
                    'size': uploaded_file.size,
                    'is_valid': is_valid,
                    'page_count': page_count
                })
        
        # Display files
        if st.session_state.uploaded_files:
            # File list header
            st.write(f"**Files ({len(st.session_state.uploaded_files)})**")
            
            # List files
            for i, file_info in enumerate(st.session_state.uploaded_files):
                col_f1, col_f2, col_f3 = st.columns([3, 2, 1])
                with col_f1:
                    st.write(file_info['name'])
                with col_f2:
                    st.write(get_file_size(file_info['path']))
                with col_f3:
                    if st.button("✕", key=f"del_{i}"):
                        st.session_state.uploaded_files.pop(i)
                        st.rerun()
            
            # Calculate total original size
            total_original_size = sum(f['size'] for f in st.session_state.uploaded_files if f['is_valid'])
            
            # Output filename - SIMPLE VERSION
            st.write("")
            st.write("**Output Name**")
            
            output_name = st.text_input(
                "",
                value=st.session_state.output_filename,
                key="filename_input",
                label_visibility="collapsed"
            )
            
            if output_name:
                if not output_name.lower().endswith('.pdf'):
                    output_name = output_name + ".pdf"
                st.session_state.output_filename = output_name
    
    with col2:
        # Merge section
        valid_files = [f for f in st.session_state.uploaded_files if f['is_valid']]
        valid_count = len(valid_files)
        
        if valid_count >= 2:
            # Calculate total original size
            total_original_size = sum(f['size'] for f in valid_files)
            
            # Status
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.metric("Files", valid_count)
            with col_s2:
                # Show compression status
                if compress:
                    st.metric("Quality", quality)
                else:
                    st.metric("Compress", "Off")
            
            # Show original size
            if total_original_size > 0:
                st.write("")
                st.write(f"**Original:** {format_size(total_original_size)}")
            
            # Merge button
            if st.button("Merge PDFs", type="primary", use_container_width=True):
                with st.spinner(""):
                    try:
                        # Prepare
                        temp_dir = tempfile.gettempdir()
                        output_path = os.path.join(temp_dir, st.session_state.output_filename)
                        valid_file_paths = [f['path'] for f in valid_files]
                        
                        # Store original size
                        original_size = total_original_size
                        
                        # Merge
                        merged_path = merge_pdfs(valid_file_paths, output_path)
                        
                        # Compress if requested and Ghostscript available
                        compressed_size = None
                        if compress and gs_available:
                            compressed_path = os.path.join(temp_dir, "compressed_" + st.session_state.output_filename)
                            if compress_with_ghostscript(merged_path, compressed_path, quality):
                                # Use compressed version
                                import shutil
                                shutil.copy2(compressed_path, output_path)
                                compressed_size = get_file_size_bytes(output_path)
                                try:
                                    os.remove(compressed_path)
                                except:
                                    pass
                        
                        # If no compression or compression failed, get final size
                        if compressed_size is None:
                            compressed_size = get_file_size_bytes(output_path)
                        
                        # Calculate reduction
                        reduction = 0
                        if original_size > 0 and compressed_size > 0:
                            reduction = ((original_size - compressed_size) / original_size) * 100
                        
                        # Store compression stats
                        st.session_state.compression_stats = {
                            'original_size': original_size,
                            'compressed_size': compressed_size,
                            'reduction': reduction,
                            'compressed': compress and gs_available
                        }
                        
                        # Store result
                        st.session_state.merged_pdf = output_path
                        st.success("")
                        
                    except Exception as e:
                        st.error("Error")
        
        elif valid_count == 1:
            st.write("Add more PDFs")
        elif st.session_state.uploaded_files:
            st.write("Check PDFs")
        else:
            st.write("Upload PDFs")
        
        # Download section with size display
        if st.session_state.merged_pdf and os.path.exists(st.session_state.merged_pdf):
            st.write("")
            st.write("**Download**")
            
            # Show size information
            if st.session_state.compression_stats:
                stats = st.session_state.compression_stats
                original_size = stats.get('original_size', 0)
                compressed_size = stats.get('compressed_size', 0)
                reduction = stats.get('reduction', 0)
                was_compressed = stats.get('compressed', False)
                
                if was_compressed and original_size > 0 and compressed_size > 0:
                    st.markdown(f"""
                    <div class="size-info">
                        <div class="size-original">Original: {format_size(original_size)}</div>
                        <div class="size-compressed">Compressed: {format_size(compressed_size)}</div>
                        <div class="size-reduction">Reduced by: {reduction:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                elif original_size > 0:
                    st.markdown(f"""
                    <div class="size-info">
                        <div class="size-compressed">Size: {format_size(original_size)}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            with open(st.session_state.merged_pdf, "rb") as f:
                st.download_button(
                    "Download",
                    data=f,
                    file_name=st.session_state.output_filename,
                    mime="application/pdf",
                    use_container_width=True
                )
            
            # Reset button
            if st.button("New Merge", use_container_width=True, type="secondary"):
                st.session_state.merged_pdf = None
                st.session_state.compression_stats = {}
                st.rerun()

if __name__ == "__main__":
    main()
