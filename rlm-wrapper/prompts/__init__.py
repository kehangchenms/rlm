"""
Prompt modules for appraisal review.

This package contains modular prompt sections that can be composed
based on the question category being processed.
"""

from .universal import (
    INTRODUCTION,
    CRITICAL_FORMATTING,
    SECTION_A_STANDARD,
    SECTION_A1_EVALUATIVE,
    CRITICAL_INSTRUCTIONS,
)
from .section_b_value import SECTION_B_VALUE_CONCLUSIONS
from .section_c_reconciliation import SECTION_C_RECONCILIATION
from .section_d_site import SECTION_D_SITE_VALUATION
from .section_e_findings import SECTION_E_REVIEWER_FINDINGS
from .section_f_risk import SECTION_F_RISK_ASSESSMENT
from .section_g_expanded import SECTION_G_EXPANDED_INSIGHTS
from .section_h_dcf import SECTION_H_DCF_ANALYSIS
from .section_i_property import SECTION_I_PROPERTY_INFO

__all__ = [
    # Universal sections
    "INTRODUCTION",
    "CRITICAL_FORMATTING",
    "SECTION_A_STANDARD",
    "SECTION_A1_EVALUATIVE",
    "CRITICAL_INSTRUCTIONS",
    # Category-specific sections
    "SECTION_B_VALUE_CONCLUSIONS",
    "SECTION_C_RECONCILIATION",
    "SECTION_D_SITE_VALUATION",
    "SECTION_E_REVIEWER_FINDINGS",
    "SECTION_F_RISK_ASSESSMENT",
    "SECTION_G_EXPANDED_INSIGHTS",
    "SECTION_H_DCF_ANALYSIS",
    "SECTION_I_PROPERTY_INFO",
]
