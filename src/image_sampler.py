from bs4 import BeautifulSoup
import requests
import re
import os
import random
import json
import logging

from rx.subjects import Subject

from src.utils.file_utils import ensure_dir_exists, absolute_path_of

gallery_name_format = 'galleries{}.json'
cache_dir_name = absolute_path_of('.cache')
gallery_file_path_format = cache_dir_name + '/{}'
image_header_prefix = ['a', 'aa', 'ba', 'i']
url_base = 'hitomi.la/galleries'
image_hosts = ['https://{}.{}'.format(prefix, url_base) for prefix in image_header_prefix]

logger = logging.getLogger('app')

# TODO: Possible data corruption. Consider wrapping into class
cache_galleries_progress = Subject()
sample_books_progress = Subject()
sample_images_progress = Subject()


class Image:
    def __init__(self, urls, gallery):
        self.urls = urls
        self.gallery = gallery


def sample_random(gallery_sample_count, image_sample_count, include_cover=True):
    gallery_count = _get_gallery_count()

    logger.info('Preparing gallery caches.')
    _cache_galleries(gallery_count)

    logger.info('Sampling random books.')
    books = _sample_random_books(gallery_count, gallery_sample_count)
    images = _sample_images_from_books(books, image_sample_count, include_cover)

    return images


def _find_first_valid_url_idx(img_urls):
    for i in range(len(img_urls)):
        logger.debug('Checking {}'.format(img_urls[i]))
        if requests.head(img_urls[i]).status_code == 200:
            return i
    return -1


def _get_gallery_count():
    searchlib_contents = requests.get('https://ltn.hitomi.la/searchlib.js').text
    gallery_count = re.compile('number_of_gallery_jsons = (\d*)').search(searchlib_contents).group(1)
    return int(gallery_count)


def _cache_galleries(gallery_count):
    # TODO: Set cache expiration limit
    ensure_dir_exists(cache_dir_name)
    for i in range(0, gallery_count):
        cache_galleries_progress.on_next((i + 1, gallery_count))
        gallery_name = gallery_name_format.format(i)
        gallery_url = 'https://ltn.hitomi.la/' + gallery_name
        out_file_name = gallery_file_path_format.format(gallery_name)
        if os.path.isfile(out_file_name):
            continue

        response = requests.get(gallery_url)

        with open(out_file_name, 'w') as out_file:
            logger.info('Caching {} into {}...'.format(gallery_name, out_file_name))
            out_file.write(response.content.decode('utf-8'))


def _sample_random_books(gallery_count, sample_count):
    gallery_idx = random.randint(0, gallery_count - 1)
    gallery_name = gallery_name_format.format(gallery_idx)
    gallery_file_path = gallery_file_path_format.format(gallery_name)
    with open(gallery_file_path, 'r') as gallery_file:
        sample_books_progress.on_next((0, 1))
        gallery = json.load(gallery_file)
        sample_books_progress.on_next((1, 1))
        indices = random.sample(range(len(gallery)), sample_count)

        books = []
        for idx in indices:
            books.append(gallery[idx])

        return books


def _sample_images_from_books(books, image_sample_count, include_cover):
    images = {}
    books_cnt = len(books)
    for idx in range(books_cnt):
        sample_images_progress.on_next((idx + 1, books_cnt))

        book = books[idx]
        logger.info('Sampling random images for book {}.'.format(book['id']))
        image_names = [img_name for img_name in _sample_image_names(book['id'], image_sample_count, include_cover)]
        img_urls = ['{}/{}/{}'.format(image_host, book['id'], img_name) for image_host in image_hosts for img_name in image_names]

        logger.info('Examining valid image urls for book {}.'.format(book['id']))
        first_valid_url_idx = _find_first_valid_url_idx(img_urls)
        if first_valid_url_idx < 0:
            logger.warning('Couldn\'t find valid url prefix for book {}'.format(book['id']))
            continue
        img_urls = img_urls[first_valid_url_idx:first_valid_url_idx+image_sample_count+(1 if include_cover else 0)]
        images[str(book['id'])] = Image(img_urls, book)

    return images


def _sample_image_names(gallery_id, sample_count, include_cover):
    res = requests.get('https://hitomi.la/reader/{}.html'.format(gallery_id))
    dom = BeautifulSoup(res.text, 'html5lib')
    img_divs = dom.find_all('div', {'class': 'img-url'})

    get_img_name = lambda img_div: re.compile('.*hitomi.la/galleries/\d*/(.*)').match(img_div.text).group(1)

    indices = random.sample(range(1 if include_cover else 0, len(img_divs)), sample_count)
    img_names = [get_img_name(img_divs[0])] if include_cover else []
    for idx in indices:
        img_div = img_divs[idx]
        img_name = get_img_name(img_div)
        img_names.append(img_name)

    logger.debug('Sampled images: {}'.format(img_names))
    return img_names
