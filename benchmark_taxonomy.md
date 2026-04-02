# LLM/VLM/Audio-Language Model Benchmark Taxonomy

**Research Date:** April 2026
**Purpose:** Inform AI prompts for extraction and classification of benchmarks from model cards

---

## 1. Common Benchmark Names and Variations

### 1.1 Naming Convention Patterns

Benchmarks appear in various formats across model cards:

| Pattern | Examples |
|---------|----------|
| **Standard Names** | MMLU, GSM8K, HumanEval, C-Eval |
| **With Variants** | MMLU-Pro, MMLU-Redux, MMLU-ProX |
| **Version Numbers** | LongBench v2, BFCL-V4, MMBenchEN-DEV-v1.1 |
| **Shot Context** | 5-shot MMLU, MMLU (5-shot), 0-shot HellaSwag |
| **Subsets/Splits** | ARC-c (challenge), ARC-e (easy), test-clean, test-other |
| **With Context** | VideoMME(w sub.), VideoMME(w/o sub.), RefCOCO(avg) |
| **Qualified Names** | GPQA Diamond, SuperGPQA |
| **Date Variants** | HMMT Feb 25, HMMT Nov 25, AIME 2024, AIME 2025 |
| **Abbreviations** | AA-LCR, CC-OCR, VQA, ASR, WER |
| **Case Variations** | GSM8K, GSM-8K, GSM8k, gsm8k |

### 1.2 Shot Count Variations

Common patterns for few-shot specifications:
- **Zero-shot**: 0-shot, zero-shot, (0-shot)
- **One-shot**: 1-shot, one-shot
- **Few-shot**: 3-shot, 5-shot, few-shot (typically 3-5 examples)
- **Many-shot**: 10-shot, 25-shot

**Note:** Shot counts may appear as:
- Prefix: "5-shot MMLU"
- Suffix: "MMLU (5-shot)"
- In description: "MMLU evaluated with 5 examples"
- Omitted (requires checking documentation)

---

## 2. Top 30+ Common Benchmarks by Category

### 2.1 Knowledge & General Understanding

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **MMLU** | Massive Multitask Language Understanding; 57 academic subjects | Accuracy (%) |
| **MMLU-Pro** | Enhanced MMLU with harder questions | Accuracy (%) |
| **MMLU-Redux** | Cleaned/validated version of MMLU | Accuracy (%) |
| **C-Eval** | Chinese evaluation benchmark | Accuracy (%) |
| **CMMLU** | Chinese Massive Multitask Language Understanding | Accuracy (%) |
| **TriviaQA** | Trivia question answering, 650K+ QA pairs | EM, F1 |
| **Natural Questions (NQ)** | Google search queries + Wikipedia answers | EM, F1 |
| **SQuAD** | Stanford Question Answering Dataset | EM, F1 |

### 2.2 Reasoning & Commonsense

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **ARC** | AI2 Reasoning Challenge (science questions) | Accuracy (%) |
| **ARC-c** | ARC Challenge set (harder subset) | Accuracy (%) |
| **ARC-e** | ARC Easy set | Accuracy (%) |
| **HellaSwag** | Common sense reasoning about grounded situations | Accuracy (%) |
| **PIQA** | Physical Interaction QA (physical commonsense) | Accuracy (%) |
| **WinoGrande** | Winograd Schema Challenge (44k problems) | Accuracy (%) |
| **CommonSenseQA** | Commonsense reasoning questions | Accuracy (%) |
| **BoolQ** | Boolean yes/no questions | Accuracy (%) |
| **OBQA** | OpenBookQA | Accuracy (%) |

### 2.3 Mathematical Reasoning

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **GSM8K** | Grade School Math (8.5K word problems) | Accuracy (%) |
| **MATH** | Competition-level math (5K problems) | Accuracy (%) |
| **AIME** | American Invitational Mathematics Examination | Accuracy (%) |
| **HMMT** | Harvard-MIT Math Tournament (Feb/Nov variants) | Accuracy (%) |
| **OlymMATH** | Olympiad-level mathematical problems | Accuracy (%) |
| **Omni-MATH** | 4428 competition-level problems, 33+ sub-domains | Accuracy (%) |
| **IMO-AnswerBench** | International Math Olympiad problems | Accuracy (%) |
| **MathVision** | Visual mathematical reasoning | Accuracy (%) |
| **MathVista** | Math + visual understanding | Accuracy (%) |
| **We-Math** | Math problem solving | Accuracy (%) |

