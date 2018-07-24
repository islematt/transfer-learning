import os
from urllib.parse import urlparse
import requests
import logging

from utils.file_utils import ensure_dir_exists
from image_sampler import sample_random
from image_labeler import classify_images

logger = logging.getLogger('app')


def download(url, out_file_dir, out_file_name):
    out_file_dir_path = os.path.join('out', out_file_dir)
    ensure_dir_exists(out_file_dir_path)

    response = requests.get(url, stream=True)
    if not response.ok:
        logger.error("Resource {} couldn't be downloaded.".format(url))
        return None

    out_file_path = os.path.join(out_file_dir_path, out_file_name)
    with open(out_file_path, 'wb') as out_file:
        for block in response.iter_content(1024):
            if not block:
                break

            out_file.write(block)

    return out_file_path


def _get_file_name_from_url(url):
    parsed_url = urlparse(url)
    return os.path.basename(parsed_url.path)


def match(gallery_sample_count, image_sample_count, include_cover=True):
    logger.info("Collecting random images...")
    images = sample_random(gallery_sample_count, image_sample_count, include_cover)
    out_file_paths = []
    for _, image in images.items():
        logger.info("Downloading images for gallery {}...".format(image.gallery['id']))
        for url in image.urls:
            file_name = _get_file_name_from_url(url)
            logger.info("Downloading image {}...".format(url))
            out_file_path = download(url, str(image.gallery['id']), file_name)
            out_file_paths.append(out_file_path)

    logger.debug("Downloaded images: \n{}".format(out_file_paths))
    return classify_images(out_file_paths)


if __name__ == '__main__':
    match()
