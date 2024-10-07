import os
import json
import spacy
import re
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
import scispacy

!pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_ner_bc5cdr_md-0.5.4.tar.gz

# Load spaCy model for NLP processing for biomedical entities
nlp = spacy.load("en_ner_bc5cdr_md")

# Paths to patient and clinical trial folders
patient_folder = r'/content/drive/MyDrive/sample/patient_data'
trial_folder = r'/content/drive/MyDrive/sample/clinical_trials'

# Utility function to load all JSON files from a folder
def load_json_files(folder_path):
    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.json')]
    data = []
    for file in files:
        with open(file, 'r') as f:
            data.append(json.load(f))
    return data

# Function to extract age from eligibility criteria text
def extract_age_from_criteria(criteria_text, age_type="minimum"):
    """Extracts age (either minimum or maximum) from the eligibility criteria text."""
    if age_type == "minimum":
        # Look for the minimum age using a regex pattern (e.g., "Age > 18 years" or "18 years or older")
        match = re.search(r'age\s*(>=|>|older than)\s*(\d+)\s*(years?|months?)', criteria_text, re.I)
    else:
        # Look for the maximum age using a regex pattern (e.g., "Age <= 65 years" or "65 years or younger")
        match = re.search(r'age\s*(<=|<|younger than)\s*(\d+)\s*(years?|months?)', criteria_text, re.I)

    if match:
        age_value = int(match.group(2))
        age_unit = match.group(3).lower()

        # Convert age to months if necessary
        if "year" in age_unit:
            return age_value * 12
        elif "month" in age_unit:
            return age_value
    return None

# Function to convert age from string (e.g., "18 Years") to months
def convert_age_to_months(age_str):
    """Converts an age string like '18 Years' or '6 Months' into months."""
    if not age_str:
        return None  # Return None if age_str is None or empty
    if 'month' in age_str.lower():
        return int(re.search(r'\d+', age_str).group())
    elif 'year' in age_str.lower():
        return int(re.search(r'\d+', age_str).group()) * 12
    return None

# Function to calculate patient age in months
def calculate_patient_age(birth_date_str):
    """Calculates patient's age in months from birth date."""
    birth_year = int(birth_date_str.split('-')[0])
    current_year = datetime.now().year
    return (current_year - birth_year) * 12

# Function to extract inclusion and exclusion criteria from the eligibility criteria text
def extract_criteria_from_text(criteria_text):
    """Extracts inclusion and exclusion criteria from a well-formatted string."""
    inclusion_criteria = ""
    exclusion_criteria = ""

    # Extract inclusion criteria (starts from "INCLUSION CRITERIA")
    inclusion_match = re.search(r'INCLUSION CRITERIA:(.*?)(EXCLUSION CRITERIA:|$)', criteria_text, re.S | re.I)
    if inclusion_match:
        inclusion_criteria = inclusion_match.group(1).strip()

    # Extract exclusion criteria (starts from "EXCLUSION CRITERIA")
    exclusion_match = re.search(r'EXCLUSION CRITERIA:(.*)', criteria_text, re.S | re.I)
    if exclusion_match:
        exclusion_criteria = exclusion_match.group(1).strip()

    return inclusion_criteria, exclusion_criteria

# Function to process inclusion and exclusion criteria using NLP
def process_criteria_with_nlp(criteria_text):
    """Processes inclusion and exclusion criteria using NLP techniques."""
    inclusion_text, exclusion_text = extract_criteria_from_text(criteria_text)
    inclusion_conditions = set()  # Using set to avoid duplicates
    exclusion_conditions = set()  # Using set to avoid duplicates

    # Process inclusion criteria
    inclusion_doc = nlp(inclusion_text)
    for ent in inclusion_doc.ents:
        if ent.label_ == 'DISEASE':
            inclusion_conditions.add(ent.text.lower())

    # Process exclusion criteria (if any)
    exclusion_doc = nlp(exclusion_text)
    for ent in exclusion_doc.ents:
        if ent.label_ == 'DISEASE' and ent.text.lower() not in inclusion_conditions:
            exclusion_conditions.add(ent.text.lower())

    #print("Inclusion conditions: " + ", ".join(inclusion_conditions))
    #print("Exclusion conditions: " + ", ".join(exclusion_conditions))

    return {
        'inclusion': {
            'conditions': list(inclusion_conditions)  # Converting back to list for consistency
        },
        'exclusion': {
            'conditions': list(exclusion_conditions)  # Converting back to list for consistency
        }
    }