### 2.4 Code Generation & Software Engineering

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **HumanEval** | 164 Python programming tasks | Pass@1, Pass@10 |
| **MBPP** | Mostly Basic Python Problems (~1K tasks) | Pass@1 |
| **SWE-bench** | Real-world GitHub issues (software engineering) | % Resolved |
| **SWE-bench Verified** | Validated subset of SWE-bench | % Resolved |
| **SWE-bench Multilingual** | Multi-language version | % Resolved |
| **LiveCodeBench** | Contamination-free, continuously updated coding | Pass@1 |
| **LiveCodeBench v6** | Latest version | Pass@1 |
| **BigCodeBench** | Large-scale code benchmark | Pass@1 |
| **RepoBench** | Repository-level code completion | Accuracy (%) |
| **OJBench** | Online judge problems | Accuracy (%) |

### 2.5 Long Context

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **LongBench** | Bilingual long-context tasks | Accuracy (%) |
| **LongBench v2** | Extended version with more domains | Accuracy (%) |
| **RULER** | 13 task configurations for long context | Accuracy (%) |
| **InfiniteBench (∞-Bench)** | Tasks >100K tokens | Accuracy (%) |
| **AA-LCR** | Long context reasoning | Accuracy (%) |
| **Needle-in-Haystack (NIAH)** | Retrieval from long context | Accuracy (%) |
| **LongGenBench** | Long-form generation | Quality scores |
| **LongReason** | Synthetic long-context reasoning | Accuracy (%) |

### 2.6 Instruction Following

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **IFEval** | Instruction-Following Evaluation (verifiable instructions) | Prompt-level, Inst-level accuracy |
| **IFBench** | Instruction following benchmark | Accuracy (%) |
| **AlpacaEval** | Automatic evaluation of instruction-following | Win rate (%) |
| **AlpacaEval 2.0** | Length-controlled version | LC Win rate (%) |
| **MT-Bench** | Multi-turn conversation benchmark (80 questions) | Score (1-10) |
| **Arena-Hard** | Challenging subset from Chatbot Arena | Win rate (%) |
| **MultiChallenge** | Multi-constraint instruction following | Accuracy (%) |

### 2.7 Multilingual

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **MMMLU** | Multilingual MMLU | Accuracy (%) |
| **MMLU-ProX** | Multilingual MMLU-Pro (29 languages) | Accuracy (%) |
| **FLORES-200** | Machine translation (200 languages) | BLEU, chrF |
| **Belebele** | Reading comprehension (122 languages) | Accuracy (%) |
| **XNLI** | Cross-lingual Natural Language Inference | Accuracy (%) |
| **MGSM** | Multilingual Grade School Math | Accuracy (%) |
| **NOVA-63** | 63-language benchmark | Accuracy (%) |
| **INCLUDE** | Multilingual inclusion benchmark | Accuracy (%) |
| **Global PIQA** | Multilingual physical reasoning | Accuracy (%) |
| **PolyMATH** | Multilingual mathematical reasoning | Accuracy (%) |
| **WMT24++** | Translation benchmark | BLEU, COMET |
| **MAXIFE** | Cross-lingual instruction following | Accuracy (%) |

### 2.8 Safety, Truthfulness & Bias

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **TruthfulQA** | Truthfulness evaluation (817 questions, 38 categories) | % Truthful |
| **ToxiGen** | Hate speech detection (274K statements, 13 groups) | % Toxic |
| **BBQ** | Bias Benchmark for QA (social biases) | Accuracy, Bias score |
| **DecodingTrust** | 8 perspectives on trustworthiness | Multiple metrics |
| **AdvGLUE** | Adversarial robustness on GLUE tasks | Accuracy (%) |

### 2.9 Tool Use & Function Calling

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **BFCL** | Berkeley Function Calling Leaderboard | Accuracy (%) |
| **BFCL-V2** | Enterprise-contributed data | Accuracy (%) |
| **BFCL-V3** | Multi-turn function calling | Accuracy (%) |
| **BFCL-V4** | Latest version | Accuracy (%) |
| **API-Bench** | Single-turn API interactions | Accuracy (%) |
| **NFCL** | Nexus Function Calling Leaderboard | Accuracy (%) |

