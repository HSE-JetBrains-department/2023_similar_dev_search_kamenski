import json
import logging
import os.path
import time

from git.data_extractor import get_repo_info

from stargazers.stargazers import get_repo_stargazers, stargazers_path


start_repo_ = 'https://github.com/pytorch/pytorch'
clone_path_ = '../util/cloned_repos'
result_file_ = '../result/developers_data.json'

github_token_path = '../util/github-token.txt'

logger = logging.getLogger(__name__)


def investigate_repository(start_repo_url: str, clone_path: str, result_file: str) -> None:
    """
    Save info about repositories to json file.
    :param result_file: path to output data (json file)
    :param clone_path: path to directory where repo is cloned
    :param start_repo_url: url of start repo (i.e. pytorch)
    """

    all_repos_info = {}

    logger.info('Dealing with Pytorch repository...')
    repo_name = 'pytorch'
    repo_info = get_repo_info(start_repo_url, repo_name, clone_path)
    all_repos_info[repo_name] = repo_info

    logger.info('Start looking for stargazers...')
    with open(github_token_path, 'r') as token_file:
        github_token = token_file.read()
    repos = get_repo_stargazers('pytorch/pytorch', github_token, return_top_n_repos=2)
    print(repos)

    if os.path.exists(stargazers_path):
        logger.info('Start investigating all Pytorch stargazers repositories...')
        start_time = time.time()
        for full_repo_name in repos:
            repo_url = f'https://github.com/{full_repo_name}'
            repo_name = full_repo_name.split('/')[-1]
            if repo_name not in all_repos_info:
                repo_info = get_repo_info(repo_url, repo_name, clone_path)
                all_repos_info[repo_name] = repo_info
        logger.info(f'Stargazers investigating finished.\n--- {time.time() - start_time} seconds ---')
    else:
        logger.warning('No stargazers found. Results might be incorrect')

    with open(result_file, "w") as f:
        f.write(json.dumps(all_repos_info, indent=6, ensure_ascii=False))


if __name__ == "__main__":
    investigate_repository(start_repo_, clone_path_, result_file_)
