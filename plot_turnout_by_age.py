#!/usr/bin/env python3

import csv
from typing import Dict, List
from matplotlib import pyplot as plt
import json

DATA_FILE = './data/voters.txt'
KEY_FILE = 'key.json'

ELECTION_YEAR = 2020 # choose presidential election years from 2000 - 2020
ELECTION_DAY = {
    2020: '03',
    2016: '08',
    2012: '06',
    2008: '04',
    2004: '02',
    2000: '07'
}
ELECTION_DATE = f'11/{ELECTION_DAY[ELECTION_YEAR]}/{ELECTION_YEAR}'
ELECTION_TAG = f'{ELECTION_DATE} General'

MINIMUM_REGISTERED_VOTERS = 50
TOTAL_COUNTIES = None

KEY_FILE = './key.json' # file that contains the 'conversion key' that will allow you to predict votes cast in each county.

def str_to_int(date: str) -> int:
    """Converts date in form MM/DD/YYYY to and integer of form YYYYMMDD. """
    tokens = date.strip().split('/')
    return int(f'{tokens[2]}{tokens[0]}{tokens[1]}')

def get_age(start_date: str, end_date: str) -> int:
    """Returns integer age given dates in form MM/DD/YYYY. """
    start = str_to_int(start_date)
    end = str_to_int(end_date)
    diff = end - start
    if diff < 0:
        return diff / 10000.0
    else:
        return int(diff / 10000)

def meets_deadline(date: str, deadline: str) -> bool:
    date_int = str_to_int(date)
    deadline_int = str_to_int(deadline)
    meets = date_int <= deadline_int
    return meets

def get_voters() -> Dict[str, List[any]]:
    counties = set()
    total_votes = 0
    rows = 0
    with open(DATA_FILE, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            header = row
            break
        county_index = header.index('County')
        dob_index = header.index('Birthdate')
        reg_index = header.index('Registration Date')
        voters = {}
        for row in reader:
            rows += 1
            r = row[reg_index]
            if not r:
                print(f'skipping no registration date: {row}')
                continue
            if not meets_deadline(r, ELECTION_DATE):
                continue
            c = row[county_index]
            counties.add(c)
            if c not in voters:
                voters[c] = []
            b = row[dob_index]
            if not b:
                print(f'skipping no birth date: {row}')
                continue
            age = get_age(b, ELECTION_DATE)
            if age < 18:
                continue
            if age > 110:
                print(f'skipping unreasonable age: {age}')
                continue
            voted = ELECTION_TAG in row
            if voted:
                total_votes += 1
            voters[c].append({
                'age': age,
                'voted': voted,
            })

        global TOTAL_COUNTIES 
        TOTAL_COUNTIES = len(counties)
        total_voters = sum([len(voters[x]) for x in voters])
        print(f'processed {rows} rows.')
        print(f'processed {total_voters} voters in {len(counties)} counties.')
        print(f'overall turnout: {total_votes / total_voters} (total votes: {total_votes})')
        return voters

def organize_by_age(voters: List[any]) -> Dict[int, List[any]]:
    ages = {}
    for v in voters:
        a = v['age']
        if a not in ages:
            ages[a] = []
        ages[a].append(v)
    return ages

def compute_turnout(by_age: Dict[int, List[any]]):
    total_votes = 0
    total_voters = 0
    turnout = {}
    for a in by_age:
        v = by_age[a]
        voters = len(v)
        if voters < MINIMUM_REGISTERED_VOTERS:
            continue
        votes = sum([1 for x in v if x['voted']])
        turnout[a] = votes / voters
        total_votes += votes
        total_voters += voters
    print(f'\tvoters: {total_voters}')
    if total_voters == 0:
        return
    overall_turnout = total_votes / total_voters
    for a in turnout:
        turnout[a] /= overall_turnout
    return turnout

def plot_turnout(turnout: Dict[int, int], style = '-'):
    tt = list(turnout.items())
    tt.sort()
    plt.plot([x[0] for x in tt], [x[1] for x in tt], style)


if __name__ == '__main__':
    voters = get_voters()

    plotted = 0
    key = {}
    for county in voters:
        print(f'plotting county: {county}')
        vv = voters[county]
        by_age = organize_by_age(vv)
        normalized_turnout = compute_turnout(by_age)
        if normalized_turnout:
            plot_turnout(normalized_turnout)
            plotted += 1
            for age in normalized_turnout:
                if age not in key:
                    key[age] = []
                key[age].append(normalized_turnout[age])
    for age in key:
        key[age] = sum(key[age]) / len(key[age])

    plot_turnout(key, 'k:')
    json.dump(key, open(KEY_FILE, 'w'))

    print(f'plotted {plotted} counties.')
    plt.xlabel(f'Age (ages with less than {MINIMUM_REGISTERED_VOTERS} registered voters are hidden)')
    plt.ylabel('Normalized voter turnout (votes / registered voters / overall turnout fraction)')
    plt.title(f'{ELECTION_YEAR} Missouri Voter Turnout vs. Age ({plotted} of {TOTAL_COUNTIES} counties; each line = 1 county)')
    plt.show()



