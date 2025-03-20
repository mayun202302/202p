#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="trx_energy_rental",
    version="0.1.0",
    author="TRX Energy Rental Team",
    author_email="your_email@example.com",
    description="TRON能量租赁系统，提供Web应用和Telegram机器人服务",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/trx_energy_rental",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": ["*.html", "*.css", "*.js", "*.png", "*.jpg", "*.svg"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "trx-web=trx_energy_rental.app:main",
            "trx-bot=trx_energy_rental.bot.telegram_bot:main",
            "trx-monitor=trx_energy_rental.blockchain.energy_service:monitor_main",
        ],
    },
) 