### 2.10 Vision-Language (VLM) - General VQA

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **VQAv2** | Visual Question Answering (1.1M+ questions) | Accuracy (%) |
| **TextVQA** | Questions requiring reading text in images | Accuracy (%) |
| **RealWorldQA** | Real-world visual questions | Accuracy (%) |
| **MMStar** | Multi-modal evaluation | Accuracy (%) |
| **MMBench** | Bilingual perception, reasoning, knowledge | Accuracy (%) |
| **MMBenchEN-DEV-v1.1** | English development set | Accuracy (%) |
| **SimpleVQA** | Simple visual questions | Accuracy (%) |
| **HallusionBench** | Object hallucination detection | Accuracy (%) |
| **POPE** | Probing object hallucination | Accuracy, F1 |

### 2.11 Vision-Language - STEM & Reasoning

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **MMMU** | Massive Multi-discipline Multimodal Understanding (11.5K questions, 6 disciplines) | Accuracy (%) |
| **MMMU-Pro** | Enhanced MMMU | Accuracy (%) |
| **MathVision** | Visual mathematical problems | Accuracy (%) |
| **MathVista** | Math + visual (mini version exists) | Accuracy (%) |
| **We-Math** | Visual math problems | Accuracy (%) |
| **DynaMath** | Dynamic mathematical reasoning | Accuracy (%) |
| **ZEROBench** | Visual reasoning benchmark | Accuracy (%) |
| **ZEROBench_sub** | Subset of ZEROBench | Accuracy (%) |
| **VlmsAreBlind** | Vision capability testing | Accuracy (%) |
| **BabyVision** | Early vision capabilities | w/ CI, w/o CI scores |

### 2.12 Vision-Language - OCR & Document Understanding

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **DocVQA** | Document Visual QA (12.7K images) | ANLS |
| **OmniDocBench** | Document understanding | Accuracy (%) |
| **OmniDocBench1.5** | Updated version | Accuracy (%) |
| **CharXiv** | Character/text in academic papers | Accuracy (%) |
| **CharXiv(RQ)** | Research question variant | Accuracy (%) |
| **MMLongBench-Doc** | Long document understanding | Accuracy (%) |
| **CC-OCR** | OCR evaluation | Accuracy (%) |
| **OCRBench** | 1K manually verified OCR questions, 18 datasets | Accuracy (%) |
| **OCRBench v2** | Visual text localization + reasoning | Accuracy (%) |
| **AI2D_TEST** | Diagram understanding | Accuracy (%) |

### 2.13 Vision-Language - Spatial Intelligence

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **ERQA** | Spatial reasoning questions | Accuracy (%) |
| **CountBench** | Counting objects | Accuracy (%) |
| **RefCOCO** | Referring expression comprehension | Accuracy (%) |
| **RefCOCO(avg)** | Average across splits | Accuracy (%) |
| **EmbSpatialBench** | Embodied spatial reasoning | Accuracy (%) |
| **RefSpatialBench** | Reference spatial understanding | Accuracy (%) |
| **LingoQA** | Spatial language understanding | Accuracy (%) |
| **Hypersim** | Indoor scene understanding | Accuracy (%) |
| **Nuscene** | Autonomous driving scenes | mAP, NDS |

### 2.14 Vision-Language - Video Understanding

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **VideoMME** | Video understanding with/without subtitles | Accuracy (%) |
| **VideoMME(w sub.)** | With subtitles variant | Accuracy (%) |
| **VideoMME(w/o sub.)** | Without subtitles variant | Accuracy (%) |
| **VideoMMMU** | Multi-discipline video understanding | Accuracy (%) |
| **MLVU** | Multi-task long video understanding | Accuracy (%) |
| **MVBench** | Multi-modal video benchmark | Accuracy (%) |
| **LVBench** | Long video benchmark | Accuracy (%) |
| **MMVU** | Massive multi-modal video understanding | Accuracy (%) |

### 2.15 Vision-Language - Visual Agents

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **ScreenSpot Pro** | GUI element localization | Accuracy (%) |
| **OSWorld** | OS-level tasks (369 tasks, Ubuntu/Windows/macOS) | Success rate (%) |
| **OSWorld-Verified** | Validated subset | Success rate (%) |
| **AndroidWorld** | Android app interactions | Success rate (%) |
| **TIR-Bench** | Tool-integrated reasoning | Accuracy (%) |
| **V*** | Visual agent benchmark | Multiple metrics |

