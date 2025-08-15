import os
from typing import Generator, Tuple

import gradio as gr
import requests
from gradio_pdf import PDF

# Configuration
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
PIPELINE_METHODS = ["Auto", "OCR"]
PIPELINE_METHOD_VALUES = ["auto", "ocr"]
VLM_METHODS = ["VLM Engine"]
VLM_METHOD_VALUES = ["vlm-sglang-engine"]


class MarkioFrontend:
    """Simplified MarkFlow frontend"""

    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 300
        self.pdf_engine = None
        self._init_pdf_engine()

    def _init_pdf_engine(self):
        """Initialize PDF parsing engine configuration from environment variables"""
        try:
            # Read PDF parsing engine configuration from environment variables
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
        self, file, parse_method: str, save_content: bool, lang: str = "ch"
    ) -> Tuple[str, str, str]:
        """Upload file and directly get conversion result"""
        if not file:
            return "Please select a file", "", ""

        if not self.check_api():
            return "API service unavailable", "", ""

        try:
            # Get parsing method value
            methods, values = self.get_parse_methods()
            method_idx = methods.index(parse_method) if parse_method in methods else 0
            method_value = values[method_idx]

            # Prepare file data - fix file reading issue
            with open(file.name, "rb") as f:
                file_content = f.read()

            files = {"file": (file.name, file_content, "application/octet-stream")}

            # Send parameters as query parameters instead of form data
            params = {"save_parsed_content": save_content}

            # If it's a PDF file, add parsing method parameter
            file_extension = (
                file.name.lower().split(".")[-1] if "." in file.name else ""
            )
            if file_extension == "pdf":
                params["parse_method"] = method_value
                params["lang"] = lang
            # Send request to unified file parsing endpoint
            response = self.session.post(
                f"{API_BASE_URL}/parse_file", files=files, params=params
            )
            response.raise_for_status()

            result = response.json()
            parsed_content = result.get("parsed_content", "")

            if parsed_content:
                # Return status, raw content and Markdown rendered content
                status = "✅ Conversion successful"
                raw_content = f"# 📄 {file.name} Conversion Result\n\n{parsed_content}"
                rendered_content = parsed_content  # Markdown rendered content
                return status, raw_content, rendered_content
            else:
                return "Conversion result is empty", "", ""

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                error_msg = f"Unsupported file format: {e.response.json().get('detail', 'Unknown error')}"
                return error_msg, "", ""
            else:
                error_msg = f"Server error: {e.response.status_code}"
                return error_msg, "", ""
        except Exception as e:
            error_msg = f"Conversion failed: {str(e)}"
            return error_msg, "", ""

    # 让返回值与 upload_file 一致，方便UI同步更新
    def parse_url(self, url: str, save_content: bool = False) -> Tuple[str, str, str]:
        """Parse URL"""
        if not url:
            return "Please enter URL", "", ""

        if not self.check_api():
            return "API service unavailable", "", ""

        try:
            # Use query parameters, including save_parsed_content
            params = {"url": url, "save_parsed_content": str(save_content).lower()}
            response = self.session.post(f"{API_BASE_URL}/parse_url", params=params)
            response.raise_for_status()

            result = response.json()
            content = result.get("parsed_content", "")

            if content:
                status = "✅ URL parsing successful"
                formatted_content = f"# 🌐 {url}\n\n{content}"
                return status, formatted_content, formatted_content
            else:
                return "Parsing result is empty", "", ""

        except Exception as e:
            error_msg = f"Parsing failed: {str(e)}"
            return error_msg, "", ""



