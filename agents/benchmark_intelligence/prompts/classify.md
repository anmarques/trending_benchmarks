# Benchmark Classification Prompt

## Task
Classify benchmarks into multi-label categories using a comprehensive taxonomy. Each benchmark can belong to multiple primary categories and have multiple secondary attributes.

## Input Format

```json
{
  "benchmark_name": "string",
  "description": "string|null"  // Optional description or context
}
```

## Output Schema

```json
{
  "benchmark_name": "string",
  "primary_categories": [
    {
      "category": "string",
      "confidence": "number",  // 0.0-1.0
      "reasoning": "string"
    }
  ],
  "secondary_attributes": [
    {
      "attribute": "string",
      "confidence": "number",  // 0.0-1.0
      "reasoning": "string"
    }
  ],
  "modality": ["string"],  // ["text", "vision", "audio", "multimodal"]
  "domain": "string|null",  // Specific domain if applicable
  "difficulty_level": "string|null",  // "introductory", "intermediate", "advanced", "expert"
  "metadata": {
    "classification_date": "string",
    "confidence_overall": "number"  // 0.0-1.0 overall confidence
  }
}
```

## Primary Categories

Benchmarks can have **multiple primary categories**. Use the following taxonomy:

### 1. Knowledge
**Definition:** Tests factual knowledge, general understanding across academic/world domains.

**Keywords:** MMLU, TriviaQA, Natural Questions, knowledge, facts, academic, subjects, C-Eval, CMMLU

**Examples:**
- MMLU (57 academic subjects)
- TriviaQA (trivia questions)
- Natural Questions (factual QA)
- C-Eval (Chinese knowledge)

**Confidence:** 0.9-1.0 if name/description clearly indicates knowledge testing

---

### 2. Reasoning
**Definition:** Tests logical reasoning, commonsense reasoning, inference abilities.

**Keywords:** ARC, HellaSwag, PIQA, WinoGrande, reasoning, logic, commonsense, inference

**Examples:**
- ARC-c (science reasoning)
- HellaSwag (commonsense reasoning)
- PIQA (physical reasoning)
- WinoGrande (coreference reasoning)
- BoolQ (yes/no reasoning)

**Confidence:** 0.8-1.0 if reasoning is primary focus

---

### 3. Math
**Definition:** Mathematical problem solving, numerical reasoning, computation.

**Keywords:** GSM8K, MATH, AIME, math, mathematical, arithmetic, algebra, geometry, calculus, olympiad

**Examples:**
- GSM8K (grade school math)
- MATH (competition math)
- AIME (invitational math exam)
- MathVista (visual math)
- Omni-MATH (olympiad math)

**Confidence:** 0.9-1.0 if math is in name or description

---

### 4. Code
**Definition:** Code generation, programming, software engineering, debugging.

**Keywords:** HumanEval, MBPP, SWE-bench, code, programming, python, coding, software, debugging, repository

**Examples:**
- HumanEval (Python code generation)
- MBPP (Python programming)
- SWE-bench (GitHub issues)
- LiveCodeBench (code generation)
- BigCodeBench (code tasks)

**Confidence:** 0.9-1.0 if code/programming is primary task

---

### 5. Vision
**Definition:** Visual understanding, image processing, visual question answering.

**Keywords:** VQA, MMMU, visual, image, vision, picture, photo, diagram, chart, OCR, document

**Examples:**
- VQAv2 (visual questions)
- MMMU (multimodal understanding)
- DocVQA (document VQA)
- MMBench (vision benchmark)

**Confidence:** 0.9-1.0 if vision is required

---

### 6. Audio
**Definition:** Speech recognition, audio processing, sound understanding.

**Keywords:** LibriSpeech, audio, speech, ASR, WER, sound, spoken, voice

**Examples:**
- LibriSpeech (speech recognition)
- Audio ASR benchmarks

**Confidence:** 1.0 if audio/speech is primary modality

---

### 7. Multilingual
**Definition:** Non-English or cross-lingual evaluation, multilingual capabilities.

