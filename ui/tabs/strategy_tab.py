import math

import pandas as pd
import plotly.express as px
import streamlit as st


def _safe_divide(a, b):
    if b in (0, 0.0, None):
        return 0.0
    return a / b


def _calculate_strategy_metrics(
    market_share_pct: float,
    niche_turnover: float,
    avg_check: float,
    sku_count: float,
    cr_pct: float,
    impressions_per_ruble: float,
):
    market_share = market_share_pct / 100
    cr = cr_pct / 100

    revenue = niche_turnover * market_share
    orders = _safe_divide(revenue, avg_check)
    revenue_per_sku = _safe_divide(revenue, sku_count)

    total_impressions = _safe_divide(orders, cr)
    impressions_per_sku = _safe_divide(total_impressions, sku_count)

    ad_spend = _safe_divide(total_impressions, impressions_per_ruble)
    drr = _safe_divide(ad_spend, revenue)

    orders_per_sku = _safe_divide(orders, sku_count)

    return {
        "revenue": revenue,
        "orders": orders,
        "revenue_per_sku": revenue_per_sku,
        "total_impressions": total_impressions,
        "impressions_per_sku": impressions_per_sku,
        "ad_spend": ad_spend,
        "drr": drr,
        "orders_per_sku": orders_per_sku,
        "cr_pct": cr_pct,
    }


def _format_money(value: float) -> str:
    return f"{value:,.0f} ₽".replace(",", " ")


def _format_number(value: float, digits: int = 0) -> str:
    return f"{value:,.{digits}f}".replace(",", " ")


def _format_percent(value: float, digits: int = 2) -> str:
    return f"{value * 100:.{digits}f}%"


def render_strategy_tab():
    st.subheader("Модель стратегии роста")

    left_col, right_col = st.columns([0.34, 0.66])

    with left_col:
        st.markdown("### Входные параметры")

        market_share_pct = st.number_input(
            "Доля рынка, %",
            min_value=0.0,
            max_value=100.0,
            value=5.0,
            step=0.1,
        )

        niche_turnover = st.number_input(
            "Оборот ниши, ₽ / месяц",
            min_value=0.0,
            value=50_000_000.0,
            step=100_000.0,
        )

        avg_check = st.number_input(
            "Средний чек, ₽",
            min_value=1.0,
            value=8_000.0,
            step=100.0,
        )

        sku_count = st.number_input(
            "Количество артикулов, шт",
            min_value=1.0,
            value=50.0,
            step=1.0,
        )

        cr_pct = st.number_input(
            "CR из показа в заказ, %",
            min_value=0.01,
            max_value=100.0,
            value=1.2,
            step=0.1,
        )

        impressions_per_ruble = st.number_input(
            "Показы на 1 рубль (CPV1)",
            min_value=0.01,
            value=3.0,
            step=0.1,
        )

        metrics = _calculate_strategy_metrics(
            market_share_pct=market_share_pct,
            niche_turnover=niche_turnover,
            avg_check=avg_check,
            sku_count=sku_count,
            cr_pct=cr_pct,
            impressions_per_ruble=impressions_per_ruble,
        )

        st.markdown("---")
        st.markdown("### Расчетные показатели")

        st.write(f"**Выручка:** { _format_money(metrics['revenue']) }")
        st.write(f"**Заказы:** { _format_number(metrics['orders']) }")
        st.write(f"**Выручка на 1 артикул:** { _format_money(metrics['revenue_per_sku']) }")
        st.write(f"**Показы всего:** { _format_number(metrics['total_impressions']) }")
        st.write(f"**Показы на 1 артикул:** { _format_number(metrics['impressions_per_sku']) }")
        st.write(f"**Рекламные расходы:** { _format_money(metrics['ad_spend']) }")
        st.write(f"**ДРР:** { _format_percent(metrics['drr']) }")
        st.write(f"**Заказы на 1 артикул:** { _format_number(metrics['orders_per_sku'], 2) }")

    with right_col:
        st.markdown("### Позиция модели относительно конкурентов")

        competitors = pd.DataFrame(
            [
                {
                    "name": "Ritter",
                    "impressions": 5_500_000,
                    "cr_pct": 0.95,
                    "revenue": 42_000_000,
                    "group": "Конкурент",
                },
                {
                    "name": "Rosso Sole",
                    "impressions": 2_300_000,
                    "cr_pct": 1.15,
                    "revenue": 16_000_000,
                    "group": "Конкурент",
                },
                {
                    "name": "Ledcity",
                    "impressions": 1_800_000,
                    "cr_pct": 1.35,
                    "revenue": 14_500_000,
                    "group": "Конкурент",
                },
                {
                    "name": "Cassina",
                    "impressions": 4_100_000,
                    "cr_pct": 0.72,
                    "revenue": 27_000_000,
                    "group": "Конкурент",
                },
            ]
        )

        model_point = pd.DataFrame(
            [
                {
                    "name": "Моя модель",
                    "impressions": metrics["total_impressions"],
                    "cr_pct": metrics["cr_pct"],
                    "revenue": metrics["revenue"],
                    "group": "Моя модель",
                }
            ]
        )

        chart_df = pd.concat([competitors, model_point], ignore_index=True)

        fig = px.scatter(
            chart_df,
            x="impressions",
            y="cr_pct",
            size="revenue",
            color="group",
            text="name",
            hover_name="name",
            hover_data={
                "impressions": ":,.0f",
                "cr_pct": ":.2f",
                "revenue": ":,.0f",
                "group": False,
            },
            size_max=70,
        )

        fig.update_traces(textposition="top center")

        median_x = chart_df["impressions"].median()
        median_y = chart_df["cr_pct"].median()

        fig.add_vline(
            x=median_x,
            line_width=1,
            line_dash="dash",
            opacity=0.5,
        )

        fig.add_hline(
            y=median_y,
            line_width=1,
            line_dash="dash",
            opacity=0.5,
        )

        fig.update_layout(
            xaxis_title="Показы всего",
            yaxis_title="CR из показа в заказ, %",
            showlegend=True,
            height=650,
        )

        fig.update_xaxes(showgrid=True, tickformat=",")
        fig.update_yaxes(showgrid=True)

        st.plotly_chart(fig, use_container_width=True)