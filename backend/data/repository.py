"""The data boundary used by the API and engine, rather than duplicated SQL."""
from uuid import UUID

from .models import (
    AccessContext, Department, Engagement, EngagementFound,
    EngagementNotFound, EngagementResult, Vendor,
)


class DataRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_engagement(self, engagement_id: UUID | str, access_context: AccessContext) -> EngagementResult:
        """Return permitted engagement with vendor/department, or typed not_found.

        Missing and forbidden IDs deliberately share the same result. The API
        must derive access_context from authentication; this method cannot do so.
        Invalid UUID strings raise ValueError at this internal boundary.
        """
        identifier = UUID(str(engagement_id))
        row = self.connection.execute(
            """
            SELECT e.engagement_id, e.source_key, e.title, e.source_uri,
                   v.vendor_id, v.source_key AS vendor_source_key,
                   v.name AS vendor_name, v.source_uri AS vendor_source_uri,
                   d.department_id, d.source_key AS department_source_key,
                   d.name AS department_name, d.source_uri AS department_source_uri
            FROM engagements e
            JOIN vendors v ON v.vendor_id = e.vendor_id
            JOIN departments d ON d.department_id = e.department_id
            WHERE e.engagement_id = %s AND e.department_id = ANY(%s::uuid[])
            """,
            (identifier, list(access_context.allowed_department_ids)),
        ).fetchone()
        if row is None:
            return EngagementNotFound(engagement_id=identifier)
        return EngagementFound(engagement=Engagement(
            engagement_id=row["engagement_id"], source_key=row["source_key"],
            title=row["title"], source_uri=row["source_uri"],
            vendor=Vendor(
                vendor_id=row["vendor_id"], source_key=row["vendor_source_key"],
                name=row["vendor_name"], source_uri=row["vendor_source_uri"],
            ),
            department=Department(
                department_id=row["department_id"], source_key=row["department_source_key"],
                name=row["department_name"], source_uri=row["department_source_uri"],
            ),
        ))

