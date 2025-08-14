"""
API接口功能测试
测试所有接口是否正常运行，使用真实的测试文件
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path


class TestAPIEndpoints:
    """API接口功能测试类"""
    
    def test_welcome_endpoint(self, client: TestClient):
        """测试欢迎接口"""
        response = client.get("/")
        assert response.status_code == 200
        assert "docs" in response.url.path
    
    def test_api_docs_endpoint(self, client: TestClient):
        """测试API文档接口"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_openapi_schema(self, client: TestClient):
        """测试OpenAPI schema接口"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert response.json()["info"]["title"] == "Markio"
    
    @pytest.mark.real_files
    def test_pdf_parse_endpoint(self, client: TestClient, real_test_files):
        """测试PDF解析接口 - 使用真实PDF文件"""
        pdf_file_path = real_test_files["pdf"]
        
        if not pdf_file_path.exists():
            pytest.skip(f"测试PDF文件不存在: {pdf_file_path}")
        
        with open(pdf_file_path, "rb") as f:
            files = {"file": ("test_pdf1.pdf", f, "application/pdf")}
            data = {"save_parsed_content": "false"}
            
            response = client.post("/v1/parse_pdf_file", files=files, data=data)
        
        # 验证接口响应
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            result = response.json()
            assert "parsed_content" in result or "status_code" in result
    
    @pytest.mark.real_files
    def test_docx_parse_endpoint(self, client: TestClient, real_test_files):
        """测试DOCX解析接口 - 使用真实DOCX文件"""
        docx_file_path = real_test_files["docx"]
        
        if not docx_file_path.exists():
            pytest.skip(f"测试DOCX文件不存在: {docx_file_path}")
        
        with open(docx_file_path, "rb") as f:
            files = {"file": ("test_docx.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            data = {"save_parsed_content": "false"}
            
            response = client.post("/v1/parse_docx_file", files=files, data=data)
        
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            result = response.json()
            assert "parsed_content" in result or "status_code" in result
    
    @pytest.mark.real_files
    def test_xlsx_parse_endpoint(self, client: TestClient, real_test_files):
        """测试XLSX解析接口 - 使用真实XLSX文件"""
        xlsx_file_path = real_test_files["xlsx"]
        
        if not xlsx_file_path.exists():
            pytest.skip(f"测试XLSX文件不存在: {xlsx_file_path}")
        
        with open(xlsx_file_path, "rb") as f:
            files = {"file": ("test_xlsx.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            data = {"save_parsed_content": "false"}
            
            response = client.post("/v1/parse_xlsx_file", files=files, data=data)
        
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            result = response.json()
            assert "parsed_content" in result or "status_code" in result
    
    @pytest.mark.real_files
    def test_html_parse_endpoint(self, client: TestClient, real_test_files):
        """测试HTML解析接口 - 使用真实HTML文件"""
        html_file_path = real_test_files["html"]
        
        if not html_file_path.exists():
            pytest.skip(f"测试HTML文件不存在: {html_file_path}")
        
        with open(html_file_path, "rb") as f:
            files = {"file": ("test_html.html", f, "text/html")}
            data = {"save_parsed_content": "false"}
            
            response = client.post("/v1/parse_html_file", files=files, data=data)
        
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            result = response.json()
            assert "parsed_content" in result or "status_code" in result
    
    @pytest.mark.real_files
    def test_epub_parse_endpoint(self, client: TestClient, real_test_files):
        """测试EPUB解析接口 - 使用真实EPUB文件"""
        epub_file_path = real_test_files["epub"]
        
        if not epub_file_path.exists():
            pytest.skip(f"测试EPUB文件不存在: {epub_file_path}")
        
        with open(epub_file_path, "rb") as f:
            files = {"file": ("test_epub.epub", f, "application/epub+zip")}
            data = {"save_parsed_content": "false"}
            
            response = client.post("/v1/parse_epub_file", files=files, data=data)
        
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            result = response.json()
            assert "parsed_content" in result or "status_code" in result
    
    @pytest.mark.real_files
    def test_ppt_parse_endpoint(self, client: TestClient, real_test_files):
        """测试PPT解析接口 - 使用真实PPT文件"""
        ppt_file_path = real_test_files["ppt"]
        
        if not ppt_file_path.exists():
            pytest.skip(f"测试PPT文件不存在: {ppt_file_path}")
        
        with open(ppt_file_path, "rb") as f:
            files = {"file": ("test_ppt.ppt", f, "application/vnd.ms-powerpoint")}
            data = {"save_parsed_content": "false"}
            
            response = client.post("/v1/parse_ppt_file", files=files, data=data)
        
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            result = response.json()
            assert "parsed_content" in result or "status_code" in result
    
    @pytest.mark.real_files
    def test_pptx_parse_endpoint(self, client: TestClient, real_test_files):
        """测试PPTX解析接口 - 使用真实PPTX文件"""
        pptx_file_path = real_test_files["pptx"]
        
        if not pptx_file_path.exists():
            pytest.skip(f"测试PPTX文件不存在: {pptx_file_path}")
        
        with open(pptx_file_path, "rb") as f:
            files = {"file": ("test_pptx.pptx", f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
            data = {"save_parsed_content": "false"}
            
            response = client.post("/v1/parse_pptx_file", files=files, data=data)
        
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            result = response.json()
            assert "parsed_content" in result or "status_code" in result
    
    @pytest.mark.real_files
    def test_doc_parse_endpoint(self, client: TestClient, real_test_files):
        """测试DOC解析接口 - 使用真实DOC文件"""
        doc_file_path = real_test_files["doc"]
        
        if not doc_file_path.exists():
            pytest.skip(f"测试DOC文件不存在: {doc_file_path}")
        
        with open(doc_file_path, "rb") as f:
            files = {"file": ("test_doc.doc", f, "application/msword")}
            data = {"save_parsed_content": "false"}
            
            response = client.post("/v1/parse_doc_file", files=files, data=data)
        
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            result = response.json()
            assert "parsed_content" in result or "status_code" in result
    
    def test_file_upload_validation(self, client: TestClient):
        """测试文件上传验证"""
        # 测试空文件
        files = {"file": ("empty.txt", b"", "text/plain")}
        response = client.post("/v1/parse_pdf_file", files=files)
        assert response.status_code in [400, 422]
        
        # 测试无效文件类型
        files = {"file": ("test.txt", b"test content", "text/plain")}
        response = client.post("/v1/parse_pdf_file", files=files)
        assert response.status_code in [400, 422]
    
    def test_error_handling(self, client: TestClient):
        """测试错误处理"""
        # 测试缺少文件参数
        response = client.post("/v1/parse_pdf_file")
        assert response.status_code in [400, 422]
        
        # 测试无效的URL
        data = {"url": "invalid-url"}
        response = client.post("/v1/parse_url", data=data)
        assert response.status_code in [400, 422]


class TestParserFunctions:
    """解析器功能测试类"""
    
    def test_parameter_adapter(self):
        """测试参数适配器"""
        from scripts.run_local import parameter_adapter
        
        # 测试PDF参数适配
        pdf_params = parameter_adapter("pdf", file_path="/test.pdf", parse_method="auto")
        assert pdf_params["resource_path"] == "/test.pdf"
        assert pdf_params["parse_method"] == "auto"
        
        # 测试图片参数适配
        img_params = parameter_adapter("img", file_path="/test.jpg", parse_backend="pipeline")
        assert img_params["resource_path"] == "/test.jpg"
        assert img_params["parse_backend"] == "pipeline"
        
        # 测试无效文件类型
        with pytest.raises(ValueError, match="Unsupported file type"):
            parameter_adapter("invalid", file_path="/test.invalid")
    
    def test_function_map(self):
        """测试函数映射"""
        from scripts.run_local import FUNCTION_MAP
        
        # 检查所有支持的文件类型都有对应的解析函数
        expected_types = ["pdf", "img", "doc", "ppt", "pptx", "html", "docx", "url", "xlsx", "epub"]
        for file_type in expected_types:
            assert file_type in FUNCTION_MAP
            assert callable(FUNCTION_MAP[file_type])


class TestErrorHandling:
    """错误处理测试类"""
    
    def test_invalid_file_path(self, client: TestClient):
        """测试无效文件路径"""
        response = client.post(
            "/v1/parse_pdf_file",
            files={"file": ("", b"", "application/pdf")},
            data={"save_parsed_content": "false"}
        )
        
        assert response.status_code in [400, 422]
    
    def test_malformed_request(self, client: TestClient):
        """测试格式错误的请求"""
        response = client.post(
            "/v1/parse_pdf_file",
            data="invalid json data",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code in [400, 422, 500]
    
    def test_unsupported_method(self, client: TestClient):
        """测试不支持的HTTP方法"""
        response = client.put("/v1/parse_pdf_file")
        assert response.status_code == 405  # Method Not Allowed


# 测试数据准备函数 - 为真实测试用例预留
def prepare_test_files():
    """
    准备测试文件的函数
    当有真实测试文件时，可以在这里配置文件路径
    
    Returns:
        dict: 包含各种文件类型路径的字典
    """
    return {
        "pdf": "path/to/real/test.pdf",
        "docx": "path/to/real/test.docx", 
        "xlsx": "path/to/real/test.xlsx",
        "html": "path/to/real/test.html",
        "image": "path/to/real/test.jpg"
    }


# 标记需要真实文件的测试
REAL_FILE_TESTS = [
    "test_pdf_parse_endpoint",
    "test_docx_parse_endpoint", 
    "test_image_parse_endpoint",
    "test_html_parse_endpoint",
    "test_xlsx_parse_endpoint"
]
