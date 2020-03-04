"""
This is intended to be run on the output of com.h1insights.pipeline.reports.BuildExternalPersonMaps
where the output was written to:

    s3://az-us-commercial-h1-staging/spark-json/raw/{project_name}/

running:

    python parse_and_push_az_json.py {project_name}

will read those files and write to:

   s3://az-us-commercial-h1-staging/spark-json/processed/{project_name}/

Read and write locations are configurable by changing the global variables BUCKET and PREFIX.
"""

import json
from json.decoder import JSONDecodeError
import boto3
import codecs
import sys

PAYMENT_KEYS_DEFAULTS = [
    ("amount", None),
    ("associated_drug", None),
    ("id", None),
    ("nature_of_payment", None),
    ("payer_company", None),
    ("payer_country", None),
    ("payment_date", None),
    ("payment_form", None),
]

PUBLICATION_KEYS_DEFAULTS = [
    ("abstract", None),
    ("altmetrics", None),
    ("citation_count", None),
    ("collaborators", []),
    ("date_published", None),
    ("doi", None),
    ("id", None),
    ("journal", None),
    ("keywords", None),
    ("pmid", None),
    ("publication_types", None),
    ("publisher", None),
    ("title", None),
    ("url", None),
]

CONGRESS_KEYS_DEFAULTS = [
    ("organizer_name", None),
    ("presented_date", None),
    ("session_type", None),
    ("start_date", None),
    ("title", None),
    ("type", None),
]

AFFILIATION_KEYS_DEFAULTS = [
    ("city", None),
    ("id", None),
    ("name", None),
    ("state", None),
    ("street1", None),
    ("street2", None),
    ("street3", None),
    ("type", None),
    ("zip", None),
]

CLINICAL_TRIAL_KEYS_DEFAULTS = [
    ("brief_title", None),
    ("completion_date", None),
    ("eligibility_criteria", None),
    ("enrollment", None),
    ("id", None),
    ("last_update_posted", None),
    ("last_update_submitted", None),
    ("official_title", None),
    ("phase", None),
    ("primary_completion_date", None),
    ("start_date", None),
    ("status", None),
    ("summary", None),
    ("type", None),
    ("url", None),
]

PEOPLE_KEYS_DEFAULTS = [
    ("affiliations", None),
    ("clinical_trials", None),
    ("congresses", None),
    ("designations", None),
    ("emails", None),
    ("fax", None),
    ("first_name", None),
    ("h_index", None),
    ("id", None),
    ("last_name", None),
    ("last_updated", None),
    ("middle_name", None),
    ("npi", None),
    ("payments", None),
    ("phone", None),
    ("publications", None),
    ("specialty", None),
    ("tags", None),
    ("title", None),
    ("type", None),
    ("url", None),
    ("works", None),
    ("affiliations", []),
    ("clinical_trials", []),
    ("congresses", []),
    ("payments", []),
    ("publications", []),
]

CLIENT = boto3.client('s3')


def replace_missing_keys_with_none(d, parent_key, expected_child_keys):
    records = d[parent_key]
    if records:
        for record in records:
            for expected_key in expected_child_keys:
                if expected_key[0] not in record.keys():
                    record[expected_key[0]] = expected_key[1]


def parse_json_input_stream(input_file, process_callable: callable, **kwargs):
    """
    This function streams the body of a potentially very large file with
    many newline delimited json objects inside of it from S3 and calls an a arbitrary
    function on each json object.

    This allows us to process files on S3 that may be many gigabytes using minimal
    system memory since only one json object is in memory at a time.

    :param input_file:
    :param process_callable:
    :return:
    """
    body = input_file['Body']
    reader = codecs.getreader('utf-8')(body)
    line = reader.readline()

    # NOTE:
    # The reason for this block is that `readline` reads until it sees a newline character
    # but many of the titles and abstracts of publications have newline characters in them.
    # Trying to parse invalid json raises a JSONDecodeError. Since we know that all of the json
    # objects are valid, we can catch these errors knowing that we are in the middle of a valid object.
    # We can call `readline` again and append it to the part of the object we already had and try again.
    # Eventually we will reach the newline at the end of the JSON object and read in the valid json.

    while line:
        try:
            deserialized_json_body = json.loads(line)
            line = reader.readline()
            process_callable(deserialized_json_body, **kwargs)
        except JSONDecodeError:
            line += reader.readline()


def process_object(obj, **kwargs):
    """
    This does the following to a json object to make it look the same as the API responses
    that AstraZeneca is used to:

        - Spark omits keys when there is no value, this puts all keys back in with a default value of None or [].
        - It takes the json object and wraps it in an array where it is the only element
        - It pretty prints it with an indent of 2
        - It uploads to S3 to a folder where each file is named based on the person id of the object inside

    :param obj: A person object
    :return:
    """
    bucket_name = kwargs["bucket_name"]
    project_name = kwargs["project_name"]
    date = kwargs["date"]
    for expected_key in PEOPLE_KEYS_DEFAULTS:
        if expected_key[0] not in obj.keys():
            obj[expected_key[0]] = expected_key[1]
    replace_keys_list = [
        ("payments", PAYMENT_KEYS_DEFAULTS),
        ("publications", PUBLICATION_KEYS_DEFAULTS),
        ("congresses", CONGRESS_KEYS_DEFAULTS),
        ("affiliations", AFFILIATION_KEYS_DEFAULTS),
        ("clinical_trials", CLINICAL_TRIAL_KEYS_DEFAULTS)
    ]
    for key_replace in replace_keys_list:
        replace_missing_keys_with_none(obj, key_replace[0], key_replace[1])
    person_id = obj["id"]
    key = f"{project_name}/{date}/JSON/processed/{person_id}.json"
    CLIENT.put_object(Body=f'{json.dumps([obj], indent=2)}\n', Bucket=bucket_name, Key=key)


def parse_and_push(bucket_name, date, project_name):
    # lstrip in case we pass in an empty project name
    # since AZ wants project 9 to have no prefix on the bucket
    # this differes from project 37 which they want prefixed with 'eu-oncology'
    #
    # Q: Why don't we write it then move it afterwards, instead of this hacky way?
    # A: It is expensive and time-consuming to move all of the files that way since
    #    AZ expects the files to be 1 json file per KOL and there are very many of them
    prefix = f"{project_name}/{date}/JSON/raw/".lstrip('/')
    keys = [obj["Key"] for obj in CLIENT.list_objects(Bucket=bucket_name, Prefix=prefix)["Contents"]]
    for key in keys:
        if key[-4:] == "json":
            input_object = CLIENT.get_object(Bucket=bucket_name, Key=key)
            print(f"parsing {key}")
            parse_json_input_stream(input_object, process_object, project_name=project_name, bucket_name=bucket_name, date=date)
