"""Read-only Jalna v1 feasibility audit. No model fitting or clock correction.

Run from the repository root:
python -B -m scripts.audit_tasgaonkar --data-dir data/tasgaonkar/v1 --output outputs/tasgaonkar/audit.json
Output contains logger-level metadata: keep it out of version control.
"""
import argparse
import collections
import csv
from datetime import datetime
import json
import math
from pathlib import Path
import re

MISSING = {'', 'na', 'n/a', 'nan', 'reserve', 'not available', '-'}


def number(value):
    """Classify missing and nonnumeric values without silently coercing them."""
    text = value.strip()
    if text.lower() in MISSING:
        return None, 'missing'
    try:
        result = float(text)
    except ValueError:
        return None, 'invalid'
    return (result, 'valid') if math.isfinite(result) else (None, 'invalid')


def read_table(path):
    """Actual v1 CSVs require cp1252; preserve duplicate headers positionally."""
    with Path(path).open(encoding='cp1252', newline='') as stream:
        rows = list(csv.reader(stream))
    if not rows:
        raise ValueError('Empty CSV')
    header, rows = rows[0], rows[1:]
    if any(len(row) != len(header) for row in rows):
        raise ValueError('Ragged CSV; refusing ambiguous column mapping')
    return header, rows


def column(header, name):
    matches = [i for i, value in enumerate(header) if value.strip() == name]
    if len(matches) != 1:
        raise ValueError(f'Expected unique column: {name}')
    return matches[0]


def parse_timestamp(date, time, order):
    """Explicit hypotheses only; returns naive time, never assumes a timezone."""
    if order not in ('DMY', 'MDY'):
        raise ValueError('Order must be DMY or MDY')
    for separator in ('-', '/'):
        for year in ('%Y', '%y'):
            pattern = separator.join(('%d', '%m', year) if order == 'DMY' else ('%m', '%d', year))
            for clock in ('%I:%M:%S %p', '%H:%M:%S', '%H:%M'):
                try:
                    return datetime.strptime(date.strip() + ' ' + time.strip(), pattern + ' ' + clock)
                except ValueError:
                    pass
    return None


def parse_month_label(value):
    """Return month and optional year, preserving unknown labels as unknown."""
    numeric, status = number(value)
    if status == 'valid' and numeric.is_integer() and 1 <= numeric <= 12:
        return int(numeric), None
    for pattern in ('%b-%y', '%B-%y', '%b', '%B'):
        try:
            parsed = datetime.strptime(value.strip(), pattern)
            return parsed.month, parsed.year if '%y' in pattern else None
        except ValueError:
            pass
    return None, None


def timestamp_profile(rows, date_i, time_i, month_i, order, cadence_minutes):
    parsed = [parse_timestamp(row[date_i], row[time_i], order) for row in rows]
    valid = [stamp for stamp in parsed if stamp is not None]
    counts = collections.Counter(valid)
    unique = sorted(counts)
    deltas = [(right-left).total_seconds()/60 for left, right in zip(unique, unique[1:])]
    month_comparable = month_mismatches = 0
    year_comparable = year_mismatches = 0
    for row, stamp in zip(rows, parsed):
        month, status = number(row[month_i])
        if status != 'valid':
            text=row[month_i].strip()
            for pattern in ('%b-%y','%B-%y','%b','%B'):
                try:
                    month=datetime.strptime(text,pattern).month
                    status='valid'
                    break
                except ValueError:
                    pass
        if stamp is not None and status == 'valid':
            month_comparable += 1
            month_mismatches += month != stamp.month
        _, label_year = parse_month_label(row[month_i])
        if stamp is not None and label_year is not None:
            year_comparable += 1
            year_mismatches += label_year != stamp.year
    return parsed, {
        'order_hypothesis': order, 'timezone': 'unverified; naive diagnostics only',
        'parse_failures': len(rows)-len(valid), 'unique_timestamps': len(unique),
        'duplicate_rows': sum(count-1 for count in counts.values()),
        'backward_steps_in_file': sum(b<a for a,b in zip(valid,valid[1:])),
        'first': unique[0].isoformat() if unique else None,
        'last': unique[-1].isoformat() if unique else None,
        'month_comparable': month_comparable, 'month_mismatches': month_mismatches,
        'year_comparable': year_comparable, 'year_mismatches': year_mismatches,
        'cadence_minutes': cadence_minutes,
        'gaps_over_cadence': sum(delta>cadence_minutes for delta in deltas),
        'largest_gap_minutes': max(deltas, default=0),
        'noncadence_steps': sum(delta!=cadence_minutes for delta in deltas),
        'off_hour_rows': sum(bool(t.minute or t.second) for t in valid),
    }


