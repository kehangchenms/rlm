"""
Section G: Expanded Appraisal Insights (Group 20)

This section applies to Category 20 - Expanded Appraisal Insights
Contains 21 specialized questions (Q1-Q21) with detailed prompts.

Note: This is a large section. For efficiency, you may want to use only the
relevant subsection based on which Q1-Q21 questions are being processed.
"""

# Q1: Non-Mathematical Narrative Consistency
SECTION_G_Q1_NARRATIVE = """
--------------------------------------------------------------------------------
Q1: NON-MATHEMATICAL NARRATIVE CONSISTENCY & LOGIC REVIEW
--------------------------------------------------------------------------------

**Non-Mathematical Narrative Consistency & Logic Review**

You are a valuation quality-assurance reviewer. Review the report for **NON-MATHEMATICAL** issues and clearly explain every inconsistency, error, or flaw in the narrative, assumptions, definitions, and logic.

**Critical constraints:**
- Do **NOT** perform or re-check arithmetic
- Assume all numerical calculations have been reviewed separately
- Work only from the text/content provided

### REVIEW FOR THE FOLLOWING NON-MATH AREAS

#### Internal contradictions
- Property facts stated differently in different sections
- Conflicting rates, values, dates, or conclusions
- Narrative descriptions that conflict with tables, charts, or exhibits

#### Definition / terminology inconsistencies
- Terms defined or used inconsistently
- Inconsistent use of units or time bases
- Misuse of appraisal terminology

#### Methodology / logic issues
- Inputs that don't support conclusions
- Unsupported or contradictory adjustments
- Inconsistent treatment between approaches

#### Other issues
- Date mismatches
- Mislabeled exhibits
- Unclear extraordinary assumptions

### OUTPUT FORMAT
List each issue numbered 1-n with:
- SHORT TITLE OF ISSUE
- Type: (Contradiction / Definition/Terminology / Methodology/Logic / Other)
- Pages/Sections
- Description
- Example/Quote
- Correct/Expected Logic
- Severity (Red / Yellow / Green)

End with Summary of Non-Mathematical Inconsistencies and overall Traffic Light Rating.
"""

# Q2: Math Issues (Non-Metric)
SECTION_G_Q2_MATH = """
--------------------------------------------------------------------------------
Q2: MATH ISSUES (NON-METRIC)
--------------------------------------------------------------------------------

**Math Issues (Non-Metric) - Arithmetic & Numeric Consistency Review**

Check the appraisal for math-related problems. Work only from provided text.

### METRICS TO EXCLUDE FROM REVIEW
Do NOT review these metrics:
- GIM, GRM, EGIM, NOI Multiplier, Cap Rate, GPM, P/Rev
- EBITDA, P/EBITDA, EBITDA Margin, NOI Margin
- Cash-on-Cash Return, Yield on Cost, DSCR, Debt Yield

### FOCUS ONLY ON
1. Incorrect calculations (NOI, cash flow, unit prices, totals)
2. Inconsistent numbers between sections
3. Percentage and rate problems
4. Basic arithmetic errors

### OUTPUT FORMAT
List each math issue numbered 1-n with:
- SHORT TITLE OF MATH ISSUE
- Type: (Incorrect Calculation / Inconsistent Numbers / Percentage/Rate Problem / Basic Arithmetic Error)
- Pages/Sections
- Description
- Example/Numbers
- Correct/Expected Math
- Severity (Red / Yellow / Green)

End with Summary of Math Issues and overall Traffic Light Rating.
"""

# Q3-Q17: Metric QA Questions (shared prompt)
SECTION_G_Q3_Q17_METRICS = """
--------------------------------------------------------------------------------
Q3-Q17: METRIC QA QUESTIONS
--------------------------------------------------------------------------------

You are a **senior valuation and financial analysis assistant**.

For each metric question, respond with:
1. **Metric name** - Full name and acronym
2. **Plain-English definition** - What it measures
3. **Standard formula** - With variable definitions
4. **Required data inputs** - Key data needed
5. **Interpretation of the provided value** - Low/typical/high assessment

Use traffic-light rating:
- **RED** = High concern / outside typical ranges
- **YELLOW** = Borderline / near edge of typical ranges
- **GREEN** = Consistent with market norms

The 15 metric questions are:
- Q3: GIM - Gross Income Multiplier
- Q4: GRM - Gross Rent Multiplier
- Q5: EGIM - Effective Gross Income Multiplier
- Q6: NOI Multiplier - Price/NOI
- Q7: Cap Rate - Capitalization Rate
- Q8: GPM - Gross Profit Margin
- Q9: P/Rev - Price to Revenue
- Q10: EBITDA
- Q11: P/EBITDA
- Q12: EBITDA Margin
- Q13: NOI Margin
- Q14: Cash-on-Cash Return (CoC)
- Q15: Yield on Cost (YoC)
- Q16: DSCR - Debt Service Coverage Ratio
- Q17: Debt Yield
"""

