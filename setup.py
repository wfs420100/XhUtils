# wfs420100--2022/12/29
from os.path import dirname, abspath, join
from setuptools import setup, find_packages


def starting():
    homepath = dirname(abspath(__file__))
    with open(join(homepath, "version.txt"), "r", encoding="utf8") as fr:
        version = fr.read().strip()

    with open(join(homepath, "readme.md"), "r", encoding="utf8") as fr:
        long_description = fr.read()

    with open(join(homepath, "requirements.txt"), "r", encoding="utf8") as fr:
        install_requires = [line.strip() for line in fr.readlines()]

    setup(
        name="xh_utils",
        version=version,
        description="xh personal Python util libs",
        long_description=long_description,
        long_description_content_type="text/markdown",
        author="wfs420100",
        author_email="wfs420100@126.com",
        url="https://github.com/wfs420100/XhUtils",
        packages=find_packages(),
        install_requires=install_requires,
        license="Apache License 2.0",
        classifiers=[
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
        ]
    )


if __name__ == '__main__':
    print("wfs420100")
    starting()
