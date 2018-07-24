import os
from urllib.parse import urlparse
import requests

from file_utils import ensure_dir_exists
from image_sampler import sample_random
from image_labeler import classify_images


def download(url, out_file_dir, out_file_name):
    out_file_dir_path = os.path.join('out', out_file_dir)
    ensure_dir_exists(out_file_dir_path)

    response = requests.get(url, stream=True)
    if not response.ok:
        # TODO: handle
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


if __name__ == '__main__':
    images = sample_random(1, 0)
    out_file_paths = []
    for _, image in images.items():
        for url in image.urls:
            file_name = _get_file_name_from_url(url)
            out_file_path = download(url, str(image.gallery['id']), file_name)
            out_file_paths.append(out_file_path)

    print(out_file_paths)
    results = classify_images(out_file_paths)
    for result in results:
        print(result)
    pass
