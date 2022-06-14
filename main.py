import os
import random

import requests
from dotenv import load_dotenv
from urllib.parse import urlparse


def download_image(name, img_url):
    filepath = f"{name}{get_extension(img_url)}"

    response = requests.get(img_url)
    response.raise_for_status()

    with open(filepath, "wb") as file:
        file.write(response.content)
    return filepath


def get_extension(img_url):
    parsed_url = urlparse(img_url)
    extension = os.path.splitext(parsed_url.path)[1]
    return extension


def get_comic_info(comic_num):
    comic_info_url = "https://xkcd.com/{comic}/info.0.json"

    response = requests.get(comic_info_url.format(comic=comic_num))
    response.raise_for_status()
    return response.json()["img"], response.json()["alt"], response.json()["title"]


def get_upload_url(token, group_id, version):
    url = "https://api.vk.com/method/photos.getWallUploadServer"
    params = {
        "access_token": token,
        "v": version,
        "group_id": group_id
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()["response"]["upload_url"]


def upload_to_server(token, group_id, version, filename):
    url = get_upload_url(token, group_id, version)
    with open(filename, "rb") as file:
        files = {
            "photo": file
        }

        response = requests.post(url, files=files)
        response.raise_for_status()

        server = response.json()["server"]
        hash = response.json()["hash"]
        photo = response.json()["photo"]
    return server, hash, photo


def save_photo_to_wall(token, group_id, version, filename):
    url = "https://api.vk.com/method/photos.saveWallPhoto"
    server, hash, photo = upload_to_server(token, group_id, version, filename)

    params = {
        "access_token": token,
        "photo": photo,
        "v": version,
        "group_id": group_id,
        "server": server,
        "hash": hash
    }

    response = requests.post(url, params=params)
    response.raise_for_status()
    return response.json()


def public_to_group(token, group_id, version, filename, comment):
    url = "https://api.vk.com/method/wall.post"
    saved_photo_info = save_photo_to_wall(token, group_id, version, filename)
    owner_id = saved_photo_info["response"][0]["owner_id"]
    media_id = saved_photo_info["response"][0]["id"]
    attachments = f"photo{owner_id}_{media_id}"

    params = {
        "access_token": token,
        "attachments": attachments,
        "v": version,
        "owner_id": -int(group_id),
        "message": comment,
        "from_group": "1"
    }

    response = requests.post(url, params=params)
    response.raise_for_status()
    return f"Комикс загружен в группу {group_id}."


def get_comics_num():
    last_comic_url = "https://xkcd.com/info.0.json"
    response = requests.get(last_comic_url)
    response.raise_for_status()
    return response.json()["num"]


def generate_random_comic():
    total_comics = get_comics_num()
    random_comic_num = random.randint(1, total_comics)
    img_url, comment, title = get_comic_info(random_comic_num)
    return img_url, comment, title


if __name__ == "__main__":
    load_dotenv()

    api_version = 5.131

    client_id = os.getenv("VK_CLIENT_ID")
    access_token = os.getenv("VK_ACCESS_TOKEN")
    group_id = os.getenv("VK_GROUP_ID")

    img_url, author_comment, title = generate_random_comic()
    comic_filepath = download_image(title, img_url)

    print(public_to_group(access_token, group_id, api_version, comic_filepath, author_comment))

    os.remove(comic_filepath) 
