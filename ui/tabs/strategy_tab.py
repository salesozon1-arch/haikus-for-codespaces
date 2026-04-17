import pandas as pd
import plotly.express as px
import streamlit as st


def _safe_divide(a, b):
    if b in (0, 0.0, None):
        return 0.0
    return a / b


def _format_money(value: float) -> str:
    return f"{value:,.0f} ₽".replace(",", " ")


def _format_number(value: float, digits: int = 0) -> str:
    return f"{value:,.{digits}f}".replace(",", " ")


def _format_percent(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}%"


def _format_delta_pct(forecast_value: float, plan_value: float, digits: int = 1) -> str:
    if plan_value in (0, 0.0, None):
        return "—"
    delta = ((forecast_value / plan_value) - 1) * 100
    return f"{delta:+.{digits}f}%"


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


def _default_competitors():
    df = pd.DataFrame(
        [
            {"Бренд": "Ritter", "Показы всего": 5_500_000.0, "CR, %": 0.095, "Выручка, ₽": 42_000_000.0},
            {"Бренд": "Rosso Sole", "Показы всего": 2_300_000.0, "CR, %": 0.115, "Выручка, ₽": 16_000_000.0},
            {"Бренд": "Ledcity", "Показы всего": 1_800_000.0, "CR, %": 0.135, "Выручка, ₽": 14_500_000.0},
            {"Бренд": "Cassina", "Показы всего": 4_100_000.0, "CR, %": 0.072, "Выручка, ₽": 27_000_000.0},
        ]
    )

    df["Бренд"] = df["Бренд"].astype(str)
    df["Показы всего"] = pd.to_numeric(df["Показы всего"], errors="coerce").astype(float)
    df["CR, %"] = pd.to_numeric(df["CR, %"], errors="coerce").astype(float)
    df["Выручка, ₽"] = pd.to_numeric(df["Выручка, ₽"], errors="coerce").astype(float)
    return df


