# Benchmark Intelligence Agent

An AI-powered agent that automatically discovers, extracts, classifies, and tracks trending benchmarks from Hugging Face model cards.

## Overview

The Benchmark Intelligence Agent monitors the latest trending models on Hugging Face, extracts benchmark results from their model cards, classifies benchmarks using a comprehensive taxonomy, and generates consolidated reports. This enables continuous tracking of which benchmarks are most commonly used in the AI community.

### Key Features

- **Automated Discovery**: Fetches trending models from Hugging Face
- **Intelligent Extraction**: Uses Claude AI to parse model cards and extract benchmark results
- **Multi-label Classification**: Categorizes benchmarks across 13 primary categories
- **Comprehensive Taxonomy**: Supports secondary attributes, modalities, and difficulty levels
- **Caching System**: Efficient caching to minimize API calls and redundant processing
- **Scheduled Execution**: Can run as a cron job for continuous monitoring
- **Flexible Architecture**: Supports both API and MCP client modes

## Installation

### Prerequisites

- Python 3.8 or higher
- Anthropic API key (for Claude AI)
- Internet connection (for Hugging Face API access)

### Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure authentication**:
   Create `agents/benchmark_intelligence/config/auth.yaml` based on the example:
   ```bash
   cp agents/benchmark_intelligence/config/auth.yaml.example \
      agents/benchmark_intelligence/config/auth.yaml
   ```

   Edit `auth.yaml` and add your Anthropic API key:
   ```yaml
   anthropic:
     api_key: "your-api-key-here"
   ```

3. **Verify installation**:
   ```python
   from agents.benchmark_intelligence.tools import discover_models
   models = discover_models.get_trending_models(limit=5)
   print(f"Found {len(models)} trending models")
   ```

## Configuration

### Authentication (`config/auth.yaml`)

Configure API credentials for external services:

```yaml
# Anthropic API (required for classification)
anthropic:
  api_key: "sk-ant-..."

# Optional: Hugging Face token (for private models)
huggingface:
  token: "hf_..."
```

### Lab Configuration (`config/labs.yaml`)

Configure AI lab providers to track:

```yaml
labs:
  - name: "Anthropic"
    pattern: "anthropic|claude"
  - name: "OpenAI"
    pattern: "openai|gpt"
  - name: "Meta"
    pattern: "meta|llama"
  # ... additional labs
```

### Taxonomy (`config/categories.yaml`)