def value_profile(rows, i):
    statuses = collections.Counter()
    values = []
    for row in rows:
        value, status = number(row[i])
        statuses[status] += 1
        if status == 'valid':
            values.append(value)
    return dict(statuses) | {'minimum': min(values, default=None), 'maximum': max(values, default=None)}


def duplicate_conflicts(rows, stamps, value_i):
    values = collections.defaultdict(set)
    for row,stamp in zip(rows,stamps):
        value,status=number(row[value_i])
        if stamp is not None and status=='valid':
            values[stamp].add(value)
    return sum(len(v)>1 for v in values.values())


def classify_duplicates(rows, stamps, value_indices):
    """Classify timestamp groups without merging, deleting or preferring rows."""
    grouped = collections.defaultdict(list)
    for row_number, (row, stamp) in enumerate(zip(rows, stamps), 2):
        if stamp is not None:
            grouped[stamp].append((row_number, row))
    counts = collections.Counter()
    details = []
    for stamp, group in sorted(grouped.items()):
        if len(group) < 2:
            continue
        payloads = [tuple(number(row[i]) for i in value_indices) for _, row in group]
        if any(status == 'invalid' for payload in payloads for _, status in payload):
            category = 'invalid_payload'
        elif any(len({payload[j][0] for payload in payloads if payload[j][1] == 'valid'}) > 1
                 for j in range(len(value_indices))):
            category = 'conflicting_measurements'
        elif len(set(payloads)) == 1:
            category = 'identical_measurements'
        else:
            category = 'complementary_missingness'
        counts[category] += 1
        details.append({'timestamp': stamp.isoformat(), 'source_rows': [n for n, _ in group],
                        'category': category,
                        'all_raw_fields_identical': len({tuple(r) for _, r in group}) == 1})
    return {'group_counts': dict(counts), 'groups': details,
            'excess_rows': sum(len(g['source_rows']) - 1 for g in details)}


def identifier_mapping(indoor_header, housing_ids):
    """Only trim boundary whitespace; RH is a channel of the same logger.

    Collisions are a hard error, never a many-to-one automatic join.
    Output contains real IDs and belongs only in ignored local storage.
    """
    normalized = [value.strip() for value in housing_ids]
    if len(set(normalized)) != len(normalized):
        raise ValueError('Housing identifier collision after whitespace normalization')
    channels = []
    for i, raw in enumerate(indoor_header):
        match = re.fullmatch(r'(\d{8})(?:\s*\(RH\))?', raw.strip())
        if match:
            channels.append({'column_index': i, 'raw_header': raw, 'logger_id': match[1],
                             'channel': 'rh' if '(RH)' in raw else 'temperature'})
    temp_ids = [c['logger_id'] for c in channels if c['channel'] == 'temperature']
    if len(set(temp_ids)) != len(temp_ids):
        raise ValueError('Duplicate temperature-channel identifier')
    temp, houses = set(temp_ids), set(normalized)
    return {'rule': 'exact string equality after boundary whitespace removal; no fuzzy matching',
            'channels': channels, 'matched_temperature_ids': sorted(temp & houses),
            'indoor_only_ids': sorted(temp - houses), 'housing_only_ids': sorted(houses - temp),
            'household_grouping_verified': False}


