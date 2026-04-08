from decimal import Decimal
from .pattern_detection import PatternDetector
from .recurring_detection import RecurringDetector

class RecommendationEngine:
    def __init__(self, user):
        self.user = user
        self.pattern_detector = PatternDetector(user)
        self.recurring_detector = RecurringDetector(user)
    
    def generate_recommendations(self):
        recommendations = []
        
        # Check for recurring subscriptions
        recurring = self.recurring_detector.detect_recurring()
        for sub in recurring:
            recommendations.append({
                'title': f'Review {sub["merchant"].title()} Subscription',
                'description': f'You have a recurring ${sub["amount"]:.2f} {sub["frequency"]} payment to {sub["merchant"].title()} ({sub["count"]} payments detected). Consider if you still need this subscription.',
                'potential_savings': Decimal(str(sub['amount'])) * (12 if sub['frequency'] == 'monthly' else 52)
            })
        
        # Get spending patterns and generate recommendations
        overspending = self.pattern_detector.detect_overspending()
        if overspending:
            recommendations.append({
                'title': 'Reduce Daily Spending',
                'description': 'You have several days with unusually high spending. Consider setting a daily budget of $50 and tracking expenses using a spending tracker app.',
                'potential_savings': Decimal('200.00')
            })
        
        # Check impulse spending
        impulse = self.pattern_detector.detect_impulse_spending()
        if impulse:
            recommendations.append({
                'title': 'Control Impulse Purchases',
                'description': 'You make many small purchases. Try the 24-hour rule: wait a day before making any non-essential purchase under $50.',
                'potential_savings': Decimal('100.00')
            })
        
        # Check weekend spending
        weekend = self.pattern_detector.detect_weekend_spending()
        if weekend:
            recommendations.append({
                'title': 'Plan Weekend Activities',
                'description': 'Weekend spending is significantly higher. Try planning free or low-cost weekend activities like hiking, picnics, or home movie nights.',
                'potential_savings': Decimal('150.00')
            })
        
        # Check category trends
        trends = self.pattern_detector.detect_category_trends()
        for trend in trends:
            recommendations.append({
                'title': trend['title'],
                'description': trend['description'] + ' Review recent purchases in this category to see if you can reduce spending.',
                'potential_savings': Decimal('100.00')
            })
        
        return recommendations
