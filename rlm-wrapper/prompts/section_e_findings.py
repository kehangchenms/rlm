"""
Section E: Reviewer Findings with Data Extraction

This section applies to Category 9 - "Reviewer Findings, Opinions and Conclusions"
Contains specialized instructions for 4 questions requiring narrative + data extraction.
"""

SECTION_E_REVIEWER_FINDINGS = """
================================================================================
SECTION E: REVIEWER FINDINGS WITH DATA EXTRACTION (Group #9)
================================================================================

Group #9 contains 4 questions requiring both narrative evaluation AND structured data extraction.
For each question, scan relevant sections, extract required data fields while reading, formulate
narrative findings, and output in the required format.

---
QUESTION 1: Sales Comparison Approach (Group #9, Question 1)
---

When answering "Sales Comparison Approach - What does the appraisal report state about the Sales
Comparison Approach (e.g., comparables, adjustments, and final conclusion), and as an expert reviewer,
what are your findings, opinions, and conclusions about the adequacy, support, and credibility of
this approach?", you must:

1. Scan the Sales Comparison Approach section
2. Extract the following data fields:
   - Range of Comparable Sales - Unadjusted Unit Range: Look for the range of unadjusted sales prices per unit (e.g., $32.31 - $69.59/SF)
   - Adjusted Unit Range: Look for the range of adjusted sales prices per unit after adjustments (e.g., $34.25 - $55.51/SF)
   - Subject Unit Conclusion: Look for the final concluded unit value for the subject property (e.g., $38.00/SF)
   - Number of Comparable Sales: Count how many comparable sales were used (e.g., Six, Three, etc.)
   - Adjustment Grid included in Appraisal? (Yes/No): Check if an adjustment grid/table is present
3. Provide narrative evaluation of adequacy, support, and credibility

OUTPUT FORMAT:
{
"answer":
A. Data Extraction Fields:
Range of Comparable Sales - Unadjusted Unit Range: [extracted value or "Not stated"]
Adjusted Unit Range: [extracted value or "Not stated"]
Subject Unit Conclusion: [extracted value or "Not stated"]
Number of Comparable Sales: [extracted value or "Not stated"]
Adjustment Grid included in Appraisal? (Yes/No): [Yes/No or "Not stated"]

B. Narrative Question Response:
[Your narrative evaluation with findings, opinions, and conclusions. Include page citations using [Page X] format.]
",
"transcription": [Brief summary focusing on key findings]
}

---
QUESTION 2: Income Approach (Group #9, Question 2)
---

When answering "Income Approach - What does the appraisal report state about the Income Approach
(e.g., assumptions, inputs, capitalization), and as an expert reviewer, what are your findings,
opinions, and conclusions regarding the support for inputs and credibility of the conclusion?", you must:

1. Scan the Income Approach section
2. Extract the following data fields:
   - Estimated NOI of property ($): Net Operating Income in dollars (e.g., 148,271)
   - Current Occupancy (%): Current occupancy percentage (e.g., 95.04)
   - Stabilized Occupancy (%): Stabilized occupancy percentage (e.g., 91)
   - Capitalization Method Employed: Direct Capitalization / DCF (Discounted Cash Flow) / Other
   - Capitalization Rate (%): Cap rate used (e.g., 8.7)
   - Discount Rate (%): Discount rate if DCF method used
   - Income Growth Rate (%): Projected income growth rate
   - Expense Growth Rate (%): Projected expense growth rate
   - Terminal Cap Rate (%): Terminal cap rate if DCF method used
3. Provide narrative evaluation of support for inputs and credibility

OUTPUT FORMAT:
{
"answer": "
A. Data Extraction Fields:
Estimated NOI of property ($): [extracted value or "Not stated"]
Current Occupancy (%): [extracted value or "Not stated"]
Stabilized Occupancy (%): [extracted value or "Not stated"]
Capitalization Method Employed: [Direct/DCF/Other or "Not stated"]
Capitalization Rate (%): [extracted value or "Not stated"]
Discount Rate (%): [extracted value or "Not stated" or "N/A"]
Income Growth Rate (%): [extracted value or "Not stated" or "N/A"]
Expense Growth Rate (%): [extracted value or "Not stated" or "N/A"]
Terminal Cap Rate (%): [extracted value or "Not stated" or "N/A"]

B. Narrative Question Response:
[Your narrative evaluation with findings, opinions, and conclusions. Include page citations using [Page X] format.]
",
"transcription": [Brief summary focusing on key findings]
}

---
QUESTION 3: Cost Approach (Group #9, Question 3)
---

When answering "Cost Approach - What does the appraisal report state about the Cost Approach
(land value, replacement cost, depreciation), and as an expert reviewer, what are your findings,
opinions, and conclusions about its reliability and support? Cite pages. If the Cost Approach is
not developed, explain why and evaluate whether that omission is reasonable.", you must:

1. Scan the Cost Approach section (or check if it was not developed)
2. Extract the following data fields:
   - Land Value ($): Concluded land value in dollars
   - Depreciation ($ or %): Depreciation amount in dollars or percentage
3. Provide narrative evaluation of reliability and support (or explain omission)

OUTPUT FORMAT:
{
"answer":
A. Data Extraction Fields:
Land Value ($): [extracted value or "Not stated" or "N/A - Cost Approach not developed"]
Depreciation ($ or %): [extracted value or "Not stated" or "N/A - Cost Approach not developed"]

B. Narrative Question Response:
[Your narrative evaluation with findings, opinions, and conclusions. If Cost Approach not developed, explain why and evaluate reasonableness of omission. Include page citations using [Page X] format.]
",
"transcription": [Brief summary focusing on key findings or noting approach was not developed]
}

---
QUESTION 4: Reconciliation (Group #9, Question 4)
---

When answering "Reconciliation - What does the appraisal report state about the Reconciliation,
and as an expert reviewer, what are your findings, opinions, and conclusions about the adequacy,
support, and credibility of the reconciliation?", you must evaluate the reconciliation against
the following 8 criteria:

EIGHT-POINT RECONCILIATION CRITERIA:
1. Significant mathematical calculations are presented clearly and accurately
2. The appraisal appears to be internally consistent and does not contradict itself
3. Each approach to value presented reflects recognized valuation methods and techniques and is logical
4. The weight attributed to each approach to value is supported and appears reasonable in light of the information contained in the appraisal
5. The final value conclusion(s) logically reconcile with the values derived through each approach to value and the weights attributed
6. The exclusion of any approaches to value is supported with a logical explanation and appears reasonable
7. The Highest and Best Use analysis appears to be reasonable and well supported
8. The amount of detail provided with respect to information analyzed in developing the value conclusion(s) appears consistent with its significance

EVALUATION APPROACH:
- For each criterion, assess whether it is met, not met, or not applicable
- Extract supporting evidence from the appraisal with page citations
- Provide an overall Yes/No/N/A determination

OUTPUT FORMAT:
{
"answer": "Yes / No / N/A

Supporting Evidence:
Evaluate each of the 8 criteria:

1. Mathematical calculations: [Assessment with evidence and page citations]
2. Internal consistency: [Assessment with evidence and page citations]
3. Recognized valuation methods: [Assessment with evidence and page citations]
4. Weight attribution support: [Assessment with evidence and page citations]
5. Value reconciliation logic: [Assessment with evidence and page citations]
6. Approach exclusion justification: [Assessment with evidence and page citations]
7. Highest and Best Use support: [Assessment with evidence and page citations]
8. Detail consistency: [Assessment with evidence and page citations]

Overall Conclusion: [Summarize overall adequacy, support, and credibility of reconciliation]
",
"transcription": [Brief summary of reconciliation adequacy - e.g., "Adequate and well-supported" or "Weak reconciliation - insufficient weighting justification"]
}

NOTE: If reconciliation is not developed in the appraisal, answer "N/A" and explain why.
"""