### 2.16 Vision-Language - Medical

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **SLAKE** | Medical visual QA | Accuracy (%) |
| **PMC-VQA** | PubMed Central visual QA | Accuracy (%) |
| **MedXpertQA-MM** | Multi-modal medical questions | Accuracy (%) |
| **PubMedQA** | Biomedical yes/no/maybe questions (~1K pairs) | Accuracy (%) |

### 2.17 Audio & Speech

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **LibriSpeech** | ASR corpus (1000 hours, read English) | WER (%) |
| **LibriSpeech test-clean** | Clean test set | WER (%) |
| **LibriSpeech test-other** | Other test set | WER (%) |
| **LibriSpeech dev-clean** | Clean dev set | WER (%) |
| **LibriSpeech dev-other** | Other dev set | WER (%) |
| **LibriSpeech-Long** | Long-form speech generation/processing | Multiple metrics |

### 2.18 Agent & Interactive Tasks

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **WebArena** | Web-based agent tasks (812 tasks) | Success rate (%) |
| **VisualWebArena** | Multi-modal web agent tasks (910 tasks) | Success rate (%) |
| **AgentBench** | Multi-modal agent capabilities | Success rate (%) |
| **TAU2-Bench** | Agent understanding benchmark | Accuracy (%) |
| **VITA-Bench** | Visual interactive task agent | Success rate (%) |
| **DeepPlanning** | Planning capabilities | Success rate (%) |

### 2.19 Domain-Specific

| Benchmark | Description | Typical Metrics |
|-----------|-------------|-----------------|
| **LegalBench** | Legal reasoning (162 tasks, 6 types) | Accuracy (%) |
| **FinQA** | Financial numerical reasoning | Accuracy (%) |
| **PubMedQA** | Biomedical research questions | Accuracy (%) |
| **MedQA** | Medical examination questions | Accuracy (%) |

---

## 3. Benchmark Categories (Multi-Label Taxonomy)

Benchmarks can belong to multiple categories. The following taxonomy supports multi-label classification:

### Primary Categories

1. **Knowledge**
   - Tests factual knowledge across domains
   - Examples: MMLU, TriviaQA, Natural Questions, C-Eval

2. **Reasoning**
   - Tests logical and commonsense reasoning
   - Examples: ARC, HellaSwag, PIQA, WinoGrande, CommonSenseQA

3. **Math**
   - Mathematical problem solving and reasoning
   - Examples: GSM8K, MATH, AIME, HMMT, MathVision

4. **Code**
   - Code generation, debugging, software engineering
   - Examples: HumanEval, MBPP, SWE-bench, LiveCodeBench

5. **Vision**
   - Visual understanding and reasoning (images/video)
   - Examples: VQAv2, MMMU, DocVQA, VideoMME

6. **Audio**
   - Speech and audio processing
   - Examples: LibriSpeech, audio ASR benchmarks

7. **Multilingual**
   - Non-English or cross-lingual evaluation
   - Examples: MMMLU, FLORES, Belebele, XNLI, C-Eval

8. **Safety**
   - Truthfulness, toxicity, bias, robustness
   - Examples: TruthfulQA, ToxiGen, BBQ, AdvGLUE

9. **Long-Context**
   - Tasks requiring long context windows
   - Examples: LongBench, RULER, InfiniteBench, AA-LCR

10. **Instruction-Following**
    - Following complex or multi-step instructions
    - Examples: IFEval, AlpacaEval, MT-Bench

11. **Tool-Use**
    - Function calling, API usage, tool integration
    - Examples: BFCL, API-Bench, tool-use tasks

12. **Agent**
    - Interactive, multi-step, environment-based tasks
    - Examples: WebArena, OSWorld, AgentBench

13. **Domain-Specific**
    - Specialized domains (medical, legal, finance, etc.)
    - Examples: LegalBench, FinQA, PubMedQA, MedXpertQA

### Secondary Attributes

