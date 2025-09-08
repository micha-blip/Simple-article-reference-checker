# Simple reference checker

This notebook provides tools to check the validity of references in scientific articles using DOIs.
The goal is to help identify potentially fabricated or hallucinated references, which can be a concern with AI-generated content, 
and thereby contribute to improving the reliability and integrity of scientific literature.


# Installation instructions
Please install the following dependencies:
```bash
pip install numpy pandas requests Bio
```


# Example Usage
To check the references of a publication, extract the DOI and call the following command:
```bash
python check_references.py 10.3389/fmed.2024.1348884
```
