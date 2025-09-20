from setuptools import setup, find_packages
import os

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

# Include shell scripts and other files
data_files = []
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.sh') or file in ['README.md', 'USER_GUIDE.md', 'autoclicker_settings.json']:
            data_files.append((os.path.join('share', 'autoclicker', root[2:]), [os.path.join(root, file)]))

setup(
    name="autoclicker",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AutoClicker for Ubuntu - Finds and clicks on user-defined images or text",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/superman2002/AutoClicker",
    packages=find_packages(),
    py_modules=["autoclicker", "autoclicker_gui"],
    include_package_data=True,
    install_requires=requirements,
    data_files=data_files,
    entry_points={
        'console_scripts': [
            'autoclicker=autoclicker:main',
            'autoclicker-gui=autoclicker_gui:main',
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires='>=3.8',
)