def render_strategy_tab():
    st.header("Стратегия роста")

    left_col, right_col = st.columns([0.38, 0.62], vertical_alignment="top")

    with left_col:
        st.subheader("Входные параметры")

        c1, c2 = st.columns(2)

        with c1:
            market_share_pct = st.number_input("Доля рынка, %", 0.0, 100.0, 5.0, 0.1)
            niche_turnover_bln = st.number_input("Оборот ниши, млрд ₽", 0.0, 100.0, 2.0, 0.1)
            avg_check = st.number_input("Средний чек, ₽", 1.0, 100000.0, 8000.0, 100.0)
            sku_count = st.number_input("Кол-во артикулов", 1.0, 10000.0, 50.0, 1.0)
            cr_pct = st.number_input("CR, %", 0.001, 10.0, 0.10, 0.005, format="%.3f")
            impressions_per_ruble = st.number_input("Показы / рубль", 0.01, 100.0, 3.0, 0.1)

        with c2:
            drr_plan_pct = st.number_input("ДРР план, %", 0.0, 100.0, 12.0, 0.1)
            profitability_plan_pct = st.number_input("Рентабельность план, %", -100.0, 100.0, 18.0, 0.1)
            revenue_plan = st.number_input("План выручки, ₽", 0.0, 1e12, 120_000_000.0, 100_000.0)
            orders_plan = st.number_input("Заказы план", 0.0, 1e9, 15000.0, 100.0)

        metrics = _calculate_strategy_metrics(
            market_share_pct,
            niche_turnover_bln,
            avg_check,
            sku_count,
            cr_pct,
            impressions_per_ruble,
            drr_plan_pct,
            profitability_plan_pct,
            revenue_plan,
        )

        st.markdown("---")
        st.subheader("Что нужно обеспечить")

        m1, m2 = st.columns(2)

        with m1:
            st.metric("Выручка", _format_money(metrics["revenue"]))
            st.metric("Заказы", _format_number(metrics["orders"]))
            st.metric("Выручка / SKU", _format_money(metrics["revenue_per_sku"]))
            st.metric("Заказы / SKU", _format_number(metrics["orders_per_sku"]))
            st.metric("Выручка / день", _format_money(metrics["revenue_per_day"]))
            st.metric("Заказы / день", _format_number(metrics["orders_per_day"], 1))

        with m2:
            st.metric("Показы", _format_number(metrics["total_impressions"]))
            st.metric("Показы / SKU", _format_number(metrics["impressions_per_sku"]))
            st.metric("Реклама", _format_money(metrics["ad_spend"]))
            st.metric("РБ / день", _format_money(metrics["daily_ad_budget"]))
            st.metric("Недельный РБ / SKU", _format_money(metrics["weekly_ad_budget_per_sku"]))
            st.metric("ДРР прогноз", _format_percent(metrics["drr_forecast_pct"]))

        st.markdown("---")
        st.subheader("Сравнение с планом")

        p1, p2, p3 = st.columns(3)

        with p1:
            st.metric("План выручки", _format_money(revenue_plan))
            st.metric("План рентабельности", _format_percent(profitability_plan_pct))
            st.metric("План прибыль", _format_money(metrics["net_profit_plan"]))
            st.metric("Заказы план", _format_number(orders_plan))

        with p2:
            st.metric("Прогноз выручки", _format_money(metrics["revenue"]))
            st.metric("Прогноз рентабельности", _format_percent(metrics["profitability_forecast_pct"]))
            st.metric("Прогноз прибыль", _format_money(metrics["net_profit_forecast"]))

        with p3:
            st.metric("Δ выручки", _format_delta_pct(metrics["revenue"], revenue_plan))
            st.metric("Δ рентабельности", _format_delta_pct(metrics["profitability_forecast_pct"], profitability_plan_pct))
            st.metric("Δ прибыли", _format_delta_pct(metrics["net_profit_forecast"], metrics["net_profit_plan"]))

        with right_col:
        if "competitors" not in st.session_state:
            st.session_state["competitors"] = _default_competitors()

        base_df = st.session_state["competitors"].copy()

        if "Бренд" not in base_df.columns:
            base_df["Бренд"] = ""
        if "Показы всего" not in base_df.columns:
            base_df["Показы всего"] = None
        if "CR, %" not in base_df.columns:
            base_df["CR, %"] = None
        if "Выручка, ₽" not in base_df.columns:
            base_df["Выручка, ₽"] = None

        edited = st.data_editor(
            base_df,
            num_rows="dynamic",
            use_container_width=True,
            key="comp_editor",
            column_config={
                "Бренд": st.column_config.TextColumn("Бренд"),
                "Показы всего": st.column_config.NumberColumn(
                    "Показы всего",
                    min_value=0.0,
                    step=1000.0,
                    format="%.0f",
                ),
                "CR, %": st.column_config.NumberColumn(
                    "CR, %",
                    min_value=0.0,
                    step=0.005,
                    format="%.3f",
                ),
                "Выручка, ₽": st.column_config.NumberColumn(
                    "Выручка, ₽",
                    min_value=0.0,
                    step=100000.0,
                    format="%.0f",
                ),
            },
        )

        st.session_state["competitors"] = edited.copy()

        raw_df = edited.copy()

        raw_df["Бренд"] = raw_df["Бренд"].fillna("").astype(str).str.strip()

        for col in ["Показы всего", "CR, %", "Выручка, ₽"]:
            raw_df[col] = pd.to_numeric(raw_df[col], errors="coerce")

        competitors_df = raw_df.dropna(subset=["Бренд", "Показы всего", "CR, %", "Выручка, ₽"]).copy()
        competitors_df = competitors_df[competitors_df["Бренд"] != ""].copy()
        competitors_df = competitors_df[competitors_df["Показы всего"] > 0].copy()
        competitors_df = competitors_df[competitors_df["CR, %"] > 0].copy()
        competitors_df = competitors_df[competitors_df["Выручка, ₽"] > 0].copy()

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

        if len(chart_df) > 0:
            fig = px.scatter(
                chart_df,
                x="Показы всего",
                y="CR, %",
                size="Выручка, ₽",
                color="Бренд",
                text="Бренд",
                size_max=70,
            )
            fig.update_traces(textposition="top center")
            fig.update_layout(height=550)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Заполни хотя бы одну строку конкурента: бренд, показы, CR и выручку.")