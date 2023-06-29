import requests
import pandas as pd
from tqdm import tqdm
import numpy as np
from mediawiki_action_api import get_images, get_image_info, get_categories, get_assessment
from datetime import datetime
import os
import re
import json


def full_extraction(project_name, project_type):
    if project_type == "wp":
        extract_wikiproject_articles(project_name)

    if project_type == "list":
        extract_list_articles(project_name)

    extract_categories(project_name, project_type)
    extract_images(project_name, project_type)
    extract_images_data(project_name, project_type)
    build_json_output(project_name, project_type)


def build_json_output(project_name, project_type):
    # Load articles to Dataframe
    articles_path = f'output/{project_type}_{project_name}/{project_type}_{project_name}.csv'
    df_articles = pd.read_csv(articles_path)

    images_path = f'output/{project_type}_{project_name}/{project_type}_{project_name}_images.csv'
    df_images = pd.read_csv(images_path)

    df_articles["images"] = ""

    # Convert categories list to array
    for index, row in df_articles.iterrows():

        categories = str(row["categories"]).split(",")
        df_articles.at[index, 'categories'] = categories

        images = json.loads(df_images.loc[df_images['article'] == row["article"]].to_json(orient='records'))
        df_articles.at[index, 'images'] = images

    # Convert Dataframe to JSON
    json_articles = json.loads(df_articles.to_json(orient='records'))

    # Create info json
    date = datetime.today().strftime('%Y-%m-%d')
    project = "List"
    if project_type == "wp":
        project = "Wikiproject"
    project = f"{project} {project_name}"

    info = {"name": project, "date": date}

    # Merge json
    json_output = {
        "info": info,
        "data": json_articles
    }

    with open(f'output/{project_type}_{project_name}/{project_type}_{project_name}.json', 'w') as outfile:
        json.dump(json_output, outfile)
        outfile.close()


def extract_wikiproject_articles(wikiproject_id):
    print("\nARTICLES EXTRACTION")

    # Skip function if the file already exists
    if os.path.exists(f"output/wp_{wikiproject_id}/wp_{wikiproject_id}.csv"):
        pbar = tqdm(total=1)
        pbar.update(1)
        pbar.close()
        return

    quality_grades = [
        "A",
        "B",
        "C",
        "FA",
        "FL",
        "List",
        "GA",
        "Start",
        "Stub",
        "Unassessed"
    ]

    url = f'https://api.wp1.openzim.org/v1/projects/{wikiproject_id}/articles'

    first_params = {
        "numRows": 500,
        "page": 1
    }

    session = requests.Session()

    page_number = 0
    df_tot = pd.DataFrame({'A': []})

    r = session.get(url=url, params=first_params)
    data = r.json()
    tot_pages = data["pagination"]["total_pages"]

    pbar = tqdm(total=tot_pages)

    while True:
        page_number += 1

        params = {
            "numRows": 500,
            "page": page_number
        }

        r = session.get(url=url, params=params)
        data = r.json()

        tot_pages = data["pagination"]["total_pages"]

        pbar.update(1)

        df = pd.DataFrame(data["articles"])
        if df_tot.empty:
            df_tot = df
        else:
            df_tot = pd.concat([df_tot, df])

        if page_number >= tot_pages:
            break

    pbar.close()

    # Remove "-Class" from importance and quality
    df_tot['quality'] = df_tot['quality'].str.replace('-Class', '')
    df_tot['importance'] = df_tot['importance'].str.replace('-Class', '')

    # Filter not necessary pages (categories, redirects, etc.)
    df_tot = df_tot[df_tot["quality"].isin(quality_grades)].reset_index(drop=True)

    # Drop not necessary columns
    df_tot.drop(['article_history_link', 'article_talk', 'article_talk_link', 'quality_updated', 'importance_updated'], axis=1, inplace=True)

    # Save the dataframe as CSV
    df_tot.to_csv(f'output/wp_{wikiproject_id}/wp_{wikiproject_id}.csv', index=False, encoding='utf-8-sig')


def extract_list_articles(list_name):
    print("\nASSESSMENT EXTRACTION")

    articles_path = f'output/list_{list_name}/list_{list_name}.csv'

    # Load list of articles
    article_list = pd.read_csv(f'input/{list_name}.csv').iloc[:, 0].tolist()

    # Check if file already exists
    if os.path.exists(articles_path):
        df = pd.read_csv(articles_path)
    else:
        df = pd.DataFrame({
            "article": article_list,
            "article_link": np.nan,
            "importance": np.nan,
            "quality": np.nan,
        })
        df.to_csv(articles_path, index=False, encoding='utf-8-sig')

    pbar = tqdm(total=len(article_list))

    for index, row in df.iterrows():
        if pd.isna(row["article_link"]):
            article_info = get_assessment(row["article"])

            df.at[index, 'article_link'] = article_info["url"]
            df.at[index, 'quality'] = str(article_info["quality"]).replace('-Class', '')
            df.at[index, 'importance'] = str(article_info["importance"]).replace('-Class', '')

            if index % 100 == 0:
                df.to_csv(articles_path, index=False, encoding='utf-8-sig')

        pbar.update(1)

    df.to_csv(articles_path, index=False, encoding='utf-8-sig')
    pbar.close()


