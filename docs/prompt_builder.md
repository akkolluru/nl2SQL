# Prompt Builder Component

## Purpose

The prompt builder component creates structured prompts that guide the LLM in generating appropriate SQL queries. It combines user questions with database schema information to provide context-aware prompting.

## Functionality

- **Prompt Composition**: Combines system instructions, schema information, and user questions
- **Schema Integration**: Incorporates database schema into the prompt for context
- **Instruction Formatting**: Provides clear instructions to the LLM about expected output
- **Example Integration**: Optionally includes few-shot examples to guide the model

## Key Features

- System instruction template for consistent LLM behavior
- Schema-aware prompting to ensure valid table/column usage
- Clean prompt formatting without unnecessary commentary
- Optional example-based guidance

## System Instructions

The component includes a system instruction template that tells the LLM:
- To convert English questions into single MySQL SELECT queries
- To output only SQL without commentary
- To use only tables/columns from the provided schema
- To prefer safe queries that don't modify data

## How It Works

1. Takes a user question and database schema as input
2. Combines the system instructions with the schema information
3. Optionally adds few-shot examples if provided
4. Formats the user question and requests SQL output
5. Returns a complete prompt ready for LLM consumption

## Prompt Structure

The generated prompt follows this structure:
```
[SYSTEM_INSTR]
Database schema (compact):
[schema_text]

[Examples (optional)]
[examples_block]

Question: [user_question]
SQL:
```

## Safety Considerations

- Ensures schema information is properly formatted for LLM consumption
- Prevents injection of malicious content through proper formatting
- Maintains consistency in LLM instructions to ensure predictable behavior