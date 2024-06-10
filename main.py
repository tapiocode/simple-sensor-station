#!/usr/bin/env python3

# Copyright (c) 2024 tapiocode
# https://github.com/tapiocode
# MIT License

import os
os.environ["RUUVI_BLE_ADAPTER"] = "bleak"

import asyncio
import uuid
from ruuvitag_sensor.ruuvi import RuuviTagSensor
from server.database import DatabaseConnection
from server.aiohttp import get_web_app, web_server

DATABASE = "readings.db"
DEVICE_UUID = uuid.getnode()

async def ruuvitag_reader(db):
    async for ruuvitag_read_data in RuuviTagSensor.get_data_async():
        db.write_sensor_data(ruuvitag_read_data)

async def run_tasks():
    db = DatabaseConnection()
    db.init_db(DATABASE)
    app = get_web_app(db)

    sensor_reader_task = asyncio.create_task(ruuvitag_reader(db))
    web_server_task = asyncio.create_task(web_server(app))
    await asyncio.gather(sensor_reader_task, web_server_task)

if __name__ == "__main__":
    asyncio.run(run_tasks())
