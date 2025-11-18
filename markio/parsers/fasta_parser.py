"""
FASTA Parser Module

This module provides functionality for parsing FASTA (Fast-All) format files,
commonly used in bioinformatics for nucleotide or peptide sequences.

FASTA format structure:
- Header line starting with '>' followed by sequence identifier and description
- One or more lines containing the sequence data
- Multiple sequences can exist in a single file

Features:
- Parse single or multiple FASTA sequences
- Extract sequence metadata (ID, description)
- Calculate sequence statistics (length, GC content for DNA)
- Validate sequence format
- Convert to Markdown format with metadata preservation
"""

from pathlib import Path
from typing import Dict, List, Optional
import re

from markio.utils.file_utils import func_processing_time, process_resource_path
from markio.utils.logger_config import get_logger

logger = get_logger(__name__)


class FASTASequence:
    """Represents a single FASTA sequence with metadata"""

    def __init__(self, header: str, sequence: str):
        """
        Initialize a FASTA sequence object.

        Args:
            header: The header line (without '>' prefix)
            sequence: The sequence data
        """
        self.raw_header = header
        self.sequence = sequence.replace(" ", "").replace("\n", "").upper()
        self._parse_header()
        self._calculate_stats()

    def _parse_header(self):
        """Parse header to extract ID and description"""
        parts = self.raw_header.split(maxsplit=1)
        self.id = parts[0] if parts else "Unknown"
        self.description = parts[1] if len(parts) > 1 else ""

    def _calculate_stats(self):
        """Calculate sequence statistics"""
        self.length = len(self.sequence)
        self.gc_content = None

        # Calculate GC content for DNA sequences
        if self._is_dna_sequence():
            g_count = self.sequence.count("G")
            c_count = self.sequence.count("C")
            if self.length > 0:
                self.gc_content = ((g_count + c_count) / self.length) * 100

    def _is_dna_sequence(self) -> bool:
        """Check if sequence is likely DNA (contains only ATGCN characters)"""
        dna_chars = set("ATGCN")
        return all(char in dna_chars for char in self.sequence)

    def _is_protein_sequence(self) -> bool:
        """Check if sequence is likely protein"""
        # Standard amino acid codes
        protein_chars = set("ACDEFGHIKLMNPQRSTVWY")
        return all(char in protein_chars for char in self.sequence)

    def get_sequence_type(self) -> str:
        """Determine sequence type"""
        if self._is_dna_sequence():
            return "DNA"
        elif self._is_protein_sequence():
            return "Protein"
        else:
            return "Unknown"

    def to_dict(self) -> Dict:
        """Convert sequence to dictionary representation"""
        result = {
            "id": self.id,
            "description": self.description,
            "type": self.get_sequence_type(),
            "length": self.length,
            "sequence": self.sequence,
        }
        if self.gc_content is not None:
            result["gc_content"] = round(self.gc_content, 2)
        return result

    def to_markdown(self) -> str:
        """Convert sequence to Markdown format"""
        md = f"### Sequence: {self.id}\n\n"

        if self.description:
            md += f"**Description:** {self.description}\n\n"

        md += f"**Type:** {self.get_sequence_type()}\n\n"
        md += f"**Length:** {self.length} bp/aa\n\n"

        if self.gc_content is not None:
            md += f"**GC Content:** {self.gc_content:.2f}%\n\n"

        md += "**Sequence:**\n\n```\n"
        # Format sequence in blocks of 60 characters
        for i in range(0, len(self.sequence), 60):
            md += self.sequence[i : i + 60] + "\n"
        md += "```\n\n"

        return md


