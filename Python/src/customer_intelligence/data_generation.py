from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import CONFIG

ARCHETYPES = {
    "High Value Loyal": {
        "share": 0.14,
        "monthly_rate": 1.05,
        "value": 1.75,
        "lifetime": 90,
        "discount": 0.20,
        "engagement": 0.82,
        "friction": 0.10,
    },
    "Growth": {
        "share": 0.22,
        "monthly_rate": 0.62,
        "value": 1.20,
        "lifetime": 52,
        "discount": 0.38,
        "engagement": 0.70,
        "friction": 0.17,
    },
    "Deal Seeker": {
        "share": 0.20,
        "monthly_rate": 0.46,
        "value": 0.92,
        "lifetime": 33,
        "discount": 0.80,
        "engagement": 0.62,
        "friction": 0.24,
    },
    "Routine": {
        "share": 0.25,
        "monthly_rate": 0.38,
        "value": 0.82,
        "lifetime": 45,
        "discount": 0.36,
        "engagement": 0.52,
        "friction": 0.19,
    },
    "At Risk": {
        "share": 0.12,
        "monthly_rate": 0.27,
        "value": 1.05,
        "lifetime": 20,
        "discount": 0.45,
        "engagement": 0.34,
        "friction": 0.48,
    },
    "One-time": {
        "share": 0.07,
        "monthly_rate": 0.14,
        "value": 0.72,
        "lifetime": 7,
        "discount": 0.66,
        "engagement": 0.25,
        "friction": 0.35,
    },
}

CATEGORIES = [
    "Apparel",
    "Beauty",
    "Electronics",
    "Home",
    "Sports",
    "Accessories",
    "Footwear",
    "Wellness",
]


@dataclass
class GeneratedData:
    customers: pd.DataFrame
    products: pd.DataFrame
    orders: pd.DataFrame
    order_lines: pd.DataFrame
    interactions: pd.DataFrame
    campaigns: pd.DataFrame
    campaign_responses: pd.DataFrame


def _month_end(value: pd.Timestamp) -> pd.Timestamp:
    return value + pd.offsets.MonthEnd(0)


