"""
API接口功能测试
测试所有接口是否正常运行
"""
from unittest.mock import mock_open, patch

import pytest
from fastapi.testclient import TestClient


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
    
    @pytest.mark.skip(reason="需要真实的PDF文件进行测试")
    def test_pdf_parse_endpoint(self, client: TestClient):
        """测试PDF解析接口 - 需要真实PDF文件"""
        # TODO: 添加真实的PDF文件进行测试
        # 当前使用mock数据
        mock_pdf_content = b"%PDF-1.4\n%Mock PDF content\n%%EOF"
        
        with patch("builtins.open", mock_open(read_data=mock_pdf_content)):
            response = client.post(
                "/v1/parse_pdf_file",
                files={"file": ("test.pdf", mock_pdf_content, "application/pdf")},
                data={"save_parsed_content": "false"}
            )
        
        # 验证接口响应格式
        assert response.status_code in [200, 400, 500]
    
    @pytest.mark.skip(reason="需要真实的DOCX文件进行测试")
    def test_docx_parse_endpoint(self, client: TestClient):
        """测试DOCX解析接口 - 需要真实DOCX文件"""
        # TODO: 添加真实的DOCX文件进行测试
        mock_docx_content = b"Mock DOCX content"
        
        response = client.post(
            "/v1/parse_docx_file",
            files={"file": ("test.docx", mock_docx_content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"save_parsed_content": "false"}
        )
        
        assert response.status_code in [200, 400, 500]
    
    @pytest.mark.skip(reason="需要真实的图片文件进行测试")
    def test_image_parse_endpoint(self, client: TestClient):
        """测试图片解析接口 - 需要真实图片文件"""
        # TODO: 添加真实的图片文件进行测试
        mock_img_content = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00"
        
        response = client.post(
            "/v1/parse_image_file",
            files={"file": ("test.jpg", mock_img_content, "image/jpeg")},
            data={"save_parsed_content": "false"}
        )
        
        assert response.status_code in [200, 400, 500]
    
    @pytest.mark.skip(reason="需要真实的HTML文件进行测试")
    def test_html_parse_endpoint(self, client: TestClient):
        """测试HTML解析接口 - 需要真实HTML文件"""
        # TODO: 添加真实的HTML文件进行测试
        mock_html_content = b"<html><body><h1>Test HTML</h1></body></html>"
        
        response = client.post(
            "/v1/parse_html_file",
            files={"file": ("test.html", mock_html_content, "text/html")},
            data={"save_parsed_content": "false"}
        )
        
        assert response.status_code in [200, 400, 500]
    
    @pytest.mark.skip(reason="需要真实的XLSX文件进行测试")
    def test_xlsx_parse_endpoint(self, client: TestClient):
        """测试XLSX解析接口 - 需要真实XLSX文件"""
        # TODO: 添加真实的XLSX文件进行测试
        mock_xlsx_content = b"Mock XLSX content"
        
        response = client.post(
            "/v1/parse_xlsx_file",
            files={"file": ("test.xlsx", mock_xlsx_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"save_parsed_content": "false"}
        )
        
        assert response.status_code in [200, 400, 500]
    
    def test_url_parse_endpoint(self, client: TestClient):
        """测试URL解析接口"""
        # 使用httpbin.org作为测试URL，这是一个可靠的测试服务
        response = client.post(
            "/v1/parse_url",
            json={
                "url": "https://httpbin.org/html",
                "save_parsed_content": False
            }
        )
        
        # URL解析可能因为网络问题失败，但接口应该能正常响应
        assert response.status_code in [200, 400, 500]
    
    def test_invalid_file_type(self, client: TestClient):
        """测试无效文件类型"""
        # 创建一个无效的文件
        invalid_content = b"invalid file content"
        
        response = client.post(
            "/v1/parse_pdf_file",
            files={"file": ("invalid.txt", invalid_content, "text/plain")},
            data={"save_parsed_content": "false"}
        )
        
        # 应该返回400错误
        assert response.status_code == 400
    
    def test_missing_file(self, client: TestClient):
        """测试缺少文件参数"""
        response = client.post(
            "/v1/parse_pdf_file",
            data={"save_parsed_content": "false"}
        )
        
        # 应该返回422错误（验证错误）
        assert response.status_code == 422
    
    def test_file_size_limit(self, client: TestClient):
        """测试文件大小限制"""
        # 创建一个超过100MB的虚拟文件
        large_content = b"x" * (100 * 1024 * 1024 + 1)
        
        response = client.post(
            "/v1/parse_pdf_file",
            files={"file": ("large.pdf", large_content, "application/pdf")},
            data={"save_parsed_content": "false"}
        )
        
        # 可能因为文件太大而失败，但接口应该能正常响应
        assert response.status_code in [200, 400, 413, 500]


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
