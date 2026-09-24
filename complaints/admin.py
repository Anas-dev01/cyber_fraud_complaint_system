from django.contrib import admin
from .models import Complaint, Evidence, VictimProfile

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('tracking_id', 'victim', 'fraud_type', 'status', 'created_at')
    list_filter = ('status', 'fraud_type')
    search_fields = ('tracking_id', 'description')
    readonly_fields = ('tracking_id', 'created_at', 'updated_at')

@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'file', 'uploaded_at')

@admin.register(VictimProfile)
class VictimProfileAdmin(admin.ModelAdmin):
    list_display = ('user',)
    search_fields = ('user__username', 'user__email')
