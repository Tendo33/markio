import os
from typing import Generator, Tuple

import gradio as gr
import requests
from gradio.exceptions import Error as gr_Error
from gradio_pdf import PDF

# Configuration
BASE_URL = "http://0.0.0.0:8000"
API_BASE_URL = f"{BASE_URL}/v1"
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
VLM_METHODS = ["VLM Engine (vLLM)"]
VLM_METHODS_VALUES = ["vlm-vllm-engine"]


class MarkioFrontend:
    """Simplified MarkFlow frontend"""

    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 300
        self.api_token = (os.getenv("MARKIO_API_TOKEN", "") or "").strip()
        if self.api_token:
            self.session.headers.update(
                {"Authorization": f"Bearer {self.api_token}"}
            )
        self.pdf_engine = None
        self._init_pdf_engine()

    def _init_pdf_engine(self):
        """Initialize PDF parsing engine configuration from environment variables"""
        try:
            self.pdf_engine = os.getenv("PDF_PARSE_ENGINE", "pipeline")
            print(f"📋 PDF parsing engine configuration: {self.pdf_engine}")
        except Exception as e:
            print(f"⚠️ Failed to read PDF parsing engine configuration: {e}")
            self.pdf_engine = "pipeline"

    def get_parse_methods(self):
        """Get currently available parsing methods"""
        if self.pdf_engine in ["vlm-vllm-engine", "vlm-vllm-client"]:
            return VLM_METHODS, VLM_METHODS_VALUES
        else:
            return PIPELINE_METHODS, PIPELINE_METHOD_VALUES

    def check_api(self) -> bool:
        """Check if API is available"""
        try:
            response = self.session.get(f"{BASE_URL}/docs", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def upload_file(
        self, file, parse_method: str, save_content: bool, lang: str = "ch"
    ) -> Tuple[str, str, str]:
        """Upload file and directly get conversion result"""
        if not file:
            raise ValueError("❌ Please select a file first")

        if not self.check_api():
            raise ConnectionError(
                "❌ API service is unavailable. Please check if the backend is running."
            )

        try:
            # Get parsing method value
            methods, values = self.get_parse_methods()
            method_idx = methods.index(parse_method) if parse_method in methods else 0
            method_value = values[method_idx]

            # Prepare file data - fix file reading issue
            with open(file.name, "rb") as f:
                file_content = f.read()

            files = {
                "file": (
                    os.path.basename(file.name),
                    file_content,
                    "application/octet-stream",
                )
            }

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
                raw_content = f"# 📄 {os.path.basename(file.name)} Conversion Result\n\n{parsed_content}"
                rendered_content = parsed_content
                return status, raw_content, rendered_content
            else:
                raise ValueError(
                    "❌ Conversion result is empty. Please check the file content or parsing method."
                )

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                detail = e.response.json().get("detail", "Unknown error")
                raise TypeError(
                    f"❌ Unsupported file format or invalid request: {detail}"
                )
            else:
                raise ConnectionError(
                    f"❌ Server error: {e.response.status_code} - {e.response.text}"
                )
        except Exception as e:
            # Re-throw a more generic exception for the frontend to catch
            raise RuntimeError(f"❌ Conversion failed: {str(e)}")

    def parse_url(self, url: str, save_content: bool = False) -> Tuple[str, str, str]:
        """Parse URL"""
        if not url:
            raise ValueError("❌ Please enter a valid URL")

        if not self.check_api():
            raise ConnectionError(
                "❌ API service is unavailable. Please check if the backend is running."
            )

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
                raise ValueError("❌ Parsing result is empty")

        except Exception as e:
            # Re-throw a more generic exception for the frontend to catch
            raise RuntimeError(f"❌ URL parsing failed: {str(e)}")


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
                    with gr.Tab("📄 File Parsing"):
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
                            # Language selection for OCR
                            lang_choices = [
                                ("简体中文 (ch)", "ch"),
                                ("中文手写 (ch_server)", "ch_server"),
                                ("繁体中文 (chinese_cht)", "chinese_cht"),
                                ("英文 (en)", "en"),
                                ("韩文 (korean)", "korean"),
                                ("日文 (japan)", "japan"),
                                ("泰米尔文 (ta)", "ta"),
                                ("泰卢固文 (te)", "te"),
                                ("格鲁吉亚文 (ka)", "ka"),
                            ]
                            lang_dropdown = gr.Dropdown(
                                choices=[(x[0], x[1]) for x in lang_choices],
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

                        gr.Markdown("")
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

                        gr.Markdown("")
                        # PDF preview component
                        pdf_preview = PDF(
                            label="PDF Preview",
                            interactive=False,
                            visible=True,
                            height=600,
                        )

                    # URL parsing
                    with gr.Tab("🌐 URL Parsing"):
                        # 第一行：URL输入框和保存内容复选框
                        with gr.Row():
                            url_input = gr.Textbox(
                                label="Web URL",
                                placeholder="https://example.com",
                                scale=5,
                            )
                            url_save_content = gr.Checkbox(
                                label="Save content",
                                value=False,
                                scale=1,
                            )
                        # 第二行：Parse按钮和Clear按钮
                        with gr.Row():
                            url_btn = gr.Button("🌐 Parse", variant="primary", scale=2)
                            url_clear_btn = gr.ClearButton(value="Clear", scale=1)
                        # 独立状态栏
                        url_status = gr.Textbox(
                            label="Parsing Status",
                            lines=1,
                            interactive=False,
                        )

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
            2. Select parsing method and language as needed
            3. Check whether to save parsed content to a file
            4. Click "Start Conversion"
            5. Wait for conversion to complete, the result will be displayed directly
            
            **URL Parsing**:
            1. Enter the web URL to parse
            2. Check whether to save parsed content to a file
            3. Click the "Parse" button
            4. Wait for parsing to complete
            
            **Parsing Method Description**:
            - **Pipeline Engine** (PDF_PARSE_ENGINE=pipeline):
                - **Auto Select**: Automatically choose the best parsing method.
                - **OCR Engine**: Use Optical Character Recognition to process images or scanned documents.
            - **VLM Engine** (PDF_PARSE_ENGINE=vlm-vllm-engine):
                - **VLM Engine**: Use a Visual Language Model (vLLM) for parsing.
            
            **Supported Formats**:
            - **Documents**: PDF, Word (.doc, .docx), PowerPoint (.ppt, .pptx), Excel (.xlsx), HTML, EPUB
            - **Images**: PNG, JPEG, WebP, GIF, BMP, TIFF, SVG, ICO, HEIC, AVIF
            
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
            # 1. Update UI to loading state
            yield {
                upload_btn: gr.update(value="🚀 Converting...", interactive=False),
                upload_status: gr.update(value="Processing, please wait..."),
                raw_result: gr.update(value=""),
                rendered_result: gr.update(value=""),
            }
            try:
                # 2. Call the backend function
                status, raw, rendered = app.upload_file(file, method, save, lang)
                # 3. If successful, update UI with the results
                yield {
                    upload_btn: gr.update(
                        value="🚀 Start Conversion", interactive=True
                    ),
                    upload_status: gr.update(value=status),
                    raw_result: gr.update(value=raw),
                    rendered_result: gr.update(value=rendered),
                }
            except Exception as e:
                # 4. If any exception is caught
                # First, reset the UI to its initial state
                yield {
                    upload_btn: gr.update(
                        value="🚀 Start Conversion", interactive=True
                    ),
                    upload_status: gr.update(value=""),  # Clear the status box
                }
                # Then, raise a gr.Error to show a prominent notification
                raise gr_Error(str(e))

        def handle_url_parse(url, save) -> Generator:
            # 1. Update UI to loading state
            yield {
                url_btn: gr.update(value="🌐 Parsing...", interactive=False),
                url_status: gr.update(value="Parsing URL, please wait..."),
                upload_status: gr.update(value=""),
                raw_result: gr.update(value=""),
                rendered_result: gr.update(value=""),
            }
            try:
                # 2. Call the backend function
                status, raw, rendered = app.parse_url(url, save)
                # 3. If successful, update UI with the results
                yield {
                    url_btn: gr.update(value="🌐 Parse", interactive=True),
                    url_status: gr.update(value=status),
                    upload_status: gr.update(value=""),
                    raw_result: gr.update(value=raw),
                    rendered_result: gr.update(value=rendered),
                }
            except Exception as e:
                # 4. If any exception is caught
                # First, reset the UI to its initial state
                yield {
                    url_btn: gr.update(value="🌐 Parse", interactive=True),
                    url_status: gr.update(value=""),  # Clear the status box
                }
                # Then, raise a gr.Error to show a prominent notification
                raise gr_Error(str(e))

        def update_pdf_preview(file):
            """Only show PDF preview when a PDF file is uploaded"""
            if file and os.path.splitext(file.name.lower())[1] == ".pdf":
                return gr.update(value=file.name)
            else:
                return gr.update(value=None)

        # Event handlers
        file_input.change(
            fn=update_pdf_preview,
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
            outputs=[url_btn, url_status, upload_status, raw_result, rendered_result],
        )
        url_clear_btn.add(
            [
                url_input,
                url_status,
                raw_result,
                rendered_result,
            ]
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
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)


if __name__ == "__main__":
    main()
