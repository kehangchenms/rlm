"""
Section I: Property Information Extraction

This section applies to property name and address extraction questions.
Used across multiple categories when extracting basic property information.
"""

SECTION_I_PROPERTY_INFO = """
================================================================================
SECTION I: PROPERTY INFORMATION EXTRACTION
================================================================================

For questions asking "What is the property name of the subject property being appraised?":
- First, look for an explicitly stated property name in the appraisal report
- IMPORTANT: If no explicit property name is found, you MUST use the property address (street number and street name) as the property name
- Do NOT return "N/A" for the answer or transcription if a property address exists in the document
- Both the answer AND transcription must contain the property name or property address - NEVER leave transcription as "N/A" if an address is available
- Format: Provide just the street number and street name (e.g., "4322 Glenmore Avenue")
- Example: If no property name but address "4322 Glenmore Avenue" exists, answer should explain this and transcription MUST be "4322 Glenmore Avenue"

For questions asking "What is the property address (street number and street name) of the subject property being appraised?":
- Extract ONLY the street number and street name (e.g., "4322 Glenmore Avenue")
- Do NOT include city, state, or zip code as those are asked in separate questions
"""
