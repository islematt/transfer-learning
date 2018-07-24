# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests
import re
import urllib
import json
import os
import random
import json

from utils.file_utils import ensure_dir_exists

gallery_name_format = 'galleries{}.json'
cache_dir_name = 'cache'
gallery_file_path_format = cache_dir_name + '/{}'
image_header_prefix = ['a', 'aa', 'ba', 'i']
url_base = 'hitomi.la/galleries'
image_hosts = ['https://{}.{}'.format(prefix, url_base) for prefix in image_header_prefix]

class Image:
    def __init__(self, urls, gallery):
        self.urls = urls
        self.gallery = gallery


def sample_random(gallery_sample_count, image_sample_count, include_cover=True):
    gallery_count = _get_gallery_count()
    _cache_galleries(gallery_count)
    galleries = _sample_random_galleries(gallery_count, gallery_sample_count)
    images = {}
    print('len(galleries): {}'.format(len(galleries)))
    for gallery in galleries:
        image_names = [img_name for img_name in _sample_image_names(gallery['id'], image_sample_count, include_cover)]
        img_urls = ['{}/{}/{}'.format(image_host, gallery['id'], img_name) for image_host in image_hosts for img_name in image_names]

        first_valid_url_idx = _find_first_valid_url_idx(img_urls)
        if first_valid_url_idx < 0:
            continue
        img_urls = img_urls[first_valid_url_idx:first_valid_url_idx+image_sample_count+(1 if include_cover else 0)]
        images[str(gallery['id'])] = Image(img_urls, gallery)

    return images


def _find_first_valid_url_idx(img_urls):
    for i in range(len(img_urls)):
        if requests.head(img_urls[i]).status_code == 200:
            return i
    return -1


def _get_gallery_count():
    searchlib_contents = requests.get('https://ltn.hitomi.la/searchlib.js').text
    gallery_count = re.compile('number_of_gallery_jsons = (\d*)').search(searchlib_contents).group(1)
    return int(gallery_count)


def _cache_galleries(gallery_count):
    ensure_dir_exists(cache_dir_name)
    for i in range(0, gallery_count):
        gallery_name = gallery_name_format.format(i)
        gallery_url = 'https://ltn.hitomi.la/' + gallery_name
        out_file_name = gallery_file_path_format.format(gallery_name)
        if os.path.isfile(out_file_name):
            print('{} exists. Skipping download.'.format(out_file_name))
            continue

        response = requests.get(gallery_url)

        with open(out_file_name, 'w') as out_file:
            print('Downloading {} into {}...'.format(gallery_name, out_file_name))
            out_file.write(response.content.decode('utf-8'))


def _sample_random_galleries(gallery_count, sample_count):
    gallery_idx = random.randint(0, gallery_count - 1)
    gallery_name = gallery_name_format.format(gallery_idx)
    gallery_file_path = gallery_file_path_format.format(gallery_name)
    with open(gallery_file_path, 'r') as gallery_file:
        gallery = json.load(gallery_file)
        indices = random.sample(range(len(gallery)), sample_count)

        galleries = []
        for idx in indices:
            galleries.append(gallery[idx])

        return galleries


def _sample_image_names(gallery_id, sample_count, include_cover):
    res = requests.get('https://hitomi.la/reader/{}.html'.format(gallery_id))
    dom = BeautifulSoup(res.text, 'html5lib')
    img_divs = dom.find_all('div', {'class': 'img-url'})

    get_img_name = lambda img_div: re.compile('.*hitomi.la\/galleries\/\d*\/(.*)').match(img_div.text).group(1)

    indices = random.sample(range(1 if include_cover else 0, len(img_divs)), sample_count)
    img_names = [get_img_name(img_divs[0])] if include_cover else []
    for idx in indices:
        img_div = img_divs[idx]
        img_name = get_img_name(img_div)
        img_names.append(img_name)

    return img_names


if __name__ == '__main__':
    images = sample_random(1, 0)
    for _, image in images.items():
        # image = images[k]
        print('{}'.format(image.urls))
        print('{}'.format(image.gallery))
        print('\n')
