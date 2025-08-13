from enum import Enum
from typing import Optional

from pydantic import Field

from markio.schemas.parser_base import BaseParserConfig


class PDF_PARSE_TYPE(str, Enum):
    ocr = "ocr"
    auto = "auto"
    txt = "txt"


class PDF_PARSE_LANG(str, Enum):
    ch = "ch"
    ch_server = "ch_server"
    ch_lite = "ch_lite"
    chinese_cht = "chinese_cht"
    en = "en"
    korean = "korean"
    japan = "japan"
    ta = "ta"
    te = "te"
    ka = "ka"


class PDFParserConfig(BaseParserConfig):
    parse_method: PDF_PARSE_TYPE = Field(
        default=PDF_PARSE_TYPE.auto, description="Specify the PDF parsing method"
    )
    lang: PDF_PARSE_LANG = Field(
        default=PDF_PARSE_LANG.ch,
        description="Language of the document",
    )
    save_middle_content: bool = Field(
        default=False,
        description="If set to true, the parsed content will be saved to a file.",
    )
    start_page: Optional[int] = Field(
        default=0,
        description="Start page to parse",
    )
    end_page: Optional[int] = Field(
        default=None,
        description="End page to parse",
    )


class DOCXParserConfig(BaseParserConfig):
    pass


class HTMLParserConfig(BaseParserConfig):
    pass


class EPUBParserConfig(BaseParserConfig):
    pass


class ImageParserConfig(BaseParserConfig):
    pass


class PPTParserConfig(BaseParserConfig):
    pass


class PPTXParserConfig(BaseParserConfig):
    pass


class XLSXParserConfig(BaseParserConfig):
    pass
