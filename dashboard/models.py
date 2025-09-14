from django.db import models
from django.conf import settings
import uuid
import json
from datetime import datetime

class TimeStampedUUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# API testing models removed

#

#

#

#

#

#

#
