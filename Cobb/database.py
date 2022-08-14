import logging
from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticCollection
import certifi
from time import perf_counter

class MongoDB:
    def __init__(self, uri):
        self.tlsca_ = certifi.where()
        self._client = AsyncIOMotorClient(uri, tlsCAFile=self.tlsca_)
        self._db_name = self._client['Cobb']

    async def ping(self):
        st_time = perf_counter()
        await self._db_name.command("ping")
        logging.info(f'MongoDB Pinged: {round((perf_counter() - st_time), 2)}s')

    def make_collection(self, name: str) -> AgnosticCollection:
        return self._db_name[name]