def create_simple_interface():
    """Create simplified interface"""
    app = MarkioFrontend()

    with gr.Blocks(
        title="Markio - Intelligent Document Conversion",
    ) as demo:
        # Use a more modern header
        gr.Markdown("""
        <div style="text-align: center; padding: 20px 0; background: linear-gradient(90deg, #536DFE, #42A5F5); color: white; border-radius: 12px; margin: 0 0 20px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <h1 style="margin: 0; font-size: 2.8em; font-weight: 700;">✨ Markio</h1>
            <p style="margin: 10px 0 0; font-size: 1.3em; opacity: 0.9;">Intelligent Document & Web Content Conversion</p>
        </div>
        """)
        with gr.Row():
            with gr.Column(variant="panel", scale=5):
                with gr.Tabs():
                    # File upload
                    with gr.Tab("📄File Parsing"):
                        file_input = gr.File(
                            label="Please upload a file",
                            file_types=SUPPORTED_FORMATS,
                            file_count="single",
                        )

                        with gr.Row():
                            # Dynamic parsing method selection
                            methods, values = app.get_parse_methods()

                            parse_method = gr.Dropdown(
                                choices=methods,
                                value=methods[0] if methods else "Auto Select",
                                label="Parsing Method",
                                info="PDF files will choose parsing engine based on environment variable",
                                visible=app.pdf_engine == "pipeline",
                                scale=2,
                            )

                            lang_choices = [
                                ("ch", "简体中文 (ch)"),
                                ("ch_server", "中文手写 (ch_server)"),
                                ("chinese_cht", "繁体中文 (chinese_cht)"),
                                ("en", "英文 (en)"),
                                ("korean", "韩文 (korean)"),
                                ("japan", "日文 (japan)"),
                                ("ta", "泰米尔文 (ta)"),
                                ("te", "泰卢固文 (te)"),
                                ("ka", "格鲁吉亚文 (ka)"),
                            ]

                            lang_dropdown = gr.Dropdown(
                                choices=[(x[1], x[0]) for x in lang_choices],
                                value="ch",
                                label="Language",
                                info="Select the language for parsing (Only PDF format supports)",
                                visible=app.pdf_engine == "pipeline",
                                scale=2,
                            )

                            save_content = gr.Checkbox(
                                label="Save content",
                                value=False,
                                scale=1,
                            )

                        gr.Markdown("")  # Add a little vertical space

                        with gr.Row():
                            upload_btn = gr.Button(
                                "🚀 Start Conversion", variant="primary", scale=2
                            )
                            clear_btn = gr.ClearButton(value="Clear", scale=1)

                        upload_status = gr.Textbox(
                            label="Conversion Status",
                            lines=1,
                            interactive=False,
                        )

                        gr.Markdown("")  # Add a little vertical space

                        # PDF preview component
                        pdf_preview = PDF(
                            label="PDF Preview",
                            interactive=False,
                            visible=True,
                            height=600,
                        )

                    # URL parsing
                    with gr.Tab("🌐 URL Parsing"):
                        with gr.Row():
                            url_input = gr.Textbox(
                                label="Web URL",
                                placeholder="https://example.com",
                                scale=5,  # Give more space to the input field
                            )
                            url_save_content = gr.Checkbox(
                                label="Save content",
                                value=False,
                                scale=1,
                            )
                            url_btn = gr.Button("🌐 Parse", variant="primary", scale=1)

            with gr.Column(variant="panel", scale=5):
                with gr.Tabs():
                    with gr.Tab("Markdown rendering"):
                        rendered_result = gr.Markdown(
                            label="Markdown rendering",
                            show_copy_button=True,
                            line_breaks=True,
                        )
                    with gr.Tab("Markdown text"):
                        raw_result = gr.TextArea(
                            lines=45, show_copy_button=True, label="Raw Content"
                        )

        # Help section
        with gr.Accordion("❓ Help", open=False):
            gr.Markdown("""
            ## 📖 Usage Instructions
            
            **File Conversion**:
            1. Select file to convert
            2. Select parsing method
            3. Select whether to save parsed content to file
            4. Click Start Conversion
            5. Wait for conversion to complete, result will be displayed directly
            
            **URL Parsing**:
            1. Enter web URL to parse
            2. Select whether to save parsed content to file
            3. Click Parse button
            4. Wait for parsing to complete
            
            **Parsing Method Description**:
            - **Pipeline Engine** (PDF_PARSE_ENGINE=pipeline):
                - Auto Select: Automatically choose best parsing method based on file content
                - OCR Engine: Use Optical Character Recognition to process image content
                - Text Extraction: Directly extract text content
            - **VLM Engine** (PDF_PARSE_ENGINE=vlm-sglang-engine):
                - VLM Engine: Use Visual Language Model for parsing
            
            **Supported Formats**:
            - **Documents**: PDF, Word (.doc, .docx), PowerPoint (.ppt, .pptx), Excel (.xlsx), HTML, EPUB
            - **Images**: PNG, JPEG (.jpg, .jpeg), WebP, GIF, BMP, TIFF (.tiff, .tif), SVG, ICO, HEIC (.heic, .heif), AVIF
            
            **Features**:
            - 🚀 Sync Processing, No Wait for Task Completion
            - 📄 Double Row Display: Left shows raw content, right shows Markdown Rendered
            - 🎯 Auto Recognize File Type and Choose Best Parser
            - 💾 Choose to Save Parsed Content to File (Supports File and URL Parsing)
            - ⚙️ Support Multiple PDF Parsing Engine Configurations
            - 📋 Support Copy Raw Content
            
            **API Documentation**: http://localhost:9086/docs
            """)

        # Event handlers

        def handle_upload(file, method, save, lang) -> Generator:
            if not file:
                yield {upload_status: gr.update(value="请先选择一个文件")}
                return

            # 1. 更新UI为加载状态
            yield {
                upload_btn: gr.update(value="🚀 转换中...", interactive=False),
                upload_status: gr.update(value="正在处理，请稍候..."),
            }
            # 2. 调用后端函数
            status, raw, rendered = app.upload_file(file, method, save, lang)
            # 3. 更新UI为结果状态
            yield {
                upload_btn: gr.update(value="🚀 开始转换", interactive=True),
                upload_status: gr.update(value=status),
                raw_result: gr.update(value=raw),
                rendered_result: gr.update(value=rendered),
            }

        def handle_url_parse(url, save) -> Generator:
            if not url:
                yield {upload_status: gr.update(value="请输入URL")}
                return

            # 1. 更新UI为加载状态
            yield {
                url_btn: gr.update(value="🌐 解析中...", interactive=False),
                upload_status: gr.update(value="正在解析URL，请稍候..."),
                raw_result: gr.update(value=""),  # 清空上一次的结果
                rendered_result: gr.update(value=""),
            }
            # 2. 调用后端函数
            status, raw, rendered = app.parse_url(url, save)
            # 3. 更新UI为结果状态
            yield {
                url_btn: gr.update(value="🌐 解析", interactive=True),
                upload_status: gr.update(value=status),
                raw_result: gr.update(value=raw),
                rendered_result: gr.update(value=rendered),
            }

        # Update PDF preview when file is uploaded
        file_input.change(
            fn=lambda x: x,
            inputs=[file_input],
            outputs=[pdf_preview],
        )

        upload_btn.click(
            fn=handle_upload,
            inputs=[file_input, parse_method, save_content, lang_dropdown],
            outputs=[upload_btn, upload_status, raw_result, rendered_result],
        )

        url_btn.click(
            fn=handle_url_parse,
            inputs=[url_input, url_save_content],
            outputs=[url_btn, upload_status, raw_result, rendered_result],
        )

        clear_btn.add(
            [
                file_input,
                url_input,
                raw_result,
                rendered_result,
                upload_status,
                pdf_preview,
            ]
        )

    return demo


def main():
    demo = create_simple_interface()
    demo.launch(server_name="0.0.0.0", server_port=7861, share=False, show_error=True)


if __name__ == "__main__":
    main()
