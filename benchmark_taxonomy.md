# LLM/VLM/Audio-Language Model Benchmark Taxonomy

**Last Updated:** April 2026
**Purpose:** Inform AI prompts for extraction and classification of benchmarks from model cards
**Version:** 1.0.0

---

## Categories

This taxonomy organizes AI model benchmarks into 14 major categories based on the types of capabilities they evaluate. Each category includes representative benchmarks commonly found in model documentation.

### 1. Knowledge & General Understanding

Benchmarks evaluating factual knowledge, world understanding, and general question answering across diverse topics including academic subjects, general knowledge tests, and proficiency exams.

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **MMLU** | Massive Multitask Language Understanding - 57 subjects from STEM to humanities | Accuracy (5-shot) |
| **MMLU-Pro** | More challenging version of MMLU with harder questions | Accuracy (5-shot, CoT) |
| **MMLU-redux** | Cleaned and deduplicated version of MMLU | Accuracy |
| **AGIEval** | Human-centric standardized exams (GRE, LSAT, SAT, etc.) | Accuracy (3-5 shot) |
| **ARC-Challenge** | Grade-school science questions requiring reasoning | Accuracy (25-shot) |
| **TriviaQA-Wiki** | Trivia questions with Wikipedia evidence | Accuracy (5-shot) |
| **GRE** | Graduate Record Examination questions | Accuracy |
| **SAT** | Standardized college admission test | Accuracy |
| **LSAT** | Law School Admission Test | Accuracy |
| **AP** | Advanced Placement exams | Accuracy |
| **GMAT** | Graduate Management Admission Test | Accuracy |

### 2. Reasoning & Commonsense

Benchmarks evaluating logical reasoning, commonsense understanding, analytical thinking, and natural language inference including situation understanding and physical reasoning.

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **CommonSenseQA** | Commonsense reasoning over everyday scenarios | Accuracy (7-shot) |
| **Winogrande** | Winograd schema challenge - pronoun resolution | Accuracy (5-shot) |
| **BIG-Bench Hard** | Challenging tasks from BIG-Bench requiring reasoning | Accuracy (3-shot, CoT) |
| **BBH** | BIG-Bench Hard subset | Accuracy (3-shot) |
| **PiQA** | Physical interaction question answering | Accuracy |
| **SiQA** | Social interaction question answering | Accuracy |
| **OpenBookQA** | Open-book exam style questions | Accuracy |
| **HellaSwag** | Commonsense natural language inference | Accuracy (10-shot) |
| **PAWS** | Paraphrase adversaries from word scrambling | Accuracy |

### 3. Mathematical Reasoning

Benchmarks evaluating mathematical problem solving, quantitative reasoning, numerical understanding, and theorem proving across various difficulty levels.

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **GSM8K** | Grade school math word problems (8K examples) | Accuracy (8-shot, CoT) |
| **MATH** | Competition-level mathematics problems | Accuracy (4-shot, CoT) |
| **AIME** | American Invitational Mathematics Examination | Accuracy |
| **GSM-Plus** | Adversarial version of GSM8K | Accuracy |
| **MGSM** | Multilingual grade school math | Accuracy |
| **TheoremQA** | Theorem-based question answering | Accuracy (5-shot) |

### 4. Code Generation & Software Engineering

Benchmarks evaluating code generation, programming capabilities, software engineering tasks, and multilingual code synthesis across different programming languages.

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **HumanEval** | Python code generation from docstrings | Pass@k (0-shot) |
| **HumanEval+** | Extended HumanEval with more test cases | Pass@k (0-shot) |
| **MBPP** | Mostly Basic Python Problems | Pass@k (0-shot) |
| **MBPP+** | Extended MBPP with additional test cases | Pass@k (0-shot) |
| **MBPP++** | Further extended MBPP | Pass@k (0-shot) |
| **MultiPL-E** | HumanEval translated to 18+ programming languages | Pass@k (0-shot) |
| **LiveCodeBench** | Continuously updated coding benchmark with recent problems | Pass@1 |
| **SWE-bench** | Software engineering tasks from real GitHub issues | Resolution rate |

### 5. Reading Comprehension

Benchmarks evaluating reading comprehension, text understanding, question answering based on provided context, and information extraction from passages.

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **SQuAD** | Stanford Question Answering Dataset | F1, Exact Match (1-shot) |
| **SQuAD V2** | SQuAD with unanswerable questions | F1, Exact Match |
| **QuAC** | Question Answering in Context - conversational QA | F1 (1-shot) |
| **BoolQ** | Boolean yes/no questions from passages | Accuracy (0-shot) |
| **DROP** | Discrete Reasoning Over Paragraphs | F1 (3-shot) |
| **RACE** | Reading comprehension from English exams | Accuracy |

### 6. Science & STEM

Benchmarks evaluating scientific knowledge, STEM understanding, domain-specific scientific reasoning, and graduate-level science questions.

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **GPQA** | Graduate-level Physics, Biology, Chemistry QA | Accuracy (0-shot, CoT) |
| **MMLU-stem** | STEM subset of MMLU | Accuracy |
| **TheoremQA** | Science and mathematics theorem-based questions | Accuracy (5-shot) |

### 7. Long Context Understanding

