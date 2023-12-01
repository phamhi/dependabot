import requests
import json
import time
import os
import sys

from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning
from f import *

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# get token and org from env variables
str_github_token = os.getenv('GITHUB_TOKEN')
str_github_org = os.getenv('GITHUB_ORG')

str_default_github_org = 'myorg' # default Github Org
str_default_output_file = 'output.json'

int_sleep = 0
bool_ssl_verify = False

dict_global_headers = {
    'Accept': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'Authorization': f'Bearer {str_github_token}',
}

# default sort to full_name
dict_global_params = dict(
    sort='full_name',
)

class BadCredentialException(Exception):
    pass

# Get repositories for the specified organization on specific page
# https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#list-organization-repositories
def get_repos_per_page(page: int, per_page=100) -> (list):
    dict_params = dict_global_params.copy()
    dict_params['per_page'] = per_page
    dict_params['page'] = page

    res = requests.get(f'https://api.github.com/orgs/{str_github_org}/repos',
                       verify=bool_ssl_verify,
                       headers=dict_global_headers,
                       params=dict_params)
    logger.info(f'page={page},res.status_code = {res.status_code}')

    if res.status_code == 401:
        raise BadCredentialException(res.text)
    # /fi

    if res.status_code != 200:
        logger.info(f'page={page},no more data')
        return []
    # /fi

    list_data = json.loads(res.text)
    logger.info(f'number of records returned={len(list_data)}')
    return list_data
# /def

# Get all repositories for the specified organization.
def get_all_repos() -> (list):
    page = 1
    list_all_repos = []

    while True:
        list_returned_repos = get_repos_per_page(page)

        if len(list_returned_repos) == 0:
            break
        # /if

        list_all_repos.extend(list_returned_repos)
        logger.info(f'total number of records={len(list_all_repos)}')

        page += 1
        time.sleep(int_sleep)
    # / while

    return list_all_repos
# /def

# Return whether dependency alerts are enabled or disabled for a repository
# https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#check-if-vulnerability-alerts-are-enabled-for-a-repository
def is_dependabot_enabled(repo_name: str) -> (bool):
    res = requests.get(f'https://api.github.com/repos/{str_github_org}/{repo_name}/vulnerability-alerts',
                       verify=bool_ssl_verify,
                       headers=dict_global_headers)
    ret = False

    if res.status_code == 204:
        ret = True
    # /elif

    logger.debug(f'repo_name={repo_name},res.status_code={res.status_code},ret={ret}')
    return ret
# /def

# Main
if __name__ == '__main__':
    # parse arguments passed
    args = parse_args()

    int_verbosity = args.verbosity
    bool_show_dependabot_alerts_only = args.dependabot_alerts_only
    str_output_file = args.output_file
    bool_output_stdout = args.output_stdout

    logger = logging.getLogger(__name__)
    c_handler = logging.StreamHandler()
    c_handler.setFormatter(logging.Formatter('%(funcName)s:%(levelname)s:%(message)s'))
    logger.addHandler(c_handler)

    # set logging verbosity
    logger.setLevel(int_verbosity)

    logger.info(f'mode "show-dependabot-alerts-only":"{bool_show_dependabot_alerts_only}"')
    logger.info(f'verbosity "level":"{logging.getLevelName(int_verbosity)}"')

    if not str_github_token:
        logger.error('environment variable "GITHUB_TOKEN" is not set or empty.')
        sys.exit(1)
    # /if

    if not str_github_org:
        str_github_org = str_default_github_org
        logger.info(f'github org:"{str_github_org}"')
    # /if

    list_data = []
    try:
        # list_data = get_repos_per_page(page=1, per_page=5) # limit to 2 records
        list_data = get_all_repos()
    except Exception as e:
        logger.error(e)
        exit(1)
    # /try

    logger.info(f'got a total of {len(list_data)} repo(s)')
    # with open('debug.out', 'wb') as f:
    #     pickle.dump(list_data, f)

    if not len(list_data):
        exit(1)
    # /if

    dict_data = dict()

    for count,i in enumerate(list_data, 1):
        str_name = i['name']
        logger.info(f'({count}/{len(list_data)})processing:{str_name}')
        bool_dependabot_alerts = is_dependabot_enabled(str_name)

        if not bool_dependabot_alerts and bool_show_dependabot_alerts_only:
            continue
        # /if
        dict_data[str_name] = dict()
        dict_data[str_name]['dependabot_alerts'] = bool_dependabot_alerts
    # /for

    # convert to json
    str_output_json = json.dumps(dict_data, indent=2)

    # display output to stdout
    if bool_output_stdout:
        print(str_output_json)
    # /if

    # datetime formatting
    now = datetime.now()
    str_default_now= now.strftime('%Y-%m-%d_%H:%M:%S.%f')

    # write output to json file
    if str_output_file == 'default':
        str_output_file = f'output.{str_default_now}.json'
    # /if
    logger.info(f'writing result to: "{str_output_file}"')
    with open(str_output_file, 'w') as f:
        f.write(str_output_json)
    # /with

# /if