Defines the 13 primary categories and secondary attributes. See [Categories](#categories) section.

### Benchmark Taxonomy (`config/benchmark_taxonomy.md`)

Comprehensive reference of 100+ common benchmarks with descriptions, variations, and patterns.

## Usage

### Manual Execution

#### 1. Discover Trending Models

```python
from agents.benchmark_intelligence.tools.discover_models import get_trending_models

# Fetch top 50 trending models
models = get_trending_models(limit=50)

for model in models:
    print(f"{model['id']}: {model['downloads']} downloads")
```

#### 2. Parse Model Card

```python
from agents.benchmark_intelligence.tools.parse_model_card import parse_model_card

# Parse a specific model card
result = parse_model_card("meta-llama/Llama-3.3-70B-Instruct")

print(f"Found {len(result.get('benchmarks', []))} benchmarks")
```

#### 3. Extract Benchmarks

```python
from agents.benchmark_intelligence.tools.extract_benchmarks import extract_benchmarks_from_card

# Extract benchmarks using Claude AI
model_card_text = "..."  # Your model card content
benchmarks = extract_benchmarks_from_card(model_card_text)

for benchmark in benchmarks:
    print(f"{benchmark['canonical_name']}: {benchmark['score']}")
```

#### 4. Classify Benchmarks

```python
from agents.benchmark_intelligence.tools.classify import classify_benchmark

# Classify a single benchmark
result = classify_benchmark(
    benchmark_name="MMLU",
    description="57 academic subjects covering knowledge"
)

print(f"Categories: {[cat['category'] for cat in result['primary_categories']]}")
print(f"Modality: {result['modality']}")
print(f"Confidence: {result['metadata']['confidence_overall']:.2f}")
```

#### 5. Generate Consolidated Report

```python
from agents.benchmark_intelligence.tools.consolidate import consolidate_benchmarks

# Process all trending models and generate report
report = consolidate_benchmarks(
    model_limit=50,
    output_dir="reports/",
    classify=True
)

print(f"Processed {report['total_models']} models")
print(f"Found {report['total_benchmarks']} unique benchmarks")
```

### Scheduled Execution

Set up a cron job for automated daily/weekly runs:

```bash
# Daily at 2 AM
0 2 * * * cd /path/to/trending_benchmarks && python -m agents.benchmark_intelligence.tools.consolidate --output reports/daily

# Weekly on Monday at 1 AM
0 1 * * 1 cd /path/to/trending_benchmarks && python -m agents.benchmark_intelligence.tools.consolidate --output reports/weekly --limit 100
```

### Command-Line Interface

Run the consolidation tool directly:

```bash
# Basic usage - process top 50 models
python -m agents.benchmark_intelligence.tools.consolidate

# Custom options
python -m agents.benchmark_intelligence.tools.consolidate \
  --limit 100 \
  --output reports/custom \
  --classify \
  --no-cache

# Help
python -m agents.benchmark_intelligence.tools.consolidate --help
```

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Benchmark Intelligence Agent               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Flow Pipeline                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐      ┌──────────────┐      ┌────────────┐ │
│  │  Discover   │─────▶│    Parse     │─────▶│  Extract   │ │
│  │   Models    │      │  Model Card  │      │ Benchmarks │ │
│  └─────────────┘      └──────────────┘      └────────────┘ │
│        │                     │                      │        │
│        │                     │                      │        │
│        ▼                     ▼                      ▼        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Cache Layer (SQLite)                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                              │                              │
│                              ▼                              │
│  ┌─────────────┐      ┌──────────────┐      ┌────────────┐ │
│  │  Classify   │─────▶│ Consolidate  │─────▶│   Report   │ │
│  │ Benchmarks  │      │    Data      │      │ Generation │ │
│  └─────────────┘      └──────────────┘      └────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
         │                      │                      │
         ▼                      ▼                      ▼
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│ Hugging Face │     │   Claude AI      │     │    Reports   │
│     API      │     │  (Anthropic)     │     │  (JSON/CSV)  │
└──────────────┘     └──────────────────┘     └──────────────┘
```

### Component Overview

#### 1. **Discovery Layer** (`tools/discover_models.py`)
- Fetches trending models from Hugging Face
- Filters by downloads, recency, and relevance
- Supports pagination and custom queries

#### 2. **Parsing Layer** (`tools/parse_model_card.py`)
- Downloads and parses model card markdown
- Extracts metadata (downloads, likes, tags)
- Preprocesses text for extraction

#### 3. **Extraction Layer** (`tools/extract_benchmarks.py`)
- Uses Claude AI with structured prompts
- Extracts benchmark names, scores, and metadata
- Handles various naming conventions and formats
- Normalizes benchmark names using taxonomy

#### 4. **Classification Layer** (`tools/classify.py`)
- Multi-label classification using Claude AI
- Assigns 1-13 primary categories per benchmark
- Adds secondary attributes and modality
- Provides confidence scores and reasoning

#### 5. **Cache Layer** (`tools/cache.py`)
- SQLite-based persistent caching
- Caches model cards, extractions, classifications
- Prevents redundant API calls
- Supports cache invalidation and updates

#### 6. **Consolidation Layer** (`tools/consolidate.py`)
- Aggregates data across all models
- Deduplicates benchmarks
- Generates summary statistics
- Produces JSON/CSV reports

#### 7. **Client Layer** (`clients/`)
- `api_client.py`: Direct Anthropic API client
- `mcp_client.py`: MCP protocol client
- `factory.py`: Client factory with fallback logic
- Supports multiple AI providers

### Data Flow

1. **Input**: Hugging Face trending models list
2. **Fetch**: Download model cards (with caching)
3. **Extract**: Use Claude to parse benchmark results
4. **Classify**: Categorize benchmarks using taxonomy
5. **Consolidate**: Aggregate and deduplicate results
6. **Output**: Generate reports (JSON, CSV, markdown)

### Caching Strategy

The agent uses multi-level caching to optimize performance:

- **Model Card Cache**: Stores raw model card content (TTL: 7 days)
- **Extraction Cache**: Stores extracted benchmarks (TTL: 14 days)
- **Classification Cache**: Stores classification results (TTL: 30 days)

Cache keys are generated from content hashes to ensure consistency.

## Categories

### Primary Categories (Multi-label)

The taxonomy includes 13 primary categories. Benchmarks can belong to multiple categories:

1. **Knowledge**: Factual knowledge, general understanding (MMLU, TriviaQA)
2. **Reasoning**: Logical reasoning, commonsense (ARC, HellaSwag, PIQA)
3. **Math**: Mathematical problem solving (GSM8K, MATH, AIME)
4. **Code**: Programming, software engineering (HumanEval, SWE-bench)
5. **Vision**: Visual understanding, VQA (MMMU, DocVQA)
6. **Audio**: Speech recognition, audio processing (LibriSpeech)
7. **Multilingual**: Cross-lingual evaluation (FLORES, Belebele, C-Eval)
8. **Safety**: Truthfulness, bias, toxicity (TruthfulQA, ToxiGen)
9. **Long-Context**: Tasks requiring >4K tokens (LongBench, RULER)
10. **Instruction-Following**: Complex instructions (IFEval, MT-Bench)
11. **Tool-Use**: Function calling, API usage (BFCL)
12. **Agent**: Interactive, autonomous tasks (WebArena, OSWorld)
13. **Domain-Specific**: Medical, legal, finance, science (LegalBench, MedQA)

### Secondary Attributes

Additional characteristics that enhance classification:

- **OCR/Text**: Reading text from images (DocVQA, OCRBench)
- **Spatial**: Spatial reasoning (RefCOCO, CountBench)
- **Medical**: Healthcare domain (SLAKE, PMC-VQA)
- **Video**: Temporal video understanding (VideoMME, MLVU)
- **Document**: Document processing (OmniDocBench)
- **Competition**: Real competition-based (AIME, IMO)
- **Contamination-Free**: Continuously updated (LiveCodeBench)
- **Real-World**: Real-world tasks (SWE-bench, WebArena)
- **STEM**: Science/Tech/Engineering/Math focus
- **Multimodal**: Multiple modalities (vision+text, etc.)

### Modalities

Base modalities for benchmarks:

- `text`: Text-only LLM tasks
- `vision`: Image/visual understanding
- `audio`: Speech/audio processing
- `multimodal`: Combination of modalities

### Difficulty Levels

- **Introductory**: Basic tasks, high baseline scores
- **Intermediate**: Standard evaluation, moderate difficulty
- **Advanced**: Challenging tasks, low baseline scores
- **Expert**: Competition-level, specialized expertise

## Output Format

### Consolidated Report (JSON)

```json
{
  "metadata": {
    "timestamp": "2026-04-02T10:30:00Z",
    "model_count": 50,
    "benchmark_count": 127,
    "version": "1.0"
  },
  "benchmarks": [
    {
      "canonical_name": "MMLU",
      "frequency": 45,
      "categories": ["Knowledge"],
      "modality": ["text"],
      "models": [
        {
          "model_id": "meta-llama/Llama-3.3-70B-Instruct",
          "score": 86.5,
          "metric": "accuracy",
          "context": "5-shot"
        }
      ]
    }
  ],
  "statistics": {
    "top_benchmarks": ["MMLU", "GSM8K", "HumanEval"],
    "category_distribution": {
      "Knowledge": 38,
      "Math": 24,
      "Code": 19
    }
  }
}
```

### Summary Statistics

- **Benchmark Frequency**: How often each benchmark appears
- **Category Distribution**: Breakdown by primary category
- **Lab Adoption**: Which labs use which benchmarks
- **Trending Benchmarks**: Recently emerging benchmarks
- **Score Distributions**: Statistical analysis of scores

## Troubleshooting

### Common Issues

#### 1. API Key Errors

```
Error: Anthropic API key not found
```

**Solution**: Ensure `config/auth.yaml` contains valid API key:
```yaml
anthropic:
  api_key: "sk-ant-..."
```

#### 2. Rate Limiting

```
Error: Rate limit exceeded
```

**Solution**: The agent automatically handles rate limits with exponential backoff. If issues persist:
- Reduce batch size
- Increase delay between requests
- Use caching to minimize API calls

#### 3. Model Card Parsing Failures

```
Warning: Failed to parse model card for model-id
```

**Solution**:
- Check model exists on Hugging Face
- Verify model card is publicly accessible
- Some models may have non-standard formatting

#### 4. Classification Errors

```
Error: Failed to classify benchmark
```

**Solution**:
- Check Claude API is accessible
- Verify benchmark name/description is valid
- Review classification prompt in `prompts/classify.md`

#### 5. Cache Corruption

```
Error: Database is locked
```

**Solution**:
```bash
# Clear cache and rebuild
rm -rf cache/*.db
python -m agents.benchmark_intelligence.tools.consolidate --no-cache
```

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or set environment variable:
```bash
export LOG_LEVEL=DEBUG
python -m agents.benchmark_intelligence.tools.consolidate
```

### Performance Optimization

1. **Use Caching**: Always enable cache unless explicitly testing
2. **Batch Processing**: Process models in batches to handle rate limits
3. **Parallel Requests**: Use async clients for concurrent processing
4. **Filter Early**: Apply filters at discovery stage to reduce processing
5. **Incremental Updates**: Only process new models since last run

### Data Quality Issues

#### Missing Benchmarks

Some models may not report benchmarks in standard format. The agent uses AI extraction to handle variations, but edge cases may occur.

**Mitigation**:
- Review extraction prompts in `prompts/` directory
- Add benchmark patterns to taxonomy
- Manually verify high-profile models

#### Incorrect Classification

Classification uses AI and may occasionally misclassify benchmarks.

**Mitigation**:
- Review confidence scores (low confidence may indicate uncertainty)
- Manually verify critical classifications
- Provide feedback to improve prompts

## Development

### Project Structure

```
agents/benchmark_intelligence/
├── README.md                    # This file
├── config/
│   ├── auth.yaml.example       # Authentication template
│   ├── auth.yaml              # Authentication (gitignored)
│   ├── categories.yaml        # Taxonomy definition
│   ├── labs.yaml             # AI lab configuration
│   └── benchmark_taxonomy.md # Reference documentation
├── prompts/
│   ├── classify.md           # Classification prompt
│   └── extract.md           # Extraction prompt
├── clients/
│   ├── __init__.py
│   ├── base.py              # Base client interface
│   ├── api_client.py        # Anthropic API client
│   ├── mcp_client.py        # MCP client
│   └── factory.py           # Client factory
└── tools/
    ├── __init__.py
    ├── discover_models.py   # Model discovery
    ├── parse_model_card.py  # Card parsing
    ├── extract_benchmarks.py # Benchmark extraction
    ├── classify.py          # Classification
    ├── consolidate.py       # Aggregation
    ├── cache.py            # Caching layer
    ├── fetch_docs.py       # Documentation fetching
    └── _claude_client.py   # Claude API wrapper
```

### Adding New Categories

1. Edit `config/categories.yaml`
2. Add category definition with keywords and examples
3. Update classification prompt in `prompts/classify.md`
4. Test with sample benchmarks

### Extending Extraction

1. Review `prompts/extract.md` for extraction instructions
2. Add benchmark patterns to `config/benchmark_taxonomy.md`
3. Test with diverse model cards
4. Update confidence thresholds if needed

### Testing

```bash
# Run unit tests (if available)
pytest tests/

# Manual testing with specific model
python -c "
from agents.benchmark_intelligence.tools.parse_model_card import parse_model_card
result = parse_model_card('meta-llama/Llama-3.3-70B-Instruct')
print(result)
"
```

## Contributing

Contributions welcome! Areas for improvement:

- Additional benchmark patterns
- More robust parsing for edge cases
- Enhanced classification logic
- Performance optimizations
- Additional output formats
- Integration with other platforms (beyond Hugging Face)

## License

See repository root for license information.

## Support

For issues, questions, or feature requests, please contact the maintainers or open an issue in the repository.

---

**Version**: 1.0
**Last Updated**: 2026-04-02
**Maintainer**: Benchmark Intelligence Team
