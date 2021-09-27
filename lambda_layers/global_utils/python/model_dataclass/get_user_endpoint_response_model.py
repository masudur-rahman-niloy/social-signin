from __future__ import annotations

from typing import List

from pydantic import BaseModel


class Attributes(BaseModel):
    string: List[str]


class Demographic(BaseModel):
    AppVersion: str
    Locale: str
    Make: str
    Model: str
    ModelVersion: str
    Platform: str
    PlatformVersion: str
    Timezone: str


class Location(BaseModel):
    City: str
    Country: str
    Latitude: float
    Longitude: float
    PostalCode: str
    Region: str


class Metrics(BaseModel):
    string: float


class UserAttributes(BaseModel):
    string: List[str]


class User(BaseModel):
    UserAttributes: UserAttributes
    UserId: str


class EndpointItem(BaseModel):
    Address: str
    ApplicationId: str
    Attributes: Attributes
    ChannelType: str
    CohortId: str
    CreationDate: str
    Demographic: Demographic
    EffectiveDate: str
    EndpointStatus: str
    Id: str
    Location: Location
    Metrics: Metrics
    OptOut: str
    RequestId: str
    User: User


class EndpointsResponse(BaseModel):
    Item: List[EndpointItem]


class UserEndpointsResponseModel(BaseModel):
    EndpointsResponse: EndpointsResponse
