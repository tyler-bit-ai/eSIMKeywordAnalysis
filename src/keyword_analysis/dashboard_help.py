"""Single source of truth for dashboard help and section explanations."""

from __future__ import annotations

from dataclasses import dataclass

from keyword_analysis.scoring import (
    CORE_STABLE_SCORE_THRESHOLD,
    CORE_STABLE_SIGNAL_COUNT,
    HIGH_PRIORITY_THRESHOLD,
    MEDIUM_PRIORITY_THRESHOLD,
    RISING_SCORE_THRESHOLD,
    RISING_SIGNAL,
    SIGNAL_WEIGHTS,
)


@dataclass(frozen=True)
class DashboardSectionSpec:
    id: str
    title: str
    business_meaning: str
    how_to_use: str
    scoring_note: str


@dataclass(frozen=True)
class ScoreRuleSpec:
    title: str
    summary: str
    formula_steps: tuple[str, ...]
    signal_weights: dict[str, int]
    marketing_priority_rules: tuple[str, ...]
    bucket_rules: tuple[str, ...]


SECTION_SPECS: tuple[DashboardSectionSpec, ...] = (
    DashboardSectionSpec(
        id="kpi",
        title="Top KPIs",
        business_meaning="지금 데이터셋에서 바로 주목할 타깃 규모와 변동성을 빠르게 판단하는 요약 카드입니다.",
        how_to_use="High Priority Targets와 Rising Keywords가 많으면 지금 바로 콘텐츠나 랜딩 페이지 실험을 시작할 후보가 많다는 뜻입니다.",
        scoring_note="이 카드는 이미 계산된 priority score, keyword bucket, noisy 판정을 집계한 결과입니다.",
    ),
    DashboardSectionSpec(
        id="action_views",
        title="Action Views",
        business_meaning="실행 우선순위별로 키워드를 바로 나눠 보는 운영용 뷰입니다.",
        how_to_use="Target Now는 즉시 집행, Watch는 추적 관찰, Review Manually는 사람이 직접 걸러야 하는 키워드로 보면 됩니다.",
        scoring_note="marketing_priority, keyword_bucket, is_noisy 조건으로 분류됩니다.",
    ),
    DashboardSectionSpec(
        id="marketing_exports",
        title="Marketing Exports",
        business_meaning="랜딩 페이지 주제와 콘텐츠 브리프 주제를 빠르게 뽑는 마케팅 실무용 후보 목록입니다.",
        how_to_use="Landing Page Candidates는 직접 전환을 노리는 페이지 기획에, Content Brief Candidates는 비교/가이드형 콘텐츠 기획에 사용합니다.",
        scoring_note="follow_on_modifier와 priority_score를 기준으로 마케팅 제작 용도에 맞는 키워드를 선별합니다.",
    ),
    DashboardSectionSpec(
        id="target_comparison",
        title="Korea Marketing Target Comparison",
        business_meaning="한국 eSIM 관련 키워드를 한 표에서 비교해 어떤 키워드가 더 강한 신호를 받는지 판단하는 기준 표입니다.",
        how_to_use="priority_score가 높고 observed_signals가 다양한 키워드를 우선 검토하고, origin_seeds와 raw_variants로 맥락을 확인합니다.",
        scoring_note="priority_score, marketing_priority, keyword_bucket, observed_signals가 핵심 판단 기준입니다.",
    ),
    DashboardSectionSpec(
        id="modifier_comparison",
        title="Modifier Comparison",
        business_meaning="best, unlimited data, with phone number 같은 수식어 유형별 시장성을 비교하는 표입니다.",
        how_to_use="평균 점수가 높은 modifier는 별도 랜딩 페이지나 광고 그룹으로 분리할 가치가 있습니다.",
        scoring_note="같은 modifier 그룹의 keyword_count와 avg_priority_score를 집계합니다.",
    ),
    DashboardSectionSpec(
        id="signal_summary",
        title="Signal Badge Summary",
        business_meaning="각 키워드가 어떤 Google 신호에서 반복적으로 관찰되는지 보여주는 신뢰도 요약입니다.",
        how_to_use="autocomplete, related_search, trends_related가 함께 잡히는 경우를 더 믿고 우선순위를 높게 해석합니다.",
        scoring_note="observed_signals를 풀어서 signal별 keyword_count와 평균 점수를 보여줍니다.",
    ),
    DashboardSectionSpec(
        id="seed_lineage",
        title="Root Seed Lineage",
        business_meaning="어떤 seed query가 실제 유효한 파생 키워드를 많이 만들어내는지 보는 시드 효율 분석입니다.",
        how_to_use="효율이 높은 seed는 향후 재수집, 확장 실험, 마케팅 카테고리 확장에 우선 사용합니다.",
        scoring_note="origin_seeds를 분해해서 seed별 keyword_count와 평균 점수를 집계합니다.",
    ),
    DashboardSectionSpec(
        id="snapshot_delta",
        title="Snapshot Delta",
        business_meaning="이전 스냅샷과 비교해 새로 뜨거나 사라진 키워드, 순위 변화 키워드를 보는 변화 감지 도구입니다.",
        how_to_use="새로 뜬 키워드는 빠른 테스트 후보로, score가 급상승한 키워드는 우선 모니터링 대상으로 봅니다.",
        scoring_note="이전/현재 ranked_keywords.csv를 비교해 new, disappeared, rank_delta, bucket change를 계산합니다.",
    ),
)


def get_section_spec(section_id: str) -> DashboardSectionSpec:
    for spec in SECTION_SPECS:
        if spec.id == section_id:
            return spec
    raise KeyError(f"Unknown dashboard section: {section_id}")


def build_score_rule_spec() -> ScoreRuleSpec:
    return ScoreRuleSpec(
        title="How scoring works",
        summary="이 점수는 실제 검색량이 아니라, 여러 Google 공개 신호에서 반복 관측된 정도와 상업적 의도를 합쳐 우선순위를 계산한 값입니다.",
        formula_steps=(
            "signal weight 합계에 신호 종류 수 보너스를 더합니다.",
            "더 높은 위치에 나온 키워드는 rank bonus를 받습니다.",
            "best, cheap, plan, prepaid, unlimited 같은 상업적 표현이 있으면 commercial bonus가 붙습니다.",
            "같은 키워드가 여러 번 관측될수록 observation count가 누적됩니다.",
        ),
        signal_weights=SIGNAL_WEIGHTS,
        marketing_priority_rules=(
            f"high: priority_score >= {HIGH_PRIORITY_THRESHOLD}",
            f"medium: priority_score >= {MEDIUM_PRIORITY_THRESHOLD} and < {HIGH_PRIORITY_THRESHOLD}",
            f"test: priority_score < {MEDIUM_PRIORITY_THRESHOLD}",
        ),
        bucket_rules=(
            f"core_stable: signal_count >= {CORE_STABLE_SIGNAL_COUNT} and priority_score >= {CORE_STABLE_SCORE_THRESHOLD}",
            f"rising: evidence_signals includes {RISING_SIGNAL} and priority_score >= {RISING_SCORE_THRESHOLD}",
            "niche_long_tail: 위 두 조건에 모두 해당하지 않는 나머지 키워드",
        ),
    )


def build_help_payload() -> dict[str, object]:
    score_rule = build_score_rule_spec()
    return {
        "score_rule": score_rule,
        "sections": SECTION_SPECS,
    }
