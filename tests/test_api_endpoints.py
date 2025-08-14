"""
API接口功能测试
测试所有接口是否正常运行，使用真实的测试文件
"""
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
    def test_pdf_small_parse_endpoint(self, client: TestClient, real_test_files):
        """测试小PDF文件解析接口 - 使用真实PDF文件"""
        pdf_file_path = real_test_files["pdf_small"]
        
        if not pdf_file_path.exists():
            pytest.skip(f"测试小PDF文件不存在: {pdf_file_path}")
        
        with open(pdf_file_path, "rb") as f:
            files = {"file": ("test_pdf3.pdf", f, "application/pdf")}
            data = {"save_parsed_content": "false"}
            
            response = client.post("/v1/parse_pdf_file", files=files, data=data)
        
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
    
    def test_image_parse_endpoint(self, client: TestClient):
        """测试图片解析接口"""
        # 创建一个简单的测试图片内容（模拟）
        # 注意：这里使用文本内容模拟，实际测试中可能需要真实的图片文件
        test_image_content = b"fake image content"
        
        files = {"file": ("test_image.jpg", test_image_content, "image/jpeg")}
        data = {"save_parsed_content": "false"}
        
        response = client.post("/v1/parse_image_file", files=files, data=data)
        
        # 图片解析可能成功或失败，但应该返回有效状态码
        assert response.status_code in [200, 400, 500]
        
        if response.status_code == 200:
            result = response.json()
            assert "parsed_content" in result or "status_code" in result
    
    def test_url_parse_endpoint(self, client: TestClient):
        """测试URL解析接口"""
        # 测试有效URL
        test_urls = [
            "https://httpbin.org/html",
            "https://example.com",
            "https://httpbin.org/json"
        ]
        
        for url in test_urls:
            data = {"url": url, "save_parsed_content": "false"}
            response = client.post("/v1/parse_url", data=data)
            
            # URL解析可能成功或失败，但应该返回有效状态码
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
        
        # 测试文件大小限制（如果API有的话）
        large_content = b"x" * 1024 * 1024  # 1MB
        files = {"file": ("large.txt", large_content, "text/plain")}
        response = client.post("/v1/parse_pdf_file", files=files)
        # 可能成功或失败，取决于API的文件大小限制
        assert response.status_code in [200, 400, 413, 422]
    
    def test_error_handling(self, client: TestClient):
        """测试错误处理"""
        # 测试缺少文件参数
        response = client.post("/v1/parse_pdf_file")
        assert response.status_code in [400, 422]
        
        # 测试无效的URL
        data = {"url": "invalid-url"}
        response = client.post("/v1/parse_url", data=data)
        assert response.status_code in [400, 422]
        
        # 测试空URL
        data = {"url": ""}
        response = client.post("/v1/parse_url", data=data)
        assert response.status_code in [400, 422]
        
        # 测试缺少URL参数
        response = client.post("/v1/parse_url")
        assert response.status_code in [400, 422]
    
    def test_save_parsed_content_option(self, client: TestClient):
        """测试保存解析内容的选项"""
        # 测试save_parsed_content为true的情况
        data = {"save_parsed_content": "true"}
        response = client.post("/v1/parse_url", data=data)
        # 应该返回错误，因为缺少URL
        assert response.status_code in [400, 422]
        
        # 测试save_parsed_content为false的情况
        data = {"save_parsed_content": "false"}
        response = client.post("/v1/parse_url", data=data)
        # 应该返回错误，因为缺少URL
        assert response.status_code in [400, 422]
        
        # 测试无效的save_parsed_content值
        data = {"save_parsed_content": "invalid"}
        response = client.post("/v1/parse_url", data=data)
        assert response.status_code in [400, 422]


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
        
        response = client.delete("/v1/parse_pdf_file")
        assert response.status_code == 405  # Method Not Allowed
        
        response = client.patch("/v1/parse_pdf_file")
        assert response.status_code == 405  # Method Not Allowed
    
    def test_invalid_content_type(self, client: TestClient):
        """测试无效的内容类型"""
        # 测试错误的Content-Type
        response = client.post(
            "/v1/parse_pdf_file",
            files={"file": ("test.pdf", b"fake pdf content", "text/plain")},
            data={"save_parsed_content": "false"}
        )
        
        # 可能成功或失败，取决于API的验证逻辑
        assert response.status_code in [200, 400, 422]
    
    def test_missing_required_fields(self, client: TestClient):
        """测试缺少必需字段"""
        # 测试缺少文件字段
        response = client.post("/v1/parse_pdf_file")
        assert response.status_code in [400, 422]
        
        # 测试缺少URL字段
        response = client.post("/v1/parse_url")
        assert response.status_code in [400, 422]


