"""HEAD folder downloader from a selected repository."""

import asyncio
import hashlib
import logging
import os

import numpy
import requests

file_list = []
dir_list = []
timeout = 5
base_url = 'https://gitea.radium.group/'
api_url = 'https://gitea.radium.group/api/v1/repos/'


async def _get_head(repository):
    """
    Get HEAD folder address.

    Args:
        repository : str
            a string in a format <owner>/<repository name>

    Returns:
        HEAD folder address
    """
    repo_url = '{0}{1}.git'.format(base_url, repository)
    process = await asyncio.create_subprocess_exec(
        'git',
        'ls-remote',
        repo_url,
        stdout=asyncio.subprocess.PIPE,
    )

    process_result, _ = await process.communicate()
    process_result = process_result.decode()
    for row in process_result.split('\n'):
        if ('HEAD' in row):
            return row.split('\t')[0]


def _fill_file_list(dir_contents, repository, current_dir=None):
    """
    Fill list of files from repository.

    Args:
        dir_contents : list(dict())
            list of dictionaries of files
        repository : str
            a string in a format <owner>/<repository name>
        current_dir : str
            current directory name
    """
    for dir_item in dir_contents:
        item_name = dir_item['name']
        if (current_dir is not None):
            item_name = '{0}/{1}'.format(current_dir, item_name)
        match dir_item['type']:
            case 'file':
                file_list.append(item_name)
            case 'dir':
                dir_list.append(item_name)
    if (dir_list.count == 0):
        return

    if (current_dir is not None):
        dir_list.remove(current_dir)

    _dir_lookup(dir_list, repository)


def _dir_lookup(directory_list, repository):
    """
    Assist function for filling files list.

    Args:
        directory_list : list(str)
            list of directiries names
        repository : str
            a string in a format <owner>/<repository name>
    """
    for dir_name in directory_list:
        dir_contents_url = '{0}{1}/contents/{2}/'.format(
            api_url,
            repository,
            dir_name,
        )
        dir_contents = requests.get(
            dir_contents_url,
            timeout=timeout,
        ).json()
        _fill_file_list(dir_contents, repository, current_dir=dir_name)


def _preprocess(repo, filepath):
    """
    Bootstrap before download.

    Args:
        repo : str
            a string in a format <owner>/<repository name>
        filepath :
            str a string of a name of the directory

    Returns:
        list of filenames
    """
    if (not os.path.exists(filepath)):
        os.mkdir(filepath)
    contents_url = '{0}{1}/contents'.format(
        api_url,
        repo,
    )
    dir_contents = requests.get(contents_url, timeout=timeout).json()
    _fill_file_list(dir_contents, repo)

    return file_list


def _download_files(repository, head, filepath, files):
    """
    Download files from HEAD folder of selected repo.

    Args:
        repository : str
            a string in a format <owner>/<repository name>
        head: str
            HEAD folder address
        filepath :
            str a string of a name of the directory
        files : list(str)
            list of filenames to calculate SHA256 for
    """
    for filename in files:
        url = '{0}{1}/raw/commit/{2}/{3}'.format(
            base_url,
            repository,
            head,
            filename,
        )
        raw_text = requests.get(url, timeout=timeout).text
        if ('/' in filename):
            # split by the last '/'
            # separating the filename and the directories
            dir_path = filename.rsplit('/', 1)[0]
            dir_path = filepath + dir_path
            if (not os.path.exists(dir_path)):
                try:
                    os.makedirs(dir_path)
                except FileExistsError:
                    logging.warning(
                        'Dir {0} already exists\n'.format(
                            dir_path,
                        ),
                        timeout=timeout,
                    )

        with open(filepath + filename, 'w') as open_file:
            open_file.write(raw_text)


def _calculate_sha256(filepath, filelist, output_filename='SHA256'):
    """
    Calculate SHA256 hash for a list of files.

    Args:
        filepath : str
            name of the directory to put the result in
        filelist : list(str)
            list of filenames to calculate SHA256 for
        output_filename : str
            name of the output file
    """
    output = '[SHA256]\n'

    for filename in filelist:
        with open(filepath + filename, 'rb') as open_file:
            sha_hex = hashlib.sha256(open_file.read()).hexdigest()
            output += '{0}______{1}\n'.format(filename, sha_hex)
    with open(filepath + output_filename, 'w') as output_file:
        output_file.write(output)


async def download_repo_async(repository, filepath, async_procs=3):
    """
    Download files from HEAD from a repository and calculate SHA256.

    Args:
        repository : str
            a string in a format <owner>/<repository name>
        filepath :
            str a string of a name of the directory
        async_procs : int
            a number of asynchronous processes to run the download
    """
    filelist = _preprocess(repository, filepath)
    head = await _get_head(repository)
    # batches of files for each proc to download
    batches = numpy.array_split(filelist, async_procs)
    loop = asyncio.get_event_loop()
    futures = [
        loop.run_in_executor(
            None,
            _download_files,
            repository,
            head,
            filepath,
            batches[proc],
        ) for proc in range(0, async_procs)
    ]
    await asyncio.gather(*futures)

    _calculate_sha256(filepath, filelist)

if __name__ == '__main__':
    base_filepath = './tmp/'
    num_of_procs = 3
    repo_name = 'radium/project-configuration'
    asyncio.run(download_repo_async(repo_name, base_filepath, num_of_procs))