def generate_customers(rng: np.random.Generator) -> pd.DataFrame:
    n = CONFIG.n_customers
    archetype_names = list(ARCHETYPES)
    archetype_probabilities = [ARCHETYPES[name]["share"] for name in archetype_names]
    archetypes = rng.choice(archetype_names, size=n, p=archetype_probabilities)

    acquisition_months = pd.date_range(CONFIG.data_start, CONFIG.data_end, freq="MS")
    growth_weights = np.linspace(0.72, 1.38, len(acquisition_months))
    seasonal_weights = np.array(
        [1.00, 0.91, 0.96, 1.02, 1.03, 0.95, 0.91, 0.94, 1.07, 1.13, 1.39, 1.46] * 4
    )
    weights = growth_weights * seasonal_weights
    weights /= weights.sum()
    acquisition_month = rng.choice(acquisition_months, size=n, p=weights)
    acquisition_dates = pd.to_datetime(acquisition_month) + pd.to_timedelta(
        rng.integers(0, 26, size=n), unit="D"
    )

    regions = rng.choice(
        [
            "Marmara",
            "Aegean",
            "Central Anatolia",
            "Mediterranean",
            "Black Sea",
            "Southeastern Anatolia",
            "Eastern Anatolia",
        ],
        size=n,
        p=[0.36, 0.15, 0.17, 0.12, 0.09, 0.07, 0.04],
    )
    preferred_channel = rng.choice(
        ["Mobile App", "Web", "Marketplace", "Store"],
        size=n,
        p=[0.33, 0.31, 0.21, 0.15],
    )
    age_band = rng.choice(
        ["18-24", "25-34", "35-44", "45-54", "55+"],
        size=n,
        p=[0.14, 0.33, 0.27, 0.17, 0.09],
    )
    loyalty_map = {
        "High Value Loyal": ["Gold", "Platinum"],
        "Growth": ["Silver", "Gold"],
        "Deal Seeker": ["Bronze", "Silver"],
        "Routine": ["Bronze", "Silver"],
        "At Risk": ["Silver", "Gold"],
        "One-time": ["Bronze", "Bronze"],
    }
    loyalty_tier = [
        rng.choice(loyalty_map[archetype], p=[0.58, 0.42]) for archetype in archetypes
    ]
    consent_probability = np.array(
        [0.94 if channel in {"Mobile App", "Web"} else 0.82 for channel in preferred_channel]
    )
    consent_flag = rng.binomial(1, consent_probability)

    latent_value = np.array(
        [ARCHETYPES[archetype]["value"] for archetype in archetypes]
    ) * rng.lognormal(0, 0.18, size=n)
    engagement = np.clip(
        np.array([ARCHETYPES[archetype]["engagement"] for archetype in archetypes])
        + rng.normal(0, 0.08, size=n),
        0.05,
        0.98,
    )
    price_sensitivity = np.clip(
        np.array([ARCHETYPES[archetype]["discount"] for archetype in archetypes])
        + rng.normal(0, 0.09, size=n),
        0.05,
        0.98,
    )
    service_friction = np.clip(
        np.array([ARCHETYPES[archetype]["friction"] for archetype in archetypes])
        + rng.normal(0, 0.07, size=n),
        0.02,
        0.95,
    )
    lifetime_months = np.array(
        [
            max(1, int(rng.exponential(ARCHETYPES[archetype]["lifetime"])))
            for archetype in archetypes
        ]
    )
    attrition_date = pd.Series(acquisition_dates) + pd.to_timedelta(
        lifetime_months * 30, unit="D"
    )
    end_date = pd.Timestamp(CONFIG.data_end)
    attrition_date = attrition_date.where(attrition_date <= end_date, pd.NaT)

    customers = pd.DataFrame(
        {
            "customer_id": [f"C{i:06d}" for i in range(1, n + 1)],
            "acquisition_date": acquisition_dates,
            "acquisition_channel": preferred_channel,
            "preferred_channel": preferred_channel,
            "region": regions,
            "age_band": age_band,
            "loyalty_tier": loyalty_tier,
            "marketing_consent": consent_flag.astype(int),
            "archetype": archetypes,
            "attrition_date": attrition_date,
            "latent_value_index": np.round(latent_value, 4),
            "engagement_index": np.round(engagement, 4),
            "price_sensitivity_index": np.round(price_sensitivity, 4),
            "service_friction_index": np.round(service_friction, 4),
        }
    )
    return customers


def generate_products(rng: np.random.Generator) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    product_id = 1
    price_ranges = {
        "Apparel": (450, 1650),
        "Beauty": (220, 980),
        "Electronics": (1200, 6800),
        "Home": (350, 2800),
        "Sports": (420, 2400),
        "Accessories": (180, 1300),
        "Footwear": (650, 2600),
        "Wellness": (240, 1550),
    }
    for category in CATEGORIES:
        low, high = price_ranges[category]
        for index in range(1, 7):
            price = float(rng.uniform(low, high))
            margin_pct = float(rng.uniform(0.31, 0.58))
            records.append(
                {
                    "product_id": f"P{product_id:04d}",
                    "sku": f"{category[:3].upper()}-{index:03d}",
                    "category": category,
                    "product_name": f"{category} Collection {index}",
                    "list_price": round(price, 2),
                    "standard_cost": round(price * (1 - margin_pct), 2),
                    "margin_pct": round(margin_pct, 4),
                }
            )
            product_id += 1
    return pd.DataFrame(records)


