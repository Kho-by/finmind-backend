from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal
from collections import defaultdict

class PatternDetector:
    def __init__(self, user):
        self.user = user
        self.transactions = user.transactions.all()
    
    def detect_overspending(self):
        """Detect if user is spending more than 30% above average"""
        insights = []
        
        # Get last 30 days transactions
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_transactions = self.transactions.filter(timestamp__gte=thirty_days_ago)
        
        if recent_transactions.count() < 5:
            return insights
        
        # Calculate average daily spending
        daily_spending = defaultdict(float)
        for t in recent_transactions:
            date = t.timestamp.date()
            daily_spending[date] += float(t.amount)
        
        if not daily_spending:
            return insights
            
        avg_daily = sum(daily_spending.values()) / len(daily_spending)
        
        # Check for overspending days
        overspend_days = []
        for date, amount in daily_spending.items():
            if amount > avg_daily * 1.3:  # 30% above average
                overspend_days.append((date, amount, (amount/avg_daily - 1) * 100))
        
        if overspend_days:
            # Take the worst overspending day
            worst_day = max(overspend_days, key=lambda x: x[2])
            date, amount, percentage = worst_day
            insights.append({
                'type': 'overspending',
                'title': 'High Spending Day Detected',
                'description': f'On {date}, you spent ${amount:.2f}, which is {percentage:.0f}% above your average daily spend of ${avg_daily:.2f}. Consider reviewing this day\'s transactions.',
                'severity': 4 if percentage > 50 else 3
            })
        
        return insights
    
    def detect_impulse_spending(self):
        """Detect small frequent purchases that might be impulse buys"""
        insights = []
        
        # Get last 7 days transactions
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_transactions = self.transactions.filter(timestamp__gte=seven_days_ago)
        
        # Look for transactions under $25
        impulse_transactions = [t for t in recent_transactions if float(t.amount) < 25]
        
        if len(impulse_transactions) >= 5:
            total_impulse = sum(float(t.amount) for t in impulse_transactions)
            avg_impulse = total_impulse / len(impulse_transactions)
            insights.append({
                'type': 'impulse',
                'title': 'Frequent Small Purchases',
                'description': f'You made {len(impulse_transactions)} purchases under $25 in the last week, totaling ${total_impulse:.2f} (average ${avg_impulse:.2f} each). Consider if these were all necessary.',
                'severity': 3
            })
        
        return insights
    
    def detect_late_night_spending(self):
        """Detect spending between 10 PM and 4 AM"""
        insights = []
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_transactions = self.transactions.filter(timestamp__gte=thirty_days_ago)
        
        late_night = []
        for t in recent_transactions:
            hour = t.timestamp.hour
            if hour >= 22 or hour <= 4:
                late_night.append(t)
        
        if len(late_night) >= 3:
            total_late = sum(float(t.amount) for t in late_night)
            insights.append({
                'type': 'late_night',
                'title': 'Late Night Spending Pattern',
                'description': f'You made {len(late_night)} purchases after 10 PM in the last month, totaling ${total_late:.2f}. Late-night spending is often impulsive. Try waiting until morning to make these purchases.',
                'severity': 2
            })
        
        return insights
    
    def detect_weekend_spending(self):
        """Detect weekend spending spikes"""
        insights = []
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_transactions = self.transactions.filter(timestamp__gte=thirty_days_ago)
        
        weekend_total = 0
        weekday_total = 0
        weekend_count = 0
        weekday_count = 0
        
        for t in recent_transactions:
            if t.timestamp.weekday() >= 5:  # 5=Saturday, 6=Sunday
                weekend_total += float(t.amount)
                weekend_count += 1
            else:
                weekday_total += float(t.amount)
                weekday_count += 1
        
        if weekend_count > 0 and weekday_count > 0:
            avg_weekend = weekend_total / weekend_count
            avg_weekday = weekday_total / weekday_count
            
            if avg_weekend > avg_weekday * 1.5:
                insights.append({
                    'type': 'weekend',
                    'title': 'Weekend Spending Spike',
                    'description': f'You spend {((avg_weekend/avg_weekday)-1)*100:.0f}% more on weekends (${avg_weekend:.2f}/day) compared to weekdays (${avg_weekday:.2f}/day). Consider planning weekend activities within a budget.',
                    'severity': 3
                })
        
        return insights
    
    def detect_category_trends(self):
        """Detect which categories are growing fastest"""
        insights = []
        
        # Compare last 30 days with previous 30 days
        now = timezone.now()
        period1_start = now - timedelta(days=60)
        period1_end = now - timedelta(days=30)
        period2_start = now - timedelta(days=30)
        
        period1_txns = self.transactions.filter(
            timestamp__gte=period1_start,
            timestamp__lt=period1_end
        )
        period2_txns = self.transactions.filter(timestamp__gte=period2_start)
        
        # Group by category
        category_spending = defaultdict(lambda: {'period1': 0, 'period2': 0})
        
        for t in period1_txns:
            category_spending[t.category]['period1'] += float(t.amount)
        
        for t in period2_txns:
            category_spending[t.category]['period2'] += float(t.amount)
        
        # Find categories with significant increase
        for category, amounts in category_spending.items():
            if amounts['period1'] > 0:
                increase = ((amounts['period2'] - amounts['period1']) / amounts['period1']) * 100
                if increase > 50 and amounts['period2'] > 100:
                    category_name = dict(Transaction.CATEGORY_CHOICES).get(category, category)
                    insights.append({
                        'type': 'trend',
                        'title': f'Rising {category_name} Spending',
                        'description': f'Your {category_name} spending has increased by {increase:.0f}% compared to last month (${amounts["period1"]:.2f} → ${amounts["period2"]:.2f}).',
                        'severity': 2
                    })
        
        return insights
