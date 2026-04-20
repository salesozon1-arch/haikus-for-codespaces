import math
import re

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================
# УТИЛИТЫ
# =========================

def _safe_divide(a, b):
    if b in (0, 0.0, None) or pd.isna(b):
        return 0.0
    return a / b


def _format_money(value: float) -> str:
    return f"{value:,.0f} ₽".replace(",", " ")


def _format_number(value: float, digits: int = 0) -> str:
    return f"{value:,.{digits}f}".replace(",", " ")


def _format_percent(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}%"


def _format_delta_pct(forecast_value: float, plan_value: float, digits: int = 1) -> str:
    if plan_value in (0, 0.0, None) or pd.isna(plan_value):
        return "—"
    delta = ((forecast_value / plan_value) - 1) * 100
    return f"{delta:+.{digits}f}%"


def _delta_color_class(forecast_value: float, plan_value: float) -> str:
    if plan_value in (0, 0.0, None) or pd.isna(plan_value):
        return "neutral"
    return "positive" if forecast_value >= plan_value else "negative"


def _render_big_kpi(title: str, value: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div class="strategy-big-kpi">
            <div class="strategy-big-kpi-title">{title}</div>
            <div class="strategy-big-kpi-value">{value}</div>
            <div class="strategy-big-kpi-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_small_kpi(title: str, value: str):
    st.markdown(
        f"""
        <div class="strategy-small-kpi">
            <div class="strategy-small-kpi-title">{title}</div>
            <div class="strategy-small-kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_compare_card(metric_name: str, plan_value: str, forecast_value: str, delta_value: str, delta_class: str):
    st.markdown(
        f"""
        <div class="strategy-compare-card">
            <div class="strategy-compare-title">{metric_name}</div>
            <div class="strategy-compare-grid">
                <div class="strategy-compare-col">
                    <div class="strategy-compare-label">План</div>
                    <div class="strategy-compare-value">{plan_value}</div>
                </div>
                <div class="strategy-compare-col">
                    <div class="strategy-compare-label">Прогноз</div>
                    <div class="strategy-compare-value">{forecast_value}</div>
                </div>
                <div class="strategy-compare-col">
                    <div class="strategy-compare-label">Δ</div>
                    <div class="strategy-compare-delta {delta_class}">{delta_value}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _inject_styles():
    st.markdown(
        """
        <style>
        .strategy-panel-title {
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .strategy-block-subtitle {
            font-size: 0.8rem;
            color: #6b7280;
            margin-bottom: 0.6rem;
        }

        .strategy-big-kpi {
            background: linear-gradient(180deg, #f7f9fc 0%, #eef3f9 100%);
            border: 1px solid rgba(49, 71, 114, 0.12);
            border-radius: 16px;
            padding: 14px 16px;
            min-height: 110px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        }

        .strategy-big-kpi-title {
            font-size: 0.9rem;
            color: #5f6b7a;
            margin-bottom: 6px;
        }

        .strategy-big-kpi-value {
            font-size: 1.6rem;
            font-weight: 800;
            line-height: 1.15;
            color: #18212f;
        }

        .strategy-big-kpi-subtitle {
            font-size: 0.82rem;
            color: #708090;
            margin-top: 6px;
        }

        .strategy-small-kpi {
            background: #ffffff;
            border: 1px solid rgba(49, 71, 114, 0.10);
            border-radius: 14px;
            padding: 12px 14px;
            min-height: 84px;
            margin-bottom: 10px;
        }

        .strategy-small-kpi-title {
            font-size: 0.85rem;
            color: #68768a;
            margin-bottom: 6px;
        }

        .strategy-small-kpi-value {
            font-size: 1.12rem;
            font-weight: 700;
            color: #1b2533;
        }

        .strategy-compare-card {
            background: #ffffff;
            border: 1px solid rgba(49, 71, 114, 0.12);
            border-radius: 16px;
            padding: 16px;
            min-height: 120px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        }

        .strategy-compare-title {
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 12px;
            color: #1b2533;
        }

        .strategy-compare-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 12px;
        }

        .strategy-compare-label {
            font-size: 0.78rem;
            color: #7a8797;
            margin-bottom: 4px;
        }

        .strategy-compare-value {
            font-size: 1rem;
            font-weight: 700;
            color: #1b2533;
        }

        .strategy-compare-delta {
            font-size: 1rem;
            font-weight: 800;
        }

        .strategy-compare-delta.positive {
            color: #12805c;
        }

        .strategy-compare-delta.negative {
            color: #c0392b;
        }

        .strategy-compare-delta.neutral {
            color: #6b7280;
        }

        .strategy-dev-header {
            background: linear-gradient(180deg, #fbfbfd 0%, #f5f7fb 100%);
            border: 1px solid rgba(49,71,114,0.12);
            border-radius: 18px;
            padding: 16px 18px;
            margin: 8px 0 16px 0;
        }

        .strategy-dev-header-title {
            font-size: 1.15rem;
            font-weight: 800;
            color: #1b2533;
        }

        .strategy-dev-header-subtitle {
            font-size: 0.9rem;
            color: #6b7280;
            margin-top: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================
# РАСЧЕТЫ ВЕРХНЕГО БЛОКА
# =========================

def _calculate_strategy_metrics(
    market_share_pct,
    niche_turnover_bln,
    avg_check,
    sku_count,
    cr_pct,
    impressions_per_ruble,
    drr_plan_pct,
    profitability_plan_pct,
    revenue_plan,
):
    niche_turnover = niche_turnover_bln * 1_000_000_000
    market_share = market_share_pct / 100
    cr = cr_pct / 100

    revenue = niche_turnover * market_share
    orders = _safe_divide(revenue, avg_check)

    revenue_per_sku = _safe_divide(revenue, sku_count)
    orders_per_sku = _safe_divide(orders, sku_count)

    total_impressions = _safe_divide(orders, cr)
    impressions_per_sku = _safe_divide(total_impressions, sku_count)

    ad_spend = _safe_divide(total_impressions, impressions_per_ruble)
    drr_forecast_pct = _safe_divide(ad_spend, revenue) * 100

    orders_per_day = orders / 30
    revenue_per_day = revenue / 30
    daily_ad_budget = ad_spend / 30
    weekly_ad_budget_per_sku = _safe_divide(daily_ad_budget, sku_count) * 7

    profitability_forecast_pct = profitability_plan_pct + (drr_plan_pct - drr_forecast_pct)

    net_profit_forecast = revenue * (profitability_forecast_pct / 100)
    net_profit_plan = revenue_plan * (profitability_plan_pct / 100)

    return {
        "revenue": revenue,
        "orders": orders,
        "revenue_per_sku": revenue_per_sku,
        "orders_per_sku": orders_per_sku,
        "total_impressions": total_impressions,
        "impressions_per_sku": impressions_per_sku,
        "ad_spend": ad_spend,
        "drr_forecast_pct": drr_forecast_pct,
        "orders_per_day": orders_per_day,
        "revenue_per_day": revenue_per_day,
        "daily_ad_budget": daily_ad_budget,
        "weekly_ad_budget_per_sku": weekly_ad_budget_per_sku,
        "profitability_forecast_pct": profitability_forecast_pct,
        "net_profit_forecast": net_profit_forecast,
        "net_profit_plan": net_profit_plan,
        "cr_pct": cr_pct,
    }


# =========================
# КОНКУРЕНТЫ
# =========================

def _default_competitors():
    return pd.DataFrame(
        [
            {"Бренд": "Ritter", "Показы всего": 5_500_000.0, "CR, %": 0.095, "Выручка, ₽": 42_000_000.0},
            {"Бренд": "Rosso Sole", "Показы всего": 2_300_000.0, "CR, %": 0.115, "Выручка, ₽": 16_000_000.0},
            {"Бренд": "Ledcity", "Показы всего": 1_800_000.0, "CR, %": 0.135, "Выручка, ₽": 14_500_000.0},
            {"Бренд": "Cassina", "Показы всего": 4_100_000.0, "CR, %": 0.072, "Выручка, ₽": 27_000_000.0},
        ]
    )


def _prepare_competitors_for_chart(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()

    if "Бренд" not in prepared.columns:
        prepared["Бренд"] = ""
    if "Показы всего" not in prepared.columns:
        prepared["Показы всего"] = None
    if "CR, %" not in prepared.columns:
        prepared["CR, %"] = None
    if "Выручка, ₽" not in prepared.columns:
        prepared["Выручка, ₽"] = None

    prepared["Бренд"] = prepared["Бренд"].fillna("").astype(str).str.strip()

    for col in ["Показы всего", "CR, %", "Выручка, ₽"]:
        prepared[col] = pd.to_numeric(prepared[col], errors="coerce")

    prepared = prepared.dropna(subset=["Бренд", "Показы всего", "CR, %", "Выручка, ₽"]).copy()
    prepared = prepared[prepared["Бренд"] != ""].copy()
    prepared = prepared[prepared["Показы всего"] > 0].copy()
    prepared = prepared[prepared["CR, %"] > 0].copy()
    prepared = prepared[prepared["Выручка, ₽"] > 0].copy()

    return prepared


# =========================
# НОВЫЕ БЛОКИ — СЕГМЕНТЫ И SKU
# =========================

def _default_price_segments():
    return pd.DataFrame(
        [
            {"Ценовой сегмент": "0 – 199", "Наши продажи": 0.0, "Общие продажи": 365760.0, "Целевая доля, %": 0.0},
            {"Ценовой сегмент": "200 – 299", "Наши продажи": 0.0, "Общие продажи": 249100.0, "Целевая доля, %": 0.0},
            {"Ценовой сегмент": "300 – 399", "Наши продажи": 0.0, "Общие продажи": 459334.0, "Целевая доля, %": 0.0},
            {"Ценовой сегмент": "400 – 499", "Наши продажи": 0.0, "Общие продажи": 2374570.0, "Целевая доля, %": 0.0},
            {"Ценовой сегмент": "500 – 749", "Наши продажи": 0.0, "Общие продажи": 3412969.0, "Целевая доля, %": 0.0},
            {"Ценовой сегмент": "750 – 999", "Наши продажи": 0.0, "Общие продажи": 4849697.0, "Целевая доля, %": 0.0},
            {"Ценовой сегмент": "1 000 – 1 249", "Наши продажи": 0.0, "Общие продажи": 11816561.0, "Целевая доля, %": 0.0},
            {"Ценовой сегмент": "1 250 – 1 499", "Наши продажи": 29490.0, "Общие продажи": 7973979.0, "Целевая доля, %": 0.0},
            {"Ценовой сегмент": "1 500 – 1 999", "Наши продажи": 25471.0, "Общие продажи": 37638425.0, "Целевая доля, %": 1.0},
            {"Ценовой сегмент": "2 000 – 2 499", "Наши продажи": 1365742.0, "Общие продажи": 71097167.0, "Целевая доля, %": 2.5},
            {"Ценовой сегмент": "2 500 – 2 999", "Наши продажи": 3781161.0, "Общие продажи": 63083280.0, "Целевая доля, %": 7.0},
            {"Ценовой сегмент": "3 000 – 3 499", "Наши продажи": 2085690.0, "Общие продажи": 65408993.0, "Целевая доля, %": 4.0},
            {"Ценовой сегмент": "3 500 – 3 999", "Наши продажи": 1462173.0, "Общие продажи": 75867259.0, "Целевая доля, %": 3.0},
            {"Ценовой сегмент": "4 000 – 4 999", "Наши продажи": 3775748.0, "Общие продажи": 119609564.0, "Целевая доля, %": 5.0},
            {"Ценовой сегмент": "5 000 – 5 999", "Наши продажи": 1986849.0, "Общие продажи": 105959537.0, "Целевая доля, %": 3.0},
            {"Ценовой сегмент": "6 000 – 6 999", "Наши продажи": 254275.0, "Общие продажи": 78960207.0, "Целевая доля, %": 3.0},
            {"Ценовой сегмент": "7 000 – 7 999", "Наши продажи": 30000.0, "Общие продажи": 55489541.0, "Целевая доля, %": 3.0},
            {"Ценовой сегмент": "8 000 – 8 999", "Наши продажи": 56000.0, "Общие продажи": 48195744.0, "Целевая доля, %": 3.0},
            {"Ценовой сегмент": "9 000 – 9 999", "Наши продажи": 309950.0, "Общие продажи": 42682408.0, "Целевая доля, %": 3.0},
            {"Ценовой сегмент": "10 000 – 12 499", "Наши продажи": 0.0, "Общие продажи": 99149469.0, "Целевая доля, %": 3.0},
            {"Ценовой сегмент": "12 500 – 14 999", "Наши продажи": 0.0, "Общие продажи": 76256259.0, "Целевая доля, %": 3.0},
            {"Ценовой сегмент": "15 000 – 19 999", "Наши продажи": 0.0, "Общие продажи": 105975829.0, "Целевая доля, %": 3.0},
            {"Ценовой сегмент": "20 000 – 24 999", "Наши продажи": 0.0, "Общие продажи": 61554369.0, "Целевая доля, %": None},
            {"Ценовой сегмент": "25 000 – 29 999", "Наши продажи": 0.0, "Общие продажи": 42158552.0, "Целевая доля, %": None},
            {"Ценовой сегмент": "30 000 – 34 999", "Наши продажи": 0.0, "Общие продажи": 19500600.0, "Целевая доля, %": None},
            {"Ценовой сегмент": "35 000 – 39 999", "Наши продажи": 0.0, "Общие продажи": 15272593.0, "Целевая доля, %": None},
            {"Ценовой сегмент": "40 000 – 49 999", "Наши продажи": 0.0, "Общие продажи": 17081685.0, "Целевая доля, %": None},
            {"Ценовой сегмент": "50 000 – 74 999", "Наши продажи": 0.0, "Общие продажи": 19846627.0, "Целевая доля, %": None},
            {"Ценовой сегмент": "75 000 – 99 999", "Наши продажи": 0.0, "Общие продажи": 6316341.0, "Целевая доля, %": None},
            {"Ценовой сегмент": "> 100 000", "Наши продажи": 0.0, "Общие продажи": 12155578.0, "Целевая доля, %": None},
        ]
    )


def _parse_segment_bounds(segment_label: str):
    s = str(segment_label).replace(" ", "")
    if s.startswith(">"):
        low = float(s.replace(">", "").replace("–", "").replace("—", ""))
        return low, math.inf

    nums = re.findall(r"\d+", s)
    if len(nums) >= 2:
        return float(nums[0]), float(nums[1])

    return 0.0, math.inf


def _segment_for_avg_check(avg_check: float, segment_labels: list[str]) -> str:
    if pd.isna(avg_check):
        return ""
    value = float(avg_check)

    for label in segment_labels:
        low, high = _parse_segment_bounds(label)
        if math.isinf(high):
            if value >= low:
                return label
        else:
            if low <= value <= high:
                return label
    return ""


def _default_sku_forecast():
    return pd.DataFrame(
        [
            {"Артикул": "700001", "Показы": None, "CR, %": None, "Средний чек, ₽": None, "Рентабельность, %": None, "Факт: показы": None, "Факт: CR, %": None, "Факт: средний чек, ₽": None},
            {"Артикул": "700002", "Показы": None, "CR, %": None, "Средний чек, ₽": None, "Рентабельность, %": None, "Факт: показы": None, "Факт: CR, %": None, "Факт: средний чек, ₽": None},
            {"Артикул": "700003", "Показы": None, "CR, %": None, "Средний чек, ₽": None, "Рентабельность, %": None, "Факт: показы": None, "Факт: CR, %": None, "Факт: средний чек, ₽": None},
            {"Артикул": "700004", "Показы": None, "CR, %": None, "Средний чек, ₽": None, "Рентабельность, %": None, "Факт: показы": None, "Факт: CR, %": None, "Факт: средний чек, ₽": None},
        ]
    )


def _calculate_sku_forecast_table(df: pd.DataFrame, impressions_per_ruble: float, segment_labels: list[str]) -> pd.DataFrame:
    calc = df.copy()

    for col in ["Показы", "CR, %", "Средний чек, ₽", "Рентабельность, %", "Факт: показы", "Факт: CR, %", "Факт: средний чек, ₽"]:
        if col not in calc.columns:
            calc[col] = None

    calc["Артикул"] = calc.get("Артикул", "").fillna("").astype(str)

    numeric_cols = ["Показы", "CR, %", "Средний чек, ₽", "Рентабельность, %", "Факт: показы", "Факт: CR, %", "Факт: средний чек, ₽"]
    for col in numeric_cols:
        calc[col] = pd.to_numeric(calc[col], errors="coerce")

    calc["Ценовой сегмент"] = calc["Средний чек, ₽"].apply(lambda x: _segment_for_avg_check(x, segment_labels))
    calc["Заказы, шт"] = calc["Показы"] * (calc["CR, %"] / 100.0)
    calc["Заказано, сумма"] = calc["Заказы, шт"] * calc["Средний чек, ₽"]
    calc["Чистая прибыль"] = calc["Заказано, сумма"] * (calc["Рентабельность, %"] / 100.0)
    calc["Бюджет, месяц"] = calc["Показы"] / impressions_per_ruble
    calc["РБ неделя"] = calc["Бюджет, месяц"] / 4.0
    calc["РБ день"] = calc["Бюджет, месяц"] / 30.0
    calc["ДРР, %"] = calc["Бюджет, месяц"] / calc["Заказано, сумма"] * 100.0

    calc = calc.replace([math.inf, -math.inf], pd.NA)
    return calc


def _build_segments_result_table(base_df: pd.DataFrame, sku_forecast_df: pd.DataFrame) -> pd.DataFrame:
    result = base_df.copy()

    result["Наши продажи"] = pd.to_numeric(result["Наши продажи"], errors="coerce").fillna(0.0)
    result["Общие продажи"] = pd.to_numeric(result["Общие продажи"], errors="coerce").fillna(0.0)
    result["Целевая доля, %"] = pd.to_numeric(result["Целевая доля, %"], errors="coerce")

    market_total = result["Общие продажи"].sum()

    result["Наша доля, %"] = result.apply(
        lambda row: _safe_divide(row["Наши продажи"], row["Общие продажи"]) * 100,
        axis=1,
    )
    result["Доля сегмента, %"] = result["Общие продажи"].apply(lambda x: _safe_divide(x, market_total) * 100)
    result["Недополученные продажи"] = (
        (result["Общие продажи"] * (result["Целевая доля, %"] / 100.0)) - result["Наши продажи"]
    ).clip(lower=0)
    result["Потенциальная выручка план"] = result["Наши продажи"] + result["Недополученные продажи"]

    # агрегат по артикульному прогнозу
    sku_valid = sku_forecast_df.copy()
    sku_valid["Заказано, сумма"] = pd.to_numeric(sku_valid["Заказано, сумма"], errors="coerce")
    sku_valid["Ценовой сегмент"] = sku_valid["Ценовой сегмент"].fillna("").astype(str)

    segment_forecast = (
        sku_valid.dropna(subset=["Заказано, сумма"])
        .groupby("Ценовой сегмент", dropna=False)["Заказано, сумма"]
        .sum()
        .reset_index(name="Потенциальная выручка прогноз")
    )

    result = result.merge(segment_forecast, how="left", left_on="Ценовой сегмент", right_on="Ценовой сегмент")
    result["Потенциальная выручка прогноз"] = result["Потенциальная выручка прогноз"].fillna(0.0)
    result["Доля, которую мы сможем занять, %"] = result.apply(
        lambda row: _safe_divide(row["Потенциальная выручка прогноз"], row["Общие продажи"]) * 100,
        axis=1,
    )

    return result


# =========================
# ОСНОВНОЙ РЕНДЕР
# =========================

def render_strategy_tab():
    _inject_styles()

    st.header("Стратегия роста")

    # ---------- верхняя сетка ----------
    top_left, top_right = st.columns([0.42, 0.58], vertical_alignment="top")

    with top_left:
        st.markdown('<div class="strategy-panel-title">Входные параметры</div>', unsafe_allow_html=True)

        metrics_row = st.columns(3)
        with metrics_row[0]:
            market_share_pct = st.number_input(
                "Доля рынка, %",
                min_value=0.0,
                max_value=100.0,
                value=5.0,
                step=0.1,
                key="strategy_market_share_pct",
            )
            _render_big_kpi("Целевая доля", _format_percent(market_share_pct), "Ключевой вход")

        with metrics_row[1]:
            niche_turnover_bln = st.number_input(
                "Оборот ниши, млрд ₽",
                min_value=0.0,
                max_value=100.0,
                value=2.0,
                step=0.1,
                key="strategy_niche_turnover_bln",
            )
            _render_big_kpi("Емкость ниши", f"{niche_turnover_bln:.1f} млрд ₽", "Месячный объем")

        with metrics_row[2]:
            cr_pct = st.number_input(
                "CR, %",
                min_value=0.001,
                max_value=10.0,
                value=0.10,
                step=0.005,
                format="%.3f",
                key="strategy_cr_pct",
            )
            _render_big_kpi("Конверсия", _format_percent(cr_pct, 3), "Из показа в заказ")

        st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

        in_col1, in_col2 = st.columns(2)

        with in_col1:
            avg_check = st.number_input(
                "Средний чек, ₽",
                min_value=1.0,
                max_value=100000.0,
                value=8000.0,
                step=100.0,
                key="strategy_avg_check",
            )

            sku_count = st.number_input(
                "Кол-во артикулов",
                min_value=1.0,
                max_value=10000.0,
                value=50.0,
                step=1.0,
                key="strategy_sku_count",
            )

            impressions_per_ruble = st.number_input(
                "Показы / рубль",
                min_value=0.01,
                max_value=100.0,
                value=3.0,
                step=0.1,
                key="strategy_impressions_per_ruble",
            )

        with in_col2:
            drr_plan_pct = st.number_input(
                "ДРР план, %",
                min_value=0.0,
                max_value=100.0,
                value=12.0,
                step=0.1,
                key="strategy_drr_plan_pct",
            )

            profitability_plan_pct = st.number_input(
                "Рентабельность план, %",
                min_value=-100.0,
                max_value=100.0,
                value=18.0,
                step=0.1,
                key="strategy_profitability_plan_pct",
            )

            revenue_plan = st.number_input(
                "План выручки, ₽",
                min_value=0.0,
                max_value=1e12,
                value=120_000_000.0,
                step=100_000.0,
                key="strategy_revenue_plan",
            )

        orders_plan = st.number_input(
            "Заказы план",
            min_value=0.0,
            max_value=1e9,
            value=15000.0,
            step=100.0,
            key="strategy_orders_plan",
        )

    metrics = _calculate_strategy_metrics(
        market_share_pct=market_share_pct,
        niche_turnover_bln=niche_turnover_bln,
        avg_check=avg_check,
        sku_count=sku_count,
        cr_pct=cr_pct,
        impressions_per_ruble=impressions_per_ruble,
        drr_plan_pct=drr_plan_pct,
        profitability_plan_pct=profitability_plan_pct,
        revenue_plan=revenue_plan,
    )

    with top_right:
        st.markdown('<div class="strategy-panel-title">Позиция бренда на рынке</div>', unsafe_allow_html=True)
        chart_placeholder = st.empty()

    # ---------- нижняя сетка ----------
    bottom_left, bottom_right = st.columns([0.42, 0.58], vertical_alignment="top")

    with bottom_left:
        st.markdown('<div class="strategy-panel-title">Что нужно обеспечить</div>', unsafe_allow_html=True)

        need_col1, need_col2 = st.columns(2)

        with need_col1:
            st.caption("Масштаб кабинета")
            _render_small_kpi("Выручка", _format_money(metrics["revenue"]))
            _render_small_kpi("Заказы", _format_number(metrics["orders"]))
            _render_small_kpi("Показы", _format_number(metrics["total_impressions"]))
            _render_small_kpi("РБ / день", _format_money(metrics["daily_ad_budget"]))
            _render_small_kpi("ДРР прогноз", _format_percent(metrics["drr_forecast_pct"]))

        with need_col2:
            st.caption("Нагрузка на 1 SKU")
            _render_small_kpi("Выручка / SKU", _format_money(metrics["revenue_per_sku"]))
            _render_small_kpi("Заказы / SKU", _format_number(metrics["orders_per_sku"], 1))
            _render_small_kpi("Показы / SKU", _format_number(metrics["impressions_per_sku"]))
            _render_small_kpi("Недельный РБ / SKU", _format_money(metrics["weekly_ad_budget_per_sku"]))
            _render_small_kpi("Выручка / день", _format_money(metrics["revenue_per_day"]))

    with bottom_right:
        st.markdown('<div class="strategy-panel-title">Конкуренты</div>', unsafe_allow_html=True)

        if "competitors" not in st.session_state:
            st.session_state["competitors"] = _default_competitors()

        base_df = st.session_state["competitors"].copy()

        for col in ["Бренд", "Показы всего", "CR, %", "Выручка, ₽"]:
            if col not in base_df.columns:
                base_df[col] = None

        edited = st.data_editor(
            base_df,
            num_rows="dynamic",
            use_container_width=True,
            key="comp_editor",
            column_config={
                "Бренд": st.column_config.TextColumn("Бренд"),
                "Показы всего": st.column_config.NumberColumn("Показы всего", min_value=0.0, step=1000.0, format="%.0f"),
                "CR, %": st.column_config.NumberColumn("CR, %", min_value=0.0, step=0.005, format="%.3f"),
                "Выручка, ₽": st.column_config.NumberColumn("Выручка, ₽", min_value=0.0, step=100000.0, format="%.0f"),
            },
        )

        st.session_state["competitors"] = edited.copy()

        competitors_df = _prepare_competitors_for_chart(edited)

        model_df = pd.DataFrame(
            [
                {
                    "Бренд": "Грани Света",
                    "Показы всего": float(metrics["total_impressions"]),
                    "CR, %": float(metrics["cr_pct"]),
                    "Выручка, ₽": float(metrics["revenue"]),
                }
            ]
        )

        chart_df = pd.concat([competitors_df, model_df], ignore_index=True)

        with chart_placeholder.container():
            if len(chart_df) > 0:
                fig = px.scatter(
                    chart_df,
                    x="Показы всего",
                    y="CR, %",
                    size="Выручка, ₽",
                    color="Бренд",
                    text="Бренд",
                    size_max=72,
                )
                fig.update_traces(
                    textposition="top center",
                    marker=dict(opacity=0.82, line=dict(width=1, color="white")),
                )
                fig.update_layout(
                    height=520,
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis_title="Показы всего",
                    yaxis_title="CR, %",
                    legend_title="Бренд",
                )
                fig.update_xaxes(showgrid=True)
                fig.update_yaxes(showgrid=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Заполни хотя бы одну строку конкурента: бренд, показы, CR и выручку.")

    # ---------- сравнение с планом ----------
    st.markdown("---")
    st.markdown('<div class="strategy-panel-title">Сравнение с планом</div>', unsafe_allow_html=True)

    compare_row_1 = st.columns(3)
    compare_row_2 = st.columns(3)

    with compare_row_1[0]:
        _render_compare_card(
            metric_name="Выручка",
            plan_value=_format_money(revenue_plan),
            forecast_value=_format_money(metrics["revenue"]),
            delta_value=_format_delta_pct(metrics["revenue"], revenue_plan),
            delta_class=_delta_color_class(metrics["revenue"], revenue_plan),
        )

    with compare_row_1[1]:
        _render_compare_card(
            metric_name="Рентабельность",
            plan_value=_format_percent(profitability_plan_pct),
            forecast_value=_format_percent(metrics["profitability_forecast_pct"]),
            delta_value=_format_delta_pct(metrics["profitability_forecast_pct"], profitability_plan_pct),
            delta_class=_delta_color_class(metrics["profitability_forecast_pct"], profitability_plan_pct),
        )

    with compare_row_1[2]:
        _render_compare_card(
            metric_name="Чистая прибыль",
            plan_value=_format_money(metrics["net_profit_plan"]),
            forecast_value=_format_money(metrics["net_profit_forecast"]),
            delta_value=_format_delta_pct(metrics["net_profit_forecast"], metrics["net_profit_plan"]),
            delta_class=_delta_color_class(metrics["net_profit_forecast"], metrics["net_profit_plan"]),
        )

    with compare_row_2[0]:
        _render_compare_card(
            metric_name="Заказы",
            plan_value=_format_number(orders_plan),
            forecast_value=_format_number(metrics["orders"]),
            delta_value=_format_delta_pct(metrics["orders"], orders_plan),
            delta_class=_delta_color_class(metrics["orders"], orders_plan),
        )

    with compare_row_2[1]:
        _render_compare_card(
            metric_name="ДРР",
            plan_value=_format_percent(drr_plan_pct),
            forecast_value=_format_percent(metrics["drr_forecast_pct"]),
            delta_value=_format_delta_pct(metrics["drr_forecast_pct"], drr_plan_pct),
            delta_class=_delta_color_class(drr_plan_pct, metrics["drr_forecast_pct"]),
        )

    with compare_row_2[2]:
        _render_compare_card(
            metric_name="Дневной рекламный бюджет",
            plan_value="—",
            forecast_value=_format_money(metrics["daily_ad_budget"]),
            delta_value="—",
            delta_class="neutral",
        )

    # =========================
    # В РАЗРАБОТКЕ
    # =========================
    st.markdown("---")
    st.markdown(
        """
        <div class="strategy-dev-header">
            <div class="strategy-dev-header-title">В разработке</div>
            <div class="strategy-dev-header-subtitle">
                Блоки декомпозиции стратегии: присутствие в ценовых сегментах и поартикульный прогноз.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # инициализация state
    if "strategy_price_segments" not in st.session_state:
        st.session_state["strategy_price_segments"] = _default_price_segments()

    if "strategy_sku_forecast" not in st.session_state:
        st.session_state["strategy_sku_forecast"] = _default_sku_forecast()

        # ---------- Блок 1 ----------
    st.subheader("Присутствие в ценовых сегментах")

    base_segments_df = st.session_state["strategy_price_segments"].copy()

    # подготовка sku блока до сегментов, чтобы агрегат уже был готов
    current_segments_labels = (
        base_segments_df["Ценовой сегмент"]
        .fillna("")
        .astype(str)
        .tolist()
    )

    sku_source_df = st.session_state["strategy_sku_forecast"].copy()
    sku_calc_df = _calculate_sku_forecast_table(
        sku_source_df,
        impressions_per_ruble=impressions_per_ruble,
        segment_labels=current_segments_labels,
    )

    segments_result_df = _build_segments_result_table(base_segments_df.copy(), sku_calc_df)

    segments_editor_df = segments_result_df[
        [
            "Ценовой сегмент",
            "Наши продажи",
            "Общие продажи",
            "Наша доля, %",
            "Доля сегмента, %",
            "Целевая доля, %",
            "Недополученные продажи",
            "Потенциальная выручка план",
            "Доля, которую мы сможем занять, %",
            "Потенциальная выручка прогноз",
        ]
    ].copy()

    seg_left, seg_right = st.columns([0.50, 0.50], vertical_alignment="top")

    with seg_left:
        segments_edited = st.data_editor(
            segments_editor_df,
            use_container_width=True,
            num_rows="dynamic",
            height=680,
            key="segments_editor",
            column_config={
                "Ценовой сегмент": st.column_config.TextColumn("Ценовой сегмент", width="medium"),
                "Наши продажи": st.column_config.NumberColumn("Наши продажи", min_value=0.0, step=10000.0, format="%.0f"),
                "Общие продажи": st.column_config.NumberColumn("Общие продажи", min_value=0.0, step=10000.0, format="%.0f"),
                "Наша доля, %": st.column_config.NumberColumn("Наша доля, %", format="%.2f", disabled=True),
                "Доля сегмента, %": st.column_config.NumberColumn("Доля сегмента, %", format="%.2f", disabled=True),
                "Целевая доля, %": st.column_config.NumberColumn("Целевая доля, %", min_value=0.0, max_value=100.0, step=0.5, format="%.2f"),
                "Недополученные продажи": st.column_config.NumberColumn("Недополученные продажи", format="%.0f", disabled=True),
                "Потенциальная выручка план": st.column_config.NumberColumn("Потенциальная выручка план", format="%.0f", disabled=True),
                "Доля, которую мы сможем занять, %": st.column_config.NumberColumn("Прогнозная доля, %", format="%.2f", disabled=True),
                "Потенциальная выручка прогноз": st.column_config.NumberColumn("Потенциальная выручка прогноз", format="%.0f", disabled=True),
            },
            column_order=[
                "Ценовой сегмент",
                "Наши продажи",
                "Общие продажи",
                "Наша доля, %",
                "Доля сегмента, %",
                "Целевая доля, %",
                "Недополученные продажи",
                "Потенциальная выручка план",
                "Доля, которую мы сможем занять, %",
                "Потенциальная выручка прогноз",
            ],
        )

        # сохраняем только редактируемую базу обратно в state
        st.session_state["strategy_price_segments"] = segments_edited[
            ["Ценовой сегмент", "Наши продажи", "Общие продажи", "Целевая доля, %"]
        ].copy()

    # после редактирования пересчитываем
    recalculated_segments_df = _build_segments_result_table(
        st.session_state["strategy_price_segments"].copy(),
        sku_calc_df,
    )

    with seg_right:
        chart_long = recalculated_segments_df.melt(
            id_vars=["Ценовой сегмент"],
            value_vars=["Наши продажи", "Потенциальная выручка план", "Потенциальная выручка прогноз"],
            var_name="Показатель",
            value_name="Значение",
        )

        fig_segments = px.bar(
            chart_long,
            x="Ценовой сегмент",
            y="Значение",
            color="Показатель",
            barmode="group",
        )

        fig_segments.update_layout(
            height=720,
            margin=dict(l=10, r=10, t=20, b=40),
            xaxis_title="Ценовой сегмент",
            yaxis_title="Выручка, ₽",
            legend_title="Срез",
        )

        fig_segments.update_xaxes(
            tickangle=-45,
            showgrid=False,
        )
        fig_segments.update_yaxes(showgrid=True)

        st.plotly_chart(fig_segments, use_container_width=True)

    # ---------- Блок 2 ----------
    st.subheader("Поартикульный прогноз")
    st.markdown(
        '<div class="strategy-block-subtitle">Ценовой сегмент определяется автоматически на основе среднего чека.</div>',
        unsafe_allow_html=True,
    )

    sku_display_df = sku_calc_df.copy()

    editable_cols = [
        "Артикул",
        "Показы",
        "CR, %",
        "Средний чек, ₽",
        "Рентабельность, %",
        "Факт: показы",
        "Факт: CR, %",
        "Факт: средний чек, ₽",
    ]

    if "strategy_sku_forecast" in st.session_state:
        base_sku_df = st.session_state["strategy_sku_forecast"].copy()
    else:
        base_sku_df = _default_sku_forecast()

    sku_edited = st.data_editor(
        base_sku_df,
        use_container_width=True,
        num_rows="dynamic",
        key="sku_forecast_editor",
        column_config={
            "Артикул": st.column_config.TextColumn("Артикул"),
            "Показы": st.column_config.NumberColumn("Показы", min_value=0.0, step=100.0, format="%.0f"),
            "CR, %": st.column_config.NumberColumn("CR, %", min_value=0.0, step=0.01, format="%.3f"),
            "Средний чек, ₽": st.column_config.NumberColumn("Средний чек, ₽", min_value=0.0, step=100.0, format="%.0f"),
            "Рентабельность, %": st.column_config.NumberColumn("Рентабельность, %", step=0.1, format="%.2f"),
            "Факт: показы": st.column_config.NumberColumn("Факт: показы", min_value=0.0, step=100.0, format="%.0f"),
            "Факт: CR, %": st.column_config.NumberColumn("Факт: CR, %", min_value=0.0, step=0.01, format="%.3f"),
            "Факт: средний чек, ₽": st.column_config.NumberColumn("Факт: средний чек, ₽", min_value=0.0, step=100.0, format="%.0f"),
        },
    )

    st.session_state["strategy_sku_forecast"] = sku_edited.copy()

    sku_calc_df = _calculate_sku_forecast_table(
        sku_edited.copy(),
        impressions_per_ruble=impressions_per_ruble,
        segment_labels=current_segments_labels,
    )

    st.dataframe(
        sku_calc_df[
            [
                "Артикул",
                "Ценовой сегмент",
                "Показы",
                "CR, %",
                "Заказы, шт",
                "Средний чек, ₽",
                "Заказано, сумма",
                "Рентабельность, %",
                "Чистая прибыль",
                "Бюджет, месяц",
                "РБ неделя",
                "РБ день",
                "ДРР, %",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )