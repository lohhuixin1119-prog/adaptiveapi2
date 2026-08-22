from schemas import AdaptInputV1, AdaptOutputV2

class V1ToV2Adapter:
    """Handles schema transformations from API Version 1 to Version 2."""
    
    PRIORITY_MAP = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
        "CRITICAL": 4
    }

    @classmethod
    def transform(cls, v1_input: AdaptInputV1) -> AdaptOutputV2:
        # Extract raw metadata priority, defaulting to LOW
        raw_priority = v1_input.metadata.get("priority", "LOW").upper()
        
        return AdaptOutputV2(
            id=v1_input.user.id,
            name=v1_input.user.fullName,
            action=v1_input.action.lower(),
            priority=cls.PRIORITY_MAP.get(raw_priority, 1)
        )
