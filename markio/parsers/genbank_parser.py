"""
GenBank Parser Module

This module provides functionality for parsing GenBank format files,
a standard format used by NCBI for storing annotated nucleotide and protein sequences.

GenBank format structure:
- LOCUS: Entry name, length, molecule type, shape, division, date
- DEFINITION: Brief description
- ACCESSION: Unique identifier
- VERSION: Version number
- KEYWORDS: Keywords for searching
- SOURCE: Organism information
- FEATURES: Biological features with locations
- ORIGIN: The sequence data

Features:
- Parse GenBank records with full metadata
- Extract sequence features and annotations
- Support multiple records in single file
- Convert to structured Markdown format
- Preserve biological annotations
- Enhanced analysis with BioPython

Dependencies:
- BioPython: Included in default installation for enhanced parsing
"""

import re
from pathlib import Path
from typing import Dict, List, Optional

from markio.utils.file_utils import func_processing_time, process_resource_path
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)

# Try to import BioPython for enhanced parsing
try:
    from Bio import SeqIO
    from Bio.SeqUtils import gc_fraction

    BIOPYTHON_AVAILABLE = True
    logger.info("BioPython detected - Enhanced GenBank analysis enabled")
except ImportError:
    BIOPYTHON_AVAILABLE = False
    logger.info("BioPython not found - Using basic GenBank parsing")


class GenBankRecord:
    """Represents a single GenBank record with metadata and features"""

    def __init__(self):
        """Initialize an empty GenBank record"""
        self.locus = {}
        self.definition = ""
        self.accession = ""
        self.version = ""
        self.keywords = ""
        self.source = {}
        self.features = []
        self.sequence = ""
        self.references = []

    def to_dict(self) -> Dict:
        """Convert record to dictionary representation"""
        return {
            "locus": self.locus,
            "definition": self.definition,
            "accession": self.accession,
            "version": self.version,
            "keywords": self.keywords,
            "source": self.source,
            "features": self.features,
            "sequence_length": len(self.sequence),
            "gc_content": self._calculate_gc_content(),
        }

    def _calculate_gc_content(self) -> Optional[float]:
        """Calculate GC content of sequence"""
        if not self.sequence:
            return None

        sequence_upper = self.sequence.upper()
        g_count = sequence_upper.count("G")
        c_count = sequence_upper.count("C")
        total = len(self.sequence)

        if total > 0:
            return ((g_count + c_count) / total) * 100
        return None

    def to_markdown(self) -> str:
        """Convert record to Markdown format"""
        md = f"### GenBank Record: {self.locus.get('name', 'Unknown')}\n\n"

        # Basic information
        md += "#### Basic Information\n\n"

        if self.locus:
            md += "**LOCUS:**\n"
            for key, value in self.locus.items():
                md += f"- {key.title()}: {value}\n"
            md += "\n"

        if self.definition:
            md += f"**DEFINITION:** {self.definition}\n\n"

        if self.accession:
            md += f"**ACCESSION:** {self.accession}\n\n"

        if self.version:
            md += f"**VERSION:** {self.version}\n\n"

        if self.keywords:
            md += f"**KEYWORDS:** {self.keywords}\n\n"

        # Source information
        if self.source:
            md += "#### Source\n\n"
            for key, value in self.source.items():
                md += f"**{key.title()}:** {value}\n\n"

        # Features table
        if self.features:
            md += "#### Features\n\n"
            md += "| Type | Location | Qualifiers |\n"
            md += "|------|----------|------------|\n"

            for feature in self.features:
                feature_type = feature.get("type", "")
                location = feature.get("location", "")
                qualifiers = feature.get("qualifiers", {})

                # Format qualifiers
                qual_str = "<br>".join(
                    [f"{k}: {v}" for k, v in qualifiers.items()][:3]
                )  # Limit to first 3
                if len(qualifiers) > 3:
                    qual_str += "<br>..."

                md += f"| {feature_type} | {location} | {qual_str} |\n"

            md += "\n"

        # Sequence information
        if self.sequence:
            md += "#### Sequence\n\n"
            md += f"**Length:** {len(self.sequence)} bp\n\n"

            gc_content = self._calculate_gc_content()
            if gc_content is not None:
                md += f"**GC Content:** {gc_content:.2f}%\n\n"

            md += "**Sequence Data:**\n\n```\n"
            # Format sequence in blocks of 60 characters with line numbers
            for i in range(0, len(self.sequence), 60):
                line_num = i + 1
                seq_block = self.sequence[i : i + 60]
                md += f"{line_num:>9} {seq_block}\n"
            md += "```\n\n"

        return md


