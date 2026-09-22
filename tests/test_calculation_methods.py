from app.api.v1.calculation_methods import get_calculation_methods


def test_calculation_methods_endpoint_returns_all_supported_v1_settings() -> None:
    response = get_calculation_methods()

    assert response.model_dump() == {
        "calculation_methods": [
            "muslim_world_league",
            "egyptian",
            "karachi",
            "umm_al_qura",
            "dubai",
            "iacad_dubai",
            "moon_sighting_committee",
            "north_america",
            "kuwait",
            "qatar",
            "singapore",
            "uoif",
        ],
        "madhabs": ["shafi", "hanafi"],
        "high_latitude_rules": [
            "middle_of_the_night",
            "seventh_of_the_night",
            "twilight_angle",
        ],
    }
