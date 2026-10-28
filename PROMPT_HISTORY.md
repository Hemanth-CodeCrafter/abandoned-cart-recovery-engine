# ChatGPT Prompt History
## Abandoned Cart Recovery & Attribution Engine

### 1. Understanding the Assignment

**Prompt 1:** I have received this assignment and need to complete it within the given time. Help me understand the requirements, expected deliverables, and the most practical way to approach the project as a fresher.

**Prompt 2:** Review the assignment guidelines and FAQ. Explain what I need to submit, how the solution will be evaluated, and what I should prioritize to deliver a working implementation.

### 2. Planning the Implementation

**Prompt 3:** Help me choose the appropriate backend framework for this assignment. Can I use FastAPI instead of Django, and how should I structure the project?

**Prompt 4:** Guide me through the implementation step by step, as a senior backend developer would guide a fresher. Keep the solution practical, maintainable, and aligned with the assignment requirements.

### 3. Generating and Implementing the Code

**Prompt 5:** Help me implement a deterministic synthetic-data generator with configurable dataset sizes and a fixed random seed so that I can reproduce the same output.

**Prompt 6:** Help me implement the required entities, relationships, identifiers, SQL schema, and data exports while maintaining referential integrity across the generated datasets.

**Prompt 7:** Help me introduce labelled data-quality anomalies and implement validation checks that distinguish intentional anomalies from unexpected errors.

**Prompt 8:** Help me implement the abandoned-cart eligibility rules, including the inactivity threshold and handling carts that have already been purchased or recovered.

**Prompt 9:** Help me implement consent validation at message-send time and enforce the customer communication frequency cap.

**Prompt 10:** Help me implement order attribution using qualifying click events, customer identity, send status, and the attribution time window.

**Prompt 11:** Review the existing implementation before making further changes. Identify edge cases and improve the code without unnecessarily rewriting functionality that already works.

### 4. Testing and Debugging

**Prompt 12:** Help me write automated tests for the core business rules, including abandonment eligibility, consent, frequency caps, and order attribution.

**Prompt 13:** Help me validate the generated datasets for missing references, duplicate identifiers, inconsistent timestamps, incorrect cart totals, and other data-integrity issues.

**Prompt 14:** Show me how to verify that the generator produces reproducible results when I use the same seed and scale.

**Prompt 15:** Help me verify the generated SQL database by checking the expected tables and foreign-key integrity using SQLite.

**Prompt 16:** Help me troubleshoot test failures or warnings and distinguish actual implementation errors from non-blocking warnings.

### 5. Documentation and Final Verification

**Prompt 17:** Help me prepare a clear README with installation instructions, dependencies, data-generation commands, validation steps, test commands, API startup instructions, and verification examples.

**Prompt 18:** Help me document the data model, entities, relationships, identifiers, timestamps, and important fields in a data dictionary.

**Prompt 19:** Review the submission requirements and help me document the assumptions, limitations, AI assistance, and verification performed without claiming functionality that has not been tested.

### 6. How I Used ChatGPT

I used ChatGPT throughout the development process to understand the requirements, plan the implementation, generate and modify code, implement business rules, develop tests, troubleshoot issues, and prepare documentation.

ChatGPT generated substantial portions of the code. I applied the suggested changes in my local project and ran the implementation to check its behaviour. I used the results of these checks to assess whether the generator, validation logic, tests, and SQL schema were working as expected.

### 7. Verification Performed

During development, I ran the following checks:

- Generated starter and full datasets using a fixed seed.
- Ran the data validator at both scales.
- Checked reproducibility using the same seed and scale.
- Executed the automated test suite.
- Loaded the generated SQL into SQLite and checked the table count and foreign-key integrity.

The recorded results showed successful generation, no reported validation errors, four labelled anomaly warnings, reproducible output, passing tests, and eleven SQLite tables with no foreign-key violations in the database check.

These checks helped me identify and verify the behaviour of the implementation. They do not guarantee that every possible edge case has been covered.

### 8. Record Accuracy

This document summarizes the main types of prompts I used during my ChatGPT-assisted development. The prompt entries are reconstructed summaries, not verbatim copies of every message in the original conversation.

I acknowledge that ChatGPT contributed substantially to the implementation. I am responsible for reviewing the submitted project, understanding its core logic, explaining my design decisions, and being transparent about its limitations.

