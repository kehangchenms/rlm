"""
Section B: Value Conclusions

This section applies to Category 5 - "Value Conclusion(s) in the Report Under Review"
Contains specialized instructions for extracting and formatting value conclusions.
"""

SECTION_B_VALUE_CONCLUSIONS = """
================================================================================
SECTION B: SPECIALIZED APPROACH FOR "Value Conclusion(s) in the Report Under Review"
================================================================================

When you encounter any question containing "Value Conclusion(s) in the Report Under Review", follow these SPECIFIC instructions:

Step 1: Focus on Key Sections First
- Always start by scanning the Letter of Transmittal and Reconciliation sections of the appraisal report.
- These sections typically summarize the final opinions of value and should be the primary source of the Market Value conclusion.
- IMPORTANT: Always record the page numbers where you find each section in the format [Page X] or [Page X-Y] (e.g., [Page 2] or [Page 7-8]).

Step 2: Market Value As Is (Required)
- The Market Value As Is conclusion is always required. Record the following details:
  1. Property/Phase/Premise (if applicable)
  2. Value Type = Market Value As Is
  3. Property Rights (e.g., Fee Simple, Leased Fee)
  4. Date of Value
  5. Value Conclusion (numeric and unit basis, e.g., $380,000 or $7.02/SF)

Step 3: Other Value Types (Optional)
- After capturing Market Value As Is, scan the rest of the appraisal report for any of the additional value types listed in the Value Type Checklist below.
- If a value is provided, extract and record the same details as above, including the page number where found in the format [Page X] or [Page X-Y].
- If not provided, mark the field as "Not Reported."

Step 4: Note Assumptions/Conditions
- If extraordinary assumptions or hypothetical conditions apply to any reported value, include them in the notes.

Additional Rule
- If the Value Type is one of the following:
  - Insurable Replacement Cost
  - Allocation - Furniture, Fixtures, and Equipment (FF&E) (in value above)
  - Allocation - Intangible/Business Value (in value above)
- Then the Property Rights must always be set to "N/A" (option 5), regardless of how it is stated in the appraisal report.

Value Type Checklist
1. Market Value As Is (Required)
2. Prospective Market Value Upon Completion (Optional)
3. Prospective Market Value Upon Stabilization (Optional)
4. Insurable Replacement Cost (Optional)
5. Hypothetical Market Value As If Complete (Optional)
6. Hypothetical Market Value As If Stabilized (Optional)
7. Hypothetical Market Value As If Vacant & Available for Sale or Lease (Optional)
8. Hypothetical Market Value As If Vacant & Available for Lease (Go Dark) (Optional)
9. Market Value As Is of the Going Concern (Optional)
10. Market Value of the Going Concern Upon Completion (Optional)
11. Market Value of the Going Concern Upon Stabilization (Optional)
12. Allocation - Market Value of the Real Estate (in value above) (Optional)
13. Allocation - Furniture, Fixtures, and Equipment (FF&E) (in value above) (Optional)
14. Allocation - Intangible/Business Value (in value above) (Optional)
15. Aggregate Sale Proceeds (Optional)
16. Disposition Value (Optional)
17. Liquidation Value (Optional)

Property Rights Checklist
1. Fee Simple
2. Leased Fee
3. Leasehold
4. Other
5. N/A

When Transcribing the answer for the "Value Conclusion(s) in the Report Under Review" question:
- Format each value type the same as in the answer
- Do NOT include the summary or sections reviewed
- The transcription may be longer than 100 characters due to the detailed nature of this question.
- Do NOT include the notes or page numbers in the transcription.
- Do NOT include the value types that were "Not Reported" in the transcription.
- Separate each value type entry with a blank line.

FORMAT FOR VALUE CONCLUSIONS QUESTION:
When answering the "Value Conclusion(s) in the Report Under Review" question, format your response as follows:

{
    "answer": "
SUMMARY:
[Provide a brief summary stating which value conclusions were found, their amounts, and which value types were Not Reported]

SECTIONS REVIEWED:
- Letter of Transmittal [Page X-Y]
- Executive Summary [Page X-Y]
- Reconciliation [Page X-Y]
[List all sections reviewed with their page numbers]

VALUE CONCLUSIONS:
1. Market Value As Is [Page X]
   Property/Phase/Premise: [name if applicable]
   Property Rights: [Fee Simple/Leased Fee/etc.]
   Date of Value: [date]
   Value Conclusion: [amount]
   Notes: [any assumptions/conditions]

2. [Next Value Type if found] [Page X]
   Property/Phase/Premise: [name if applicable]
   Property Rights: [appropriate rights or N/A]
   Date of Value: [date]
   Value Conclusion: [amount]
   Notes: [any assumptions/conditions]

[Continue for all found value types]
",
"transcription": "
1. Market Value As Is
   Property/Phase/Premise: Convenience Store/Gas Station
   Property Rights: Fee Simple
   Date of Value: August 4, 2024
   Value Conclusion: $4,170,000

2. Market Value As Is
   Property/Phase/Premise: Self Storage Facility
   Property Rights: Fee Simple
   Date of Value: August 4, 2024
   Value Conclusion: $900,000

3. Insurable Replacement Cost
   Property/Phase/Premise: Convenience Store/Gas Station
   Property Rights: N/A
   Date of Value: August 4, 2024
   Value Conclusion: $1,226,670

4. Insurable Replacement Cost
   Property/Phase/Premise: Self Storage Facility
   Property Rights: N/A
   Date of Value: August 4, 2024
   Value Conclusion: $695,756

[Continue for all found value types]
"
}
"""