def weather_integrity(header, rows):
    """Compare redundant calendar fields; do not interpret reception clock as sampling."""
    date_i, month_i = column(header, 'DD/MM/YYYY'), column(header, 'Month')
    trailing_i = column(header, 'Date')
    time_columns = [i for i, h in enumerate(header) if h.strip() == 'Time']
    if len(time_columns) != 2:
        raise ValueError('Expected two positional weather Time columns')
    time_i = time_columns[0]
    stamps = [parse_timestamp(r[date_i], r[time_i], 'DMY') for r in rows]
    comparisons = {}
    for leading_order in ('DMY', 'MDY'):
        for trailing_order in ('DMY', 'MDY'):
            comparable = equal = 0
            for row in rows:
                leading = parse_timestamp(row[date_i], '00:00', leading_order)
                trailing = parse_timestamp(row[trailing_i], '00:00', trailing_order)
                if leading is not None and trailing is not None:
                    comparable += 1
                    equal += leading.date() == trailing.date()
            comparisons[f'{leading_order}_leading_{trailing_order}_trailing'] = {
                'comparable': comparable, 'equal_calendar_dates': equal,
                'unequal_calendar_dates': comparable - equal}
    mismatches, blocks = [], []
    year_comparable = year_mismatches = 0
    groups = collections.Counter()
    for row_number, (row, stamp) in enumerate(zip(rows, stamps), 2):
        month, year = parse_month_label(row[month_i])
        if stamp is None or month is None:
            continue
        if year is not None:
            year_comparable += 1
            year_mismatches += year != stamp.year
        if month != stamp.month or (year is not None and year != stamp.year):
            group = (stamp.strftime('%Y-%m'), row[month_i])
            groups[group] += 1
            detail = {'source_row': row_number, 'parsed_timestamp': stamp.isoformat(),
                      'raw_fields_by_position': {str(i): row[i] for i in
                                                (date_i, time_i, 2, month_i, time_columns[1], trailing_i,
                                                 column(header, 'ReceiveTime'), column(header, 'ReceiveDate'))}}
            mismatches.append(detail)
            if blocks and blocks[-1]['last_source_row'] == row_number - 1 and blocks[-1]['group'] == list(group):
                blocks[-1]['last_source_row'] = row_number
                blocks[-1]['count'] += 1
            else:
                blocks.append({'first_source_row': row_number, 'last_source_row': row_number,
                               'group': list(group), 'count': 1})
    reception_day_differences = collections.Counter()
    for row, stamp in zip(rows, stamps):
        receive = parse_timestamp(row[column(header, 'ReceiveDate')], '00:00', 'MDY')
        if stamp is not None and receive is not None:
            reception_day_differences[(receive.date() - stamp.date()).days] += 1
    value_indices = [column(header, label) for label in
                     ('Air temperature', 'Solar radiation', 'Humidity', 'Pressure')]
    return {'status': 'diagnostics only; timezone and interval semantics unverified',
            'field_positions': {str(i): name for i, name in enumerate(header)},
            'date_order_comparisons': comparisons,
            'receive_date_mdy_minus_leading_date_dmy_days': dict(sorted(reception_day_differences.items())),
            'year_label_comparable': year_comparable, 'year_label_disagreements': year_mismatches,
            'month_year_disagreements': len(mismatches),
            'disagreement_groups': [{'parsed_year_month': a, 'raw_month_label': b, 'rows': n}
                                    for (a, b), n in sorted(groups.items())],
            'disagreement_blocks': blocks, 'disagreement_details': mismatches,
            'duplicates': classify_duplicates(rows, stamps, value_indices),
            'duplicate_payload_fields': [header[i] for i in value_indices]}


