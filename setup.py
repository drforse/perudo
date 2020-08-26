import setuptools

setuptools.setup(
    name="perudo_bot",
    version="0.1.0",
    author="drforse",
    author_email="george.lifeslice@gmail.com",
    description="Telegram bot to play perudo",
    long_description="Telegram bot to play perudo",
    long_description_content_type="text/markdown",
    url="https://github.com/drforse/perudo",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)