from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = [
        line.strip() for line in f.readlines()
        if line.strip() and not line.strip().startswith("#")
    ]

setup(
    name="orga",
    version="0.14.0",
    description="Orga - Project Management System",
    author="Orga",
    author_email="info@orga.localhost",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
    license="GNU Affero General Public License v3",
)
