"""
Underwriting configuration — every constant here traces to the analysis in this
repo's valuation memos (NET_WORTH_AND_GITHUB_BENCHMARK.md, VALUATION_MEMO_v2).
Tune these; the pipeline is deterministic given inputs + config.
"""

# ---------------------------------------------------------------- valuation ----
VALUATION = {
    "cocomo_rate_per_pm": 6_000,        # blended global loaded $/person-month
    "cocomo_a": 2.4, "cocomo_b": 1.05,  # organic basic COCOMO
    "dedup_default": 0.60,              # unique-SLOC fraction (variant discount)
    "replacement_net_multiplier": 0.10,  # pre-revenue/illiquidity haircut on gross
    "bom_deployable_unit": 8_000,
    "bom_platform_unit": 12_000,
    "bom_experiment_unit": 1_200,
    "bom_haircut": 0.50,
    "quality_tested_unit": 7_000,
    "quality_scrap_per_repo": 500,
    "quality_haircut": 0.60,
    "embodied_monthly": 9_000,
    "embodied_ai_tooling": 18_000,
    "income_arr_multiple": 2.0,         # used only when recurring_revenue > 0
    "income_option_value": 25_000,      # pre-revenue optionality
    "eligible_exclusion": 0.80,         # ineligible-collateral exclusion on central value
}

# ------------------------------------------------------------- risk factors ----
# weight sums to 1.0; each factor value is 0 (low risk) .. 1 (high risk)
RISK_WEIGHTS = {
    "no_recurring_revenue": 0.22,
    "ip_not_entity_owned": 0.18,
    "illiquid_market": 0.15,
    "key_person_single_author": 0.12,
    "low_test_coverage": 0.10,
    "security_hygiene": 0.08,
    "duplication_concentration": 0.08,
    "weak_deployability": 0.07,
}
RISK_GRADE_BANDS = [          # (max_score_inclusive, grade)
    (0.20, "A"), (0.35, "B"), (0.55, "C"), (0.75, "D"), (1.01, "E"),
]
# advance rate (loan-to-value) by grade for illiquid IP collateral
ADVANCE_RATE = {"A": 0.50, "B": 0.38, "C": 0.27, "D": 0.17, "E": 0.10}

# coverage target: test_functions / implemented_defs at/above this = full credit
TEST_COVERAGE_TARGET = 0.20

# ------------------------------------------------------------- benchmark CDF ---
# GitHub all-time, type:user totals measured via search API (point-in-time).
GITHUB_POPULATION = {
    "total_users": 131_273_884,
    "users_with_repo": 60_706_835,
    # users with MORE than N repos  (for repo-rank percentile)
    "repos_gt": {10: 9_264_265, 100: 243_297, 175: 81_684, 1000: 3_196, 5000: 241},
    # users with MORE than N followers
    "followers_gt": {4: 4_140_957},
    "followers_gte": {100: 147_048, 1000: 8_230},
}

# ----------------------------------------------------------------- decision ----
DECISION_RULES = {
    "min_borrowing_base_to_offer": 5_000,
    "grades_requiring_conditions": {"C", "D", "E"},
}
