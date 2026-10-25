import asyncio
import sqlite3

import pytest

from profiles.repository import Repository
from profiles.service import Actor, ProfileError, ProfileService, normalize_name


def run(coroutine):
    return asyncio.run(coroutine)


@pytest.fixture
def repo(tmp_path):
    repository = Repository(tmp_path / "profiles.sqlite3")
    run(repository.initialize())
    return repository


def test_persistence_update_isolation(repo):
    async def scenario():
        service = ProfileService(repo)
        await service.define(Actor(1, 10), 10, "for", 8)
        assert await repo.attributes(1, 10) == {"FOR": 8}
        await service.define(Actor(1, 10), 10, "FOR", 10)
        await service.define(Actor(2, 10), 10, "FOR", -2)
        await service.define(Actor(1, 20), 20, "FOR", 3)
        reopened = Repository(repo.path)
        await reopened.initialize()
        assert await reopened.attributes(1, 10) == {"FOR": 10}
        assert await reopened.attributes(2, 10) == {"FOR": -2}
        assert await reopened.attributes(1, 20) == {"FOR": 3}

    run(scenario())


def test_permissions(repo):
    async def scenario():
        service = ProfileService(repo)
        with pytest.raises(ProfileError, match="não configurado"):
            await service.define(Actor(1, 10), 20, "FOR", 8)
        with pytest.raises(ProfileError, match="Somente"):
            await service.configure_master(Actor(1, 10), 99)
        await service.configure_master(Actor(1, 10, is_owner=True), 99)
        assert await Repository(repo.path).master_role(1) == 99
        for actor in [
            Actor(1, 10),
            Actor(1, 10, frozenset({98})),
            Actor(1, 10, is_owner=True),
            Actor(2, 10, frozenset({99})),
        ]:
            with pytest.raises(ProfileError):
                await service.define(actor, 20, "FOR", 8)
        master = Actor(1, 10, frozenset({99}))
        await service.define(master, 20, "FOR", 8)
        with pytest.raises(ProfileError):
            await service.remove(Actor(1, 30), 20, "FOR")
        assert await repo.attributes(1, 20) == {"FOR": 8}
        await service.remove(master, 20, "for")
        assert await repo.attributes(1, 20) == {}
        with pytest.raises(ProfileError, match="não cadastrado"):
            await service.remove(master, 20, "FOR")
        await service.configure_master(Actor(1, 30, can_manage_guild=True), 100)
        with pytest.raises(ProfileError):
            await service.define(master, 20, "FOR", 8)
        with pytest.raises(ProfileError, match="everyone"):
            await service.configure_master(Actor(1, 10, is_owner=True), 1)

    run(scenario())


@pytest.mark.parametrize(
    "name", ["", "2FOR", "FOR; DROP TABLE profiles", "ÁGIL", "A" * 33, "D20", "d100000", "X-Y"]
)
def test_invalid_names(name):
    with pytest.raises(ProfileError):
        normalize_name(name)


def test_bounds_and_no_profile_on_read(repo):
    async def scenario():
        service = ProfileService(repo)
        assert await repo.attributes(1, 10) == {}
        with repo.connection() as conn:
            assert conn.execute("SELECT COUNT(*) FROM profiles").fetchone()[0] == 0
        for value in [True, 1.5, 1_000_000_001, -1_000_000_001]:
            with pytest.raises(ProfileError):
                await service.define(Actor(1, 10), 10, "FOR", value)
        for index in range(40):
            await service.define(Actor(1, 10), 10, f"A{index}", index)
        with pytest.raises(ProfileError, match="40"):
            await service.define(Actor(1, 10), 10, "EXTRA", 1)
        await service.define(Actor(1, 10), 10, "A0", 100)
        assert (await repo.attributes(1, 10))["A0"] == 100

    run(scenario())


def test_foreign_key(repo):
    with pytest.raises(sqlite3.IntegrityError), repo.connection() as conn:
        conn.execute("INSERT INTO attributes VALUES (?, ?, ?, ?)", (1, 10, "FOR", 8))


def test_concurrent_attribute_limit(repo):
    async def scenario():
        service = ProfileService(repo)
        results = await asyncio.gather(
            *[service.define(Actor(1, 10), 10, f"A{i}", i) for i in range(45)],
            return_exceptions=True,
        )
        assert sum(isinstance(item, ProfileError) for item in results) == 5
        assert len(await repo.attributes(1, 10)) == 40

    run(scenario())
