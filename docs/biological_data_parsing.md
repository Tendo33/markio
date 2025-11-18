# Biological Data Parsing Guide

Markio now supports parsing of biological sequence data formats commonly used in bioinformatics and genomics research. This feature allows you to convert FASTA and GenBank format files into structured, readable Markdown documents.

## 🔬 BioPython Integration

Markio includes **BioPython by default** for enhanced biological sequence analysis capabilities:

### Features Included
- ✅ Parse FASTA and GenBank files
- ✅ Advanced sequence statistics
- ✅ Precise GC content calculation (DNA)
- ✅ Intelligent sequence type detection
- ✅ **Protein properties analysis:**
  - Molecular weight
  - Isoelectric point (pI)
  - Aromaticity
  - Instability index
  - GRAVY (hydropathy)
- ✅ **Enhanced GenBank parsing** with accurate feature extraction
- ✅ **Precise calculations** using BioPython's algorithms

### Installation

BioPython is included in the default installation:
```bash
pip install markio
```

All biological data analysis features are available immediately after installation. No additional setup required!

## Supported Formats

### 1. FASTA Format

FASTA is a text-based format for representing nucleotide or peptide sequences. It's one of the most widely used formats in bioinformatics.

**Supported File Extensions:**
- `.fasta` - Standard FASTA
- `.fa` - Short form
- `.fna` - FASTA nucleic acid
- `.faa` - FASTA amino acid
- `.ffn` - FASTA nucleotide coding regions
- `.fsa` - FASTA sequence alignment
- `.fas` - Alternative
- `.txt` - Plain text

**Features:**
- Parse single or multiple sequences
- Automatic sequence type detection (DNA, Protein, Unknown)
- Calculate sequence statistics:
  - Sequence length
  - GC content (for DNA sequences)
  - Type distribution
- Format sequences in readable blocks
- Extract metadata (ID, description)

**Example FASTA File:**
```
>NM_000546.6 Homo sapiens tumor protein p53 (TP53), transcript variant 1
ATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCTCTGAGTCAGGAAACATTTTCA
GACCTATGGAAACTACTTCCTGAAAACAACGTTCTGTCCCCCTTGCCGTCCCAAGCAATG
GATGATTTGATGCTGTCCCCGGACGATATTGAACAATGGTTCACTGAAGACCCAGGTCCA
>NM_001126112.3 Homo sapiens tumor protein p53 (TP53), transcript variant 2
ATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCTCTGAGTCAGGAAACATTTTCA
GACCTATGGAAACTACTTCCTGAAAACAACGTTCTGTCCCCCTTGCCGTCCCAAGCAATG
```

### 2. GenBank Format

GenBank is a comprehensive database format used by NCBI that includes both sequence data and extensive biological annotations.

**Supported File Extensions:**
- `.gb` - Standard GenBank
- `.gbk` - GenBank
- `.genbank` - Full name
- `.gbff` - GenBank flat file
- `.txt` - Plain text

**Features:**
- Parse complete GenBank records
- Extract metadata:
  - LOCUS information (name, length, molecule type, date)
  - DEFINITION (description)
  - ACCESSION number
  - VERSION
  - SOURCE and ORGANISM
- Parse feature tables with:
  - Feature types (CDS, gene, mRNA, etc.)
  - Locations and coordinates
  - Qualifiers (annotations)
- Extract sequence data
- Calculate GC content
- Support multiple records per file

**Example GenBank File:**
```
LOCUS       NM_000546              1182 bp    mRNA    linear   PRI 05-JAN-2024
DEFINITION  Homo sapiens tumor protein p53 (TP53), transcript variant 1.
ACCESSION   NM_000546
VERSION     NM_000546.6
KEYWORDS    RefSeq; MANE Select.
SOURCE      Homo sapiens (human)
  ORGANISM  Homo sapiens
            Eukaryota; Metazoa; Chordata; Craniata; Vertebrata; Euteleostomi;
            Mammalia; Eutheria; Euarchontoglires; Primates; Haplorrhini;
            Catarrhini; Hominidae; Homo.
FEATURES             Location/Qualifiers
     source          1..1182
                     /organism="Homo sapiens"
                     /mol_type="mRNA"
     gene            1..1182
                     /gene="TP53"
                     /gene_synonym="P53; TRP53"
ORIGIN
        1 atggaggagc cgcagtcaga tcctagcgtc gagccccctc tgagtcagga aacattttca
       61 gacctatgga aactacttcc tgaaaacaac gttctgtccc ccttgccgtc ccaagcaatg
//
```

