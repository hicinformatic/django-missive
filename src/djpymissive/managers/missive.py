from django.db import models
from django.db.models.expressions import Subquery, OuterRef
from django.db.models import F, Max
from django.db.models.functions import Coalesce


class MissiveManager(models.Manager):

    def last_event_subquery(self, field: str = "event"):
        from ..models.event import MissiveEvent
        return Subquery(
            MissiveEvent.objects.filter(
                missive=OuterRef("pk"),
            ).order_by("-occurred_at", "-id").values("event")[:1],
            output_field=models.CharField(),
        )
    
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(
            count_event=models.Count("to_missiveevent"),
            last_event=self.last_event_subquery(field="event"),
            last_event_description=self.last_event_subquery(field="description"),
            last_event_date=Coalesce(Max("to_missiveevent__occurred_at"), F("created_at")),
            count_related_object=models.Count("to_missiverelatedobject"),
        )
        return qs