from setuptools import setup

setup(
    name="streamstaff",
    version="0.1",
    description="Real-Time Signal Processing API using pylsl streams",
    url="https://github.com/merlin-neurotech/streamstaff",
    author="Merlin Neurotech",
    author_email="mnc@clubs.queensu.ca",
    license="MIT",
    packages=["streamstaff"],
    install_requires=["pylsl", "pyqtgraph", "pyqt5", "numpy", "scipy"],
    zip_safe=False,
)
