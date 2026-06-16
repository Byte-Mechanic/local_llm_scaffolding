# Copyright (c) 2026 Byte-Mechanic
# SPDX-License-Identifier: MIT

"""This file contains utility functions for tools to call.

This file has multiple utility functions that serve a basic purpose and can be
used by each plugin instead of tools having to rely on other tools existing in
order to function.
"""

import logging
from fake_useragent import UserAgent
import markdownify
from bs4 import BeautifulSoup
import re
import time
import requests

logger = logging.getLogger(__name__)
logger.info(f'Logger "{logger.name}" Initiated.')

def fetch_link_md(url: str) -> str:
    attempt: int = 0
    wait_time: int = 1
    retry_codes = [429, 502, 503, 504] 
    while wait_time < 8:
        time.sleep(wait_time)
        attempt += 1
        logger.info(f'{f"[Attempt {attempt}] " if attempt > 1 else ""}'
                    f'Fetching Markdown for: {url}...')
        web_headers = {
                'Accept': ('text/html,application/xhtml+xml,application/xml;q=0.9,'
                           '*/*;q=0.8'),
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'en-US,en;q=0.9',
                'Dnt': '1',
                'Priority': 'u=0, i',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Sec-Gpc': '1',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': UserAgent(platforms=['desktop']).firefox,
                'Connection': 'keep-alive',
                }
        try:
            raw_page = requests.get(url, headers=web_headers)
            raw_page.raise_for_status()
        except requests.HTTPError as err:
            logger.error(f'HTTPError occured. Status Code: '
                         f'{raw_page.status_code} \n{err}')
            if raw_page.status_code in retry_codes:
                wait_time = wait_time * 2
                continue
            else:
                return (f'Webpage could not be fetched. '
                        f'returned unrecoverable code {raw_page.status_code}')
        soup = BeautifulSoup(raw_page.content, 'html.parser')
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside',
                         'iframe']):
            logger.info(f'[{str(tag)}] Tag Decomposed.')
            tag.decompose()
        main_content = (soup.find('main') or soup.find('article') or 
                        soup.find('body'))
        markdown_page_temp = markdownify.markdownify(str(main_content) 
                                                     if main_content 
                                                     else str(soup))
        markdown_page = re.sub('(\r\n|\n|\r){3,}', '\n', markdown_page_temp)
        logger.info(f'Returning Markdown:\n{markdown_page}')
        return str(markdown_page)
    logger.error(f'Webpage could not be reached after [{attempt}] retrys.')
    return f'Webpage could not be reached after [{attempt}] retrys.'