def extract_categories(project_name, project_type):
    articles_path = f'output/{project_type}_{project_name}/{project_type}_{project_name}.csv'

    # Load list of articles
    df = pd.read_csv(articles_path)

    if "categories" not in df:
        df["categories"] = np.nan

    print("\nCATEGORIES EXTRACTION")
    sect = []
    pbar = tqdm(total=len(df))

    for index, row in df.iterrows():
        if pd.isna(row["categories"]):
            sect.append(row["article"])

        if len(sect) >= 50 or index + 1 == len(df):
            # Extract categories
            cat_info = get_categories(sect)
            df_sect = pd.DataFrame.from_dict(cat_info)

            # Split dataframe
            df_categories = df[["article", "categories"]]
            df.drop('categories', axis=1, inplace=True)

            # Join old info with new info
            df_categories = pd.concat([df_categories, df_sect]).dropna().reset_index(drop=True)

            # Merge the split dataset
            df = pd.merge(df, df_categories.drop_duplicates(keep='first'), how="left", on=['article'],
                          validate="many_to_one")

            # Save dataframe to csv file
            df.to_csv(articles_path, index=False, encoding='utf-8-sig')

            # Clear selection
            sect = []

        pbar.update(1)

    pbar.close()


def extract_images(project_name, project_type):

    articles_path = f'output/{project_type}_{project_name}/{project_type}_{project_name}.csv'
    images_path = f'output/{project_type}_{project_name}/{project_type}_{project_name}_images.csv'

    # Load list of pages
    df = pd.read_csv(articles_path)
    if "n_images" not in df:
        df["n_images"] = np.nan

    # Create, if not existing, and load images dataset
    if not os.path.exists(images_path):
        df_images = pd.DataFrame(columns=['article', 'title', 'url', 'page url', 'thumbnail url', 'file_type', 'width', 'height', "resolution"])
        df_images.to_csv(images_path, index=False, encoding='utf-8-sig')
    else:
        df_images = pd.read_csv(images_path)

    print("\nIMAGES EXTRACTION")
    pbar = tqdm(total=len(df))

    for index, row in df.iterrows():
        if pd.isna(row["n_images"]):
            images = get_images(row["article"])

            n_images = len(images)
            df.at[index, 'n_images'] = n_images

            temp_images = pd.DataFrame({
                "article": row["article"],
                "title": images
            })

            df_images = pd.concat([df_images, temp_images]).reset_index(drop=True)

            if index % 100 == 0:
                df.to_csv(articles_path, index=False, encoding='utf-8-sig')
                df_images.to_csv(images_path, index=False, encoding='utf-8-sig')

        pbar.update(1)

    df.to_csv(articles_path, index=False, encoding='utf-8-sig')
    df_images.to_csv(images_path, index=False, encoding='utf-8-sig')
    pbar.close()


def extract_images_data(project_name, project_type):
    images_path = f'output/{project_type}_{project_name}/{project_type}_{project_name}_images.csv'
    df_images = pd.read_csv(images_path)

    print("\nIMAGES' DATA EXTRACTION")
    sect = []
    pbar = tqdm(total=len(df_images))

    for index, row in df_images.iterrows():
        if pd.isna(row["url"]):
            sect.append(row["title"])

        if len(sect) >= 50 or index + 1 == len(df_images):
            # Extract images info
            images_info = get_image_info(sect)
            df_sect = pd.DataFrame.from_dict(images_info)

            # Split images dataframe
            df_images_data = df_images[["title", "url", "page url", "thumbnail url", "file_type", "width", "height", "resolution"]]
            df_images = df_images[["article", "title"]]

            # Join old images info with new images info
            df_images_data = pd.concat([df_images_data, df_sect]).dropna().reset_index(drop=True)

            # Merge the split dataset
            df_images = pd.merge(df_images, df_images_data.drop_duplicates(subset="title", keep='first'), how="left", on=['title'],
                                 validate="many_to_one")

            # Save dataframe to csv file
            df_images.to_csv(images_path, index=False, encoding='utf-8-sig')

            # Clear selection
            sect = []

        pbar.update(1)

    # Remove errors and save dataframe to csv file
    df_images.drop(df_images.loc[df_images['url'] == ""].index, inplace=True)
    df_images.to_csv(images_path, index=False, encoding='utf-8-sig')

    pbar.close()


def extract_wikiprojects_list():
    url = "https://api.wp1.openzim.org/v1/projects/"

    session = requests.Session()

    r = session.get(url=url)
    data = r.json()

    projects = []

    for wp in data:
        projects.append(wp["name"])

    return projects


def download_images():
    print("\nImage download started...\n")
    headers = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}
    df_images = pd.read_csv(f'output/test/Wikiproject_Chemistry_images.csv')

    pbar = tqdm(total=df_images.shape[0])

    for index, row in df_images.iterrows():
        try:
            filename = re.sub(r'[?"><:/*|]', '', row['filename'])
            if isinstance(row['thumbnail url'], str) and not os.path.exists(f"output/test/images/{filename}"):
                url = row['thumbnail url']
                r = requests.get(url, allow_redirects=True, headers=headers)
                if not r.ok:
                    print(index, row["thumbnail url"], r.status_code, r.ok)

                else:
                    file = open(f'output/test/images/{filename}', 'wb')
                    file.write(r.content)
                    file.close()

        except Exception as e:
            print(e)

        pbar.update(1)


def check_connection():
    try:
        res = requests.get('https://www.google.it/')
        if res.status_code:
            return True
        else:
            return False

    except:
        return False
