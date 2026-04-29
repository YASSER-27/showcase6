from setuptools import setup

setup(
    name='showcase6',
    version='1.0.0',
    py_modules=['show', 'pa'],
    entry_points={
        'console_scripts': [
            'showcase=show:main',
        ],
    },
    install_requires=[
        'PySide6',
        'imageio',
        'numpy',
    ],
    description='Professional 3D Showcase Builder CLI',
    author='Yassir',
)
