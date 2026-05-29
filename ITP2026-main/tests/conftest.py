from __future__ import annotations
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import Base, get_session
from app.main import app
from app.models import EmissionFactor

# In-memory SQLite används för tester — databasen finns bara i RAM och försvinner efter testet
TEST_DATABASE_URL = "sqlite:///:memory:"

# StaticPool krävs för in-memory SQLite så att alla anrop delar samma databasanslutning
# Utan StaticPool skulle varje anrop få en egen tom databas och testdata skulle försvinna
engine = create_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)

# Skapar en sessionfabrik kopplad till testdatabasmotorn
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

@pytest.fixture
def db_session():
    # Skapar alla tabeller i testdatabasen innan testet körs
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Lägger in en testfaktor så att tester som behöver en emissionsfaktor har något att jobba med
    car_factor = EmissionFactor(
        category="travel",
        key="car",
        unit="km",
        co2e_per_unit=0.2,
        source="test",
        scope="direct"
    )
    db.add(car_factor)
    db.commit()

    try:
        # yield ger sessionen till testet som använder fixture:n
        yield db
    finally:
        # Stänger sessionen och raderar alla tabeller efter testet — ren slate för nästa test
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    # Ersätter den riktiga databassessionen med testsessionen via dependency_overrides
    # Detta gör att applikationen använder testdatabasen istället för app.db under testerna
    def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    from fastapi.testclient import TestClient
    with TestClient(app) as c:
        yield c

    # Återställer dependency_overrides efter testet så att andra tester inte påverkas
    app.dependency_overrides.clear()