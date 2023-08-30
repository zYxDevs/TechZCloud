from utils.download import DL_STATUS
import aiohttp
from config import *
from utils.remote_upload import start_remote_upload
from utils.tgstreamer import work_loads, multi_clients
import asyncio
from pyrogram import Client, idle
from werkzeug.utils import secure_filename
import os
from utils.db import is_hash_in_db, save_file_in_db
from utils.file import allowed_file, delete_cache, get_file_hash
from utils.tgstreamer import media_streamer
from utils.upload import upload_file_to_channel
from utils.upload import PROGRESS


from aiohttp import web

app = web.Application()


def render_template(name):
    with open(f"templates/{name}") as f:
        return f.read()


async def upload_file(request):
    global UPLOAD_TASK

    reader = await request.multipart()
    field = await reader.next()
    filename = field.filename

    if field is None:
        return web.Response(text="No file uploaded.", content_type="text/plain")

    if not allowed_file(filename):
        return web.Response(
            text="File type not allowed", status=400, content_type="text/plain"
        )
    if filename == "":
        return web.Response(
            text="No file selected.", content_type="text/plain", status=400
        )

    filename = secure_filename(filename)
    extension = filename.rsplit(".", 1)[1]
    hash = get_file_hash()

    while is_hash_in_db(hash):
        hash = get_file_hash()
        print(hash)

    try:
        with open(os.path.join("static/uploads", f"{hash}.{extension}"), "wb") as f:
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                f.write(chunk)
    except Exception as e:
        return web.Response(
            text=f"Error saving file: {str(e)}",
            status=500,
            content_type="text/plain",
        )

    save_file_in_db(filename, hash)
    UPLOAD_TASK.append((hash, filename, extension))
    return web.Response(text=hash, content_type="text/plain", status=200)


async def home(_):
    return web.Response(text=render_template("minindex.html"), content_type="text/html")

async def bot_status(_):
    json = work_loads
    return web.json_response(json)

async def remote_upload(request):
    global aiosession
    hash = get_file_hash()
    print(request.headers)
    link = request.headers["url"]

    while is_hash_in_db(hash):
        hash = get_file_hash()

    print("Remote upload", hash)
    loop.create_task(start_remote_upload(aiosession, hash, link))
    return web.Response(text=hash, content_type="text/plain", status=200)


async def file_html(request):
    hash = request.match_info["hash"]
    download_link = f"http://cloud.techzbots.live/dl/{hash}"
    filename = is_hash_in_db(hash)["filename"]

    return web.Response(
        text=render_template("minfile.html")
        .replace("FILE_NAME", filename)
        .replace("DOWNLOAD_LINK", download_link),
        content_type="text/html",
    )


async def static_files(request):
    return web.FileResponse(f"static/{request.match_info['file']}")


async def process(request):
    global PROGRESS
    hash = request.match_info["hash"]

    if not (data := PROGRESS.get(hash)):
        return web.Response(text="Not Found", status=404, content_type="text/plain")
    data = (
        {"message": data["message"]}
        if data.get("message")
        else {"current": data["done"], "total": data["total"]}
    )
    return web.json_response(data)


async def remote_status(request):
    global DL_STATUS
    print(DL_STATUS)
    hash = request.match_info["hash"]

    if not (data := DL_STATUS.get(hash)):
        return web.Response(text="Not Found", status=404, content_type="text/plain")
    data = (
        {"message": data["message"]}
        if data.get("message")
        else {"current": data["done"], "total": data["total"]}
    )
    return web.json_response(data)


async def download(request: web.Request):
    hash = request.match_info["hash"]
    if id := is_hash_in_db(hash):
        id = id["msg_id"]
        return await media_streamer(request, id)


UPLOAD_TASK = []


async def upload_task_spawner():
    print("Task Spawner Started")
    global UPLOAD_TASK
    while True:
        if len(UPLOAD_TASK) > 0:
            task = UPLOAD_TASK.pop(0)
            loop.create_task(upload_file_to_channel(*task))
            print("Task created", task)
        await asyncio.sleep(1)


async def generate_clients():
    global multi_clients, work_loads

    print("Generating Clients")

    for i in range(len(BOT_TOKENS)):
        bot = Client(
            f"bot{i}",
            api_id=API_KEY,
            api_hash=API_HASH,
            bot_token=BOT_TOKENS[i],
        )
        await bot.start()
        multi_clients[i] = bot
        work_loads[i] = 0
        print(f"Client {i} generated")


async def start_server():
    global aiosession
    print("Starting Server")
    delete_cache()

    app.router.add_get("/", home)
    app.router.add_get("/static/{file}", static_files)
    app.router.add_get("/dl/{hash}", download)
    app.router.add_get("/file/{hash}", file_html)
    app.router.add_post("/upload", upload_file)
    app.router.add_get("/process/{hash}", process)
    app.router.add_post("/remote_upload", remote_upload)
    app.router.add_get("/remote_status/{hash}", remote_status)
    app.router.add_get("/bot_status", bot_status)

    aiosession = aiohttp.ClientSession()
    server = web.AppRunner(app)

    print("Starting Upload Task Spawner")
    loop.create_task(upload_task_spawner())
    print("Starting Client Generator")
    loop.create_task(generate_clients())

    await server.setup()
    print("Server Started")
    await web.TCPSite(server).start()
    await idle()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server())
