from setuptools import setup, find_packages

# Add shell scripts to installd ata

setup(name='sigrun',
      version='0.1.0',
      description='Sigrun is a Discord bot that manages your Valheim server.',
      packages=find_packages(),
      install_requires=[
          'aiohttp >= 3.7', 'loguru >= 0.5', 'psutil >= 5.8.0',
          'click >= 7.1.2'
      ],
      package_data={'scripts': ['*.sh']},
      entry_points='''
            [console_scripts]
            sigrun=sigrun.cli:sigrun
      ''')
