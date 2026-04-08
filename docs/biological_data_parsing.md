# Biological Data Parsing Guide

[Back to README](../README.md) | [中文版本](biological_data_parsing_zh.md)

## Current Status

Markio includes biological sequence parsing for:

- FASTA
- GenBank

BioPython is part of the default dependency set in the current project configuration, so these parsers run with the richer analysis path by default unless your environment is unusually constrained.

## API Surface

Dedicated endpoints:

- `POST /v1/parse_fasta_file`
- `POST /v1/parse_genbank_file`

These formats are **not** auto-dispatched through `/v1/parse_file`.

All `/v1/*` routes require:

- `Authorization: Bearer <JWT>`

## Parser Modules

Local parser entrypoints:

- `markio.parsers.fasta_parser.fasta_parse_main`
- `markio.parsers.genbank_parser.genbank_parse_main`

There is currently no first-class `MarkioSDK` façade method or CLI subcommand for these biological formats.

## FASTA

Supported extensions:

- `.fasta`
- `.fa`
- `.fna`
- `.faa`
- `.ffn`
- `.fsa`
- `.fas`
- `.txt`

Capabilities:

- single or multi-sequence parsing
- sequence type detection
- sequence statistics
- GC content for DNA-like sequences
- Markdown output suitable for review or downstream processing

FASTA-specific request option:

- `include_statistics`

## GenBank

Supported extensions:

- `.gb`
- `.gbk`
- `.genbank`
- `.gbff`
- `.txt`

Capabilities:

- record-level metadata extraction
- feature table extraction
- sequence inclusion control
- Markdown output with annotations and sequence content

GenBank-specific request options:

- `include_features`
- `include_sequence`

## REST API Examples

### FASTA

```bash
curl -X POST "http://localhost:8000/v1/parse_fasta_file" \
  -H "Authorization: Bearer <YOUR_JWT>" \
  -F "file=@./sample.fasta" \
  -F "include_statistics=true"
```

### GenBank

```bash
curl -X POST "http://localhost:8000/v1/parse_genbank_file" \
  -H "Authorization: Bearer <YOUR_JWT>" \
  -F "file=@./sample.gb" \
  -F "include_features=true" \
  -F "include_sequence=true"
```

## Local Python Examples

```python
import asyncio
from markio.parsers.fasta_parser import fasta_parse_main
from markio.parsers.genbank_parser import genbank_parse_main

async def main():
    fasta_markdown = await fasta_parse_main(
        resource_path="sample.fasta",
        save_parsed_content=True,
        output_dir="outputs",
        include_statistics=True,
    )

    genbank_markdown = await genbank_parse_main(
        resource_path="sample.gb",
        save_parsed_content=True,
        output_dir="outputs",
        include_features=True,
        include_sequence=True,
    )

    print(fasta_markdown[:200])
    print(genbank_markdown[:200])

asyncio.run(main())
```

## Output Shape

### FASTA output generally includes

- overall sequence counts
- sequence metadata
- per-sequence length and type hints
- GC content where applicable

### GenBank output generally includes

- record metadata
- source and organism information
- feature annotations when enabled
- sequence data when enabled

## Testing

Relevant regression coverage:

- `tests/test_biological_parsers.py`
- `tests/test_parser_route_security.py`

## Known Boundaries

- no auto-dispatch through `/v1/parse_file`
- no SDK façade methods yet
- no CLI subcommands yet