## Usage

### REST API

#### Parse FASTA File

**Endpoint:** `POST /v1/parse_fasta_file`

**Parameters:**
- `file` (UploadFile): FASTA file to parse
- `save_parsed_content` (bool): Save output to disk (default: false)
- `output_dir` (str): Output directory (default: "outputs")
- `include_statistics` (bool): Include sequence statistics (default: true)

**Example:**
```python
import httpx
import asyncio

async def parse_fasta():
    async with httpx.AsyncClient() as client:
        files = {"file": open("sequences.fasta", "rb")}
        data = {
            "save_parsed_content": "true",
            "include_statistics": "true"
        }
        resp = await client.post(
            "http://localhost:8000/v1/parse_fasta_file",
            files=files,
            data=data
        )
        result = resp.json()
        print(result['parsed_content'])
        return result

asyncio.run(parse_fasta())
```

#### Parse GenBank File

**Endpoint:** `POST /v1/parse_genbank_file`

**Parameters:**
- `file` (UploadFile): GenBank file to parse
- `save_parsed_content` (bool): Save output to disk (default: false)
- `output_dir` (str): Output directory (default: "outputs")
- `include_features` (bool): Include feature table (default: true)
- `include_sequence` (bool): Include sequence data (default: true)

**Example:**
```python
import httpx
import asyncio

async def parse_genbank():
    async with httpx.AsyncClient() as client:
        files = {"file": open("sequence.gb", "rb")}
        data = {
            "save_parsed_content": "true",
            "include_features": "true",
            "include_sequence": "true"
        }
        resp = await client.post(
            "http://localhost:8000/v1/parse_genbank_file",
            files=files,
            data=data
        )
        result = resp.json()
        print(result['parsed_content'])
        return result

asyncio.run(parse_genbank())
```

### Python SDK

```python
from markio.parsers.fasta_parser import fasta_parse_main
from markio.parsers.genbank_parser import genbank_parse_main
import asyncio

async def main():
    # Parse FASTA file
    fasta_content = await fasta_parse_main(
        resource_path="sequences.fasta",
        save_parsed_content=True,
        output_dir="./outputs",
        include_statistics=True
    )
    print("FASTA parsed successfully")
    
    # Parse GenBank file
    genbank_content = await genbank_parse_main(
        resource_path="sequence.gb",
        save_parsed_content=True,
        output_dir="./outputs",
        include_features=True,
        include_sequence=True
    )
    print("GenBank parsed successfully")

asyncio.run(main())
```

## Output Format

### FASTA Output

The parser generates structured Markdown with:
- **Summary section** with statistics:
  - Total number of sequences
  - Total sequence length
  - Sequence type distribution
  - Average GC content (for DNA)
- **Individual sequences** with:
  - Sequence ID and description
  - Detected type (DNA/Protein/Unknown)
  - Length
  - GC content (for DNA)
  - Formatted sequence (60 characters per line)

### GenBank Output

The parser generates structured Markdown with:
- **Summary section**:
  - Total number of records
  - Total sequence length
- **Individual records** with:
  - Basic information (LOCUS, DEFINITION, ACCESSION, VERSION)
  - Source information (organism, taxonomy)
  - Feature table (formatted as Markdown table)
  - Sequence data with line numbers
  - GC content

## Use Cases

### Research Applications
- **Sequence analysis**: Convert raw sequence files to readable format
- **Documentation**: Create human-readable documentation for genetic sequences
- **Data pipeline**: Integrate with bioinformatics workflows
- **Archival**: Convert sequence databases to searchable Markdown

### Bioinformatics Workflows
- **Quality control**: Review sequence data before analysis
- **Collaboration**: Share formatted sequence data with colleagues
- **Publication**: Prepare sequence data for papers and reports
- **Teaching**: Create educational materials from real sequence data

