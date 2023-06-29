import requests
import re
from urllib.parse import unquote


def get_featured_image(_pages):

    files = {}

    size = 50
    pages_split = [_pages[x:x + size] for x in range(0, len(_pages), size)]

    for pg in pages_split:

        pages = "|".join(pg)

        S = requests.Session()

        URL = "https://en.wikipedia.org/w/api.php"

        PARAMS = {
            "action": "query",
            "format": "json",
            "prop": "pageimages",
            "piprop": "original|name",
            "titles": pages,
        }

        R = S.get(url=URL, params=PARAMS)
        data = R.json()["query"]["pages"]

        for page in data:
            page_title = data[page]["title"]
            try:
                f_image_url = data[page]['original']['source']
                f_image_title = f"File:{data[page]['pageimage']}"
            except:
                f_image_url = ""
                f_image_title = ""

            files[page_title] = {"f_image_title": f_image_title, "f_image_url": f_image_url}

    return files


def get_images(_page):

    S = requests.Session()

    URL = "https://en.wikipedia.org/w/index.php"

    PARAMS = {
        "action": "raw",
        "title": _page,
    }

    R = S.get(url=URL, params=PARAMS)
    data = R.text

    if data[:9] == "#REDIRECT":
        _page = data[data.find("[[")+2:data.find("]]")]

        PARAMS = {
            "action": "raw",
            "title": _page,
        }

        R = S.get(url=URL, params=PARAMS)
        data = R.text

    file_types = [".svg", ".png", ".jpg", ".jpeg", ".gif"]
    files = []

    for f_type in file_types:
        re_string = "=.*?" + f_type + "|:.*?" + f_type
        files += re.findall(re_string, data, re.IGNORECASE)

    for i in range(len(files)):
        if "File" in files[i]:
            files[i] = files[i].split("File")[1]
        if "[[Image" in files[i]:
            files[i] = files[i].split("[[Image")[1]
        if "[[file" in files[i]:
            files[i] = files[i].split("[[file")[1]
        if "|image" in files[i]:
            files[i] = files[i].split("|image")[1]
        if "|" in files[i]:
            files[i] = files[i].split("|")[0]

    files = ["File:" + f[1:].strip() for f in files]
    files = [unquote(f) for f in files]

    for f in files[:]:
        if "/" in f:
            files.remove(f)
        elif not any(f_type in f.lower() for f_type in file_types):
            files.remove(f)

    return files


def get_image_info(_images):

    files = []

    # Remove "|" from file names
    images = []
    for img in _images:
        if "|" in img:
            temp_img = img.split("|")[0]
        else:
            temp_img = img
        images.append(temp_img)

    # Split filenames in group of 50 to send valid requests to the API
    size = 50
    images_split = [images[x:x + size] for x in range(0, len(images), size)]

    for img in images_split:

        images = "|".join(img)

        S = requests.Session()

        URL = "https://en.wikipedia.org/w/api.php"

        PARAMS = {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "iiprop": "url|thumbmime|size",
            "iiurlwidth": "500",
            "titles": images,
        }

        R = S.get(url=URL, params=PARAMS)
        data = R.json()
        if "query" in data:
            if "normalized" in data["query"]:
                normalized_list = data["query"]["normalized"]
            else:
                normalized_list = [{"from": "", "to": ""}]

            data = data["query"]["pages"]

        for d_img in data:
            try:
                title = data[d_img]["title"]
                if list(filter(lambda d: d['to'] == title, normalized_list)):
                    title = list(filter(lambda d: d['to'] == title, normalized_list))[0]["from"]

                info = data[d_img]["imageinfo"]

                url = info[0]["url"]
                page_url = info[0]["descriptionurl"]
                thumbnail_url = info[0]["thumburl"]
                width = info[0]["width"]
                height = info[0]["height"]

                file_type = title.split('.')[-1].lower()
                if file_type == "jpeg":
                    file_type = "jpg"

                if width >= 1920 or height >= 1920 or file_type == "svg":
                    resolution = "High-res"
                elif width >= 720 or height >= 720:
                    resolution = "Mid-res"
                else:
                    resolution = "Low-res"
            except:
                url = page_url = thumbnail_url = file_type = width = height = resolution = ""

            file_to_add = {
                "title": title,
                "url": url,
                "page url": page_url,
                "thumbnail url": thumbnail_url,
                "file_type": file_type,
                "width": width,
                "height": height,
                "resolution": resolution
            }

            files.append(file_to_add)

    return files


def get_assessment(_page):

    S = requests.Session()

    URL = "https://en.wikipedia.org/w/api.php"

    PARAMS = {
        "action": "query",
        "format": "json",
        "prop": "pageassessments|info",
        "inprop": "url",
        "titles": _page,
    }

    output_page = {
        "article": "",
        "url": "",
        "quality": "",
        "importance": "",
    }

    R = S.get(url=URL, params=PARAMS)
    data = R.json()
    if "query" in data:
        data = data["query"]["pages"]
        data = data[list(data.keys())[0]]

        title = data["title"]
        url = data["fullurl"]

        try:
            assessment_keys = list(data["pageassessments"].keys())

            if "Wikipedia 1.0" in assessment_keys:
                quality = data["pageassessments"]["Wikipedia 1.0"]["class"]
                importance = data["pageassessments"]["Wikipedia 1.0"]["importance"]
            elif len(assessment_keys) > 0:
                quality = data["pageassessments"][assessment_keys[0]]["class"]
                importance = data["pageassessments"][assessment_keys[0]]["importance"]
        except:
            quality = importance = ""

        if importance not in ["Top-Class", "High-Class", "Mid-Class", "Low-Class"]:
            importance = "Unassessed"

        output_page = {
            "article": title,
            "url": url,
            "quality": quality,
            "importance": importance,
        }

    return output_page


def get_categories(_pages):
    output_pages = []

    # Split pages in group of 50 to send valid requests to the API
    size = 50
    pages_split = [_pages[x:x + size] for x in range(0, len(_pages), size)]

    for pg in pages_split:

        pages = "|".join(pg)

        S = requests.Session()

        URL = "https://en.wikipedia.org/w/api.php"

        PARAMS = {
            "action": "query",
            "format": "json",
            "prop": "categories",
            "clshow": "!hidden",
            "cllimit": "500",
            "titles": pages,
        }

        R = S.get(url=URL, params=PARAMS)
        data = R.json()
        if "query" in data:
            data = data["query"]["pages"]

        for d_pg in data:
            try:
                title = data[d_pg]["title"]
                categories = []
                for cat in data[d_pg]["categories"]:
                    categories.append(cat["title"].replace("Category:", ""))

            except:
                categories = ["no category"]

            page_to_add = {
                "article": title,
                "categories": ",".join(categories)
            }

            output_pages.append(page_to_add)

    return output_pages
