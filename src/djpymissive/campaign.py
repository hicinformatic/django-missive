def run_campaign(campaign_id):
    from .models.campaign import MissiveCampaign
    scheduled = MissiveScheduledCampaign.objects.get(id=campaign_id, send_date__isnull=True)
    campaign = scheduled.campaign
    scheduled.send_date = timezone.now()
    campaign.start_campaign()
    scheduled.ended_at = timezone.now()
    scheduled.save()
    
    