# Function to match patient data to clinical trial based on inclusion and exclusion criteria
def match_patient_to_trial(patient, trial_criteria, min_age_months, max_age_months):
    """Matches a patient to a clinical trial based on dynamic criteria."""
    # Calculate patient's age in months
    patient_age_months = calculate_patient_age(patient['entry'][0]['resource']['birthDate'])

    # Safely get patient conditions (if not present, use an empty list)
    patient_conditions = set()  # Using set to avoid duplicates
    for entry in patient.get('entry', []):
        resource = entry.get('resource', {})

        # Extract condition from 'Condition' resource
        if resource.get('resourceType') == 'Condition':
            condition = resource.get('code', []).get('coding', [])[0].get('display', '').lower()
            if condition:
                patient_conditions.add(condition)

        # Extract condition from 'Encounter' resource
        if resource.get('resourceType') == 'Encounter':
            for condition in resource.get('reasonCode', []):
                display = condition.get('coding', [])[0].get('display', '').lower()
                if display:
                    patient_conditions.add(display)

    print("Patient conditions: " + ", ".join(patient_conditions))

    # Also extract allergy conditions from AllergyIntolerance section (if applicable)
    patient_allergies = set(
        allergy['code']['text'].lower()
        for allergy in patient.get('AllergyIntolerance', [])
    )

    # Age matching
    if not (min_age_months <= patient_age_months <= max_age_months):
        return False, []

    # Inclusion criteria matching
    inclusion = trial_criteria['inclusion']
    matched_criteria = []
    if inclusion['conditions']:
        # Find the conditions that match both the patient conditions and inclusion criteria
        matched_criteria = [cond for cond in inclusion['conditions'] if cond in patient_conditions]

        # If no conditions match, return False
        if not matched_criteria:
            return False, []

    # Exclusion criteria matching (also check allergies)
    exclusion = trial_criteria['exclusion']
    if exclusion['conditions'] and (any(cond in patient_conditions for cond in exclusion['conditions']) or any(cond in patient_allergies for cond in exclusion['conditions'])):
        return False, []

    # Return True if there's a match, along with the matched criteria
    return True, matched_criteria

# Function to process a single patient file
def process_patient_file(patient, trials_data):
    patient_id = patient['entry'][0]['resource']['id']
    eligible_trials = []

    for trial in trials_data:
        trial_id = trial['protocolSection']['identificationModule']['nctId']
        trial_name = trial['protocolSection']['identificationModule']['briefTitle']
        eligibility_text = trial['protocolSection']['eligibilityModule']['eligibilityCriteria']

        # Get minimumAge and maximumAge from the trial data or extract from eligibilityCriteria
        min_age_str = trial['protocolSection']['eligibilityModule'].get('minimumAge', None)
        max_age_str = trial['protocolSection']['eligibilityModule'].get('maximumAge', None)

        # If minimumAge is not available, extract from eligibility criteria text
        if not min_age_str:
            min_age_months = extract_age_from_criteria(eligibility_text, age_type="minimum")
        else:
            min_age_months = convert_age_to_months(min_age_str)

        # If maximumAge is not available, extract from eligibility criteria text
        if not max_age_str:
            max_age_months = extract_age_from_criteria(eligibility_text, age_type="maximum")
        else:
            max_age_months = convert_age_to_months(max_age_str)

        # If min_age_months is still None, default to 18 years
        if min_age_months is None:
            min_age_months = 18 * 12  # Default to 18 years

        # If max_age_months is still None, default to 100 years
        if max_age_months is None:
            max_age_months = 100 * 12  # Default to 100 years

        # Extract and process inclusion and exclusion criteria using NLP
        trial_criteria = process_criteria_with_nlp(eligibility_text)

        # Check if the patient is eligible
        bool1, matched_criteria = match_patient_to_trial(patient, trial_criteria, min_age_months, max_age_months)
        if bool1:
            eligible_trials.append({
                'trialId': trial_id,
                'trialName': trial_name,
                'eligibilityCriteriaMet': matched_criteria
            })

    return {
        'patientId': patient_id,
        'eligibleTrials': eligible_trials
    }

# Main function to process all patients and trials
def match_patients_to_trials(patient_folder, trial_folder):
    # Load patient and trial data
    patient_data = load_json_files(patient_folder)
    trial_data = load_json_files(trial_folder)

    # Use ProcessPoolExecutor for parallel processing
    results = []
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(process_patient_file, patient, trial_data) for patient in patient_data]
        for future in futures:
            results.append(future.result())

    return results

results = match_patients_to_trials(patient_folder, trial_folder)

print("Results" + str(results))

# Savinf results as a JSON file
with open('results.json', 'w') as f:
  json.dump(results, f, indent=4)

# Convert results to a DataFrame for Excel export
df_results = pd.json_normalize(results, record_path=['eligibleTrials'], meta=['patientId'])
df_results.to_excel('results.xlsx', index=False)