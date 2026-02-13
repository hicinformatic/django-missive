"""Manager for MissiveCampaign model."""

from django.db import models
from django.db.models import Case, F, Q, Value, When
from django.db.models.functions import Coalesce

from ..models.choices import MissiveStatus


class MissiveCampaignManager(models.Manager):
    """Manager for MissiveCampaign with annotated counts."""

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(
            send_date=models.Max("to_missivecampaignsend__send_date"),
            ended_at=models.Max("to_missivecampaignsend__ended_at"),
            count_missive=models.Count("to_missive", distinct=True),
            count_recipient=models.Count(
                "to_missive__to_missiverecipient", distinct=True
            ),
            count_recipient_failed=models.Count(
                "to_missive__to_missiverecipient",
                distinct=True,
                filter=Q(
                    to_missive__to_missiverecipient__status=MissiveStatus.FAILED
                ),
            ),
            count_recipient_success=models.Count(
                "to_missive__to_missiverecipient",
                distinct=True,
                filter=Q(
                    to_missive__to_missiverecipient__status=MissiveStatus.SUCCESS
                ),
            ),
            count_recipient_processing=models.Count(
                "to_missive__to_missiverecipient",
                distinct=True,
                filter=Q(
                    to_missive__to_missiverecipient__status=MissiveStatus.PROCESSING
                ),
            ),
        )
        pct_expr = lambda cnt: Coalesce(
            Case(
                When(count_recipient=0, then=Value(0.0)),
                default=cnt * 100.0 / F("count_recipient"),
                output_field=models.FloatField(),
            ),
            Value(0.0),
        )
        qs = qs.annotate(
            pct_failed=pct_expr(F("count_recipient_failed")),
            pct_success=pct_expr(F("count_recipient_success")),
            pct_processing=pct_expr(F("count_recipient_processing")),
        )
        return qs
