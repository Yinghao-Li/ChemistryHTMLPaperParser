from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='ChemistryPaperParser',
    version='0.0.1',
    author='Yinghao Li',
    author_email='yinghaoli@gatech.edu',
    license='MIT',
    url='https://github.com/Yinghao-Li/ChemistryHTMLPaperParser',
    description='Parsing HTML chemistry papers from certain publishers into plain text',
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords='data-mining natural-language-processing nlp parser chemistry',
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Chemistry',
        'Topic :: Scientific/Engineering :: Information Analysis'
    ],
    packages=find_packages(),
    python_requires=">=3.6",
)