# Q18: Business Value / EBITDA Multiplier
SECTION_G_Q18_EBITDA = """
--------------------------------------------------------------------------------
Q18: BUSINESS VALUE / EBITDA MULTIPLIER SUPPORT
--------------------------------------------------------------------------------

Answer: How was the business value or EBITDA multiplier determined and supported?

Structure response in three parts:
1. **Answer (Detailed)**:
   - If multiplier IS presented: identify location, extract values, explain determination/support, note gaps
   - If multiplier is NOT presented: state absence, identify alternative methods, evaluate reasonableness
   - Comment on consistency with rest of appraisal
   - Summarize strengths and weaknesses

2. **Transcription**: 2-5 sentence summary starting with property type

3. **Traffic Light Rating**:
   - Green: Appropriate use/non-use, reasonably explained
   - Yellow: Notable gaps or ambiguities
   - Red: Serious deficiencies or material omissions
"""

# Q19: Year of Construction & Remaining Economic Life
SECTION_G_Q19_YOC_REL = """
--------------------------------------------------------------------------------
Q19: YEAR OF CONSTRUCTION & REMAINING ECONOMIC LIFE (YOC / REL)
--------------------------------------------------------------------------------

Answer: What is the year of construction (YOC) and remaining economic life (REL)?

1. **Answer (Detailed)**:
   A. Identify YOC (original, renovations, effective age)
   B. Identify REL (years, derivation method)
   C. Comment on consistency and support
   D. If not stated, evaluate reasonableness of omission

2. **Transcription**: 2-5 sentences starting with property type

3. **Traffic Light Rating**:
   - Green: YOC and REL clearly stated, consistent
   - Yellow: Present but unclear or minor inconsistencies
   - Red: Missing, contradictory, or materially inconsistent
"""

# Q20: Discounted Cash Flow (DCF)
SECTION_G_Q20_DCF = """
--------------------------------------------------------------------------------
Q20: DISCOUNTED CASH FLOW (DCF)
--------------------------------------------------------------------------------

Determine whether DCF exists. If yes, extract components and evaluate.

1. **Detailed DCF Review**:
   A. DCF Presence (Yes/No + page refs)
   B. DCF Components (if present)
   C. Mathematical Verification
   D. Reasonableness Analysis
   E. Market Support
   F. Quality Control Summary

2. **Transcription**: 3-6 sentences summary

3. **Traffic Light Rating**:
   - Green: Present/consistent/sound OR absence is reasonable
   - Yellow: Moderate concerns or unclear omission
   - Red: Major errors/unrealistic assumptions OR inappropriate omission
"""

# Q21: SBA Use, REL, and Approaches Review
SECTION_G_Q21_SBA = """
--------------------------------------------------------------------------------
Q21: SBA USE, REL, AND APPROACHES REVIEW
--------------------------------------------------------------------------------

Review for SBA-related expectations. For each of 5 tasks, provide Answer, Transcription, and Flag.

1. **SBA Use Indicated**: Is report for SBA use?
2. **SBA as Intended User**: Is SBA listed as intended user?
3. **Remaining Economic Life Present & Value**: Is REL provided?
4. **Remaining Economic Life vs 25 Years**: Compare REL to 25 years
5. **Approaches to Value**: Which approaches are developed?

Each task requires:
- Answer: With page numbers
- Transcription: 1-3 sentence summary
- Flag: Red / Yellow / Green (never N/A)

End with overall summary and Traffic Light Rating.
"""

# Combined Section G (all Q1-Q21)
SECTION_G_EXPANDED_INSIGHTS = """
================================================================================
SECTION G: GROUP 20 - EXPANDED APPRAISAL INSIGHTS (21 Questions)
================================================================================

This section covers specialized questions for expanded appraisal insights including:
- Q1: Non-Mathematical Narrative Consistency & Logic Review
- Q2: Math Issues (Non-Metric)
- Q3-Q17: Metric QA Questions (15 metrics with shared instructions)
- Q18: Business Value / EBITDA Multiplier Support
- Q19: Year of Construction & Remaining Economic Life (YOC/REL)
- Q20: Discounted Cash Flow (DCF)
- Q21: SBA Use, REL, and Approaches Review

""" + SECTION_G_Q1_NARRATIVE + SECTION_G_Q2_MATH + SECTION_G_Q3_Q17_METRICS + SECTION_G_Q18_EBITDA + SECTION_G_Q19_YOC_REL + SECTION_G_Q20_DCF + SECTION_G_Q21_SBA


def get_section_g_for_questions(question_numbers: list) -> str:
    """
    Get only the relevant Section G subsections for specific questions.

    Args:
        question_numbers: List of Q numbers (1-21) being processed

    Returns:
        Combined prompt for only the relevant subsections
    """
    sections = []

    for q in question_numbers:
        if q == 1:
            sections.append(SECTION_G_Q1_NARRATIVE)
        elif q == 2:
            sections.append(SECTION_G_Q2_MATH)
        elif 3 <= q <= 17:
            if SECTION_G_Q3_Q17_METRICS not in sections:
                sections.append(SECTION_G_Q3_Q17_METRICS)
        elif q == 18:
            sections.append(SECTION_G_Q18_EBITDA)
        elif q == 19:
            sections.append(SECTION_G_Q19_YOC_REL)
        elif q == 20:
            sections.append(SECTION_G_Q20_DCF)
        elif q == 21:
            sections.append(SECTION_G_Q21_SBA)

    header = """
================================================================================
SECTION G: GROUP 20 - EXPANDED APPRAISAL INSIGHTS
================================================================================
"""
    return header + "\n".join(sections)
