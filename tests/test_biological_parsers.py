"""
Test cases for biological data parsers (FASTA and GenBank)
"""

import pytest
import tempfile
from pathlib import Path

from markio.parsers.fasta_parser import fasta_parse_main
from markio.parsers.genbank_parser import genbank_parse_main


# Sample FASTA data
SAMPLE_FASTA_DNA = """
>seq1 Human TP53 gene
ATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCTCTGAGTCAGGAAACATTTTCA
GACCTATGGAAACTACTTCCTGAAAACAACGTTCTGTCCCCCTTGCCGTCCCAAGCAATG
>seq2 Mouse TP53 gene
ATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCTCTGAGTCAGGAAACATTTTCA
""".strip()

SAMPLE_FASTA_PROTEIN = """
>protein1 Example protein sequence
MTEYKLVVVGAGGVGKSALTIQLIQNHFVDEYDPTIEDSYRKQVVIDGETCLLDILDTAG
QEEYSAMRDQYMRTGEGFLCVFAINNTKSFEDIHHYREQIKRVKDSEDVPMVLVGNKCDL
""".strip()

# Sample GenBank data
SAMPLE_GENBANK = """
LOCUS       TEST_SEQ                 180 bp    DNA     linear   BCT 01-JAN-2024
DEFINITION  Test sequence for parser validation.
ACCESSION   TEST001
VERSION     TEST001.1
KEYWORDS    test; validation.
SOURCE      Test organism
  ORGANISM  Test organism
            Bacteria; Test.
FEATURES             Location/Qualifiers
     source          1..180
                     /organism="Test organism"
                     /mol_type="genomic DNA"
     gene            10..170
                     /gene="testA"
                     /note="test gene A"
ORIGIN
        1 atggaggagc cgcagtcaga tcctagcgtc gagccccctc tgagtcagga aacattttca
       61 gacctatgga aactacttcc tgaaaacaac gttctgtccc ccttgccgtc ccaagcaatg
      121 gatgatttga tgctgtcccc ggacgatatt gaacaatggt tcactgaaga cccaggtcca
//
""".strip()


@pytest.fixture
def temp_fasta_file():
    """Create a temporary FASTA file for testing"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False) as f:
        f.write(SAMPLE_FASTA_DNA)
        temp_path = f.name
    yield temp_path
    Path(temp_path).unlink()


@pytest.fixture
def temp_protein_fasta_file():
    """Create a temporary protein FASTA file for testing"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".faa", delete=False) as f:
        f.write(SAMPLE_FASTA_PROTEIN)
        temp_path = f.name
    yield temp_path
    Path(temp_path).unlink()


@pytest.fixture
def temp_genbank_file():
    """Create a temporary GenBank file for testing"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".gb", delete=False) as f:
        f.write(SAMPLE_GENBANK)
        temp_path = f.name
    yield temp_path
    Path(temp_path).unlink()


class TestFASTAParser:
    """Test cases for FASTA parser"""

    @pytest.mark.asyncio
    async def test_parse_dna_fasta(self, temp_fasta_file):
        """Test parsing DNA FASTA file"""
        content = await fasta_parse_main(
            resource_path=temp_fasta_file,
            save_parsed_content=False,
            include_statistics=True,
        )

        assert content is not None
        assert "FASTA Sequence Data" in content
        assert "seq1" in content
        assert "seq2" in content
        assert "DNA" in content
        assert "GC Content" in content

    @pytest.mark.asyncio
    async def test_parse_protein_fasta(self, temp_protein_fasta_file):
        """Test parsing protein FASTA file"""
        content = await fasta_parse_main(
            resource_path=temp_protein_fasta_file,
            save_parsed_content=False,
            include_statistics=True,
        )

        assert content is not None
        assert "protein1" in content
        assert "Protein" in content
        # Protein sequences should not have GC content
        assert content.count("GC Content") == 0 or "N/A" in content

    @pytest.mark.asyncio
    async def test_fasta_with_save(self, temp_fasta_file):
        """Test FASTA parsing with file saving"""
        with tempfile.TemporaryDirectory() as temp_dir:
            content = await fasta_parse_main(
                resource_path=temp_fasta_file,
                save_parsed_content=True,
                output_dir=temp_dir,
                include_statistics=True,
            )

            assert content is not None
            # Check if output directory was created
            output_files = list(Path(temp_dir).rglob("*.md"))
            assert len(output_files) > 0

    @pytest.mark.asyncio
    async def test_fasta_statistics(self, temp_fasta_file):
        """Test FASTA statistics calculation"""
        content = await fasta_parse_main(
            resource_path=temp_fasta_file,
            save_parsed_content=False,
            include_statistics=True,
        )

        assert "Summary" in content
        assert "Total Sequences:" in content
        assert "Total Length:" in content
        assert "Sequence Types:" in content

    @pytest.mark.asyncio
    async def test_empty_fasta_file(self):
        """Test parsing empty FASTA file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False) as f:
            f.write("")  # Empty file
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="No valid FASTA sequences"):
                await fasta_parse_main(
                    resource_path=temp_path, save_parsed_content=False
                )
        finally:
            Path(temp_path).unlink()


