import requests as rq
import copy
import treelib as tr
import concurrent.futures as th
import logging as log
import threading as thr
import enum


class InputCodes(enum.Enum):
    # input codes to signal the scanning function what to do
    SKIP = enum.auto()
    PAUSE = enum.auto()
    SHUTDOWN = enum.auto()
    CONTINUE = enum.auto()
    SELECTOR = enum.auto()


def test_connection(website: str, dir_string: str):
    # check if dir_string is a valid link for website
    # website form = "http://www.urltest.domain"
    # dir_string form = "directory_name"

    website = r"{}".format(website)
    dir_string = r"{}".format(dir_string)
    full_url = f"{website}/{dir_string}"

    # testing full url
    response = rq.head(full_url, allow_redirects=True)

    # 1xx - informational
    # 2xx - success
    # 3xx - redirection
    # 4xx - client error and so on with errors
    if response.status_code >= 400:
        return False, None

    # check redirections' status if they exist and save them -- error for invalid redirections
    # see https://requests.readthedocs.io/en/latest/user/quickstart/#redirection-and-history
    if len(response.history) == 1:
        return True, None

    # explore redirections
    # |url 1| --> |url 2| --> |url 3| --> status code >= 400 STOP
    temp_tree = tr.Tree()
    temp_tree.create_node(full_url, full_url)
    chain = copy.deepcopy(full_url)
    for resp in response.history[1:]:
        if resp.status_code >= 400:
            break
        temp_tree.create_node(resp.url, resp.url, parent=chain)
        chain = resp.url

    # return if scan was successful and eventually the redirections tree
    return True, temp_tree


def recursive_cat(website_fs: tr.Tree, node: tr.Node, link: str) -> str:
    # retrieve complete link given a specific node
    if node.is_root():
        return link
    else:
        prev_node_id = node.predecessor(website_fs.identifier)
        prev_node = website_fs.get_node(prev_node_id)
        link = prev_node.tag + '/' + link
        return recursive_cat(website_fs, prev_node, link)


def link_cat(website_fs: tr.Tree, node: tr.Node) -> str:
    return recursive_cat(website_fs, node, '') + node.tag


def tree_append(website_fs: tr.Tree, parent: tr.Node, *args):
    """
    :param website_fs:
    :param parent:
    :param args:
    :return:
    """
    logger = log.getLogger(__name__)
    try:
        if type(args[0]) is tr.Tree:
            website_fs.paste(parent.identifier, args[0])
        elif type(args[0]) is str:
            website_fs.create_node(args[0], args[0], parent=parent.identifier)
        else:
            raise TypeError("tree_append cannot take other *args argument other than 'string' or 'tr.Node'")
    except TypeError as e:
        logger.exception('passed invalid variables to tree_append, shutting down')
        print(e)
        raise SystemExit
    finally:
        logger.info('new directory found')
