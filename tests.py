import os
import sys

import pytest
import requests

import script

os.mkdir('./tests/')
sys.path.append('./tests/')


correct_repository_name = 'radium/project-configuration'
correct_base_url = 'https://gitea.radium.group/'
correct_api_url = 'https://gitea.radium.group/api/v1/repos/'
currect_sub_directory = 'nitpick'
correct_head = 'eb4dc314435649737ad343ef82240b96256d5eb8'
correct_filepath = './tests/'


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'repository_name, expected',
    [pytest.param(correct_repository_name, correct_head)],
)
async def test_get_head_correct_repository_name(repository_name, expected):
    head = await script._get_head(repository_name)
    assert head == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'repository_name',
    [pytest.param('incorrectname')],
)
async def test_get_head_incorrect_repository_name(repository_name):
    head = await script._get_head('incorrectname')
    assert head is None


@pytest.mark.parametrize(
    'api_url, repository_name',
    [pytest.param(correct_api_url, correct_repository_name)],
)
def test_file_list_being_filled_from_top_directory(api_url, repository_name):
    timeout = 3
    contents_url = '{0}{1}/contents'.format(
        api_url,
        repository_name,
    )
    directory_contents = requests.get(contents_url, timeout=timeout).json()
    script._fill_file_list(
        directory_contents,
        repository_name,
        current_dir=None,
    )

    assert script.file_list is not None


@pytest.mark.parametrize(
    'api_url, repository_name, sub_directory',
    [pytest.param(
        correct_api_url,
        correct_repository_name,
        currect_sub_directory,
    ),
    ],
)
def test_file_list_being_filled_from_sub_directory(api_url, repository_name, sub_directory):
    timeout = 3
    dir_contents_url = '{0}{1}/contents/{2}/'.format(
        api_url,
        repository_name,
        sub_directory,
    )
    directory_contents = requests.get(dir_contents_url, timeout=timeout).json()
    script.dir_list = list()
    script.dir_list.append(sub_directory)
    script._fill_file_list(
        directory_contents,
        repository_name,
        current_dir=sub_directory,
    )

    assert script.file_list is not None


@pytest.mark.parametrize(
    'api_url, repository_name, sub_directory',
    [pytest.param(
        correct_api_url,
        'incorrectrepositoryname',
        currect_sub_directory,
    ),
    ],
)
def test_fill_file_list_with_incorrect_repository_name(api_url, repository_name, sub_directory):
    timeout = 3
    dir_contents_url = '{0}{1}/contents/{2}/'.format(
        api_url,
        repository_name,
        sub_directory,
    )
    with pytest.raises(requests.exceptions.JSONDecodeError) as decode_error:
        directory_contents = requests.get(
            dir_contents_url,
            timeout=timeout,
        ).json()
        assert decode_error is not None
    with pytest.raises(UnboundLocalError) as unbound_error:
        script.dir_list.append(sub_directory)
        script._fill_file_list(
            directory_contents,
            repository_name,
            current_dir=sub_directory,
        )
        assert unbound_error is not None


@pytest.mark.parametrize(
    'api_url, repository_name',
    [pytest.param(
        'incorrect.url/api/',
        correct_repository_name,
    ),
    ],
)
def test_fill_file_list_with_incorrect_api_url(api_url, repository_name):
    timeout = 5
    dir_contents_url = '{0}{1}/contents/'.format(
        api_url,
        repository_name,
    )
    with pytest.raises(requests.exceptions.MissingSchema) as schema_error:
        directory_contents = requests.get(
            dir_contents_url, timeout=timeout).json()
        assert schema_error is not None
    with pytest.raises(UnboundLocalError) as unbound_error:
        script._fill_file_list(
            directory_contents,
            repository_name,
        )
        assert unbound_error is not None


@pytest.mark.parametrize(
    'directory_list, repository',
    [pytest.param(
        [currect_sub_directory],
        correct_repository_name,
    ),
    ],
)
def test_dir_lookup(directory_list, repository):
    script.dir_list = directory_list
    script._dir_lookup(directory_list, repository)
    assert script.file_list is not None


