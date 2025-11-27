"""Shared in-memory QuerySet base class for virtual models."""

from __future__ import annotations

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db.models.query import QuerySet
from django.db.models.sql import Query


class InMemoryQuerySet(QuerySet):
    """Base class for in-memory QuerySets used by virtual models.

    This QuerySet stores data in memory rather than querying the database.
    Useful for models that don't have database tables (managed=False).
    """

    def __init__(self, model=None, data=None, query=None, using=None, hints=None):
        if query is None and model is not None:
            query = Query(model)
        super().__init__(model=model, query=query, using=using, hints=hints)
        self._result_cache = list(data or [])
        self._prefetch_done = True

    def __len__(self):
        return len(self._result_cache)

    def __getitem__(self, k):
        if isinstance(k, slice):
            return self.__class__(
                self.model,
                self._result_cache[k],
                self.query.clone(),
                using=self._db,
                hints=self._hints,
            )
        return self._result_cache[k]

    def _clone(self):
        return self.__class__(
            self.model,
            list(self._result_cache),
            self.query.clone(),
            using=self._db,
            hints=self._hints,
        )

    def all(self):
        return self._clone()

    def count(self):
        return len(self._result_cache)

    def filter(self, *args, **kwargs):
        """Filter in-memory objects with Django lookup support."""
        rslt = self._result_cache

        def _value(obj, attr):
            return getattr(obj, attr, "")

        for lookup, value in kwargs.items():
            if "__" in lookup:
                field_name, lookup_type = lookup.rsplit("__", 1)
                if lookup_type == "icontains":
                    rslt = [
                        obj
                        for obj in rslt
                        if value.lower() in str(_value(obj, field_name)).lower()
                    ]
                elif lookup_type == "contains":
                    rslt = [
                        obj for obj in rslt if value in str(_value(obj, field_name))
                    ]
                elif lookup_type == "exact":
                    rslt = [obj for obj in rslt if _value(obj, field_name) == value]
                elif lookup_type == "in":
                    rslt = [obj for obj in rslt if _value(obj, field_name) in value]
                # Other lookup types can be added here as needed
            else:
                rslt = [obj for obj in rslt if getattr(obj, lookup, None) == value]
        return self.__class__(
            self.model,
            rslt,
            self.query.clone(),
            using=self._db,
            hints=self._hints,
        )

    def order_by(self, *fields):
        """Sort in-memory objects by specified fields."""
        rslt = self._result_cache
        for field in reversed(fields):
            reverse = field.startswith("-")
            field_name = field[1:] if reverse else field
            rslt = sorted(
                rslt,
                key=lambda obj: getattr(obj, field_name, "") or "",
                reverse=reverse,
            )
        return self.__class__(
            self.model,
            rslt,
            self.query.clone(),
            using=self._db,
            hints=self._hints,
        )

    def get(self, **kwargs):
        """Get a single object matching the given lookups."""
        rslt = self._result_cache
        for attr, value in kwargs.items():
            rslt = [obj for obj in rslt if getattr(obj, attr) == value]
        if len(rslt) == 1:
            return rslt[0]
        if not rslt:
            raise ObjectDoesNotExist(
                f"{self.model.__name__} matching query does not exist."
            )
        raise MultipleObjectsReturned(
            f"Multiple {self.model.__name__} objects returned."
        )
