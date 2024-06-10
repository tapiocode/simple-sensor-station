# Copyright (c) 2024 tapiocode
# https://github.com/tapiocode
# MIT License

import sqlite3
from aiohttp import web

class DatabaseConnection:

    _instance = None
    _conn = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._conn = None
        return cls._instance

    # Opens a connection and creates tables if needed
    def init_db(self, database_filename):
        try:
            self._conn = sqlite3.connect(database_filename)
            print(f"Connect SQLite version {sqlite3.sqlite_version}")
        except sqlite3.Error as e:
            print(e)
        if self._conn is None:
            raise RuntimeError("Error! cannot create the database connection.")
        self._create_tables()

    # Unpacks [mac, payload] and writes them into database
    def write_sensor_data(self, data):
        [mac, payload] = data
        cursor = self._conn.cursor()
        source_id = self._insert_mac(cursor, mac)
        self._insert_reading(cursor, source_id, payload)
        self._conn.commit()
        cursor.close()
        print(f"Wrote reading: mac {mac}, temp. {payload['temperature']}")

    def get_sensor_data(self, request):
        def get_response(data = None, success = False, error = ""):
            return { 'data': data, 'success': success, 'error': error }
        def get_iso_timestamp(timestamp):
            date, time = str(timestamp).split(" ")
            return date + "T" + time + "Z"

        mac = request.match_info.get('mac', None)
        cursor = self._conn.cursor()
        cursor.execute("""
            SELECT
                readings.temperature,
                readings.humidity,
                readings.pressure,
                readings.timestamp
            FROM readings
            INNER JOIN sources ON
                       readings.source_id = sources.rowid AND
                       sources.mac = ?
            ORDER BY readings.timestamp DESC
            LIMIT 20
        """, (mac,))
        readings = cursor.fetchall()
        cursor.close()

        if not readings:
            return get_response(error = "No data found for mac " + mac)
        data = [
            {
                'temperature': row[0],
                'humidity': row[1],
                'pressure': row[2],
                'timestamp': get_iso_timestamp(row[3])
            }
            for row in readings
        ]
        return get_response(data = data, success = True)

    def get_sensors(self, request):
        cursor = self._conn.cursor()
        cursor.execute("SELECT type, mac, name FROM sources")
        data = cursor.fetchall()
        cursor.close()
        return [
            {
                'type': row[0],
                'mac': row[1],
                'name': row[2]
            }
            for row in data]

    async def put_sensors(self, request):
        payload = await request.json()
        mac = payload.get('mac')
        name = payload.get('name') or ""
        if not mac:
            return { 'success': False, 'error': 'No mac address given' }
        cursor = self._conn.cursor()
        self._update_source(cursor, mac, name[:255])
        self._conn.commit()
        cursor.close()
        return web.Response(text = "OK")

    # Inserts the given MAC address, returns its rowid
    def _insert_mac(self, cursor, mac):
        cursor.execute("""
            INSERT INTO sources (
                        type,
                        mac,
                        lastseen
                        )
            VALUES ('ruuvitag', ?, CURRENT_TIMESTAMP)
                ON CONFLICT (mac) DO
                       UPDATE SET lastseen = CURRENT_TIMESTAMP
        """, (
            mac,
            ))
        cursor.execute("SELECT rowid FROM sources WHERE mac = ?", (mac,))
        return cursor.fetchone()[0]

    def _update_source(self, cursor, mac, name):
        cursor.execute("""
            UPDATE sources
            SET name = ?
            WHERE mac = ?
        """, (
            name,
            mac
            ))

    def _insert_reading(self, cursor, source_id, payload):
        cursor.execute("""
            INSERT INTO readings (
                        source_id,
                        temperature,
                        humidity,
                        pressure,
                        timestamp
                        )
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            source_id,
            payload['temperature'],
            payload['humidity'],
            payload['pressure'],
            ))

    def _create_tables(self):
        try:
            print("Creating tables")
            cursor = self._conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    type varchar(10),
                    mac varchar(17) UNIQUE,
                    name varchar(255) DEFAULT "",
                    lastseen timestamp
                );
                """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS readings (
                    source_id integer REFERENCES sources(rowid),
                    temperature numeric,
                    humidity numeric,
                    pressure numeric,
                    timestamp timestamp
                );
                """)
            cursor.close()
        except sqlite3.Error as e:
            print(e)