@pytest.mark.parametrize(
    'directory_list, repository',
    [pytest.param(
        [currect_sub_directory],
        correct_repository_name,
    ),
    ],
)
def test_dir_lookup_with_incorrect_global_dir_list(directory_list, repository):
    with pytest.raises(ValueError) as value_error:
        script._dir_lookup(directory_list, repository)
        assert value_error is not None


@pytest.mark.parametrize(
    'directory_list, repository',
    [pytest.param(
        ['incorrectdirectoryname'],
        correct_repository_name,
    ),
    ],
)
def test_dir_lookup_with_incorrect_directory_list(directory_list, repository):
    script.dir_list = directory_list
    with pytest.raises(TypeError) as type_error:
        script._dir_lookup(directory_list, repository)
        assert type_error is not None


@pytest.mark.parametrize(
    'directory_list, repository',
    [pytest.param(
        [currect_sub_directory],
        'incorrectrepositoryname',
    ),
    ],
)
def test_dir_lookup_with_incorrect_repository_name(directory_list, repository):
    script.dir_list = directory_list
    with pytest.raises(requests.exceptions.JSONDecodeError) as decode_error:
        script._dir_lookup(directory_list, repository)
        assert decode_error is not None


@pytest.mark.parametrize(
    'repository, filepath',
    [pytest.param(
        correct_repository_name,
        correct_filepath,
    ),
    ],
)
def test_preprocess(repository, filepath):
    filelist = script._preprocess(repository, filepath)
    assert filelist is not None
    assert os.path.exists(filepath)


@pytest.mark.parametrize(
    'repository, filepath',
    [pytest.param(
        'incorrectrepositoryname',
        correct_filepath,
    ),
    ],
)
def test_preprocess_with_incorrect_repository_name(repository, filepath):
    with pytest.raises(TypeError) as type_error:
        script._preprocess(repository, filepath)
        assert type_error is not None
    assert os.path.exists(filepath)


@pytest.mark.parametrize(
    'repository, filepath',
    [pytest.param(
        correct_repository_name,
        '/incorrect/filepath/',
    ),
    ],
)
def test_preprocess_with_incorrect_filepath(repository, filepath):
    with pytest.raises(FileNotFoundError) as file_error:
        script._preprocess(repository, filepath)
        assert file_error is not None
    assert not os.path.exists(filepath)


@pytest.mark.parametrize(
    'repository, head, filepath',
    [pytest.param(
        correct_repository_name,
        correct_head,
        correct_filepath,
    ),
    ],
)
def test_download_files(repository, head, filepath):
    filelist = script._preprocess(repository, filepath)
    script._download_files(repository, head, filepath, filelist)

    for filename in filelist:
        assert os.path.exists(filepath + filename)
        with open(filepath + filename, 'r') as open_file:
            assert 'Not found' not in open_file.read()


@pytest.mark.parametrize(
    'repository, head, filepath',
    [pytest.param(
        'incorrectrepositoryname',
        correct_head,
        correct_filepath,
    ),
    ],
)
def test_download_files_with_incorrect_repository_name(repository, head, filepath):
    with pytest.raises(TypeError) as type_error:
        filelist = script._preprocess(repository, filepath)
        script._download_files(repository, head, filepath, filelist)

        for filename in filelist:
            assert not os.path.exists(filepath + filename)
        assert type_error is not None


@pytest.mark.parametrize(
    'repository, head, filepath',
    [pytest.param(
        correct_repository_name,
        'incorrecthead',
        correct_filepath,
    ),
    ],
)
def test_download_files_with_incorrect_head(repository, head, filepath):
    filelist = script._preprocess(repository, filepath)
    script._download_files(repository, head, filepath, filelist)

    for filename in filelist:
        with open(filepath + filename, 'r') as open_file:
            assert 'Not found' in open_file.read()


