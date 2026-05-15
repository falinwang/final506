from pydantic import BaseModel


class Concert(BaseModel):
    event_name: str
    artists: list[str]
    date: str
    time: str | None
    url: str


class Track(BaseModel):
    artist: str
    title: str
    album: str
    length: str
    release_date: str


class ArtistTracks(BaseModel):
    artist: str
    tracks: list[Track]


class SearchResult(BaseModel):
    concert: Concert
    lineups: list[ArtistTracks]