@func_processing_time
async def genbank_parse_main(
    resource_path: str = "",
    save_parsed_content: bool = False,
    output_dir: str = "outputs",
    include_features: bool = True,
    include_sequence: bool = True,
) -> str:
    """
    Parse GenBank format files and convert to Markdown format.

    GenBank is a comprehensive database format that includes both sequence data
    and extensive biological annotations. This parser extracts all metadata,
    features, and sequence information.

    Features:
    - Parse complete GenBank records
    - Extract metadata (locus, definition, accession, etc.)
    - Parse feature tables with locations and qualifiers
    - Extract sequence data
    - Support multiple records per file
    - Convert to structured Markdown output

    Args:
        resource_path: Path to GenBank file (.gb, .gbk, .genbank) or URL
        save_parsed_content: Whether to save parsed markdown content to file
        output_dir: Directory where parsed content will be saved
        include_features: Whether to include feature table in output
        include_sequence: Whether to include sequence data in output

    Returns:
        str: Parsed content in Markdown format with record information

    Raises:
        FileNotFoundError: If file not found
        ValueError: If file format is invalid
        Exception: For other parsing errors

    Example:
        >>> content = await genbank_parse_main("sequence.gb")
        >>> print(content)
        # GenBank Records
        ...
    """
    local_genbank_path = await process_resource_path(
        resource_path=resource_path,
        output_dir=output_dir if save_parsed_content else None,
    )

    file_path = Path(local_genbank_path)
    file_name = file_path.stem

    logger.info(f"Starting GenBank parsing for: {file_name}")

    try:
        # Use BioPython if available for better parsing
        if BIOPYTHON_AVAILABLE:
            records = _parse_with_biopython(
                file_path=local_genbank_path,
                include_features=include_features,
                include_sequence=include_sequence,
            )
        else:
            # Fallback to basic parsing
            records = _parse_genbank_file(
                file_path=local_genbank_path,
                include_features=include_features,
                include_sequence=include_sequence,
            )

        if not records:
            raise ValueError("No valid GenBank records found in file")

        logger.info(f"Successfully parsed {len(records)} record(s)")

        # Generate Markdown content
        markdown_content = _generate_markdown(
            records=records,
            file_name=file_name,
            include_features=include_features,
            include_sequence=include_sequence,
        )

        # Save if requested
        if save_parsed_content:
            output_path = Path(output_dir) / file_name
            output_path.mkdir(parents=True, exist_ok=True)
            md_file = output_path / f"{file_name}.md"

            with open(md_file, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            logger.info(f"GenBank {file_name} saved to {md_file}")

        return markdown_content

    except Exception as e:
        logger.error(f"Error parsing GenBank file {file_name}: {str(e)}")
        raise


def _parse_with_biopython(
    file_path: str,
    include_features: bool = True,
    include_sequence: bool = True,
) -> List[GenBankRecord]:
    """
    Parse GenBank file using BioPython for enhanced accuracy.

    Args:
        file_path: Path to GenBank file
        include_features: Whether to parse feature table
        include_sequence: Whether to parse sequence data

    Returns:
        List of GenBankRecord objects
    """
    records = []

    try:
        for bio_record in SeqIO.parse(file_path, "genbank"):
            record = GenBankRecord()

            # Extract LOCUS information
            record.locus = {
                "name": bio_record.name,
                "length": len(bio_record.seq),
                "molecule_type": bio_record.annotations.get("molecule_type", ""),
                "topology": bio_record.annotations.get("topology", ""),
                "division": bio_record.annotations.get("data_file_division", ""),
                "date": bio_record.annotations.get("date", ""),
            }

            # Extract basic information
            record.definition = bio_record.description
            record.accession = bio_record.id
            record.version = bio_record.annotations.get("accessions", [""])[0]
            record.keywords = bio_record.annotations.get("keywords", [""])
            if isinstance(record.keywords, list):
                record.keywords = ", ".join(record.keywords)

            # Extract source information
            record.source = {
                "source": bio_record.annotations.get("source", ""),
                "organism": bio_record.annotations.get("organism", ""),
                "taxonomy": ", ".join(bio_record.annotations.get("taxonomy", [])),
            }

            # Extract features if requested
            if include_features:
                for feature in bio_record.features:
                    feature_dict = {
                        "type": feature.type,
                        "location": str(feature.location),
                        "qualifiers": {},
                    }
                    # Extract key qualifiers
                    for key, value in feature.qualifiers.items():
                        # Join list values
                        if isinstance(value, list):
                            feature_dict["qualifiers"][key] = ", ".join(
                                str(v) for v in value
                            )
                        else:
                            feature_dict["qualifiers"][key] = str(value)
                    record.features.append(feature_dict)

            # Extract sequence if requested
            if include_sequence:
                record.sequence = str(bio_record.seq).lower()

            records.append(record)

    except Exception as e:
        logger.error(f"BioPython parsing failed: {e}")
        # Fallback to basic parsing
        return _parse_genbank_file(file_path, include_features, include_sequence)

    return records


def _parse_genbank_file(
    file_path: str,
    include_features: bool = True,
    include_sequence: bool = True,
) -> List[GenBankRecord]:
    """
    Parse GenBank file using basic text parsing (fallback method).

    Args:
        file_path: Path to GenBank file
        include_features: Whether to parse feature table
        include_sequence: Whether to parse sequence data

    Returns:
        List of GenBankRecord objects
    """
    records = []
    current_record = None
    current_section = None
    feature_buffer = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            # New record starts with LOCUS
            if line.startswith("LOCUS"):
                if current_record is not None:
                    records.append(current_record)
                current_record = GenBankRecord()
                current_section = "LOCUS"
                _parse_locus_line(line, current_record)

            elif current_record is None:
                continue  # Skip lines before first LOCUS

            # Identify section
            elif line.startswith("DEFINITION"):
                current_section = "DEFINITION"
                current_record.definition = line[12:].strip()

            elif line.startswith("ACCESSION"):
                current_section = "ACCESSION"
                current_record.accession = line[12:].strip()

            elif line.startswith("VERSION"):
                current_section = "VERSION"
                current_record.version = line[12:].strip()

            elif line.startswith("KEYWORDS"):
                current_section = "KEYWORDS"
                current_record.keywords = line[12:].strip()

            elif line.startswith("SOURCE"):
                current_section = "SOURCE"
                current_record.source["source"] = line[12:].strip()

            elif line.startswith("  ORGANISM"):
                current_record.source["organism"] = line[12:].strip()

            elif line.startswith("FEATURES") and include_features:
                current_section = "FEATURES"

            elif line.startswith("ORIGIN") and include_sequence:
                current_section = "ORIGIN"

            elif line.startswith("//"):
                # End of record
                if current_record is not None:
                    records.append(current_record)
                current_record = None
                current_section = None

            # Continue parsing sections
            elif current_section == "DEFINITION" and line.startswith(" " * 12):
                current_record.definition += " " + line.strip()

            elif current_section == "FEATURES" and include_features:
                _parse_feature_line(line, current_record)

            elif current_section == "ORIGIN" and include_sequence:
                # Remove line numbers and spaces from sequence
                seq_line = re.sub(r"[0-9\s]", "", line)
                current_record.sequence += seq_line

    # Don't forget last record if file doesn't end with //
    if current_record is not None:
        records.append(current_record)

    return records


def _parse_locus_line(line: str, record: GenBankRecord):
    """Parse LOCUS line and extract metadata"""
    parts = line.split()
    if len(parts) >= 2:
        record.locus["name"] = parts[1]
    if len(parts) >= 3:
        record.locus["length"] = parts[2]
    if len(parts) >= 5:
        record.locus["molecule_type"] = parts[4]
    if len(parts) >= 6:
        record.locus["shape"] = parts[5]
    if len(parts) >= 7:
        record.locus["division"] = parts[6]
    if len(parts) >= 8:
        record.locus["date"] = parts[7]


def _parse_feature_line(line: str, record: GenBankRecord):
    """Parse feature table lines"""
    # Feature type (not indented with spaces at positions 5-20)
    if line[5:21].strip() and not line[5:21].startswith(" "):
        feature_type = line[5:21].strip()
        location = line[21:].strip()

        record.features.append(
            {"type": feature_type, "location": location, "qualifiers": {}}
        )

    # Qualifier line (indented with '/')
    elif line.strip().startswith("/") and record.features:
        qualifier_match = re.match(r'/(\w+)=?"?([^"]*)"?', line.strip())
        if qualifier_match:
            qual_key = qualifier_match.group(1)
            qual_value = qualifier_match.group(2)
            record.features[-1]["qualifiers"][qual_key] = qual_value


def _generate_markdown(
    records: List[GenBankRecord],
    file_name: str,
    include_features: bool = True,
    include_sequence: bool = True,
) -> str:
    """
    Generate Markdown content from parsed records.

    Args:
        records: List of GenBankRecord objects
        file_name: Name of the source file
        include_features: Whether to include features
        include_sequence: Whether to include sequence

    Returns:
        Formatted Markdown string
    """
    md = f"# GenBank Records: {file_name}\n\n"

    # Summary
    md += "## Summary\n\n"
    md += f"**Total Records:** {len(records)}\n\n"

    total_length = sum(len(rec.sequence) for rec in records)
    if total_length > 0:
        md += f"**Total Sequence Length:** {total_length:,} bp\n\n"

    md += "---\n\n"

    # Individual records
    md += "## Records\n\n"
    for idx, record in enumerate(records, 1):
        md += f"#### [{idx}/{len(records)}]\n\n"
        md += record.to_markdown()
        if idx < len(records):
            md += "---\n\n"

    return md
