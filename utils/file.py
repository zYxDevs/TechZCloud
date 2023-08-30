ALLOWED_EXTENSIONS = {
    "avi",
    "mp4",
    "zip",
    "xls",
    "mkv",
    "png",
    "xlsx",
    "mp3",
    "pdf",
    "jpeg",
    "docx",
    "jpg",
    "wma",
    "doc",
    "txt",
    "gif",
    "rtf",
    "csv",
    "rar",
    "mpg",
    "flv",
}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


from string import ascii_letters, digits
import os, random


def get_file_hash():
    while True:
        hash = "".join([random.choice(ascii_letters + digits) for _ in range(10)])
        for i in os.listdir("static/uploads"):
            if i.startswith(hash):
                continue
        return hash


def delete_cache():
    for file in os.listdir("static/uploads"):
        if file != "exists.txt":
            os.remove(f"static/uploads/{file}")
