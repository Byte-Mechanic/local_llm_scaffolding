# Copyright (c) 2026 Byte-Mechanic
# SPDX-License-Identifier: MIT

"""This tool searches and returns web results

This tool gives the model the ability to seach the web with a given 'query' and
get back the top '3' links' converted to markdown.
"""

from ..utils import fetch_link_md
import logging
import requests
import time
import json

logger = logging.getLogger(__name__)
logger.info(f'Logger "{logger.name}" Initiated.')

search_result_limit = 3

def search(query) -> list[dict]:
    search_keep_keys = ['content', 'title', 'url', 'publishedDate', 'pubdate']
    try:
        raw_search = requests.post('http://localhost:8888/search',
                                       data={'q': query, 'format': 'json'})
        raw_search.raise_for_status()
    except requests.HTTPError as e:
        error_text = (f'SearXNG instance could not be reached. '
                      f'Status code {raw_search.status_code}')
        logger.error(error_text)
        return error_text
    logger.info(f'raw_search_results:\n{json.dumps(raw_search.json(), indent=4)}')
    search_results = raw_search.json()['results']
    filtered_search_results = [{k:v 
                                for k,v in result.items() 
                                if k in search_keep_keys and v not in (None, '', [])} 
                               for result in search_results]
    logger.info(f'Returning filtered_search_results...\n'
                f'{json.dumps(filtered_search_results, indent=4)}')
    return filtered_search_results[:search_result_limit]

def run(llama_interface: LlamaInterface, query: str, objective: str) -> list[dict]:
    """
    Enables the LM to search the web. Returns a list of dicts that
    include info on each link.

    ARGS
    --------
        query:          Search query output from the LLM
        objective:      Search objective passed from the LLM. What exactly is
            the LLM looking for. This defines whether the criteria
            is broad or targeted.
    
    RETURNS
    --------
        list[dict]: List of synthesized sources
    """
    logger.info("Executing web_search tool")
    results = search(query)
    search_results = []
    for result in results:
        time.sleep(1)
        logger.info(f'Fetching link:\n{result["url"]}...')
        source_md = fetch_link_md(result['url'])
        search_results.append({result['url'] : source_md})
    return search_results
