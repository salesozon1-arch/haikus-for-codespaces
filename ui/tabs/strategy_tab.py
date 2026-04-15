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


def _calculate_strategy_metrics(
    market_share_pct: float,
    niche_turnover_bln: float,
    avg_check: float,
    sku_count: float,
    cr_pct: float,
    impressions_per_ruble: float,
    all_expenses_share_pct: float,
    drr_plan_pct: float,
    profitability_plan_pct: float,
    revenue_plan: float,
):
    niche_turnover = niche_turnover_bln * 1_000_000_000
    market_share = market_share_pct / 100
    cr = cr_pct / 100

    revenue = niche_turnover * market_share
    orders = _safe_divide(revenue, avg_check)
    revenue_per_sku = _safe_divide(revenue, sku_count)

    total_impressions = _safe_divide(orders, cr)
    impressions_per_sku = _safe_divide(total_impressions, sku_count)

    ad_spend = _safe_divide(total_impressions, impressions_per_ruble)
    drr_forecast_pct = _safe_divide(ad_spend, revenue) * 100

    orders_per_sku = _safe_divide(orders, sku_count)
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
        "total_impressions": total_impressions,
        "impressions_per_sku": impressions_per_sku,
        "ad_spend": ad_spend,
        "drr_forecast_pct": drr_forecast_pct,
        "orders_per_sku": orders_per_sku,
        "orders_per_day": orders_per_day,
        "revenue_per_day": revenue_per_day,
        "daily_ad_budget": daily_ad_budget,
        "weekly_ad_budget_per_sku": weekly_ad_budget_per_sku,
        "profitability_forecast_pct": profitability_forecast_pct,
        "net_profit_forecast": net_profit_forecast,
        "net_profit_plan": net_profit_plan,
        "cr_pct": cr_pct,
        "all_expenses_share_pct": all_expenses_share_pct,
    }


def _build_default_competitors() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Бренд": "Ritter",
                "Показы всего": 5_500_000,
                "CR, %": 0.095,
                "Выручка, ₽": 42_000_000,
            },
            {
                "Бренд": "Rosso Sole",
                "Показы всего": 2_300_000,
                "CR, %": 0.115,
                "Выручка, ₽": 16_000_000,
            },
            {
                "Бренд": "Ledcity",
                "Показы всего": 1_800_000,
                "CR, %": 0.135,
                "Выручка, ₽": 14_500_000,
            },
            {
                "Бренд": "Cassina",
                "Показы всего": 4_100_000,
                "CR, %": 0.072,
                "Выручка, ₽": 27_000_000,
            },
            {
                "Бренд": "Estares",
                "Показы всего": 3_100_000,
                "CR, %": 0.105,
                "Выручка, ₽": 21_000_000,
            },
        ]
    )


