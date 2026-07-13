from setuptools import setup, find_packages

setup(
    name="history-tracker",
    version="1.0.0",
    author="Yusra Yasin",
    description="Chrome History Tracker with batching, logging, and metrics",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yusrayasin/HistoryTracker",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.8",
)