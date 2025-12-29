"""
Analytics Service
=================
Generate insights, summaries, and reports from expense data.
"""

from collections import defaultdict
from datetime import datetime
from typing import Optional


def analyze_expenses(
    expenses: list[dict],
    group_by: str = "category",
    currency: str = "MAD"
) -> dict:
    """
    Analyze a list of expenses and generate insights.
    
    Args:
        expenses: List of expense dictionaries
        group_by: Grouping field (category, date, payment_method)
        currency: Target currency for totals
    
    Returns:
        Analytics summary with breakdown and insights
    """
    if not expenses:
        return {
            "success": True,
            "total_amount": 0,
            "currency": currency,
            "count": 0,
            "breakdown": {},
            "insights": ["No expenses to analyze"]
        }
    
    # Calculate totals
    total = 0
    breakdown = defaultdict(lambda: {"amount": 0, "count": 0})
    payment_methods = defaultdict(int)
    daily_totals = defaultdict(float)
    
    for expense in expenses:
        amount = expense.get("amount") or 0
        total += amount
        
        # Group by specified field
        group_key = expense.get(group_by) or "other"
        breakdown[group_key]["amount"] += amount
        breakdown[group_key]["count"] += 1
        
        # Track payment methods
        pm = expense.get("payment_method") or "unknown"
        payment_methods[pm] += amount
        
        # Track daily totals
        date = expense.get("date") or "unknown"
        daily_totals[date] += amount
    
    # Generate insights
    insights = []
    
    # Top category
    if breakdown:
        top_category = max(breakdown.items(), key=lambda x: x[1]["amount"])
        insights.append(
            f"Highest spending: {top_category[0]} ({top_category[1]['amount']:.2f} {currency})"
        )
    
    # Preferred payment method
    if payment_methods:
        top_payment = max(payment_methods.items(), key=lambda x: x[1])
        insights.append(
            f"Most used payment: {top_payment[0]} ({top_payment[1]:.2f} {currency})"
        )
    
    # Average expense
    avg = total / len(expenses) if expenses else 0
    insights.append(f"Average expense: {avg:.2f} {currency}")
    
    # Spending trend (if dates available)
    dated_expenses = [e for e in expenses if e.get("date")]
    if len(dated_expenses) >= 2:
        dates = sorted(set(e["date"] for e in dated_expenses))
        if len(dates) >= 2:
            first_half = sum(daily_totals[d] for d in dates[:len(dates)//2])
            second_half = sum(daily_totals[d] for d in dates[len(dates)//2:])
            if second_half > first_half:
                insights.append("📈 Spending trending upward")
            elif second_half < first_half:
                insights.append("📉 Spending trending downward")
    
    return {
        "success": True,
        "total_amount": round(total, 2),
        "currency": currency,
        "count": len(expenses),
        "breakdown": dict(breakdown),
        "insights": insights,
        "payment_summary": dict(payment_methods),
        "daily_totals": dict(daily_totals)
    }


def generate_summary(
    expenses: list[dict],
    period: str = "this period"
) -> str:
    """
    Generate a human-readable summary of expenses.
    
    Args:
        expenses: List of expenses
        period: Description of time period
    
    Returns:
        Formatted summary text
    """
    analytics = analyze_expenses(expenses)
    
    summary = f"""
📊 EXPENSE SUMMARY - {period.upper()}
{'='*40}

Total Spent: {analytics['total_amount']:.2f} {analytics['currency']}
Number of Expenses: {analytics['count']}

📁 BY CATEGORY:
"""
    
    for category, data in analytics["breakdown"].items():
        pct = (data["amount"] / analytics["total_amount"] * 100) if analytics["total_amount"] > 0 else 0
        summary += f"  • {category}: {data['amount']:.2f} {analytics['currency']} ({pct:.1f}%)\n"
    
    summary += "\n💡 INSIGHTS:\n"
    for insight in analytics["insights"]:
        summary += f"  • {insight}\n"
    
    return summary.strip()


def get_category_breakdown(expenses: list[dict]) -> dict:
    """Get simple category breakdown"""
    breakdown = defaultdict(float)
    for expense in expenses:
        category = expense.get("category") or "other"
        amount = expense.get("amount") or 0
        breakdown[category] += amount
    return dict(breakdown)


def detect_anomalies(expenses: list[dict], threshold: float = 2.0) -> list[dict]:
    """
    Detect unusual expenses based on standard deviation.
    
    Args:
        expenses: List of expenses
        threshold: Number of standard deviations for anomaly
    
    Returns:
        List of anomalous expenses
    """
    if len(expenses) < 3:
        return []
    
    amounts = [e.get("amount") or 0 for e in expenses]
    mean = sum(amounts) / len(amounts)
    variance = sum((x - mean) ** 2 for x in amounts) / len(amounts)
    std_dev = variance ** 0.5
    
    if std_dev == 0:
        return []
    
    anomalies = []
    for expense in expenses:
        amount = expense.get("amount") or 0
        z_score = abs(amount - mean) / std_dev
        if z_score > threshold:
            anomalies.append({
                **expense,
                "z_score": round(z_score, 2),
                "deviation": "high" if amount > mean else "low"
            })
    
    return anomalies