class TestGenBankParser:
    """Test cases for GenBank parser"""

    @pytest.mark.asyncio
    async def test_parse_genbank(self, temp_genbank_file):
        """Test parsing GenBank file"""
        content = await genbank_parse_main(
            resource_path=temp_genbank_file,
            save_parsed_content=False,
            include_features=True,
            include_sequence=True,
        )

        assert content is not None
        assert "GenBank Records" in content
        assert "TEST_SEQ" in content
        assert "ACCESSION" in content
        assert "TEST001" in content

    @pytest.mark.asyncio
    async def test_genbank_with_features(self, temp_genbank_file):
        """Test GenBank parsing with features"""
        content = await genbank_parse_main(
            resource_path=temp_genbank_file,
            save_parsed_content=False,
            include_features=True,
            include_sequence=False,
        )

        assert "Features" in content
        assert "gene" in content
        assert "testA" in content
        # Should not include sequence when include_sequence=False
        # (but might show length/stats)

    @pytest.mark.asyncio
    async def test_genbank_without_features(self, temp_genbank_file):
        """Test GenBank parsing without features"""
        content = await genbank_parse_main(
            resource_path=temp_genbank_file,
            save_parsed_content=False,
            include_features=False,
            include_sequence=True,
        )

        assert content is not None
        assert "TEST_SEQ" in content
        # Features table should be minimal or absent

    @pytest.mark.asyncio
    async def test_genbank_with_save(self, temp_genbank_file):
        """Test GenBank parsing with file saving"""
        with tempfile.TemporaryDirectory() as temp_dir:
            content = await genbank_parse_main(
                resource_path=temp_genbank_file,
                save_parsed_content=True,
                output_dir=temp_dir,
                include_features=True,
                include_sequence=True,
            )

            assert content is not None
            # Check if output directory was created
            output_files = list(Path(temp_dir).rglob("*.md"))
            assert len(output_files) > 0

    @pytest.mark.asyncio
    async def test_genbank_sequence_stats(self, temp_genbank_file):
        """Test GenBank sequence statistics"""
        content = await genbank_parse_main(
            resource_path=temp_genbank_file,
            save_parsed_content=False,
            include_features=True,
            include_sequence=True,
        )

        assert "Summary" in content
        assert "Total Records:" in content
        # GC content should be calculated
        assert "GC Content" in content

    @pytest.mark.asyncio
    async def test_empty_genbank_file(self):
        """Test parsing empty GenBank file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gb", delete=False) as f:
            f.write("")  # Empty file
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="No valid GenBank records"):
                await genbank_parse_main(
                    resource_path=temp_path, save_parsed_content=False
                )
        finally:
            Path(temp_path).unlink()


class TestBiologicalParserIntegration:
    """Integration tests for biological parsers"""

    @pytest.mark.asyncio
    async def test_multiple_format_parsing(self, temp_fasta_file, temp_genbank_file):
        """Test parsing both FASTA and GenBank in sequence"""
        # Parse FASTA
        fasta_content = await fasta_parse_main(
            resource_path=temp_fasta_file, save_parsed_content=False
        )
        assert fasta_content is not None

        # Parse GenBank
        genbank_content = await genbank_parse_main(
            resource_path=temp_genbank_file, save_parsed_content=False
        )
        assert genbank_content is not None

        # Both should have distinct markers
        assert "FASTA" in fasta_content
        assert "GenBank" in genbank_content

    @pytest.mark.asyncio
    async def test_output_consistency(self, temp_fasta_file):
        """Test output format consistency"""
        content = await fasta_parse_main(
            resource_path=temp_fasta_file, save_parsed_content=False
        )

        # Check Markdown structure
        assert content.startswith("#")  # Should have header
        assert "##" in content or "###" in content  # Should have subheaders
        assert "```" in content  # Should have code blocks for sequences


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