@func_processing_time
async def fasta_parse_main(
    resource_path: str = "",
    save_parsed_content: bool = False,
    output_dir: str = "outputs",
    include_statistics: bool = True,
) -> str:
    """
    Parse FASTA format files and convert to Markdown format.

    FASTA is a text-based format for representing nucleotide or peptide sequences.
    Each sequence begins with a single-line description (header) starting with '>',
    followed by lines of sequence data.

    Features:
    - Parse single or multiple sequences
    - Extract sequence metadata (ID, description, type)
    - Calculate statistics (length, GC content for DNA)
    - Validate sequence format
    - Convert to structured Markdown output

    Args:
        resource_path: Path to FASTA file or URL
        save_parsed_content: Whether to save parsed markdown content to file
        output_dir: Directory where parsed content will be saved
        include_statistics: Whether to include sequence statistics in output

    Returns:
        str: Parsed content in Markdown format with sequence information

    Raises:
        FileNotFoundError: If file not found
        ValueError: If file format is invalid
        Exception: For other parsing errors

    Example:
        >>> content = await fasta_parse_main("sequences.fasta")
        >>> print(content)
        # FASTA Sequence Data
        ...
    """
    local_fasta_path = await process_resource_path(
        resource_path=resource_path,
        output_dir=output_dir if save_parsed_content else None,
    )

    file_path = Path(local_fasta_path)
    file_name = file_path.stem

    logger.info(f"Starting FASTA parsing for: {file_name}")

    try:
        # Parse FASTA file
        sequences = _parse_fasta_file(local_fasta_path)

        if not sequences:
            raise ValueError("No valid FASTA sequences found in file")

        logger.info(f"Successfully parsed {len(sequences)} sequence(s)")

        # Generate Markdown content
        markdown_content = _generate_markdown(
            sequences=sequences,
            file_name=file_name,
            include_statistics=include_statistics,
        )

        # Save if requested
        if save_parsed_content:
            output_path = Path(output_dir) / file_name
            output_path.mkdir(parents=True, exist_ok=True)
            md_file = output_path / f"{file_name}.md"

            with open(md_file, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            logger.info(f"FASTA {file_name} saved to {md_file}")

        return markdown_content

    except Exception as e:
        logger.error(f"Error parsing FASTA file {file_name}: {str(e)}")
        raise


def _parse_fasta_file(file_path: str) -> List[FASTASequence]:
    """
    Parse FASTA file and extract sequences.

    Args:
        file_path: Path to FASTA file

    Returns:
        List of FASTASequence objects

    Raises:
        ValueError: If file format is invalid
    """
    sequences = []
    current_header = None
    current_sequence = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            if not line:  # Skip empty lines
                continue

            if line.startswith(">"):  # Header line
                # Save previous sequence if exists
                if current_header is not None:
                    seq = FASTASequence(current_header, "".join(current_sequence))
                    sequences.append(seq)

                # Start new sequence
                current_header = line[1:].strip()  # Remove '>' prefix
                current_sequence = []

            elif line.startswith(";"):  # Comment line (alternative format)
                continue

            else:  # Sequence line
                if current_header is None:
                    raise ValueError(
                        f"Sequence data found before header at line {line_num}"
                    )
                current_sequence.append(line)

    # Don't forget the last sequence
    if current_header is not None:
        seq = FASTASequence(current_header, "".join(current_sequence))
        sequences.append(seq)

    return sequences


def _generate_markdown(
    sequences: List[FASTASequence],
    file_name: str,
    include_statistics: bool = True,
) -> str:
    """
    Generate Markdown content from parsed sequences.

    Args:
        sequences: List of FASTASequence objects
        file_name: Name of the source file
        include_statistics: Whether to include summary statistics

    Returns:
        Formatted Markdown string
    """
    md = f"# FASTA Sequence Data: {file_name}\n\n"

    # Summary statistics
    if include_statistics:
        md += "## Summary\n\n"
        md += f"**Total Sequences:** {len(sequences)}\n\n"

        total_length = sum(seq.length for seq in sequences)
        md += f"**Total Length:** {total_length:,} bp/aa\n\n"

        # Type distribution
        type_counts = {}
        for seq in sequences:
            seq_type = seq.get_sequence_type()
            type_counts[seq_type] = type_counts.get(seq_type, 0) + 1

        md += "**Sequence Types:**\n\n"
        for seq_type, count in type_counts.items():
            md += f"- {seq_type}: {count}\n"
        md += "\n"

        # Average GC content for DNA sequences
        dna_sequences = [seq for seq in sequences if seq.gc_content is not None]
        if dna_sequences:
            avg_gc = sum(seq.gc_content for seq in dna_sequences) / len(dna_sequences)
            md += f"**Average GC Content (DNA):** {avg_gc:.2f}%\n\n"

        md += "---\n\n"

    # Individual sequences
    md += "## Sequences\n\n"
    for idx, seq in enumerate(sequences, 1):
        md += f"#### [{idx}/{len(sequences)}]\n\n"
        md += seq.to_markdown()
        if idx < len(sequences):
            md += "---\n\n"

    return md
