from app.core.config import Settings


def test_settings_accepts_comma_separated_cors_origins() -> None:
    settings = Settings(
        CORS_ORIGINS="http://localhost:3000, https://app.example.com",
    )

    assert [str(origin).rstrip("/") for origin in settings.CORS_ORIGINS] == [
        "http://localhost:3000",
        "https://app.example.com",
    ]


def test_settings_accepts_json_cors_origins() -> None:
    settings = Settings(CORS_ORIGINS='["http://localhost:3000"]')

    assert [str(origin).rstrip("/") for origin in settings.CORS_ORIGINS] == [
        "http://localhost:3000"
    ]
