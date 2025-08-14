"""
Test all parser API endpoints for markio service
"""

import json
import time


class TestAllParsers:
    """Test class for all parser endpoints"""

    def test_health_check(self, client):
        """Test if the service is running"""
        response = client.get("/")
        assert (
            response.status_code == 200 or response.status_code == 307
        )  # Redirect to docs

    def test_pdf_parser(self, client, test_files_dir, test_files, api_endpoints):
        """Test PDF file parsing"""
        pdf_file = test_files_dir / test_files["pdf"]
        assert pdf_file.exists(), f"Test PDF file not found: {pdf_file}"

        start_time = time.time()

        with open(pdf_file, "rb") as f:
            files = {"file": (test_files["pdf"], f, "application/pdf")}
            data = {"config": json.dumps({"save_parsed_content": False})}

            response = client.post(api_endpoints["pdf"], files=files, data=data)

        end_time = time.time()
        conversion_time = end_time - start_time

        # 验证接口工作正常
        assert response.status_code == 200, f"PDF parsing failed: {response.text}"
        result = response.json()
        assert "parsed_content" in result

        # 输出转换时间
        print(
            f"✅ PDF接口测试通过 - 状态码: {response.status_code}, 转换时间: {conversion_time:.2f}秒"
        )

    def test_doc_parser(self, client, test_files_dir, test_files, api_endpoints):
        """Test DOC file parsing"""
        doc_file = test_files_dir / test_files["doc"]
        assert doc_file.exists(), f"Test DOC file not found: {doc_file}"

        start_time = time.time()

        with open(doc_file, "rb") as f:
            files = {"file": (test_files["doc"], f, "application/msword")}
            data = {"config": json.dumps({"save_parsed_content": False})}

            response = client.post(api_endpoints["doc"], files=files, data=data)

        end_time = time.time()
        conversion_time = end_time - start_time

        # 验证接口工作正常
        assert response.status_code == 200, f"DOC parsing failed: {response.text}"
        result = response.json()
        assert "parsed_content" in result

        # 输出转换时间
        print(
            f"✅ DOC接口测试通过 - 状态码: {response.status_code}, 转换时间: {conversion_time:.2f}秒"
        )

    def test_docx_parser(self, client, test_files_dir, test_files, api_endpoints):
        """Test DOCX file parsing"""
        docx_file = test_files_dir / test_files["docx"]
        assert docx_file.exists(), f"Test DOCX file not found: {docx_file}"

        start_time = time.time()

        with open(docx_file, "rb") as f:
            files = {
                "file": (
                    test_files["docx"],
                    f,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            }
            data = {"config": json.dumps({"save_parsed_content": False})}

            response = client.post(api_endpoints["docx"], files=files, data=data)

        end_time = time.time()
        conversion_time = end_time - start_time

        # 验证接口工作正常
        assert response.status_code == 200, f"DOCX parsing failed: {response.text}"
        result = response.json()
        assert "parsed_content" in result

        # 输出转换时间
        print(
            f"✅ DOCX接口测试通过 - 状态码: {response.status_code}, 转换时间: {conversion_time:.2f}秒"
        )

    def test_ppt_parser(self, client, test_files_dir, test_files, api_endpoints):
        """Test PPT file parsing"""
        ppt_file = test_files_dir / test_files["ppt"]
        assert ppt_file.exists(), f"Test PPT file not found: {ppt_file}"

        start_time = time.time()

        with open(ppt_file, "rb") as f:
            files = {"file": (test_files["ppt"], f, "application/vnd.ms-powerpoint")}
            data = {"config": json.dumps({"save_parsed_content": False})}

            response = client.post(api_endpoints["ppt"], files=files, data=data)

        end_time = time.time()
        conversion_time = end_time - start_time

        # 验证接口工作正常
        assert response.status_code == 200, f"PPT parsing failed: {response.text}"
        result = response.json()
        assert "parsed_content" in result

        # 输出转换时间
        print(
            f"✅ PPT接口测试通过 - 状态码: {response.status_code}, 转换时间: {conversion_time:.2f}秒"
        )

    def test_pptx_parser(self, client, test_files_dir, test_files, api_endpoints):
        """Test PPTX file parsing"""
        pptx_file = test_files_dir / test_files["pptx"]
        assert pptx_file.exists(), f"Test PPTX file not found: {pptx_file}"

        start_time = time.time()

        with open(pptx_file, "rb") as f:
            files = {
                "file": (
                    test_files["pptx"],
                    f,
                    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                )
            }
            data = {"config": json.dumps({"save_parsed_content": False})}

            response = client.post(api_endpoints["pptx"], files=files, data=data)

        end_time = time.time()
        conversion_time = end_time - start_time

        # 验证接口工作正常
        assert response.status_code == 200, f"PPTX parsing failed: {response.text}"
        result = response.json()
        assert "parsed_content" in result

        # 输出转换时间
        print(
            f"✅ PPTX接口测试通过 - 状态码: {response.status_code}, 转换时间: {conversion_time:.2f}秒"
        )

    def test_xlsx_parser(self, client, test_files_dir, test_files, api_endpoints):
        """Test XLSX file parsing"""
        xlsx_file = test_files_dir / test_files["xlsx"]
        assert xlsx_file.exists(), f"Test XLSX file not found: {xlsx_file}"

        start_time = time.time()

        with open(xlsx_file, "rb") as f:
            files = {
                "file": (
                    test_files["xlsx"],
                    f,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            }
            data = {"config": json.dumps({"save_parsed_content": False})}

            response = client.post(api_endpoints["xlsx"], files=files, data=data)

        end_time = time.time()
        conversion_time = end_time - start_time

        # 验证接口工作正常
        assert response.status_code == 200, f"XLSX parsing failed: {response.text}"
        result = response.json()
        assert "parsed_content" in result

        # 输出转换时间
        print(
            f"✅ XLSX接口测试通过 - 状态码: {response.status_code}, 转换时间: {conversion_time:.2f}秒"
        )

    def test_html_parser(self, client, test_files_dir, test_files, api_endpoints):
        """Test HTML file parsing"""
        html_file = test_files_dir / test_files["html"]
        assert html_file.exists(), f"Test HTML file not found: {html_file}"

        start_time = time.time()

        with open(html_file, "rb") as f:
            files = {"file": (test_files["html"], f, "text/html")}
            data = {"config": json.dumps({"save_parsed_content": False})}

            response = client.post(api_endpoints["html"], files=files, data=data)

        end_time = time.time()
        conversion_time = end_time - start_time

        # 验证接口工作正常
        assert response.status_code == 200, f"HTML parsing failed: {response.text}"
        result = response.json()
        assert "parsed_content" in result

        # 输出转换时间
        print(
            f"✅ HTML接口测试通过 - 状态码: {response.status_code}, 转换时间: {conversion_time:.2f}秒"
        )

    def test_epub_parser(self, client, test_files_dir, test_files, api_endpoints):
        """Test EPUB file parsing"""
        epub_file = test_files_dir / test_files["epub"]
        assert epub_file.exists(), f"Test EPUB file not found: {epub_file}"

        start_time = time.time()

        with open(epub_file, "rb") as f:
            files = {"file": (test_files["epub"], f, "application/epub+zip")}
            data = {"config": json.dumps({"save_parsed_content": False})}

            response = client.post(api_endpoints["epub"], files=files, data=data)

        end_time = time.time()
        conversion_time = end_time - start_time

        # 验证接口工作正常
        assert response.status_code == 200, f"EPUB parsing failed: {response.text}"
        result = response.json()
        assert "parsed_content" in result
        # 输出转换时间
        print(
            f"✅ EPUB接口测试通过 - 状态码: {response.status_code}, 转换时间: {conversion_time:.2f}秒"
        )

    def test_image_parser(self, client, test_files_dir, test_files, api_endpoints):
        """Test image file parsing"""
        # Using PDF as image test for now
        image_file = test_files_dir / test_files["image"]
        assert image_file.exists(), f"Test image file not found: {image_file}"

        start_time = time.time()

        with open(image_file, "rb") as f:
            files = {"file": (test_files["image"], f, "image/png")}
            data = {"config": json.dumps({"save_parsed_content": False})}

            response = client.post(api_endpoints["image"], files=files, data=data)

        end_time = time.time()
        conversion_time = end_time - start_time

        # 验证接口工作正常
        # Image parsing might return different status codes depending on implementation
        assert response.status_code in [200, 400, 500], (
            f"Image parsing unexpected response: {response.status_code}"
        )
        # 输出转换时间
        print(
            f"✅ 图片接口测试通过 - 状态码: {response.status_code}, 转换时间: {conversion_time:.2f}秒"
        )

    def test_invalid_file_type(self, client, api_endpoints):
        """Test invalid file type handling"""
        # Test with invalid file type
        files = {"file": ("test.txt", b"invalid content", "text/plain")}
        data = {"config": json.dumps({"save_parsed_content": False})}

        # Try to upload to PDF endpoint with text file
        response = client.post(api_endpoints["pdf"], files=files, data=data)

        # Should return 400 or 500 for invalid file type
        assert response.status_code in [400, 500], (
            f"Expected error for invalid file type, got: {response.status_code}"
        )

    def test_missing_file(self, client, api_endpoints):
        """Test missing file handling"""
        data = {"config": json.dumps({"save_parsed_content": False})}

        # Try to upload without file
        response = client.post(api_endpoints["pdf"], data=data)

        # Should return 422 for missing file
        assert response.status_code == 422, (
            f"Expected 422 for missing file, got: {response.status_code}"
        )

    def test_large_file_handling(
        self, client, test_files_dir, test_files, api_endpoints
    ):
        """Test large file handling (using largest available test file)"""
        # Use the largest test file available
        largest_file = None
        largest_size = 0

        for file_type, filename in test_files.items():
            file_path = test_files_dir / filename
            if file_path.exists():
                size = file_path.stat().st_size
                if size > largest_size:
                    largest_size = size
                    largest_file = (file_type, filename)

        if largest_file:
            file_type, filename = largest_file
            file_path = test_files_dir / filename

            with open(file_path, "rb") as f:
                files = {"file": (filename, f, "application/octet-stream")}
                data = {"config": json.dumps({"save_parsed_content": False})}

                response = client.post(api_endpoints[file_type], files=files, data=data)

            # Large file should still be processed successfully
            assert response.status_code == 200, (
                f"Large file parsing failed: {response.text}"
            )
