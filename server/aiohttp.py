# Copyright (c) 2024 tapiocode
# https://github.com/tapiocode
# MIT License

from aiohttp import web

def get_web_app(db):
    app = web.Application()
    app.add_routes([
        web.get("/",
                lambda _: web.FileResponse("./client/index.html")),
        web.get("/api/sensors",
                lambda request: web.json_response(db.get_sensors(request))),
        web.put("/api/sensors", db.put_sensors),
        web.get("/api/sensordata/{mac}",
                lambda request: web.json_response(db.get_sensor_data(request))),
                ])
    app.router.add_static("/", "./client")
    return app

async def web_server(app, host = "0.0.0.0", port = 8080):
    runner = web.AppRunner(app)
    await runner.setup();
    site = web.TCPSite(runner, host, port)
    print(f"aiohttp web server started: http://{host}:{port}")
    await site.start()