Benchmarks evaluating performance on long-context tasks, extended documents, information retrieval from large texts, and needle-in-haystack style challenges.

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **ZeroSCROLLS** | Zero-shot evaluation on long documents | F1, Accuracy |
| **InfiniteBench** | Extremely long context tasks (100K+ tokens) | Accuracy |
| **Needle-in-a-Haystack** | Information retrieval from very long contexts | Recall |
| **QuALITY** | Long document comprehension | Accuracy |
| **RULER** | Length understanding and retrieval benchmark | Accuracy |
| **LV-Eval** | Long-context evaluation suite | Various metrics |
| **LongBench-Chat** | Long-context conversational evaluation | Quality scores |

### 8. Multilingual & Translation

Benchmarks evaluating performance across multiple languages, multilingual understanding, cross-lingual transfer, and translation quality.

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **Multilingual MGSM** | Math problems across 10+ languages | Accuracy (0-shot, CoT) |
| **Multi-Exam** | Multilingual exam questions | Accuracy |
| **Multi-Understanding** | Cross-lingual understanding tasks | Accuracy |
| **Multi-Mathematics** | Multilingual math reasoning | Accuracy |
| **Multi-Translation** | Translation quality evaluation | BLEU, COMET |
| **AMMLU** | Arabic MMLU | Accuracy |
| **JMMLU** | Japanese MMLU | Accuracy |
| **KMMLU** | Korean MMLU | Accuracy |
| **IndoMMLU** | Indonesian MMLU | Accuracy |
| **TurkishMMLU** | Turkish MMLU | Accuracy |
| **BLEnD** | Benchmark for cultural nuances in language | Accuracy |

### 9. Instruction Following

Benchmarks evaluating the ability to follow instructions precisely, execute commands accurately, and adhere to specified formats and constraints.

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **IFEval** | Instruction Following Evaluation - verifiable instructions | Strict/Loose accuracy |

### 10. Agent & Tool Use

Benchmarks evaluating function calling, API usage, integration with external tools, and agentic capabilities including planning and tool selection.

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **API-Bank** | API calling and tool use benchmark | Success rate (0-shot) |
| **BFCL** | Berkeley Function-Calling Leaderboard | Accuracy |
| **Gorilla API Bench** | API calling with documentation | Success rate |
| **API-Bench** | API interaction benchmark | Accuracy |
| **Nexus** | Tool use and planning benchmark | Success rate |

### 11. Conversational AI & Chat

Benchmarks evaluating conversational abilities, dialogue quality, multi-turn interaction, and open-ended chat performance.

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **Arena-Hard** | Human preference evaluation on challenging prompts | Win rate vs GPT-4 |
| **MT-bench** | Multi-turn conversation benchmark | GPT-4 rated score (1-10) |

### 12. Alignment & Safety

Benchmarks evaluating model alignment with human preferences, helpfulness, harmlessness, and alignment with cultural values.

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **AlignBench** | Chinese alignment benchmark | Score (multiple dimensions) |

### 13. Truthfulness & Factuality

Benchmarks evaluating factual accuracy, hallucination detection, truthful response generation, and resistance to generating misinformation.

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **TruthfulQA** | Questions that humans often answer incorrectly | Accuracy (0-shot) |

### 14. General & Comprehensive

Comprehensive benchmarks evaluating multiple capabilities across different dimensions including real-world tasks and holistic model evaluation.

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **LiveBench** | Continuously updated benchmark across multiple categories | Aggregate score |

---

## Usage Notes

### For AI Extraction Systems

When extracting benchmarks from model documentation:

1. **Match benchmark names flexibly**: Benchmarks may appear with variations (e.g., "MMLU", "mmlu", "MMLU 5-shot")
2. **Capture variants**: Note important variants like shot count (0-shot, 5-shot), prompting method (CoT), and model type (base, instruct)
3. **Category assignment**: Use this taxonomy to classify benchmarks into appropriate categories
4. **Multi-category benchmarks**: Some benchmarks may fit multiple categories (e.g., GPQA fits both Science and Reasoning)

### Taxonomy Evolution

This taxonomy is designed to evolve as new benchmark types emerge:

- New categories may be added when novel evaluation types appear
- Existing categories may be refined based on benchmark usage patterns
- Historical versions are archived in the `archive/` directory with timestamps

### Version History

- **1.0.0** (April 2026): Initial taxonomy based on ground truth analysis of Llama 3.1 and Qwen 2.5 model documentation
  - 14 categories covering 75+ unique benchmarks
  - Extracted from 181 total benchmark mentions across 2 models

---

**Metadata:**
- Source: Ground truth dataset (`tests/ground_truth/ground_truth.yaml`)
- Total Categories: 14
- Coverage: 75+ unique benchmarks
- Last Review: April 3, 2026


### Vision & Multimodal Understanding

Benchmarks for vision & multimodal understanding

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|


### Safety & Robustness

Benchmarks for safety & robustness

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|


### Domain-Specific Expertise

Benchmarks for domain-specific expertise

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|


### Factuality & Hallucination Detection

Benchmarks for factuality & hallucination detection

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|


### Speech & Audio

Benchmarks for speech & audio

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|


### Hallucination & Factuality

Benchmarks for hallucination & factuality

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|


### Web & Browser Interaction

Benchmarks for web & browser interaction

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