- **OCR/Text**: Requires reading text from images (DocVQA, OCRBench, TextVQA)
- **Spatial**: Spatial reasoning and understanding (RefCOCO, CountBench, spatial benchmarks)
- **Medical**: Healthcare and biomedical domain (SLAKE, PMC-VQA, PubMedQA)
- **Video**: Video understanding (VideoMME, MLVU, MVBench)
- **Document**: Document understanding (DocVQA, OmniDocBench)
- **Competition**: Based on real competitions (AIME, HMMT, IMO, Olympiad benchmarks)
- **Contamination-Free**: Continuously updated (LiveCodeBench, LongReason)
- **Real-World**: Based on real-world data (SWE-bench, WebArena, OSWorld)

---

## 4. How Benchmarks Appear in Model Cards

### 4.1 Format Analysis from Model Cards

Based on analysis of Qwen, Meta Llama, and Mistral model cards:

#### Table Format (Most Common)
- **HTML or Markdown tables** with benchmarks as rows
- **Model names** as columns
- **Numerical scores** in cells (typically 1-2 decimal places)
- **"--"** or "N/A" for missing scores
- **Grouped by category** (e.g., "Knowledge & STEM", "Reasoning & Coding", "Vision Understanding")

Example structure:
```
| Benchmark         | Model A | Model B | Model C |
|-------------------|---------|---------|---------|
| MMLU-Pro          | 82.5    | 80.8    | 79.1    |
| GSM8K (8-shot)    | 94.2    | 92.1    | 89.3    |
| HumanEval         | 86.6    | 78.5    | --      |
```

#### List Format (Less Common)
- Bullet points or numbered lists
- Format: "Benchmark: Score" or "Benchmark - Score%"

#### Prose Format
- Embedded in text: "achieves 86.6% on HumanEval"
- Comparative statements: "outperforms GPT-4 on MMLU"

### 4.2 Context Provided

#### Shot Count Specifications
- **Explicit**: "MMLU (5-shot)", "GSM8K (8-shot)", "0-shot HellaSwag"
- **Implicit**: Described in methodology section
- **Varied**: Different shots for different benchmarks

#### Evaluation Settings
- **Zero-shot**: No examples provided
- **Few-shot**: Typically 3-5 examples
- **Fine-tuned**: Model trained on task
- **Chain-of-thought (CoT)**: With reasoning steps
- **Self-consistency**: Multiple samples aggregated

#### Additional Context
- **Subset specifications**: "test-clean", "ARC-Challenge", "RefCOCO(avg)"
- **Version numbers**: "v1.1", "v2", "V4"
- **Special conditions**: "with reasoning", "w/ sub.", "w/o sub."
- **Metric type**: Usually implicit but sometimes noted (Pass@1, EM, F1, ANLS)

### 4.3 Common Presentation Patterns

#### Meta Llama Pattern
- Benchmarks grouped by capability (CommonSense, World Knowledge, Reading Comprehension, Math, Code)
- Shot counts specified: "7-shot", "5-shot", "8-shot", "4-shot", "0-shot"
- Clear category headers
- Both open-source and proprietary model comparisons

#### Qwen Pattern
- Extensive tables with many models
- Grouped by task type: Language (Knowledge & STEM, Instruction Following, Long Context, Reasoning & Coding, Multilingualism) and Vision (STEM & Puzzle, General VQA, Text Recognition, Spatial, Video, Visual Agent, Medical)
- Footnotes for special cases
- Scores with "--" for unavailable results
- Some scores presented as "X / Y" (e.g., BabyVision: "with CI / without CI")

#### Mistral Pattern
- Focus on efficiency metrics alongside accuracy
- Emphasis on MoE architecture advantages
- Cost-performance comparisons
- Benchmark results with model size/parameter counts

### 4.4 Special Notations

| Notation | Meaning |
|----------|---------|
| `--` | Score not available or not applicable |
| `N/A` | Not applicable |
| `(avg)` | Average across multiple splits |
| `(w sub.)` | With subtitles/additional context |
| `(w/o sub.)` | Without subtitles/additional context |
| `Pass@1` | Percentage passing on first attempt |
| `Pass@10` | Percentage passing in 10 attempts |
| `EM` | Exact Match score |
| `F1` | F1 score |
| `ANLS` | Average Normalized Levenshtein Similarity |
| `WER` | Word Error Rate |
| `*` | Footnote indicator (special evaluation conditions) |

### 4.5 Benchmark Score Ranges

Most benchmarks report:
- **Accuracy**: 0-100% (sometimes 0.0-1.0)
- **Error rates** (WER): Lower is better
- **Pass rates**: 0-100%
- **Win rates**: 0-100% (for comparative evaluations)
- **Scores**: Various scales (e.g., MT-Bench: 1-10)

