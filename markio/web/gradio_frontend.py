import os
from typing import Tuple

import gradio as gr
import requests

# API configuration
API_BASE_URL = "http://0.0.0.0:8000/v1"
SUPPORTED_FORMATS = [
    ".pdf",
    ".docx",
    ".doc",
    ".pptx",
    ".ppt",
    ".xlsx",
    ".html",
    ".epub",
    # Image formats
    ".jpg",
    ".jpeg",
    ".png",
]

# Parser method configuration
PIPELINE_METHODS = ["Auto Select", "OCR Engine", "Text Extraction"]
PIPELINE_METHOD_VALUES = ["auto", "ocr", "txt"]
VLM_METHODS = ["VLM Engine"]
VLM_METHOD_VALUES = ["vlm-sglang-engine"]


class SimpleMarkio:
    """Simplified Markio frontend interface"""

    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 300
        self.pdf_engine = None
        self._init_pdf_engine()

    def _init_pdf_engine(self):
        """Initialize PDF parsing engine from environment variables"""
        try:
            self.pdf_engine = os.getenv("PDF_PARSE_ENGINE", "pipeline")
            print(f"📋 PDF parsing engine configuration: {self.pdf_engine}")
        except Exception as e:
            print(f"⚠️ Failed to read PDF parsing engine configuration: {e}")
            self.pdf_engine = "pipeline"  # Default to pipeline

    def get_parse_methods(self):
        """Get currently available parsing methods"""
        if self.pdf_engine == "vlm-sglang-engine":
            return VLM_METHODS, VLM_METHOD_VALUES
        else:
            return PIPELINE_METHODS, PIPELINE_METHOD_VALUES

    def check_api(self) -> bool:
        """Check if API is available"""
        try:
            response = self.session.get(
                f"{API_BASE_URL.replace('/v1', '')}/docs", timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    def upload_file(
        self, file, parse_method: str, save_content: bool
    ) -> Tuple[str, str, str]:
        """Upload file and get conversion result"""
        if not file:
            return "Please select a file", "", ""

        if not self.check_api():
            return "API service unavailable", "", ""

        try:
            methods, values = self.get_parse_methods()
            method_idx = methods.index(parse_method) if parse_method in methods else 0
            method_value = values[method_idx]

            with open(file.name, "rb") as f:
                file_content = f.read()

            files = {"file": (file.name, file_content, "application/octet-stream")}

            params = {"save_parsed_content": save_content}

            if file.name.lower().endswith(".pdf"):
                params["parse_method"] = method_value

            response = self.session.post(
                f"{API_BASE_URL}/file/parse",
                files=files,
                params=params,
                timeout=300,
            )

            if response.status_code == 200:
                parsed_content = response.json().get("content", "")
                raw_content = f"# 📄 {file.name} Conversion Result\n\n{parsed_content}"
                rendered_content = parsed_content
                return "Conversion successful", raw_content, rendered_content
            else:
                return f"Conversion failed: {response.text}", "", ""

        except Exception as e:
            return f"Error during conversion: {str(e)}", "", ""

    def parse_url(self, url: str, save_content: bool) -> str:
        """Parse URL content and convert to markdown"""
        if not url:
            return "Please enter a URL"

        if not self.check_api():
            return "API service unavailable"

        try:
            params = {"save_parsed_content": save_content}
            response = self.session.post(
                f"{API_BASE_URL}/url/parse",
                json={"url": url},
                params=params,
                timeout=300,
            )

            if response.status_code == 200:
                content = response.json().get("content", "")
                return f"# 🌐 {url}\n\n{content}"
            else:
                return f"URL parsing failed: {response.text}"

        except Exception as e:
            return f"Error during URL parsing: {str(e)}"

    def create_interface(self):
        """Create Gradio interface"""
        with gr.Blocks(
            title="Markio - Document to Markdown Converter",
            theme=gr.themes.Soft(),
        ) as interface:
            gr.HTML(
                """
                <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin-bottom: 20px;">
                    <h1>🚀 Markio</h1>
                    <p>Convert documents to Markdown format with ease</p>
                </div>
                """
            )

            with gr.Tab("File Upload"):
                with gr.Row():
                    with gr.Column():
                        file_input = gr.File(
                            label="Upload Document",
                            file_types=SUPPORTED_FORMATS,
                        )

                        parse_method = gr.Dropdown(
                            choices=self.get_parse_methods()[0],
                            value="Auto Select",
                            label="Parsing Method",
                        )

                        save_content = gr.Checkbox(
                            label="Save Parsed Content",
                            value=False,
                        )

                        upload_btn = gr.Button("Convert", variant="primary")

                    with gr.Column():
                        output_text = gr.Markdown(label="Conversion Result")

                upload_btn.click(
                    self.upload_file,
                    inputs=[file_input, parse_method, save_content],
                    outputs=[output_text, output_text, output_text],
                )

            with gr.Tab("URL Parsing"):
                with gr.Row():
                    with gr.Column():
                        url_input = gr.Textbox(
                            label="Enter URL",
                            placeholder="https://example.com",
                        )

                        url_save_content = gr.Checkbox(
                            label="Save Parsed Content",
                            value=False,
                        )

                        url_btn = gr.Button("Parse URL", variant="primary")

                    with gr.Column():
                        url_output = gr.Markdown(label="Parsed Content")

                url_btn.click(
                    self.parse_url,
                    inputs=[url_input, url_save_content],
                    outputs=url_output,
                )

            with gr.Tab("Help"):
                gr.Markdown(
                    """
                    ## 📖 Usage Instructions

                    ### File Upload
                    1. Select a document file (PDF, DOCX, HTML, etc.)
                    2. Choose parsing method (Auto Select recommended)
                    3. Check "Save Parsed Content" if you want to save results
                    4. Click "Convert" to process

                    ### URL Parsing
                    1. Enter a valid URL
                    2. Choose whether to save content
                    3. Click "Parse URL" to extract content

                    ### Supported Formats
                    - **Documents**: PDF, DOCX, DOC, PPTX, PPT, XLSX
                    - **Web**: HTML, URLs
                    - **E-books**: EPUB
                    - **Images**: JPG, PNG, JPEG

                    ### Parsing Methods
                    - **Auto Select**: Automatically choose best method
                    - **OCR Engine**: Force OCR processing
                    - **Text Extraction**: Extract text directly
                    """
                )

        return interface


def main():
    """Main application entry point"""
    markio = SimpleMarkio()
    interface = markio.create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )


if __name__ == "__main__":
    main()