def generate_orders(
    rng: np.random.Generator, customers: pd.DataFrame, products: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    product_records = products.to_dict("records")
    product_by_category = {
        category: [record for record in product_records if record["category"] == category]
        for category in CATEGORIES
    }
    category_weights = {
        "High Value Loyal": np.array([0.19, 0.12, 0.16, 0.13, 0.10, 0.12, 0.11, 0.07]),
        "Growth": np.array([0.18, 0.12, 0.14, 0.12, 0.12, 0.13, 0.11, 0.08]),
        "Deal Seeker": np.array([0.22, 0.16, 0.08, 0.09, 0.11, 0.16, 0.12, 0.06]),
        "Routine": np.array([0.17, 0.13, 0.10, 0.16, 0.11, 0.12, 0.11, 0.10]),
        "At Risk": np.array([0.18, 0.12, 0.15, 0.13, 0.11, 0.12, 0.11, 0.08]),
        "One-time": np.array([0.24, 0.14, 0.09, 0.10, 0.10, 0.15, 0.12, 0.06]),
    }
    monthly_seasonality = {
        1: 0.82,
        2: 0.78,
        3: 0.90,
        4: 0.93,
        5: 0.96,
        6: 0.86,
        7: 0.82,
        8: 0.88,
        9: 1.02,
        10: 1.08,
        11: 1.52,
        12: 1.65,
    }
    channels = ["Mobile App", "Web", "Marketplace", "Store"]
    order_rows: list[dict[str, object]] = []
    line_rows: list[dict[str, object]] = []
    order_counter = 1
    line_counter = 1
    end_month = pd.Timestamp(CONFIG.data_end).to_period("M")

    for customer in customers.itertuples(index=False):
        start_month = pd.Timestamp(customer.acquisition_date).to_period("M")
        attrition = (
            pd.Timestamp(customer.attrition_date)
            if pd.notna(customer.attrition_date)
            else pd.Timestamp(CONFIG.data_end) + pd.Timedelta(days=1)
        )
        params = ARCHETYPES[customer.archetype]
        months = pd.period_range(start_month, end_month, freq="M")
        for period in months:
            month_start = period.start_time
            after_attrition = month_start > attrition
            if after_attrition and rng.random() > 0.035:
                continue
            trend = 0.92 + 0.025 * (month_start.year - 2022)
            rate = (
                params["monthly_rate"]
                * monthly_seasonality[month_start.month]
                * trend
                * (0.58 + 0.62 * customer.engagement_index)
            )
            if after_attrition:
                rate *= 0.20
            n_orders = min(int(rng.poisson(rate)), 4)
            for _ in range(n_orders):
                day = int(rng.integers(0, min(27, period.days_in_month)))
                order_date = month_start + pd.Timedelta(days=day)
                if order_date < customer.acquisition_date:
                    order_date = pd.Timestamp(customer.acquisition_date)
                if order_date > pd.Timestamp(CONFIG.data_end):
                    continue
                if rng.random() < 0.74:
                    channel = customer.preferred_channel
                else:
                    channel = rng.choice(channels)
                line_count = int(np.clip(1 + rng.poisson(1.05), 1, 4))
                gross_revenue = discount_amount = returned_amount = net_revenue = 0.0
                gross_margin = 0.0
                item_count = 0
                categories_for_order: list[str] = []
                order_id = f"O{order_counter:08d}"
                for _line in range(line_count):
                    category = rng.choice(
                        CATEGORIES,
                        p=category_weights[customer.archetype]
                        / category_weights[customer.archetype].sum(),
                    )
                    product = rng.choice(product_by_category[category])
                    quantity = int(rng.choice([1, 2, 3], p=[0.81, 0.16, 0.03]))
                    unit_price = float(product["list_price"]) * float(rng.lognormal(0, 0.035))
                    promotional_lift = 0.08 if order_date.month in {11, 12} else 0.0
                    discount_rate = float(
                        np.clip(
                            rng.beta(1.8 + 3 * customer.price_sensitivity_index, 8.5)
                            + promotional_lift,
                            0,
                            0.42,
                        )
                    )
                    line_gross = unit_price * quantity
                    line_discount = line_gross * discount_rate
                    line_net_before_return = line_gross - line_discount
                    return_probability = float(
                        np.clip(
                            0.025
                            + 0.075 * customer.service_friction_index
                            + (0.025 if category in {"Apparel", "Footwear"} else 0),
                            0.01,
                            0.17,
                        )
                    )
                    returned = bool(rng.random() < return_probability)
                    line_return = line_net_before_return if returned else 0.0
                    recognized_net = line_net_before_return - line_return
                    recognized_cost = (
                        float(product["standard_cost"]) * quantity * (0 if returned else 1)
                    )
                    line_margin = recognized_net - recognized_cost
                    line_rows.append(
                        {
                            "order_line_id": f"OL{line_counter:09d}",
                            "order_id": order_id,
                            "customer_id": customer.customer_id,
                            "order_date": order_date,
                            "product_id": product["product_id"],
                            "category": category,
                            "quantity": quantity,
                            "unit_price": round(unit_price, 2),
                            "discount_rate": round(discount_rate, 4),
                            "gross_revenue": round(line_gross, 2),
                            "discount_amount": round(line_discount, 2),
                            "returned_flag": int(returned),
                            "returned_amount": round(line_return, 2),
                            "net_revenue": round(recognized_net, 2),
                            "gross_margin": round(line_margin, 2),
                        }
                    )
                    line_counter += 1
                    item_count += quantity
                    categories_for_order.append(category)
                    gross_revenue += line_gross
                    discount_amount += line_discount
                    returned_amount += line_return
                    net_revenue += recognized_net
                    gross_margin += line_margin
                primary_category = max(
                    set(categories_for_order), key=categories_for_order.count
                )
                order_rows.append(
                    {
                        "order_id": order_id,
                        "customer_id": customer.customer_id,
                        "order_date": order_date,
                        "channel": channel,
                        "primary_category": primary_category,
                        "item_count": item_count,
                        "gross_revenue": round(gross_revenue, 2),
                        "discount_amount": round(discount_amount, 2),
                        "returned_amount": round(returned_amount, 2),
                        "net_revenue": round(net_revenue, 2),
                        "gross_margin": round(gross_margin, 2),
                        "returned_flag": int(returned_amount > 0),
                    }
                )
                order_counter += 1
    return pd.DataFrame(order_rows), pd.DataFrame(line_rows)


def generate_interactions(
    rng: np.random.Generator, customers: pd.DataFrame
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    end_period = pd.Timestamp(CONFIG.data_end).to_period("M")
    for customer in customers.itertuples(index=False):
        start_period = pd.Timestamp(customer.acquisition_date).to_period("M")
        attrition = (
            pd.Timestamp(customer.attrition_date)
            if pd.notna(customer.attrition_date)
            else pd.Timestamp(CONFIG.data_end) + pd.Timedelta(days=1)
        )
        for period in pd.period_range(start_period, end_period, freq="M"):
            month_end = period.end_time.normalize()
            active_multiplier = 0.22 if month_end > attrition else 1.0
            sessions = int(
                rng.poisson((0.7 + 6.2 * customer.engagement_index) * active_multiplier)
            )
            email_sent = int(rng.integers(1, 6)) if customer.marketing_consent else 0
            open_probability = float(
                np.clip(
                    0.08 + 0.66 * customer.engagement_index - (0.08 if month_end > attrition else 0),
                    0.02,
                    0.88,
                )
            )
            email_opens = int(rng.binomial(email_sent, open_probability))
            email_clicks = int(rng.binomial(email_opens, 0.22 + 0.18 * customer.engagement_index))
            support_tickets = int(
                rng.poisson(0.025 + 0.23 * customer.service_friction_index)
            )
            nps_response = rng.random() < 0.07
            nps_score = (
                int(
                    np.clip(
                        round(
                            8.4
                            - 5.1 * customer.service_friction_index
                            + 1.2 * customer.engagement_index
                            + rng.normal(0, 1.2)
                        ),
                        0,
                        10,
                    )
                )
                if nps_response
                else np.nan
            )
            rows.append(
                {
                    "customer_id": customer.customer_id,
                    "month": month_end,
                    "sessions": sessions,
                    "email_sent": email_sent,
                    "email_opens": email_opens,
                    "email_clicks": email_clicks,
                    "support_tickets": support_tickets,
                    "nps_score": nps_score,
                }
            )
    return pd.DataFrame(rows)


def generate_campaigns_and_responses(
    rng: np.random.Generator, customers: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    campaign_specs = [
        ("CMP001", "Spring Re-Engagement", "Win-Back", "2024-03-15", 58.0),
        ("CMP002", "VIP Private Sale", "VIP Experience", "2024-06-10", 92.0),
        ("CMP003", "Back-to-School Cross-Sell", "Cross-Sell", "2024-09-01", 46.0),
        ("CMP004", "Holiday Loyalty", "Retain & Reward", "2024-11-15", 72.0),
        ("CMP005", "New Year Reactivation", "Win-Back", "2025-01-12", 61.0),
        ("CMP006", "Mobile App Growth", "Nurture", "2025-04-18", 38.0),
        ("CMP007", "Summer Category Expansion", "Cross-Sell", "2025-07-05", 49.0),
        ("CMP008", "Holiday VIP 2025", "VIP Experience", "2025-11-12", 95.0),
    ]
    campaigns = pd.DataFrame(
        [
            {
                "campaign_id": campaign_id,
                "campaign_name": name,
                "campaign_type": campaign_type,
                "launch_date": pd.Timestamp(launch_date),
                "cost_per_contact": cost,
            }
            for campaign_id, name, campaign_type, launch_date, cost in campaign_specs
        ]
    )
    rows: list[dict[str, object]] = []
    base_response = {
        "High Value Loyal": 0.24,
        "Growth": 0.18,
        "Deal Seeker": 0.22,
        "Routine": 0.13,
        "At Risk": 0.10,
        "One-time": 0.06,
    }
    for campaign in campaigns.itertuples(index=False):
        eligible = customers[
            (customers["acquisition_date"] <= campaign.launch_date)
            & (customers["marketing_consent"] == 1)
        ].copy()
        if len(eligible) == 0:
            continue
        weights = (
            eligible["engagement_index"] * 0.6
            + eligible["latent_value_index"].clip(upper=2.0) * 0.25
            + 0.15
        )
        sample_size = min(1500, len(eligible))
        selected = eligible.sample(
            n=sample_size,
            weights=weights,
            random_state=int(rng.integers(1, 1_000_000)),
        )
        for customer in selected.itertuples(index=False):
            probability = base_response[customer.archetype]
            if campaign.campaign_type == "VIP Experience":
                probability += 0.08 * min(customer.latent_value_index, 2.0)
            if campaign.campaign_type == "Win-Back":
                probability += 0.05 * customer.price_sensitivity_index
            if campaign.campaign_type == "Cross-Sell":
                probability += 0.04 * customer.engagement_index
            probability = float(np.clip(probability + rng.normal(0, 0.025), 0.02, 0.58))
            responded = int(rng.random() < probability)
            conversion_value = (
                float(
                    rng.gamma(
                        shape=2.2,
                        scale=470 * customer.latent_value_index,
                    )
                )
                if responded
                else 0.0
            )
            rows.append(
                {
                    "campaign_id": campaign.campaign_id,
                    "customer_id": customer.customer_id,
                    "contact_date": campaign.launch_date,
                    "responded_flag": responded,
                    "conversion_value": round(conversion_value, 2),
                    "contact_cost": campaign.cost_per_contact,
                }
            )
    return campaigns, pd.DataFrame(rows)


def generate_all(seed: int = CONFIG.seed) -> GeneratedData:
    rng = np.random.default_rng(seed)
    customers = generate_customers(rng)
    products = generate_products(rng)
    orders, order_lines = generate_orders(rng, customers, products)
    interactions = generate_interactions(rng, customers)
    campaigns, campaign_responses = generate_campaigns_and_responses(rng, customers)
    return GeneratedData(
        customers=customers,
        products=products,
        orders=orders,
        order_lines=order_lines,
        interactions=interactions,
        campaigns=campaigns,
        campaign_responses=campaign_responses,
    )