**Keywords:** multilingual, cross-lingual, FLORES, Belebele, XNLI, translation, languages, Chinese, French, Spanish, MGSM, C-Eval, CMMLU

**Examples:**
- FLORES-200 (200 languages)
- Belebele (122 languages)
- XNLI (cross-lingual inference)
- C-Eval (Chinese)
- MMMLU (multilingual MMLU)

**Confidence:** 0.9-1.0 if multilingual is explicit

---

### 8. Safety
**Definition:** Truthfulness, toxicity, bias, robustness, adversarial testing.

**Keywords:** TruthfulQA, ToxiGen, BBQ, safety, truthful, toxic, bias, adversarial, trust, robustness

**Examples:**
- TruthfulQA (truthfulness)
- ToxiGen (toxicity)
- BBQ (bias)
- AdvGLUE (adversarial)
- DecodingTrust (trustworthiness)

**Confidence:** 1.0 if safety/bias/truthfulness is primary focus

---

### 9. Long-Context
**Definition:** Tasks requiring long context windows (typically >4K tokens).

**Keywords:** LongBench, RULER, long context, long-form, needle, haystack, InfiniteBench, long, AA-LCR

**Examples:**
- LongBench (long context tasks)
- RULER (long context)
- InfiniteBench (>100K tokens)
- Needle-in-Haystack

**Confidence:** 1.0 if "long" is in name/description

---

### 10. Instruction-Following
**Definition:** Following complex, multi-step, or constrained instructions.

**Keywords:** IFEval, AlpacaEval, MT-Bench, instruction, following, constraints, multi-turn, conversation

**Examples:**
- IFEval (verifiable instructions)
- AlpacaEval (instruction following)
- MT-Bench (multi-turn)
- Arena-Hard (challenging instructions)

**Confidence:** 0.9-1.0 if instruction-following is core

---

### 11. Tool-Use
**Definition:** Function calling, API usage, tool integration.

**Keywords:** BFCL, tool, function calling, API, tools, functions

**Examples:**
- BFCL (Berkeley Function Calling)
- API-Bench (API usage)
- NFCL (Nexus Function Calling)

**Confidence:** 1.0 if tool/function use is primary

---

### 12. Agent
**Definition:** Interactive, multi-step, environment-based autonomous tasks.

**Keywords:** WebArena, OSWorld, agent, interactive, environment, autonomous, planning, multi-step, task completion

**Examples:**
- WebArena (web agent tasks)
- OSWorld (OS-level tasks)
- AgentBench (agent capabilities)
- VisualWebArena (multimodal agent)

**Confidence:** 1.0 if agent/interactive is primary

---

### 13. Domain-Specific
**Definition:** Specialized domains like medical, legal, finance, science.

**Keywords:** LegalBench, FinQA, PubMedQA, MedQA, legal, medical, finance, biomedical, healthcare, law

**Examples:**
- LegalBench (legal reasoning)
- FinQA (financial reasoning)
- PubMedQA (biomedical QA)
- MedXpertQA (medical)

**Confidence:** 1.0 if domain is explicit in name/description

## Secondary Attributes

These are **additional characteristics** that can apply to benchmarks:

### OCR/Text
Requires reading text from images.
**Examples:** DocVQA, OCRBench, TextVQA, CharXiv

### Spatial
Spatial reasoning and understanding.
**Examples:** RefCOCO, CountBench, EmbSpatialBench, LingoQA

### Medical
Healthcare and biomedical domain.
**Examples:** SLAKE, PMC-VQA, MedXpertQA, PubMedQA

### Video
Video understanding (temporal reasoning).
**Examples:** VideoMME, MLVU, MVBench, VideoMMMU

### Document
Document understanding and processing.
**Examples:** DocVQA, OmniDocBench, CharXiv

### Competition
Based on real competitions.
**Examples:** AIME, HMMT, IMO, Olympiad benchmarks

### Contamination-Free
Continuously updated to avoid training data leakage.
**Examples:** LiveCodeBench, LongReason

### Real-World
Based on real-world data/tasks.
**Examples:** SWE-bench, WebArena, OSWorld, RealWorldQA

