"""Retrieving and parsing data from the Harvard Caselaw Access Project (CAP)."""

import re

import requests

from bs4 import BeautifulSoup


def get_case_json_by_id(case_id):
    return requests.get(f"https://api.case.law/v1/cases/{case_id}?full_case=true&body_format=html").json()


def get_case_by_docket_number(docket_number):
    return requests.get(f"https://api.case.law/v1/cases?court_id=9009&docket_number={docket_number}").json()


def get_longest_casebody_in_list(json_response):
    max_word_count = 0
    case_id_to_return = ""
    for case in json_response["results"]:
        word_count = case["analysis"]["word_count"]
        if word_count > max_word_count:
            max_word_count = word_count
            case_id_to_return = case["id"]
    return case_id_to_return


def parse_opinion_html(opinion_html):
    soup = BeautifulSoup(opinion_html, "html.parser")
    if soup.contents[0].name == "article":
        if len(soup) > 1:
            print(soup)
        assert len(soup) == 1
        contents = soup.contents[0].contents
    else:
        contents = soup.contents
    # Soup should now be an alternating list of paragraphs and newlines; remove newlines
    contents = [x for x in contents if x != "\n"]
    paragraphs = []
    for paragraph in contents:
        if paragraph.name not in ["p", "blockquote"]:
            if paragraph.name == "aside":
                continue
            else:
                print("error", paragraph.name)
                print(paragraph)
                print(contents)
        full_string = ""
        for piece in paragraph.contents:
            if isinstance(piece, str):
                if re.fullmatch("[\n\\s]*", piece):
                    continue
                else:
                    piece.replace("\n", "")
                    full_string += re.sub("\\s+", " ", piece).lstrip()
            elif piece.name in ["em", "strong", "s", "sup"]:
                piece.text.replace("\n", "")
                full_string += re.sub("\\s+", " ", piece.text).lstrip()
            elif piece.name == "a" and "footnotemark" in piece.attrs["class"]:
                continue
            elif piece.name == "a" and "page-label" in piece.attrs["class"]:
                continue
            elif piece.name == "aside":
                continue
            elif piece.name == "a" and "citation" in piece.attrs["class"]:
                piece.text.replace("\n", "")
                cleaned_text = re.sub("\\s+", " ", piece.text).lstrip()
                full_string += cleaned_text
            else:
                print(piece.name, piece.attrs)
                print(piece.text)
                print(paragraph)
                raise Exception
        paragraphs.append(full_string)
    return paragraphs


def get_docket_number_from_id(id):
    """Returns the docket number for a Harvard CAP case ID."""
    response = get_case_json_by_id(id)
    docket_number = response["docket_number"][4:]
    docket_number = docket_number.strip()
    docket_number = docket_number[:2] + "_" + docket_number[3:]

    # Some docket numbers contain multiple docket numbers chained together with semicolons
    # If that's the case, just take the first docket number
    semicolon_location = docket_number.find(";")
    if semicolon_location != -1:
        docket_number = docket_number[:semicolon_location]
    return docket_number