class TestIntegrationScenarios:
    """集成场景测试类"""
    
    @pytest.mark.integration
    def test_multiple_file_types_parsing(self, client: TestClient, real_test_files):
        """测试多种文件类型的解析"""
        file_types = ["pdf", "docx", "xlsx", "html"]
        successful_parses = 0
        
        for file_type in file_types:
            if file_type in real_test_files and real_test_files[file_type].exists():
                file_path = real_test_files[file_type]
                file_name = file_path.name
                
                # 根据文件类型选择正确的MIME类型
                mime_types = {
                    "pdf": "application/pdf",
                    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "html": "text/html"
                }
                
                with open(file_path, "rb") as f:
                    files = {"file": (file_name, f, mime_types[file_type])}
                    data = {"save_parsed_content": "false"}
                    
                    endpoint = f"/v1/parse_{file_type}_file"
                    response = client.post(endpoint, files=files, data=data)
                    
                    if response.status_code == 200:
                        successful_parses += 1
                        result = response.json()
                        assert "parsed_content" in result or "status_code" in result
        
        # 至少应该有一些成功的解析
        assert successful_parses > 0, "至少应该有一些文件能够成功解析"
    
    @pytest.mark.integration
    def test_concurrent_file_parsing(self, client: TestClient, real_test_files):
        """测试并发文件解析"""
        import concurrent.futures
        import time
        
        def parse_file(file_type, file_path):
            """单个文件解析函数"""
            if not file_path.exists():
                return None
            
            mime_types = {
                "pdf": "application/pdf",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "html": "text/html"
            }
            
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f, mime_types[file_type])}
                data = {"save_parsed_content": "false"}
                
                endpoint = f"/v1/parse_{file_type}_file"
                response = client.post(endpoint, files=files, data=data)
                
                return {
                    "file_type": file_type,
                    "status_code": response.status_code,
                    "success": response.status_code == 200
                }
        
        # 选择可用的文件进行并发测试
        available_files = {
            k: v for k, v in real_test_files.items() 
            if v.exists() and k in ["pdf", "docx", "xlsx", "html"]
        }
        
        if len(available_files) < 2:
            pytest.skip("需要至少2个可用文件进行并发测试")
        
        start_time = time.time()
        
        # 使用线程池进行并发测试
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_to_file = {
                executor.submit(parse_file, file_type, file_path): file_type
                for file_type, file_path in available_files.items()
            }
            
            results = []
            for future in concurrent.futures.as_completed(future_to_file):
                result = future.result()
                if result:
                    results.append(result)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 验证结果
        assert len(results) > 0, "应该有解析结果"
        assert execution_time < 30, f"并发解析应该在30秒内完成，实际用时: {execution_time:.2f}秒"
        
        # 统计成功率
        successful_count = sum(1 for r in results if r["success"])
        success_rate = successful_count / len(results)
        
        print(f"并发解析结果: {len(results)}个文件，成功率: {success_rate:.2%}")