### STEM
Science, Technology, Engineering, Mathematics focus.
**Examples:** MMMU (STEM subset), ARC, science benchmarks

### Multimodal
Requires multiple modalities (vision+text, audio+text, etc.).
**Examples:** MMMU, VideoMME, any VLM benchmark

## Classification Logic

### Step 1: Identify Modality
Determine base modality from name/description:
- **Text-only:** Most LLM benchmarks (MMLU, GSM8K, HumanEval)
- **Vision:** VQA, MMMU, DocVQA, video benchmarks
- **Audio:** LibriSpeech, ASR benchmarks
- **Multimodal:** Combines text+vision, text+audio, etc.

### Step 2: Assign Primary Categories
Use keyword matching and semantic understanding:
1. Check name for category keywords
2. Analyze description for task type
3. Assign all applicable primary categories
4. Set confidence based on clarity

### Step 3: Assign Secondary Attributes
1. Look for specialized characteristics
2. Identify domain if applicable
3. Check for special properties (contamination-free, real-world, etc.)

### Step 4: Determine Difficulty
Based on benchmark description:
- **Introductory:** Basic tasks, high baseline scores
- **Intermediate:** Standard evaluation, moderate difficulty
- **Advanced:** Challenging tasks, low baseline scores
- **Expert:** Competition-level, olympiad, specialized expertise

## Examples

### Example 1: MMLU

**Input:**
```json
{
  "benchmark_name": "MMLU",
  "description": "Massive Multitask Language Understanding covering 57 academic subjects"
}
```

**Output:**
```json
{
  "benchmark_name": "MMLU",
  "primary_categories": [
    {
      "category": "Knowledge",
      "confidence": 1.0,
      "reasoning": "Tests factual knowledge across 57 academic subjects"
    }
  ],
  "secondary_attributes": [
    {
      "attribute": "STEM",
      "confidence": 0.7,
      "reasoning": "Includes STEM subjects among the 57 domains"
    }
  ],
  "modality": ["text"],
  "domain": null,
  "difficulty_level": "intermediate",
  "metadata": {
    "classification_date": "2026-04-02",
    "confidence_overall": 1.0
  }
}
```

### Example 2: GSM8K

**Input:**
```json
{
  "benchmark_name": "GSM8K",
  "description": "Grade School Math 8K word problems"
}
```

**Output:**
```json
{
  "benchmark_name": "GSM8K",
  "primary_categories": [
    {
      "category": "Math",
      "confidence": 1.0,
      "reasoning": "Grade school math word problems"
    },
    {
      "category": "Reasoning",
      "confidence": 0.8,
      "reasoning": "Requires mathematical reasoning to solve word problems"
    }
  ],
  "secondary_attributes": [],
  "modality": ["text"],
  "domain": null,
  "difficulty_level": "introductory",
  "metadata": {
    "classification_date": "2026-04-02",
    "confidence_overall": 1.0
  }
}
```

### Example 3: HumanEval

**Input:**
```json
{
  "benchmark_name": "HumanEval",
  "description": "164 Python programming tasks for code generation"
}
```

**Output:**
```json
{
  "benchmark_name": "HumanEval",
  "primary_categories": [
    {
      "category": "Code",
      "confidence": 1.0,
      "reasoning": "Python programming and code generation tasks"
    }
  ],
  "secondary_attributes": [],
  "modality": ["text"],
  "domain": null,
  "difficulty_level": "intermediate",
  "metadata": {
    "classification_date": "2026-04-02",
    "confidence_overall": 1.0
  }
}
```

### Example 4: MMMU

**Input:**
```json
{
  "benchmark_name": "MMMU",
  "description": "Massive Multi-discipline Multimodal Understanding covering 11.5K questions across 6 disciplines including art, science, health, business"
}
```

