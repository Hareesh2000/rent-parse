from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class ListingType(StrEnum):
    ENTIRE_FLAT = "flat"
    FLATMATE = "flatmate"
    OTHER = "other"


class Listing(BaseModel):
    listing_type: ListingType = Field(
        description="Categorize the primary purpose of the listing. "
        "Use 'flat' if renting out an entire vacant property. "
        "Use 'flatmate' if they are seeking a person to share an already "
        "occupied property. Any other intent should be categorized as 'other'."
    )
    rent: int | None = Field(
        description="The exact monthly rent amount in INR as an integer (e.g., 45000), "
        "convert to integer (eg., 45K to 45000). "
        "Do not include security deposits or maintenance fees. "
        "If the listing type is 'flatmate', extract only the individual's share "
        "if mentioned. Return null if the rent is not explicitly stated."
    )
    locality: str | None = Field(
        description="The specific neighborhood or sub-locality "
        "in Bangalore (e.g., 'HSR Layout', 'Koramangala'). Extract only the area name, "
        "ignoring the city name, exact street address, or building name. "
        "Return null if the locality is not mentioned."
    )
    furnishing: Literal["furnished", "semi-furnished", "unfurnished"] | None = Field(
        description="The furnishing status of the property. "
        "Map phrases like 'fully set up' to 'furnished'. "
        "Map 'wardrobes only' or 'basic woodwork' to 'semi-furnished'. "
        "If it says 'empty', use 'unfurnished'. "
        "If not explicitly mentioned, return null."
    )
    bedrooms: int | None = Field(
        description="The total number of bedrooms in the "
        "property as an integer. For a '1 RK' or a single room for rent, extract 1. "
        "For a '3BHK', extract 3. Return null if not stated."
    )
    preferred_tenants: Literal["family", "bachelor", "any", "male", "female"] | None = (
        Field(
            description="The preferred tenant type. Map terms "
            "like 'bachelors', 'spinsters', or 'working professionals' to '"
            "bachelor'. Map 'couples' or 'family only' to 'family'. "
            "If they specify a gender (e.g., 'girls only'), "
            "choose 'female' or 'male'. "
            "If they explicitly state any tenant is allowed, use 'any'. "
            "If no restriction is mentioned, return null."
        )
    )
