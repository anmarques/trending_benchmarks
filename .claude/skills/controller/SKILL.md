# Controller Skill

**Purpose**: Manage the benchmark intelligence workflow and guide users through the 6-stage pipeline.

## Workflow Overview

The Benchmark Intelligence pipeline has **6 sequential stages**:

1. **filter_models** - Filter trending models from target labs (Qwen, Meta, Mistral, etc.)
2. **find_docs** - Find documentation URLs for filtered models
3. **parse_docs** - Extract benchmarks from documentation using AI
4. **consolidate_benchmarks** - Deduplicate and normalize benchmark names
5. **categorize_benchmarks** - Classify benchmarks into categories using AI
6. **report** - Generate comprehensive benchmark analysis report

**Or run `generate`** to execute all 6 stages sequentially.

## Your Role

When this skill is invoked:

1. **Check pipeline status** - Determine which stages have been completed
2. **Show current state** - Display what's been done and what remains
3. **Recommend next step** - Suggest the next logical stage or action
4. **Provide context** - Explain what each stage does and why it matters

## Status Checking

Check for these artifacts to determine stage completion:

- Stage 1 complete: `agents/benchmark_intelligence/data/filtered_models.json` exists
- Stage 2 complete: `agents/benchmark_intelligence/data/model_docs.json` exists  
- Stage 3 complete: `agents/benchmark_intelligence/data/parsed_docs.json` exists
- Stage 4 complete: Database has consolidated benchmarks
- Stage 5 complete: Database has categorized benchmarks
- Stage 6 complete: `agents/benchmark_intelligence/reports/` has recent report

## When To Invoke

- User asks "what should I do next?"
- User asks "what's the status?"
- User asks "where am I in the pipeline?"
- At the start of a session to orient the user
- After any stage completes to suggest next steps

## Best Practices

- Always check actual files/database before reporting status
- Provide clear, actionable next steps
- Explain WHY each stage matters
- Offer both incremental (next stage) and bulk (generate) options
- Show progress to keep users motivated
