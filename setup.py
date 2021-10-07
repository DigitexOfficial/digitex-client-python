import os
import setuptools
from setuptools.command.build_py import build_py
from distutils.spawn import spawn, find_executable

package_name = 'digitex_engine_client'

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()


class BuildPyCommand(build_py):
    """A custom build command to compile the proto file."""

    def find_protoc(self):
        protoc = os.environ.get('PROTOC', default=None)
        if protoc and os.path.exists(protoc):
            return protoc
        return find_executable('protoc')

    def run_protoc(self, protoc, source):
        print('Generating Python code from', source)
        out_path = os.path.join(self.build_lib, package_name)
        self.mkpath(out_path)
        spawn([
            protoc,
            source,
            '-I' + os.path.dirname(source),
            '--python_out=' + out_path
        ])

    def run(self):
        protoc = self.find_protoc()
        if not protoc:
            raise RuntimeError('Failed to find protoc')
        messages_proto = os.path.join('src', package_name, 'messages.proto')
        self.run_protoc(protoc, messages_proto)
        setuptools.command.build_py.build_py.run(self)

setuptools.setup(
    name='digitex-engine-client',
    version='4.145.0',
    license='GPL version 3, excluding DRM provisions',
    author='Sergey Bugaev, Pavel Yushchenko',
    author_email='Sergey Bugaev <bugaev@smartdec.com>, Pavel Yushchenko <pyushchenko@digitexfutures.com>',
    maintainer='Pavel Yushchenko <pyushchenko@digitexfutures.com>',
    maintainer_email='pyushchenko@digitexfutures.com',
    url='https://github.com/DigitexOfficial/digitex-client-python',
    packages=[package_name],
    package_dir={'': 'src'},
    install_requires=[
        'aiohttp',
        'protobuf',
        'pytz'
    ],
    cmdclass={'build_py': BuildPyCommand},
    long_description=long_description,
    long_description_content_type='text/markdown'
)