---

## 5. Extraction Guidelines for AI Prompts

### 5.1 Name Normalization Rules

When extracting benchmark names:

1. **Case Handling**: Normalize to canonical form (usually uppercase for acronyms)
   - GSM8K, gsm8k, GSM-8K → GSM8K
   - mmlu, MMLU, Mmlu → MMLU

2. **Delimiter Handling**: Preserve meaningful delimiters
   - MMLU-Pro (keep hyphen, denotes variant)
   - ARC-c, ARC-e (keep hyphen, denotes subset)
   - SWE-bench (keep hyphen, part of name)

3. **Version Handling**: Keep version indicators
   - LongBench v2
   - BFCL-V4
   - MMBenchEN-DEV-v1.1

4. **Context Extraction**: Separate benchmark name from evaluation context
   - "5-shot MMLU" → Benchmark: MMLU, Context: 5-shot
   - "VideoMME(w sub.)" → Benchmark: VideoMME, Context: with subtitles
   - "RefCOCO(avg)" → Benchmark: RefCOCO, Context: average

5. **Subset Handling**: Preserve subset indicators
   - LibriSpeech test-clean
   - ARC-Challenge (or ARC-c)
   - ZEROBench_sub

### 5.2 Score Extraction Rules

1. **Numeric Formats**: Extract from various formats
   - "82.5%", "82.5", "0.825" → 82.5
   - "Pass@1: 86.6" → 86.6
   - Handle ranges: "80-85" → could be 80, 85, or avg 82.5

2. **Missing Values**: Handle indicators
   - "--", "N/A", blank → null/missing
   - "TBD", "Coming soon" → null/missing

3. **Multiple Metrics**: Identify primary metric
   - For code: Pass@1 is primary (Pass@10 is secondary)
   - For QA: Accuracy or EM is primary (F1 is secondary)

4. **Comparative Statements**: Extract implied scores
   - "outperforms GPT-4 by 5%" → requires context
   - "achieves SOTA" → might indicate top score

### 5.3 Category Classification Heuristics

Use these keywords to assign categories:

- **Math**: math, GSM, AIME, olympiad, grade school, algebra, geometry
- **Code**: code, programming, HumanEval, MBPP, SWE, software, debugging
- **Vision**: vision, VQA, visual, image, video, OCR, document
- **Audio**: audio, speech, LibriSpeech, ASR, WER
- **Multilingual**: multilingual, FLORES, XNLI, Belebele, languages
- **Safety**: safety, truthful, toxic, bias, adversarial, BBQ
- **Long-Context**: long context, long-form, RULER, LongBench, needle
- **Instruction**: instruction, IFEval, AlpacaEval, MT-Bench
- **Tool**: tool, function calling, BFCL, API
- **Agent**: agent, WebArena, OSWorld, interactive
- **Knowledge**: MMLU, knowledge, TriviaQA, questions
- **Reasoning**: reasoning, ARC, HellaSwag, commonsense

### 5.4 Common Pitfalls to Avoid

1. **Version Confusion**: MMLU vs MMLU-Pro vs MMLU-Redux are different
2. **Subset Confusion**: ARC-c (challenge) vs ARC-e (easy) need separate tracking
3. **Context Confusion**: "5-shot MMLU" vs "0-shot MMLU" are different evaluation settings
4. **Split Confusion**: test-clean vs test-other are different subsets
5. **Name Variations**: "Natural Questions" = "NQ" = "NaturalQuestions"
6. **Shot Count Assumptions**: Don't assume shot count if not specified
7. **Metric Confusion**: Ensure correct metric (accuracy vs error rate)

---

## 6. Key Takeaways for Prompt Engineering

### For Extraction:
1. Look for **tables first** (most common format)
2. Check for **category groupings** (Knowledge, Reasoning, etc.)
3. Extract **benchmark name**, **score**, and **context** (shot count, subset) separately
4. Handle **missing values** gracefully ("--", "N/A")
5. Normalize **name variations** (case, delimiters)
6. Preserve **version indicators** (v2, V4, etc.)

### For Classification:
1. Use **multi-label classification** (benchmarks can be in multiple categories)
2. Look for **keywords** in benchmark names and descriptions
3. Consider **domain indicators** (medical, legal, finance)
4. Note **modality** (text, vision, audio, multi-modal)
5. Identify **special attributes** (long-context, contamination-free, real-world)