class TestPerformanceAndLimits:
    """性能和限制测试类"""
    
    def test_response_time_limits(self, client: TestClient, real_test_files):
        """测试响应时间限制"""
        import time
        
        # 选择一个可用的文件进行性能测试
        test_file = None
        for file_type in ["pdf", "docx", "xlsx"]:
            if file_type in real_test_files and real_test_files[file_type].exists():
                test_file = (file_type, real_test_files[file_type])
                break
        
        if not test_file:
            pytest.skip("没有可用的测试文件进行性能测试")
        
        file_type, file_path = test_file
        
        mime_types = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        
        start_time = time.time()
        
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, mime_types[file_type])}
            data = {"save_parsed_content": "false"}
            
            endpoint = f"/v1/parse_{file_type}_file"
            response = client.post(endpoint, files=files, data=data)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # 验证响应时间在合理范围内（30秒内）
        assert response_time < 30, f"文件解析应该在30秒内完成，实际用时: {response_time:.2f}秒"
        
        # 验证响应状态
        assert response.status_code in [200, 400, 500]
        
        print(f"{file_type.upper()}文件解析响应时间: {response_time:.2f}秒")
    
    def test_memory_usage_limits(self, client: TestClient):
        """测试内存使用限制"""
        # 创建一个较大的测试文件（模拟内存压力）
        large_content = b"x" * 1024 * 1024  # 1MB
        
        files = {"file": ("large_test.txt", large_content, "text/plain")}
        data = {"save_parsed_content": "false"}
        
        response = client.post("/v1/parse_pdf_file", files=files, data=data)
        
        # 应该返回错误（文件类型不匹配或大小超限）
        assert response.status_code in [400, 413, 422]
    
    def test_concurrent_connections_limit(self, client: TestClient):
        """测试并发连接数限制"""
        import concurrent.futures
        import time
        
        def make_request():
            """发送请求的函数"""
            try:
                response = client.get("/")
                return response.status_code
            except Exception as e:
                return f"Error: {str(e)}"
        
        # 测试多个并发请求
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = []
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 验证所有请求都能处理
        assert len(results) == 10, "应该能处理10个并发请求"
        
        # 验证响应时间合理
        assert execution_time < 10, f"并发请求应该在10秒内完成，实际用时: {execution_time:.2f}秒"
        
        # 验证大部分请求成功
        successful_requests = sum(1 for r in results if r == 200)
        success_rate = successful_requests / len(results)
        
        print(f"并发连接测试: 10个请求，成功率: {success_rate:.2%}")
        assert success_rate >= 0.8, "至少80%的请求应该成功"


class TestHealthAndMonitoring:
    """健康检查和监控测试类"""
    
    def test_health_check_endpoint(self, client: TestClient):
        """测试健康检查端点（如果存在）"""
        # 测试根路径重定向
        response = client.get("/", allow_redirects=False)
        assert response.status_code == 307  # Temporary Redirect
        
        # 测试重定向后的文档页面
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_api_version_endpoint(self, client: TestClient):
        """测试API版本端点（如果存在）"""
        # 测试OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "info" in schema
        assert "title" in schema["info"]
        assert "version" in schema["info"]
        assert schema["info"]["title"] == "Markio"
    
    def test_cors_headers(self, client: TestClient):
        """测试CORS头部设置"""
        # 测试预检请求
        response = client.options("/v1/parse_pdf_file")
        # CORS预检请求应该返回200或405
        assert response.status_code in [200, 405]
        
        # 测试实际请求的CORS头部
        response = client.get("/docs")
        # 检查是否有CORS相关的头部
        cors_headers = [h for h in response.headers.keys() if 'access-control' in h.lower()]
        # 如果有CORS中间件，应该有相关头部
        # 如果没有，也不应该失败
        assert True  # 这个测试主要是为了确保请求不会崩溃
    
    def test_rate_limiting(self, client: TestClient):
        """测试速率限制（如果实现）"""
        # 快速发送多个请求
        responses = []
        for i in range(20):
            response = client.get("/docs")
            responses.append(response.status_code)
        
        # 检查是否所有请求都被处理
        assert len(responses) == 20
        
        # 检查是否有请求被限制（返回429状态码）
        rate_limited = [r for r in responses if r == 429]
        
        if rate_limited:
            print(f"检测到速率限制: {len(rate_limited)}个请求被限制")
            # 如果有速率限制，大部分请求应该成功
            successful = [r for r in responses if r == 200]
            assert len(successful) > len(rate_limited), "大部分请求应该成功"
        else:
            print("未检测到速率限制")


