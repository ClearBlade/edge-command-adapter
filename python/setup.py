from setuptools import setup

setup(
    name='edge-command-adapter',
    packages=['edge-command-adapter'],
    install_requires=['requests<2.28', 'clearblade'],
    version='1.0.0',
    description='A Python ClearBlade Adapter for running shell commands natively in linux and sending the results to a ClearBlade Edge or the ClearBlade Platform',
    url='https://github.com/ClearBlade/edge-command-adapter',
    download_url='https://github.com/ClearBlade/edge-command-adapter',
    keywords=['clearblade', 'iot', 'adapter'],
    maintainer='jbouquet@clearblade.com',
    maintainer_email='dev@clearblade.com',
    package_dir={"":"src"}
)