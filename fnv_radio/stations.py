"""Radio stations the generator knows how to rebuild."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Station:
    id: str
    name: str
    plugin: str          # plugin that owns the radio quest
    quest: str           # EditorID of the quest holding the station's dialogue
    # INFO FormID -> song file to use instead of the one in the plugin ("fixed" mode)
    sound_fixes: dict = field(default_factory=dict)


STATIONS = {
    "rnv": Station(
        id="rnv",
        name="Radio New Vegas",
        plugin="FalloutNV.esm",
        quest="RadioNewVegas",
        # "Stars of the Midnight Range" points to Big Iron's sound in the vanilla game.
        sound_fixes={"0016AD03": "sound\\songs\\radionv\\mus_stars_of_the_midnight_range.mp3"},
    ),
    "bm": Station(
        id="bm",
        name="Black Mountain Radio",
        plugin="FalloutNV.esm",
        quest="RadioBlackMountain",
    ),
    "mmr": Station(
        id="mmr",
        name="Mojave Music Radio",
        plugin="FalloutNV.esm",
        quest="vCountryRadioQuest",
    ),
}
