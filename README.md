# Clinical Trial Matching Algorithm

This project implements an algorithm that matches patient data with clinical trials based on eligibility criteria. The solution uses patient data and clinical trial information, processes them using Natural Language Processing (NLP), and generates a list of eligible trials for each patient. 

## Table of Contents
- [Project Overview](#project-overview)
- [Features](#features)
- [Installation](#installation)
- [Data Sources](#data-sources)
- [Usage](#usage)
- [File Structure](#file-structure)
- [Testing](#testing)
- [License](#license)

## Project Overview
The algorithm performs the following tasks:
1. Loads patient data.
2. Scrapes clinical trial data from [clinicaltrials.gov](https://clinicaltrials.gov).
3. Matches patients to clinical trials based on inclusion/exclusion criteria.
4. Outputs eligible trials for each patient in a structured format (JSON and Excel).

## Features
- **Patient Data Matching**: Automatically matches patients to clinical trials based on age, diagnosis, gender, and other factors.
- **NLP Processing**: Uses spaCy models for processing biomedical data and extracting key information from clinical trials.
- **Concurrent Processing**: Uses parallel processing to handle multiple patients and trials efficiently.
- **Comprehensive Output**: Generates output in both JSON and Google Sheets formats for easy review.

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/clinical-trial-matching.git
cd clinical-trial-matching
```

### 2. Create a Python virtual environment
It’s a good idea to isolate the project dependencies in a virtual environment.
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install the necessary dependencies
The dependencies are listed in requirements.txt. You can install them by running:
```bash
pip install -r requirements.txt
```
Make sure that you have a version of scispacy and the associated NLP model downloaded:
```bash
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_ner_bc5cdr_md-0.5.4.tar.gz
```
## Data Sources

- **Patient Data**: Downloaded from [Synthea](https://synthea.mitre.org/downloads). This project assumes the patient data is already formatted in JSON.
- **Clinical Trials**: Scraped from [clinicaltrials.gov](https://clinicaltrials.gov), focusing on actively recruiting trials.

## Usage

### 1. Prepare Input Data
Make sure you have the following directories:
- **Patient Data**: Place the patient JSON files in the `patient_data/` directory.
- **Clinical Trial Data**: Place the clinical trial JSON files in the `clinical_trials/` directory.

### 2. Run the matching algorithm
Execute the main script to process the data and generate the output:
```bash
python matching_algorithm.py
```
### 3. Output
The script will generate two types of output:
- **JSON File**: Contains patient-trial matching results.
- **Google Sheets (optional)**: The matching results can also be uploaded to a Google Sheet for easier accessibility.

Example JSON output:
```bash
{
  "patientId": "P123",
  "eligibleTrials": [
    {
      "trialId": "T001",
      "trialName": "Study of XYZ",
      "eligibilityCriteriaMet": ["age between 18-65", "diagnosis matches condition X"]
    }
  ]
}
```
File Structure:
```bash
|-- patient_data/                    # Folder containing patient JSON files
|-- clinical_trials/                 # Folder containing clinical trial JSON files
|-- matching_algorithm.py            # Main script to run the algorithm
|-- README.md                        # Project documentation
|-- requirements.txt                 # List of dependencies
|-- output/                          # Folder for generated output files
```
## Testing

### 1. Unit Testing
To ensure that all functions perform as expected, unit tests can be written using `unittest` or `pytest`.

### 2. Integration Testing
Integration testing is necessary to verify the full workflow—loading patient data, processing trials, and generating output.

### Example of Running Unit Tests:
```bash
pytest test_matching_algorithm.py
```
### License
This project is licensed under the MIT License. See the LICENSE file for details.