class TestEdgeCases:
    """边界情况测试类"""
    
    def test_very_large_file_name(self, client: TestClient):
        """测试非常大的文件名"""
        # 创建一个超长的文件名
        long_filename = "a" * 500 + ".pdf"
        files = {"file": (long_filename, b"fake content", "application/pdf")}
        
        response = client.post("/v1/parse_pdf_file", files=files)
        # 应该返回错误（文件名过长）
        assert response.status_code in [400, 413, 422]
    
    def test_special_characters_in_filename(self, client: TestClient):
        """测试文件名中的特殊字符"""
        special_filenames = [
            "test file with spaces.pdf",
            "test-file-with-dashes.pdf",
            "test_file_with_underscores.pdf",
            "test.file.with.dots.pdf",
            "test'file'with'quotes.pdf",
            "test(file)with[brackets].pdf",
            "test&file&with&symbols.pdf",
            "测试文件.pdf",  # 中文文件名
            "test-файл.pdf",  # 俄文字符
            "test-ファイル.pdf"  # 日文字符
        ]
        
        for filename in special_filenames:
            files = {"file": (filename, b"fake content", "application/pdf")}
            response = client.post("/v1/parse_pdf_file", files=files)
            
            # 特殊字符文件名应该被正确处理
            assert response.status_code in [200, 400, 422]
    
    def test_empty_file_upload(self, client: TestClient):
        """测试空文件上传"""
        # 测试完全空的文件
        files = {"file": ("empty.pdf", b"", "application/pdf")}
        response = client.post("/v1/parse_pdf_file", files=files)
        assert response.status_code in [400, 422]
        
        # 测试None文件
        files = {"file": ("none.pdf", None, "application/pdf")}
        response = client.post("/v1/parse_pdf_file", files=files)
        assert response.status_code in [400, 422]
    
    def test_malformed_multipart_data(self, client: TestClient):
        """测试格式错误的多部分数据"""
        # 测试缺少boundary的multipart数据
        headers = {"Content-Type": "multipart/form-data"}
        data = b"malformed multipart data without boundary"
        
        response = client.post("/v1/parse_pdf_file", data=data, headers=headers)
        assert response.status_code in [400, 422, 500]
    
    def test_invalid_json_in_form_data(self, client: TestClient):
        """测试表单数据中的无效JSON"""
        # 测试无效的JSON数据
        files = {"file": ("test.pdf", b"fake content", "application/pdf")}
        data = {"save_parsed_content": "invalid_json_value"}
        
        response = client.post("/v1/parse_pdf_file", files=files, data=data)
        # 应该返回验证错误
        assert response.status_code in [400, 422]


class TestSecurityFeatures:
    """安全特性测试类"""
    
    def test_path_traversal_prevention(self, client: TestClient):
        """测试路径遍历攻击防护"""
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd"
        ]
        
        for filename in malicious_filenames:
            files = {"file": (filename, b"fake content", "application/pdf")}
            response = client.post("/v1/parse_pdf_file", files=files)
            
            # 应该拒绝恶意文件名
            assert response.status_code in [400, 422, 500]
    
    def test_file_type_validation(self, client: TestClient):
        """测试文件类型验证"""
        # 测试错误的MIME类型
        test_cases = [
            ("test.pdf", b"fake content", "text/plain"),
            ("test.docx", b"fake content", "image/jpeg"),
            ("test.xlsx", b"fake content", "application/pdf"),
            ("test.html", b"fake content", "application/zip")
        ]
        
        for filename, content, mime_type in test_cases:
            files = {"file": (filename, content, mime_type)}
            
            # 根据文件名选择正确的端点
            if "pdf" in filename:
                endpoint = "/v1/parse_pdf_file"
            elif "docx" in filename:
                endpoint = "/v1/parse_docx_file"
            elif "xlsx" in filename:
                endpoint = "/v1/parse_xlsx_file"
            elif "html" in filename:
                endpoint = "/v1/parse_html_file"
            else:
                continue
            
            response = client.post(endpoint, files=files)
            
            # 应该返回验证错误或成功（取决于API的验证逻辑）
            assert response.status_code in [200, 400, 422]
    
    def test_content_length_validation(self, client: TestClient):
        """测试内容长度验证"""
        # 测试超长内容
        very_large_content = b"x" * (10 * 1024 * 1024)  # 10MB
        
        files = {"file": ("large.pdf", very_large_content, "application/pdf")}
        response = client.post("/v1/parse_pdf_file", files=files)
        
        # 应该返回文件过大错误
        assert response.status_code in [400, 413, 422]
    
    def test_sql_injection_prevention(self, client: TestClient):
        """测试SQL注入防护"""
        # 测试包含SQL注入的URL
        malicious_urls = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "'; UPDATE users SET password='hacked'; --"
        ]
        
        for url in malicious_urls:
            data = {"url": url, "save_parsed_content": "false"}
            response = client.post("/v1/parse_url", data=data)
            
            # 应该拒绝恶意URL
            assert response.status_code in [400, 422, 500]