**Output:**
```json
{
  "benchmark_name": "MMMU",
  "primary_categories": [
    {
      "category": "Knowledge",
      "confidence": 0.9,
      "reasoning": "Multi-discipline understanding across various subjects"
    },
    {
      "category": "Vision",
      "confidence": 1.0,
      "reasoning": "Multimodal benchmark requiring visual understanding"
    },
    {
      "category": "Reasoning",
      "confidence": 0.7,
      "reasoning": "Requires reasoning across visual and textual information"
    }
  ],
  "secondary_attributes": [
    {
      "attribute": "Multimodal",
      "confidence": 1.0,
      "reasoning": "Combines vision and language understanding"
    },
    {
      "attribute": "STEM",
      "confidence": 0.8,
      "reasoning": "Includes science and health disciplines"
    }
  ],
  "modality": ["vision", "text"],
  "domain": null,
  "difficulty_level": "advanced",
  "metadata": {
    "classification_date": "2026-04-02",
    "confidence_overall": 0.9
  }
}
```

### Example 5: DocVQA

**Input:**
```json
{
  "benchmark_name": "DocVQA",
  "description": "Document Visual Question Answering with 12.7K images"
}
```

**Output:**
```json
{
  "benchmark_name": "DocVQA",
  "primary_categories": [
    {
      "category": "Vision",
      "confidence": 1.0,
      "reasoning": "Visual question answering on document images"
    },
    {
      "category": "Knowledge",
      "confidence": 0.6,
      "reasoning": "Requires understanding document content"
    }
  ],
  "secondary_attributes": [
    {
      "attribute": "OCR/Text",
      "confidence": 1.0,
      "reasoning": "Requires reading text from document images"
    },
    {
      "attribute": "Document",
      "confidence": 1.0,
      "reasoning": "Focused on document understanding"
    },
    {
      "attribute": "Multimodal",
      "confidence": 1.0,
      "reasoning": "Combines vision and text understanding"
    }
  ],
  "modality": ["vision", "text"],
  "domain": null,
  "difficulty_level": "intermediate",
  "metadata": {
    "classification_date": "2026-04-02",
    "confidence_overall": 1.0
  }
}
```

### Example 6: SWE-bench

**Input:**
```json
{
  "benchmark_name": "SWE-bench",
  "description": "Real-world GitHub issues for software engineering evaluation"
}
```

**Output:**
```json
{
  "benchmark_name": "SWE-bench",
  "primary_categories": [
    {
      "category": "Code",
      "confidence": 1.0,
      "reasoning": "Software engineering and code debugging tasks"
    },
    {
      "category": "Reasoning",
      "confidence": 0.8,
      "reasoning": "Requires reasoning about code issues and solutions"
    }
  ],
  "secondary_attributes": [
    {
      "attribute": "Real-World",
      "confidence": 1.0,
      "reasoning": "Based on actual GitHub issues"
    }
  ],
  "modality": ["text"],
  "domain": null,
  "difficulty_level": "expert",
  "metadata": {
    "classification_date": "2026-04-02",
    "confidence_overall": 1.0
  }
}
```

### Example 7: TruthfulQA

**Input:**
```json
{
  "benchmark_name": "TruthfulQA",
  "description": "817 questions across 38 categories testing truthfulness"
}
```

**Output:**
```json
{
  "benchmark_name": "TruthfulQA",
  "primary_categories": [
    {
      "category": "Safety",
      "confidence": 1.0,
      "reasoning": "Explicitly tests truthfulness and misinformation"
    },
    {
      "category": "Knowledge",
      "confidence": 0.7,
      "reasoning": "Tests factual knowledge and common misconceptions"
    }
  ],
  "secondary_attributes": [],
  "modality": ["text"],
  "domain": null,
  "difficulty_level": "intermediate",
  "metadata": {
    "classification_date": "2026-04-02",
    "confidence_overall": 1.0
  }
}
```

### Example 8: AIME 2024

**Input:**
```json
{
  "benchmark_name": "AIME 2024",
  "description": "American Invitational Mathematics Examination 2024"
}
```