def audit(root):
    ih, indoor = read_table(root/'Jalna Indoor Data.csv')
    wh, weather = read_table(root/'Jalna AWS Data.csv')
    hh, housing = read_table(root/'Jalna Housing Structure Data.csv')
    logger_columns = [i for i,h in enumerate(ih) if re.fullmatch(r'\d{8}',h.strip())]
    ids = [row[column(hh,'Logger ID')].strip() for row in housing]
    logger_names = {ih[i].strip() for i in logger_columns}
    numeric = {ih[i]: value_profile(indoor,i) for i in logger_columns}
    roof_i, structure_i = column(hh,'Roof'), column(hh,'Roof structure')
    roof_map = {'tin': 'metal', 'tin roof': 'metal', 'cement': 'cement', 'thatch': 'thatch', 'tatch': 'thatch'}
    roof_conflicts = sum(roof_map.get(row[roof_i].strip().lower(),row[roof_i].strip().lower()) != roof_map.get(row[structure_i].strip().lower(),row[structure_i].strip().lower()) for row in housing)
    result = {
        'site': 'Jalna', 'version': 1, 'clock_alignment_verified': False,
        'indoor_rows': len(indoor), 'weather_rows': len(weather), 'housing_rows': len(housing),
        'indoor_temperature_columns': len(logger_columns),
        'indoor_rh_columns': sum('RH' in h for h in ih),
        'duplicate_housing_logger_ids': len(ids)-len(set(ids)),
        'indoor_ids_without_housing': len(logger_names-set(ids)),
        'housing_ids_without_indoor': len(set(ids)-logger_names),
        'household_identity_verified': False,
        'roof_counts': dict(collections.Counter(row[structure_i].strip() for row in housing)),
        'roof_field_conflicts_after_spelling_normalization': roof_conflicts,
        'roof_geometry_counts': dict(collections.Counter(row[column(hh,'Roof geomety')].strip() for row in housing)),
        'evaporative_cooler_counts': dict(collections.Counter(row[column(hh,'Evaporative cooler')].strip() for row in housing)),
        'housing_missing_cells': sum(value.strip().lower() in MISSING for row in housing for value in row),
        'housing_total_cells': len(housing)*len(hh),
        'weather_fully_blank_rows': sum(not any(v.strip() for v in row) for row in weather),
        'logger_temperature_profiles': numeric,
        'weather_temperature': value_profile(weather,column(wh,'Air temperature')),
        'weather_solar': value_profile(weather,column(wh,'Solar radiation')),
        'timestamp_hypotheses': {},
    }
    # Both clocks are deliberately unresolved. Floor-to-hour overlap is diagnostic,
    # not a validated join or permission to discard duplicates / seconds.
    for order in ('DMY','MDY'):
        ip, indoor_profile = timestamp_profile(indoor,column(ih,'DD/MM/YYYY'),column(ih,'Time'),column(ih,'Month'),order,10)
        wp, weather_profile = timestamp_profile(weather,column(wh,'DD/MM/YYYY'),1,column(wh,'Month'),order,60)
        def hour(t):
            return t.replace(minute=0,second=0,microsecond=0)
        weather_hours = {hour(t) for row,t in zip(weather,wp) if t is not None and all(number(row[column(wh,c)])[1]=='valid' for c in ('Air temperature','Solar radiation'))}
        logger_overlap = {}
        for i in logger_columns:
            bins = collections.defaultdict(set)
            endpoints = set()
            for row,t in zip(indoor,ip):
                if t is not None and number(row[i])[1]=='valid':
                    bins[hour(t)].add(t)
                    if not t.minute and not t.second:
                        endpoints.add(t)
            logger_overlap[ih[i]] = {'hours_with_six_distinct_samples':sum(len(v)==6 for v in bins.values()),
                                    'six_sample_hours_with_weather_same_naive_bin':sum(len(v)==6 and k in weather_hours for k,v in bins.items()),
                                    'boundary_observations':len(endpoints)}
        result['timestamp_hypotheses'][order]={'indoor':indoor_profile,'weather':weather_profile,
                                              'valid_weather_hour_bins':len(weather_hours),
                                              'logger_overlap_diagnostics':logger_overlap}
    # Explicit mixed-order hypothesis suggested by parse success, not confirmed
    # clock semantics. No timezone conversion or model-ready dataset is produced.
    ip,_=timestamp_profile(indoor,column(ih,'DD/MM/YYYY'),column(ih,'Time'),column(ih,'Month'),'MDY',10)
    wp,_=timestamp_profile(weather,column(wh,'DD/MM/YYYY'),1,column(wh,'Month'),'DMY',60)
    whours=collections.defaultdict(list)
    for row,t in zip(weather,wp):
        if t is not None and all(number(row[column(wh,c)])[1]=='valid' for c in ('Air temperature','Solar radiation')):
            whours[t.replace(minute=0,second=0,microsecond=0)].append(row)
    ihours={t.replace(minute=0,second=0,microsecond=0) for t in ip if t is not None}
    longest=run=0
    previous=None
    for t in sorted(whours):
        run=run+1 if previous is not None and (t-previous).total_seconds()==3600 else 1
        longest=max(longest,run)
        previous=t
    result['mixed_order_diagnostic']={
        'indoor_order':'MDY', 'weather_order':'DMY',
        'status':'hypothesis only; hour flooring not a verified alignment',
        'shared_naive_hour_bins':len(ihours & set(whours)),
        'weather_duplicate_hour_bins':sum(len(v)>1 for v in whours.values()),
        'longest_consecutive_weather_hour_bins':longest,
        'indoor_loggers_with_conflicting_duplicate_temperatures':sum(duplicate_conflicts(indoor,ip,i)>0 for i in logger_columns),
        'weather_conflicting_duplicate_temperatures':duplicate_conflicts(weather,wp,column(wh,'Air temperature')),
        'weather_zero_temperature_rows':sum(number(row[column(wh,'Air temperature')])[0]==0 for row in weather),
    }
    result['integrity'] = {
        'weather': weather_integrity(wh, weather),
        'mapping': identifier_mapping(ih, [row[column(hh, 'Logger ID')] for row in housing]),
        'indoor_duplicates': classify_duplicates(indoor, ip, logger_columns),
        'indoor_duplicate_payload': 'temperature channels only; RH excluded',
    }
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=audit(args.data_dir)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Audit written locally. Clock and household identity remain unverified; do not commit logger-level output.')


if __name__=='__main__':
    main()
