import json

import calendar
import logging
import time

from github import Github, RateLimitExceededException

stargazers_path = '../util/stargazers.json'

logger = logging.getLogger(__name__)


def get_repo_stargazers(repo_name: str, github_token: str, max_repos_per_stargazer: int = 5,
                        max_stargazers: int = 50, return_top_n_repos: int = 10) -> list:
    """
    Returns map of username to user's repositories.
    :param repo_name: repository where we search stargazers
    :param github_token: token for authentification
    :param number_of_repo: maximum number of starred repos
    :return: map
    """

    github = Github(github_token)
    repository = github.get_repo(repo_name)

    repo_to_count = {}
    curr_count = 0

    for stargazer in repository.get_stargazers():
        if curr_count > max_stargazers:
            break
        try:
            for i, starred_repo in enumerate(stargazer.get_starred()):
                if i >= max_repos_per_stargazer:
                    break
                repo_name = starred_repo.full_name
                repo_to_count[repo_name] = repo_to_count.get(repo_name, 0) + 1
                curr_count += 1
        except RateLimitExceededException as e:
            logger.warn(f"Rate limit exception: {e}")
            wait_for_request(github)

    top_n_repos = get_top_n_repos(repo_to_count, return_top_n_repos)
    with open(stargazers_path, 'w') as f:
        f.write(json.dumps(top_n_repos, ensure_ascii=False))
    return top_n_repos


def wait_for_request(github_account: Github):
    """
    Wait until GitHub API is usable again
    :param github_account: account
    """
    search_rate_limit = github_account.get_rate_limit().search
    reset_timestamp = calendar.timegm(search_rate_limit.reset.timetuple())

    time.sleep(max(0, reset_timestamp - calendar.timegm(time.gmtime())))


def get_top_n_repos(repo_to_count: dict, top_n_repos: int) -> list:
    """
    Returns top N repos from specified stargazers
    :param top_n_repos: top occurred repos from stargazers
    :param repo_to_count: repository to its occurrences counter
    """

    all_sorted_repos = list(dict(sorted(repo_to_count.items(), key=lambda x: x[1], reverse=True)).keys())

    if top_n_repos < 1:
        logger.warn(f'param: top_n_repos cant be < 0, setting to default = 10')
        top_n_repos = 10
    if len(all_sorted_repos) < top_n_repos:
        logger.warn(f'Repos count is less than top N repos param')
        return all_sorted_repos
    return all_sorted_repos[:top_n_repos]