def render_strategy_tab():
    st.header("Стратегия роста")

    st.caption(
        "Модель рассчитывает ключевые показатели стратегии и показывает позицию бренда "
        "«Грани Света» относительно конкурентов."
    )

    left_col, right_col = st.columns([0.38, 0.62])

    with left_col:
        st.subheader("Входные параметры")

        input_col1, input_col2 = st.columns(2)

        with input_col1:
            market_share_pct = st.number_input(
                "Доля рынка, %",
                min_value=0.0,
                max_value=100.0,
                value=5.0,
                step=0.1,
                key="strategy_market_share_pct",
            )

            niche_turnover_bln = st.number_input(
                "Оборот ниши, млрд ₽ / месяц",
                min_value=0.0,
                value=2.0,
                step=0.1,
                key="strategy_niche_turnover_bln",
            )

            avg_check = st.number_input(
                "Средний чек, ₽",
                min_value=1.0,
                value=8000.0,
                step=100.0,
                key="strategy_avg_check",
            )

            sku_count = st.number_input(
                "Количество артикулов, шт",
                min_value=1.0,
                value=50.0,
                step=1.0,
                key="strategy_sku_count",
            )

            cr_pct = st.number_input(
                "CR из показа в заказ, %",
                min_value=0.001,
                max_value=100.0,
                value=0.10,
                step=0.005,
                format="%.3f",
                key="strategy_cr_pct",
            )

            impressions_per_ruble = st.number_input(
                "Показы на 1 рубль (CPV1)",
                min_value=0.01,
                value=3.0,
                step=0.1,
                key="strategy_impressions_per_ruble",
            )

        with input_col2:
            all_expenses_share_pct = st.number_input(
                "Доля расходов всех, %",
                min_value=0.0,
                max_value=100.0,
                value=35.0,
                step=0.1,
                key="strategy_all_expenses_share_pct",
            )

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
                value=120_000_000.0,
                step=100_000.0,
                key="strategy_revenue_plan",
            )

            orders_plan = st.number_input(
                "Заказы план, шт",
                min_value=0.0,
                value=15_000.0,
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
            all_expenses_share_pct=all_expenses_share_pct,
            drr_plan_pct=drr_plan_pct,
            profitability_plan_pct=profitability_plan_pct,
            revenue_plan=revenue_plan,
        )

        st.markdown("---")
        st.subheader("Расчетные показатели")

        st.markdown("##### Объем")
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.metric("Выручка", _format_money(metrics["revenue"]))
            st.metric("Выручка в день", _format_money(metrics["revenue_per_day"]))
            st.metric("Выручка на 1 артикул", _format_money(metrics["revenue_per_sku"]))
        with m_col2:
            st.metric("Заказы", _format_number(metrics["orders"]))
            st.metric("Заказы в день", _format_number(metrics["orders_per_day"], 1))
            st.metric("Заказы на 1 артикул", _format_number(metrics["orders_per_sku"], 1))

        st.markdown("##### Трафик и реклама")
        m_col3, m_col4 = st.columns(2)
        with m_col3:
            st.metric("Показы всего", _format_number(metrics["total_impressions"]))
            st.metric("Показы на 1 артикул", _format_number(metrics["impressions_per_sku"]))
            st.metric("Рекламные расходы", _format_money(metrics["ad_spend"]))
        with m_col4:
            st.metric("Дневной рекламный бюджет", _format_money(metrics["daily_ad_budget"]))
            st.metric(
                "Недельный РБ на артикул",
                _format_money(metrics["weekly_ad_budget_per_sku"]),
            )
            st.metric("ДРР прогноз", _format_percent(metrics["drr_forecast_pct"]))

        st.markdown("##### Прибыль и сравнение с планом")
        m_col5, m_col6 = st.columns(2)
        with m_col5:
            st.metric("План выручки", _format_money(revenue_plan))
            st.metric("Рентабельность план", _format_percent(profitability_plan_pct))
            st.metric("Чистая прибыль план", _format_money(metrics["net_profit_plan"]))
        with m_col6:
            st.metric(
                "Прогнозная рентабельность",
                _format_percent(metrics["profitability_forecast_pct"]),
            )
            st.metric(
                "Чистая прибыль прогноз",
                _format_money(metrics["net_profit_forecast"]),
            )
            st.metric("Заказы план, шт", _format_number(orders_plan))

        with st.expander("Дополнительные вводные"):
            st.write(f"**Доля расходов всех:** {_format_percent(all_expenses_share_pct)}")
            st.write(f"**ДРР план:** {_format_percent(drr_plan_pct)}")

    with right_col:
        st.subheader("Позиция бренда на рынке")

        if "strategy_competitors_df" not in st.session_state:
            st.session_state["strategy_competitors_df"] = _build_default_competitors()

        edited_competitors = st.data_editor(
            st.session_state["strategy_competitors_df"],
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            key="strategy_competitors_editor",
            column_config={
                "Бренд": st.column_config.TextColumn("Бренд"),
                "Показы всего": st.column_config.NumberColumn("Показы всего", min_value=0.0, step=1000.0),
                "CR, %": st.column_config.NumberColumn("CR, %", min_value=0.0, step=0.005, format="%.3f"),
                "Выручка, ₽": st.column_config.NumberColumn("Выручка, ₽", min_value=0.0, step=100000.0),
            },
        )

        competitors_df = edited_competitors.copy()
        competitors_df = competitors_df.dropna(subset=["Бренд"])
        competitors_df["Бренд"] = competitors_df["Бренд"].astype(str).str.strip()
        competitors_df = competitors_df[competitors_df["Бренд"] != ""].copy()

        for col in ["Показы всего", "CR, %", "Выручка, ₽"]:
            if col in competitors_df.columns:
                competitors_df[col] = pd.to_numeric(competitors_df[col], errors="coerce")

        competitors_df = competitors_df.dropna(subset=["Показы всего", "CR, %", "Выручка, ₽"]).copy()
        competitors_df["Тип"] = "Конкурент"

        model_df = pd.DataFrame(
            [
                {
                    "Бренд": "Грани Света",
                    "Показы всего": metrics["total_impressions"],
                    "CR, %": metrics["cr_pct"],
                    "Выручка, ₽": metrics["revenue"],
                    "Тип": "Модель",
                }
            ]
        )

        chart_df = pd.concat([competitors_df, model_df], ignore_index=True)

        if chart_df.empty:
            st.warning("Недостаточно данных для построения графика.")
        else:
            fig = px.scatter(
                chart_df,
                x="Показы всего",
                y="CR, %",
                size="Выручка, ₽",
                color="Бренд",
                text="Бренд",
                hover_name="Бренд",
                hover_data={
                    "Показы всего": ":,.0f",
                    "CR, %": ":.3f",
                    "Выручка, ₽": ":,.0f",
                    "Тип": True,
                },
                size_max=75,
            )

            fig.update_traces(
                textposition="top center",
                marker=dict(opacity=0.78, line=dict(width=1, color="white")),
            )

            median_x = chart_df["Показы всего"].median()
            median_y = chart_df["CR, %"].median()

            fig.add_vline(
                x=median_x,
                line_width=1,
                line_dash="dash",
                opacity=0.45,
            )

            fig.add_hline(
                y=median_y,
                line_width=1,
                line_dash="dash",
                opacity=0.45,
            )

            fig.update_layout(
                height=760,
                xaxis_title="Показы всего",
                yaxis_title="CR из показа в заказ, %",
                legend_title="Бренд",
            )

            fig.update_xaxes(showgrid=True)
            fig.update_yaxes(showgrid=True)

            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("Данные конкурентов")

        st.caption(
            "В таблице можно менять значения, удалять строки и добавлять новых конкурентов. "
            "График пересчитывается автоматически."
        )