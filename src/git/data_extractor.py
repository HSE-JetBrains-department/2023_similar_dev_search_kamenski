import logging
import os.path
from difflib import unified_diff

from dulwich.diff_tree import TreeChange
from dulwich.porcelain import clone
from dulwich.repo import Repo
from dulwich.walk import WalkEntry

from pathlib2 import Path

from tqdm import tqdm

logger = logging.getLogger(__name__)


def get_repo_info(url: str, repo_name: str, clone_dir_path: str) -> dict:
    """
    Returns repository description.
    Result structure: {
        'url': <repository url>,
        'commits': {
            <commit sha>: {
                'author': <author name and email>,
                'changes': [{
                        'file': <path to changed file>,
                        'blob_id': <blob id>,
                        'added': <count of added rows>,
                        'deleted': <count of deleted rows>
                    },
                    ...
                ]
            },
            ...
        }
    }
    :param url: repository url
    :clone_dir_path: path to directory with cloned repositories
    :repo_name: name of a cloning repository
    :return: dict with repository description
    """

    if not os.path.exists(clone_dir_path):
        logger.warning("Creating directory 'util/cloned_repos'...")
        os.mkdir(clone_dir_path)

    clone_path = f"{clone_dir_path}/{repo_name}"

    if os.path.exists(clone_path):
        logger.warning(f'Reading repository {repo_name}')
        repo = Repo(clone_path)
    else:
        logger.warning(f'Cloning repository {repo_name}...')
        repo = clone(url, clone_path)

    res = {
        "url": url,
        "commits": {}
    }

    logger.info(f'Investigating {repo_name}...')
    for entry in tqdm(repo.get_walker()):
        commit = entry.commit
        commit_sha = commit.sha().hexdigest()
        if len(repo.get_parents(commit_sha, commit)) > 1:
            continue
        if commit_sha not in res["commits"].keys():
            res["commits"].update({
                commit_sha: {
                    "author": commit.author.decode(),
                    "changes": []
                }
            })
        changes = get_changes(entry, repo)
        res["commits"][commit_sha]["changes"] += changes

    return res


def get_changes(entry: WalkEntry, repo: Repo) -> list:
    """
    Returns changes list.
    :param entry: entry object
    :param repo: repository object
    :return: list of changes
    """

    res = []
    for changes in entry.changes():
        if type(changes) is not list:
            changes = [changes]
        for change in changes:
            change_dict = get_change_info(change, repo)
            res.append(change_dict)
    return res


def get_change_info(change: TreeChange, repo: Repo) -> dict:
    """
    Returns change info.
    Result structure: {
        'file': <path to changed file>,
        'blob_id': <blob id>,
        'added': <count of added rows>,
        deleted': <count of deleted rows>
    }
    :param change: change object
    :param repo: repository object
    :return: change as dict
    """

    blob_path = str(Path(f"{repo.path}/{(change.new.path or change.old.path).decode()}").absolute())
    res = {
        'file': (change.new.path or change.old.path).decode(),
        'blob_id': (change.new.sha or change.old.sha).decode(),
        "blob_path": blob_path,
        'added': 0,
        'deleted': 0
    }

    try:
        old_sha = change.old.sha
        new_sha = change.new.sha

        if old_sha is None:
            res["added"] = len(repo.get_object(new_sha).data.decode().splitlines())
        elif new_sha is None:
            res["deleted"] = len(repo.get_object(old_sha).data.decode().splitlines())
        else:
            differences = unified_diff(repo.get_object(old_sha).data.decode().splitlines(),
                                       repo.get_object(new_sha).data.decode().splitlines())
            for diff in differences:
                if diff.startswith("+") and not diff.startswith("++"):
                    res["added"] += 1
                if diff.startswith("-") and not diff.startswith("--"):
                    res["deleted"] += 1
    except UnicodeDecodeError:
        return {}
    except KeyError:
        return {}
    return res