### For Validation:
1. Cross-reference benchmark names with this taxonomy
2. Verify score ranges are reasonable (typically 0-100%)
3. Check shot counts are standard (0, 1, 3, 5, 10, etc.)
4. Ensure metrics match benchmark type (Pass@1 for code, WER for audio, etc.)
5. Flag unusual or unknown benchmarks for manual review

---

## 7. Sources

### LLM Benchmarks:
- [LLM Benchmarks 2026 - Compare AI Benchmarks and Tests](https://llm-stats.com/benchmarks)
- [LLM Benchmarks Compared: MMLU, HumanEval, GSM8K and More (2026)](https://www.lxt.ai/blog/llm-benchmarks/)
- [LLM Benchmarks: Language Model Performance Comparison 2026 | CodeSOTA](https://www.codesota.com/llm)
- [Top 50 AI Model Benchmarks & Evaluation Metrics (2025 Guide)](https://o-mega.ai/articles/top-50-ai-model-evals-full-list-of-benchmarks-october-2025)

### Vision-Language Benchmarks:
- [The Ultimate Guide To VLM Evaluation Metrics, Datasets, And Benchmarks](https://learnopencv.com/vlm-evaluation-metrics/)
- [Top 10 Vision Language Models in 2026](https://www.datacamp.com/blog/top-vision-language-models)
- [VLM Benchmarks Explained](https://datature.io/glossary/vlm-benchmarks)
- [GitHub - open-compass/VLMEvalKit](https://github.com/open-compass/VLMEvalKit)

### Audio Benchmarks:
- [Best Speech Recognition Benchmark Datasets](https://labelstud.io/learningcenter/which-ai-benchmark-datasets-are-best-for-speech-recognition-tasks/)
- [LibriSpeech ASR corpus](https://www.openslr.org/12)
- [GitHub - google-deepmind/librispeech-long](https://github.com/google-deepmind/librispeech-long)

### Model Cards:
- [Qwen/Qwen3.5-9B · Hugging Face](https://huggingface.co/Qwen/Qwen3.5-9B)
- [llama-models/models/llama3_2/MODEL_CARD.md at main · meta-llama/llama-models](https://github.com/meta-llama/llama-models/blob/main/models/llama3_2/MODEL_CARD.md)
- [Meta Llama 4 Models: Features, Benchmarks, Applications & More](https://www.analyticsvidhya.com/blog/2025/04/meta-llama-4/)
- [Mistral 3: A Look at the Model Family, Benchmarks, & More](https://www.datacamp.com/blog/mistral-3)
- [Mistral Small 4: One AI Model to Replace Three (Complete Guide & Benchmarks 2026)](https://emelia.io/hub/mistral-small-4-complete-guide-benchmarks)

### Reasoning Benchmarks:
- [SOTA Reasoning on 7-Benchmark Suite](https://www.wizwand.com/sota/reasoning-on-7-benchmark-suite-arc-e-arc-c-hellaswag-winogrande-piqa-boolq-obqa-test)
- [Benchmarks for Commonsense Reasoning: Text](https://cs.nyu.edu/~davise/Benchmarks/Text.html)

### Multilingual Benchmarks:
- [GitHub - google-research/xtreme](https://github.com/google-research/xtreme)
- [MultiLoKo: a multilingual local knowledge benchmark for LLMs spanning 31 languages](https://arxiv.org/html/2504.10356v2)
- [BenchMAX: A Comprehensive Multilingual Evaluation Suite for Large Language Models](https://arxiv.org/html/2502.07346v1)

### Code Benchmarks:
- [Understanding LLM Code Benchmarks: From HumanEval to SWE-bench](https://runloop.ai/blog/understanding-llm-code-benchmarks-from-humaneval-to-swe-bench)
- [SWE-bench & LiveCodeBench Leaderboard (March 2026)](https://benchlm.ai/coding)
- [LiveCodeBench: Holistic and Contamination Free Evaluation](https://livecodebench.github.io/)
- [Best LLMs for Coding in 2026](https://onyx.app/insights/best-llms-for-coding-2026)

### Math Benchmarks:
- [Challenging the Boundaries of Reasoning: An Olympiad-Level Math Benchmark](https://arxiv.org/html/2503.21380v2)
- [GSM8K | DeepEval](https://deepeval.com/docs/benchmarks-gsm8k)
- [HMMT25 Benchmark Explained: Testing AI Math Reasoning](https://intuitionlabs.ai/articles/hmmt25-ai-benchmark-explained)
- [Omni-MATH: A Universal Olympiad Level Mathematic Benchmark](https://openreview.net/forum?id=yaqPf0KAlN)

### Safety Benchmarks:
- [10 LLM safety and bias benchmarks](https://www.evidentlyai.com/blog/llm-safety-bias-benchmarks)
- [Top 10 Open Datasets for LLM Safety, Toxicity & Bias Evaluation](https://www.promptfoo.dev/blog/top-llm-safety-bias-benchmarks/)
- [LLM Evaluation Benchmarks and Safety Datasets for 2025](https://responsibleailabs.ai/knowledge-hub/articles/llm-evaluation-benchmarks-2025)

### Long Context Benchmarks:
- [100-LongBench: Are de facto Long-Context Benchmarks...](https://arxiv.org/pdf/2505.19293)
- [GitHub - NVIDIA/RULER](https://github.com/NVIDIA/RULER)
- [LongGenBench: Benchmarking Long-Form Generation in Long Context LLMs](https://openreview.net/forum?id=3A71qNKWAS)

### Tool Use Benchmarks:
- [The Berkeley Function Calling Leaderboard (BFCL)](https://openreview.net/forum?id=2GmDdhBdDk)
- [Berkeley Function Calling Leaderboard (BFCL) V4](https://gorilla.cs.berkeley.edu/leaderboard.html)
- [Beyond the Leaderboard: Unpacking Function Calling Evaluation](https://www.databricks.com/blog/unpacking-function-calling-eval)

### Instruction Following Benchmarks:
- [IFEval | DeepEval](https://deepeval.com/docs/benchmarks-ifeval)
- [Instruction-Following Evaluation for Large Language Models](https://arxiv.org/abs/2311.07911)
- [GitHub - tatsu-lab/alpaca_eval](https://github.com/tatsu-lab/alpaca_eval)
- [MT-Bench (Multi-turn Benchmark)](https://klu.ai/glossary/mt-bench-eval)

### World Knowledge Benchmarks:
- [Natural Questions: A Benchmark for Question Answering Research](https://aclanthology.org/Q19-1026.pdf)
- [TriviaQA: A Large Scale Distantly Supervised Challenge Dataset](https://www.researchgate.net/publication/316859263_TriviaQA_A_Large_Scale_Distantly_Supervised_Challenge_Dataset_for_Reading_Comprehension)

### Domain-Specific Benchmarks:
- [Domain-Specific Benchmarks | Giskard documentation](https://docs.giskard.ai/start/glossary/llm_benchmarks/domain_specific.html)
- [LegalBench](https://www.vals.ai/benchmarks/legal_bench)
- [GitHub - HazyResearch/legalbench](https://github.com/HazyResearch/legalbench)

### Agent Benchmarks:
- [WebArena-x](https://webarena.dev/)
- [OSWorld: Benchmarking Multimodal Agents](https://os-world.github.io/)
- [GitHub - web-arena-x/visualwebarena](https://github.com/web-arena-x/visualwebarena)
- [Best AI Agent Evaluation Benchmarks: 2025 Complete Guide](https://o-mega.ai/articles/the-best-ai-agent-evals-and-benchmarks-full-2025-guide)

### Adversarial Robustness:
- [Adversarial GLUE: A Multi-Task Benchmark for Robustness Evaluation](https://arxiv.org/abs/2111.02840)
- [AdvGLUE Benchmark](https://adversarialglue.github.io/)
- [Assessing Adversarial Robustness of Large Language Models](https://arxiv.org/pdf/2405.02764)

### Multimodal Benchmarks:
- [MMMU](https://mmmu-benchmark.github.io/)
- [MMMU: A Massive Multi-discipline Multimodal Understanding](https://arxiv.org/abs/2311.16502)
- [The Landscape of Multimodal Evaluation Benchmarks](https://www.clarifai.com/blog/the-landscape-of-multimodal-evaluation-benchmarks)
- [DocVQA - Challenge 2026](https://www.docvqa.org/challenges/2026)
- [OCRBench v2](https://arxiv.org/html/2501.00321v2)
