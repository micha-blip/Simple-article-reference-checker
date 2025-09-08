import requests
import numpy as np
import pandas as pd
import sys
from Bio import Entrez # Import Entrez


def get_references_from_doi(doi, return_dataframe = True, verbose = True):
  """
  Fetches references for a given DOI, checks their existence via Crossref,
  and returns a summary or a DataFrame of the results.

  Args:
    doi (str): The DOI of the article to fetch references from.
    return_dataframe (bool, optional): If True, returns a pandas DataFrame
                                        with DOI and status. If False, returns
                                        a dictionary summary. Defaults to True.
    verbose (bool, optional): If True, prints detailed status during the
                              reference check. Defaults to True.

  Returns:
    pandas.DataFrame or dict: A DataFrame with reference DOIs and their status
                              ('article found', 'no article', 'no DOI'),
                              or a dictionary summarizing the counts of each status.
                              Returns None if the initial article DOI is not found.
  """

  api_url = f"https://api.crossref.org/v1/works/{doi}"
  headers = {"User-Agent": "SimpleFetcher"}
  print('Sending request...')

  try:
      response = requests.get(api_url, headers=headers)
      response.raise_for_status()  # Check for bad responses
      data = response.json()

      # Get the list of references from the response
      references = data["message"].get("reference", [])
      title = data["message"].get('title', [])
      title = str(title[0]).replace("\n", " ").replace('+', "")
      print('Processing response for: ' + '\x1B[3m'  + title)

      doi_list = []

      if references:
          for i, ref in enumerate(references):
              ref_key = ref.get('key', f"substitute_key_{i}") # Use a substitute key if 'key' is missing
              if "DOI" in ref:
                  doi_list.append(ref['DOI'])
              elif "unstructured" in ref:
                  doi_list.append('not found')
              else:
                  doi_list.append('not found')

  except requests.exceptions.RequestException as e:
      print(f"An error occurred: The article was not found")
      return

  check_status = check_references_for_doi(doi_list, verbose)
  print("Done, found " + str(sum(check_status == "article found")) + " existing documents, " + str(sum(check_status == "no article")) + " non-existing documents" + " and " + str(sum(check_status == 'no DOI')) + " missing DOI")

  if verbose == False:
    result = {"Found" : int(sum(check_status == "article found")), "Not found" : int(sum(check_status == "no article")), "Missing DOI" : int(sum(check_status == 'no DOI'))}
    return pd.DataFrame(result, index = range(1))



  if return_dataframe == True:
    references_checked = pd.DataFrame(doi_list,  columns=['DOI'])
    references_checked['status'] = check_status
    return references_checked




def check_references_for_doi(doi_list, verbose):
  """
  Checks the existence of a list of DOIs using the PubMed API (Entrez).

  Args:
    doi_list (list): A list of DOIs (strings) to check. 'not found' indicates
                     a missing DOI in the original reference list.
    verbose (bool): If True, prints the status and title (if found) for each DOI.

  Returns:
    numpy.ndarray: A numpy array of strings indicating the status for each DOI
                   in the input list ('article found', 'no article', 'no DOI').
  """
  # Always tell Entrez who you are
  Entrez.email = "your_email@example.com" # Replace with your email address

  status = np.full(len(doi_list), "not processed")

  for i, doi in enumerate(doi_list):
    if doi == 'not found': # if there is no doi in the original reference
      status[i] = 'no DOI'
      if verbose == True:
        print('\033[33m' + str(i+1) +" " +  "DOI missing in reference list" + '\033[0m')
      continue

    try:
        # Search PubMed for the DOI to get the PMID
        # Using a more specific search term to improve accuracy
        search_term = f'{doi}[doi]'
        search_handle = Entrez.esearch(db="pubmed", term=search_term, retmax=10) # Use retmax to limit results
        search_record = Entrez.read(search_handle)
        search_handle.close()

        pubmed_ids = search_record["IdList"]

        if pubmed_ids:
            # If PMID(s) found, fetch the article details to confirm existence and get title
            # Fetch details for the first result, as we expect only one match for a DOI
            fetch_handle = Entrez.efetch(db="pubmed", id=pubmed_ids[0], retmode="xml")
            article_record = Entrez.read(fetch_handle)
            fetch_handle.close()

            if 'PubmedArticle' in article_record and len(article_record['PubmedArticle']) > 0:
                article = article_record['PubmedArticle'][0]['MedlineCitation']['Article']
                title = article.get('ArticleTitle', 'No Title Available')

                if verbose == True:
                   print('\033[32m'  + str(i+1) + " " + title + '\033[0m')
                status[i] = "article found"
            else:
                # This case is less likely if a PMID was found, but included for robustness
                if verbose == True:
                   print('\033[31m' + str(i+1) + " " +  f"Could not fetch details for DOI: {doi}" + '\033[0m')
                status[i] = 'no article'

        else:
            if verbose == True:
               print('\033[31m' + str(i+1) + " " +  f"No article found on PubMed for DOI: {doi}" + '\033[0m')
            status[i] = 'no article' # No PMID found for the DOI

    except Exception as e: # Catch potential errors during Entrez interaction
        if verbose == True:
           print('\033[31m' + str(i+1) + " " +  f"An error occurred checking DOI '{doi}' on PubMed: {e}" + '\033[0m')
        status[i] = 'no article' # Treat any other error as article not found for simplicity

  return status



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_references.py DOI")
        sys.exit(1)

    doi = sys.argv[1]
    x = get_references_from_doi(doi=doi, return_dataframe=True, verbose=True)