@pytest.mark.parametrize(
    'repository, filepath, filename',
    [pytest.param(
        correct_repository_name,
        correct_filepath,
        'SHA256',
    ),
    ],
)
def test_calculate_sha256(repository, filepath, filename):
    filelist = script._preprocess(repository, filepath)
    script._calculate_sha256(filepath, filelist, filename)
    assert os.path.exists(filepath + filename)
    with open(filepath + filename, 'r') as open_file:
        lines = len(open_file.readlines())
        assert lines == len(filelist) + 1
    with open(filepath + filename, 'w') as open_file:
        open_file.close()


@pytest.mark.parametrize(
    'repository, filepath, filename',
    [pytest.param(
        'incorrectrepositoryname',
        correct_filepath,
        'SHA256',
    ),
    ],
)
def test_calculate_sha256_with_incorrect_repository_name(repository, filepath, filename):
    with pytest.raises(TypeError) as type_error:
        filelist = script._preprocess(repository, filepath)
        script._calculate_sha256(filepath, filelist, filename)
        assert not os.path.exists(filepath + filename)
        assert type_error is not None


@pytest.mark.parametrize(
    'repository, filepath, filename',
    [pytest.param(
        correct_repository_name,
        '/incorrect/filepath/',
        'SHA256',
    ),
    ],
)
def test_calculate_sha256_with_incorrect_filepath(repository, filepath, filename):
    with pytest.raises(FileNotFoundError) as file_error:
        filelist = script._preprocess(repository, filepath)
        script._calculate_sha256(filepath, filelist, filename)
        assert not os.path.exists(filepath + filename)
        assert file_error is not None


@pytest.mark.parametrize(
    'repository, filepath, filename',
    [pytest.param(
        correct_repository_name,
        correct_filepath,
        '/SHA/256/',
    ),
    ],
)
def test_calculate_sha256_with_incorrect_filename(repository, filepath, filename):
    with pytest.raises(FileNotFoundError) as file_error:
        filelist = script._preprocess(repository, filepath)
        script._calculate_sha256(filepath, filelist, filename)
        assert not os.path.exists(filepath + filename)
        assert file_error is not None


@pytest.mark.parametrize(
    'repository, filepath, async_procs',
    [pytest.param(
        correct_repository_name,
        correct_filepath,
        3,
    ),
    ],
)
@pytest.mark.asyncio
async def test_download_repo_async(repository, filepath, async_procs):
    filelist = script._preprocess(repository, filepath)
    await script.download_repo_async(repository, filepath, async_procs)

    for filename in filelist:
        assert os.path.exists(filepath + filename)
        with open(filepath + filename, 'r') as open_file:
            assert 'Not found' not in open_file.read()


@pytest.mark.parametrize(
    'repository, filepath, async_procs',
    [pytest.param(
        'incorrectrepositoryname',
        correct_filepath,
        3,
    ),
    ],
)
@pytest.mark.asyncio
async def test_download_repo_async_with_incorrect_repository_name(repository, filepath, async_procs):
    with pytest.raises(TypeError) as type_error:
        await script.download_repo_async(repository, filepath, async_procs)
        assert type_error is not None


@pytest.mark.parametrize(
    'repository, filepath, async_procs',
    [pytest.param(
        correct_repository_name,
        '/incorrect/filepath/',
        3,
    ),
    ],
)
@pytest.mark.asyncio
async def test_download_repo_async_with_incorrect_filepath(repository, filepath, async_procs):
    with pytest.raises(FileNotFoundError) as file_error:
        await script.download_repo_async(repository, filepath, async_procs)
        assert file_error is not None


@pytest.mark.parametrize(
    'repository, filepath, async_procs',
    [pytest.param(
        correct_repository_name,
        correct_filepath,
        0,
    ),
    ],
)
@pytest.mark.asyncio
async def test_download_repo_async_with_incorrect_async_procs(repository, filepath, async_procs):
    with pytest.raises(ValueError) as value_error:
        await script.download_repo_async(repository, filepath, async_procs)
        assert value_error is not None