**Output:**
```json
{
  "benchmark_name": "AIME 2024",
  "primary_categories": [
    {
      "category": "Math",
      "confidence": 1.0,
      "reasoning": "Mathematics examination"
    },
    {
      "category": "Reasoning",
      "confidence": 0.9,
      "reasoning": "Requires advanced mathematical reasoning"
    }
  ],
  "secondary_attributes": [
    {
      "attribute": "Competition",
      "confidence": 1.0,
      "reasoning": "Based on real mathematics competition"
    },
    {
      "attribute": "STEM",
      "confidence": 1.0,
      "reasoning": "Mathematics is a STEM discipline"
    }
  ],
  "modality": ["text"],
  "domain": null,
  "difficulty_level": "expert",
  "metadata": {
    "classification_date": "2026-04-02",
    "confidence_overall": 1.0
  }
}
```

### Example 9: WebArena

**Input:**
```json
{
  "benchmark_name": "WebArena",
  "description": "812 web-based agent tasks requiring interaction with websites"
}
```

**Output:**
```json
{
  "benchmark_name": "WebArena",
  "primary_categories": [
    {
      "category": "Agent",
      "confidence": 1.0,
      "reasoning": "Interactive agent tasks in web environments"
    },
    {
      "category": "Instruction-Following",
      "confidence": 0.8,
      "reasoning": "Agents must follow task instructions"
    }
  ],
  "secondary_attributes": [
    {
      "attribute": "Real-World",
      "confidence": 1.0,
      "reasoning": "Based on real website interactions"
    }
  ],
  "modality": ["text"],
  "domain": null,
  "difficulty_level": "expert",
  "metadata": {
    "classification_date": "2026-04-02",
    "confidence_overall": 1.0
  }
}
```

### Example 10: C-Eval

**Input:**
```json
{
  "benchmark_name": "C-Eval",
  "description": "Chinese evaluation benchmark covering multiple subjects"
}
```

**Output:**
```json
{
  "benchmark_name": "C-Eval",
  "primary_categories": [
    {
      "category": "Knowledge",
      "confidence": 1.0,
      "reasoning": "Tests knowledge across multiple subjects"
    },
    {
      "category": "Multilingual",
      "confidence": 1.0,
      "reasoning": "Chinese language benchmark"
    }
  ],
  "secondary_attributes": [],
  "modality": ["text"],
  "domain": null,
  "difficulty_level": "intermediate",
  "metadata": {
    "classification_date": "2026-04-02",
    "confidence_overall": 1.0
  }
}
```

## Special Cases

### When Description is Missing
Use name-based heuristics:
- Extract keywords from benchmark name
- Apply common patterns (e.g., "Eval" → evaluation, "QA" → question answering)
- Use lower confidence scores (0.6-0.8)
- Flag for potential review

**Example:**
```json
{
  "benchmark_name": "MathVista",
  "description": null
}
```
→ Infer: Math (from "Math") + Vision (from "Vista"), confidence 0.8

### Multi-Domain Benchmarks
Assign all relevant primary categories:
- MMMU → Knowledge + Vision + Reasoning
- MathVista → Math + Vision
- SWE-bench → Code + Reasoning

### Ambiguous Names
- Flag with lower confidence
- Use secondary attributes to add context
- Suggest manual review

## Classification Guidelines

1. **Be comprehensive:** Assign all applicable categories
2. **Use confidence scores:** Higher for explicit mentions, lower for inference
3. **Prioritize explicit information:** Name/description takes precedence
4. **Multi-label is expected:** Most benchmarks have 2-3 primary categories
5. **Document reasoning:** Always explain classification decisions
6. **Flag uncertainty:** Use confidence < 0.7 and note in reasoning

## Quality Checks

1. **At least one primary category** assigned
2. **Modality must be specified**
3. **Confidence scores between 0.0-1.0**
4. **Reasoning provided for each category**
5. **Overall confidence reflects certainty of classification**
6. **Secondary attributes are relevant and accurate**

## Important Notes

- **Multi-label is the norm**: Don't force single category
- **Context matters**: Use description when available
- **Conservative with low confidence**: Better to flag than misclassify
- **Domain-specific gets both**: e.g., MedQA gets "Domain-Specific" + "Medical" attribute
- **Modality drives some categories**: Vision benchmarks usually get "Vision" category
