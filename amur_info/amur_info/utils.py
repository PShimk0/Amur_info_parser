
#Функция для формирования строки со временем формата day/month/year
def date_string_transform(time):
    date_str = f"{time.day}/{time.month}/{time.year}"
    return date_str

#Функция формирования ссылки на следующую страницу для пагинации
def form_url(page, url):
    if "page" in url:
        url = url.replace(f"/page/{page - 1}", f"/page/{page}")
    else:
        url = (
            url.split("?article-category")[0]
            + f"page/{page}/?article-category"
            + url.split("?article-category")[1]
        )
    return url