## Technical Details

### Sequence Type Detection

**DNA Sequences:**
- Contains only A, T, G, C, N characters
- GC content is calculated automatically using BioPython

**Protein Sequences:**
- Contains standard amino acid codes (ACDEFGHIKLMNPQRSTVWY)
- Comprehensive properties analysis with BioPython

**Unknown:**
- Contains other characters or mixed types

### Performance

- **FASTA**: Optimized for large multi-sequence files with BioPython
- **GenBank**: Handles complex annotations efficiently
- **Memory**: Streaming approach for large files
- **Speed**: Fast parsing with BioPython optimizations
- **Accuracy**: BioPython ensures precise biological calculations

### Error Handling

The parsers include comprehensive error handling with BioPython validation:
- File format validation
- Invalid sequence detection
- Missing header handling
- Corrupted file detection
- Sequence integrity verification

## Examples

### Example 1: Parse Multiple FASTA Sequences

```python
# sequences.fasta contains multiple DNA sequences
content = await fasta_parse_main(
    resource_path="sequences.fasta",
    include_statistics=True
)

# Output includes:
# - Summary of all sequences
# - Individual sequence details
# - Statistics (GC content, lengths, types)
```

### Example 2: Parse GenBank with Features Only

```python
# sequence.gb contains annotated gene
content = await genbank_parse_main(
    resource_path="sequence.gb",
    include_features=True,
    include_sequence=False  # Skip sequence data
)

# Output includes:
# - Metadata (LOCUS, ACCESSION, etc.)
# - Feature table
# - No sequence data (useful for annotation review)
```

### Example 3: Batch Processing

```python
import os
from pathlib import Path

async def batch_parse_fasta(directory: str):
    """Parse all FASTA files in a directory"""
    fasta_files = Path(directory).glob("*.fasta")
    
    for fasta_file in fasta_files:
        try:
            content = await fasta_parse_main(
                resource_path=str(fasta_file),
                save_parsed_content=True,
                output_dir="./parsed_sequences"
            )
            print(f"✓ Parsed: {fasta_file.name}")
        except Exception as e:
            print(f"✗ Error parsing {fasta_file.name}: {e}")

# Run batch processing
asyncio.run(batch_parse_fasta("./raw_sequences"))
```

## Integration with Other Markio Features

Biological data parsing integrates seamlessly with other Markio features:

- **MCP Protocol**: Access via Claude Desktop or other MCP clients
- **Docker**: Use in containerized environments
- **REST API**: Standard HTTP endpoints like other parsers
- **Batch Processing**: Process multiple files efficiently
- **Output Management**: Consistent file organization

## Troubleshooting

### Common Issues

**Issue: "No valid FASTA sequences found"**
- Check file format (should start with '>')
- Verify file encoding (UTF-8 recommended)
- Ensure sequences are not empty

**Issue: "Invalid GenBank format"**
- Verify file starts with "LOCUS"
- Check for complete record (ends with "//")
- Ensure file is not truncated

**Issue: File extension not recognized**
- Use supported extensions or rename file
- Check file content type matches extension

**Issue: BioPython import errors**
- BioPython is included by default with Markio
- If you see import errors, try reinstalling: `pip install --upgrade markio`

### Getting Help

- Check API documentation: `http://localhost:8000/docs`
- Review example files in test directory
- Open GitHub issue for bugs or feature requests

## Future Enhancements

Planned improvements for biological data parsing:

- [ ] Support for additional formats (FASTQ, SAM/BAM)
- [ ] Sequence alignment visualization
- [ ] Quality score parsing (for FASTQ)
- [ ] Phylogenetic tree parsing (Newick format)
- [ ] BLAST output parsing
- [ ] Integration with biological databases (NCBI, UniProt)

---

**Note:** Markio includes BioPython for enhanced biological data parsing capabilities. This feature is designed to provide professional-grade sequence analysis while maintaining ease of use. For specialized workflows, Markio's BioPython integration can be used alongside other bioinformatics tools like BLAST, Clustal, and more.

