from setuptools import setup, find_packages

setup(
    name='taskontrol',
    version='1.0dev',
    author='Santiago Jaramillo',
    author_email='sjara@uoregon.edu',
    description='TASKontrol is a framework for developing behavioral experiments.',
    packages=find_packages(exclude=[]),
    long_description=open('README.md').read(),
    long_description_content_type='text/x-rst; charset=UTF-8',
    install_requires=[]
)


