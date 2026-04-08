from django.contrib import admin
from .models import Transaction, Insight, Recommendation

admin.site.register(Transaction)
admin.site.register(Insight)
admin.site.register(Recommendation)