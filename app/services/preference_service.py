from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.preference import UserPreference
from app.schemas.preference import PreferenceRequest, PreferenceResponseData


class PreferenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert_preferences(self, request: PreferenceRequest) -> PreferenceResponseData:
        record = self.db.get(UserPreference, request.user_id)
        if record is None:
            record = UserPreference(user_id=request.user_id, preferences=request.preferences)
        else:
            record.preferences = request.preferences

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return PreferenceResponseData(
            user_id=record.user_id,
            preferences=record.preferences,
            updated_at=record.updated_at,
        )

    def get_preferences(self, user_id: str) -> PreferenceResponseData:
        record = self.db.get(UserPreference, user_id)
        if record is None:
            raise AppException(detail="Preferences not found for user.", status_code=404, code="not_found")

        return PreferenceResponseData(
            user_id=record.user_id,
            preferences=record.preferences,
            updated_at=record.updated_at,
        )
